from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

# Exponential backoff schedule (seconds) for retryable jobs; index == attempts.
JOB_BACKOFF_SECONDS = [0, 30, 120, 600, 1800, 7200]
DEFAULT_MAX_ATTEMPTS = 6


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _trunc(value: Any, limit: int = 120) -> str | None:
    if value is None:
        return None
    return str(value)[:limit]


class Store:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        # sqlite's busy timeout performs lock acquisition retries inside the
        # driver. A contextmanager cannot replay the caller's transaction body
        # after ``yield``, so retrying here would be both misleading and unsafe.
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            # Stripe webhooks are acknowledged only after the paid order and its
            # work item commit. FULL is intentional: NORMAL-mode WAL can lose the
            # last acknowledged transaction on host/power failure.
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS kv (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TEXT
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 6,
                    dedupe_key TEXT,
                    next_attempt_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_error TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, created_at);

                -- Durable record of every Stripe event we accept, so re-delivery
                -- of the same event is idempotent even across restarts.
                CREATE TABLE IF NOT EXISTS stripe_events (
                    event_id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    payload TEXT,
                    status TEXT NOT NULL DEFAULT 'received'
                );

                -- One row per paid Checkout Session. payment_intent + PR linkage
                -- powers the refund guarantee.
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    payment_intent TEXT,
                    sku TEXT,
                    email TEXT,
                    price_id TEXT,
                    amount INTEGER,
                    currency TEXT,
                    livemode INTEGER,
                    status TEXT NOT NULL DEFAULT 'paid',
                    repo TEXT,
                    pr_url TEXT,
                    pr_number INTEGER,
                    deadline TEXT,
                    refunded INTEGER NOT NULL DEFAULT 0,
                    refund_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_purchases_pi ON purchases(payment_intent);
                CREATE INDEX IF NOT EXISTS idx_purchases_repo_pr ON purchases(repo, pr_number);

                -- First-party funnel analytics. No third-party tracker; this is
                -- the source of truth for source/utm/kit/deadline/sku/outcome so
                -- conversion drop-offs are visible and attributable.
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    name TEXT NOT NULL,
                    source TEXT,
                    utm_source TEXT,
                    utm_medium TEXT,
                    utm_campaign TEXT,
                    kit TEXT,
                    deadline TEXT,
                    sku TEXT,
                    path TEXT,
                    meta TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
                CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);

                CREATE TABLE IF NOT EXISTS rate_limits (
                    key TEXT PRIMARY KEY,
                    window_start INTEGER NOT NULL,
                    count INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS checkout_claims (
                    upload_id TEXT PRIMARY KEY,
                    source_key TEXT NOT NULL,
                    state TEXT NOT NULL,
                    session_url TEXT,
                    session_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS upload_reservations (
                    upload_id TEXT PRIMARY KEY,
                    declared_bytes INTEGER NOT NULL,
                    expires_at TEXT NOT NULL
                );

                -- Generic inbound lead capture (studio microsites + any product).
                -- Replaces FormSubmit; this row is the durable guarantee a lead is
                -- never silently dropped, independent of email delivery.
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    email TEXT NOT NULL,
                    name TEXT,
                    product TEXT,
                    source TEXT,
                    fields TEXT,
                    notified INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_leads_ts ON leads(ts);
                CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
                """
            )
            # Add columns to pre-existing `jobs` tables BEFORE creating any index
            # that references them (an old prod DB has jobs without dedupe_key).
            self._migrate_jobs_columns(conn)
            # An old prod `leads` table (created before notify-hardening) lacks `notified`.
            self._migrate_leads_columns(conn)
            self._redact_stripe_event_payloads(conn)
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_dedupe ON jobs(dedupe_key) "
                "WHERE dedupe_key IS NOT NULL"
            )

    def _migrate_jobs_columns(self, conn: sqlite3.Connection) -> None:
        # Older databases created before durability work may miss columns.
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
        for column, ddl in (
            ("max_attempts", "ALTER TABLE jobs ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 6"),
            ("dedupe_key", "ALTER TABLE jobs ADD COLUMN dedupe_key TEXT"),
            ("next_attempt_at", "ALTER TABLE jobs ADD COLUMN next_attempt_at TEXT"),
        ):
            if column not in existing:
                conn.execute(ddl)

    def _migrate_leads_columns(self, conn: sqlite3.Connection) -> None:
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(leads)")}
        if "notified" not in existing:
            conn.execute("ALTER TABLE leads ADD COLUMN notified INTEGER NOT NULL DEFAULT 0")
            # Pre-existing leads predate notify-hardening — treat them as already handled
            # so the first-boot re-send sweep does NOT spam duplicate alerts for old rows.
            # New inserts still start at notified=0 (the column default) and earn the flag
            # only on a confirmed send.
            conn.execute("UPDATE leads SET notified = 1")

    def _redact_stripe_event_payloads(self, conn: sqlite3.Connection) -> None:
        """Remove customer/billing data retained by older deployments.

        Event replay comes from Stripe, not this table. Only the object id is
        useful for incident correlation, so indefinite full-event retention is
        unnecessary and conflicts with data-minimization promises.
        """
        rows = conn.execute(
            "SELECT event_id, payload FROM stripe_events WHERE payload IS NOT NULL"
        ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["payload"])
            except (TypeError, json.JSONDecodeError):
                payload = {}
            object_id = None
            if isinstance(payload, dict):
                if set(payload) == {"object_id"}:
                    continue
                obj = (payload.get("data") or {}).get("object") or {}
                if isinstance(obj, dict) and obj.get("id"):
                    object_id = str(obj["id"])[:120]
            summary = {"object_id": object_id} if object_id else {}
            conn.execute(
                "UPDATE stripe_events SET payload = ? WHERE event_id = ?",
                (json.dumps(summary, separators=(",", ":")), row["event_id"]),
            )

    # ---- kv ---------------------------------------------------------------- #

    def put_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = None
        if ttl_seconds:
            expires_at = (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv(key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expires_at),
            )

    def get_json(self, key: str) -> Any | None:
        with self.connect() as conn:
            row = conn.execute("SELECT value, expires_at FROM kv WHERE key = ?", (key,)).fetchone()
            if not row:
                return None
            if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.now(UTC):
                conn.execute("DELETE FROM kv WHERE key = ?", (key,))
                return None
            return json.loads(row["value"])

    def delete(self, key: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM kv WHERE key = ?", (key,))

    def purge_expired_kv(self) -> int:
        """Delete expired KV rows without waiting for a later point read."""
        with self.connect() as conn:
            cur = conn.execute(
                "DELETE FROM kv WHERE expires_at IS NOT NULL AND expires_at < ?", (_now(),)
            )
            return int(cur.rowcount)

    def allow_rate(self, key: str, *, limit: int, window_seconds: int) -> bool:
        """Atomically consume one allowance in a window anchored at first use.

        Anchoring each key's window avoids the double-burst available at an
        epoch-aligned boundary (for example, eight requests at ``:59`` followed
        by eight more at ``:00``).
        """
        now = int(time.time())
        with self.connect() as conn:
            row = conn.execute(
                """
                INSERT INTO rate_limits(key, window_start, count) VALUES (?, ?, 1)
                ON CONFLICT(key) DO UPDATE SET
                    window_start = CASE
                        WHEN excluded.window_start - rate_limits.window_start >= ?
                        THEN excluded.window_start ELSE rate_limits.window_start END,
                    count = CASE
                        WHEN excluded.window_start - rate_limits.window_start >= ?
                        THEN 1 ELSE rate_limits.count + 1 END
                RETURNING count
                """,
                (key, now, window_seconds, window_seconds),
            ).fetchone()
            return bool(row and int(row["count"]) <= limit)

    def reserve_checkout(self, upload_id: str, source_key: str) -> dict[str, Any]:
        """Atomically reserve one Checkout Session for an uploaded artifact."""
        now = _now()
        stale = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM checkout_claims WHERE upload_id = ?", (upload_id,)
            ).fetchone()
            if row and row["state"] == "ready":
                return {"owner": False, **dict(row)}
            if row and row["state"] == "creating" and row["updated_at"] >= stale:
                return {"owner": False, **dict(row)}
            if row:
                conn.execute(
                    "UPDATE checkout_claims SET source_key=?, state='creating', "
                    "session_url=NULL, session_id=NULL, updated_at=? WHERE upload_id=?",
                    (source_key, now, upload_id),
                )
            else:
                conn.execute(
                    "INSERT INTO checkout_claims(upload_id, source_key, state, created_at, updated_at) "
                    "VALUES (?, ?, 'creating', ?, ?)",
                    (upload_id, source_key, now, now),
                )
            return {
                "owner": True,
                "upload_id": upload_id,
                "source_key": source_key,
                "state": "creating",
                "session_url": None,
                "session_id": None,
                "created_at": now,
                "updated_at": now,
            }

    def reserve_upload(
        self, upload_id: str, declared_bytes: int, *, ttl_seconds: int, max_total_bytes: int
    ) -> bool:
        """Atomically reserve bounded disk capacity before issuing an upload URL."""
        now = datetime.now(UTC)
        expires = (now + timedelta(seconds=ttl_seconds)).isoformat()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM upload_reservations WHERE expires_at < ?", (now.isoformat(),))
            total = int(
                conn.execute(
                    "SELECT COALESCE(SUM(declared_bytes), 0) AS n FROM upload_reservations"
                ).fetchone()["n"]
            )
            if total + declared_bytes > max_total_bytes:
                return False
            conn.execute(
                "INSERT INTO upload_reservations(upload_id, declared_bytes, expires_at) "
                "VALUES (?, ?, ?)",
                (upload_id, declared_bytes, expires),
            )
            return True

    def extend_upload_reservation(self, upload_id: str, ttl_seconds: int) -> None:
        expires = (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat()
        with self.connect() as conn:
            conn.execute(
                "UPDATE upload_reservations SET expires_at=? WHERE upload_id=?",
                (expires, upload_id),
            )

    def release_upload(self, upload_id: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM upload_reservations WHERE upload_id=?", (upload_id,))

    def complete_checkout(
        self, upload_id: str, *, session_url: str, session_id: str | None
    ) -> None:
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE checkout_claims SET state='ready', session_url=?, session_id=?, "
                "updated_at=? WHERE upload_id=? AND state='creating'",
                (session_url, session_id, _now(), upload_id),
            )
            if cur.rowcount != 1:
                raise RuntimeError("checkout reservation was lost")

    def release_checkout(self, upload_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM checkout_claims WHERE upload_id=? AND state='creating'",
                (upload_id,),
            )

    # ---- stripe events (idempotency) -------------------------------------- #

    def record_stripe_event(self, event_id: str, event_type: str, payload: Any) -> bool:
        """Claim a Stripe event for processing.

        Successfully processed/rejected events remain deduplicated. An event
        marked ``error`` is claimable again so Stripe's retry can recover from a
        transient API/database/process failure instead of being poisoned forever.
        """
        now = datetime.now(UTC)
        lease_cutoff = (now - timedelta(minutes=5)).isoformat()
        received_at = now.isoformat()
        object_id = None
        if isinstance(payload, dict):
            obj = (payload.get("data") or {}).get("object") or {}
            if isinstance(obj, dict) and obj.get("id"):
                object_id = str(obj["id"])[:120]
        summary = json.dumps({"object_id": object_id} if object_id else {}, separators=(",", ":"))
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO stripe_events(event_id, type, received_at, payload) "
                "VALUES (?, ?, ?, ?)",
                (event_id, event_type, received_at, summary),
            )
            if cur.rowcount > 0:
                return True
            retry = conn.execute(
                "UPDATE stripe_events SET status = 'received', received_at = ?, payload = ? "
                "WHERE event_id = ? AND (status = 'error' OR "
                "(status = 'received' AND received_at < ?))",
                (received_at, summary, event_id, lease_cutoff),
            )
            return retry.rowcount > 0

    def stripe_event_status(self, event_id: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status FROM stripe_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            return str(row["status"]) if row else None

    def mark_stripe_event(self, event_id: str, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE stripe_events SET status = ? WHERE event_id = ?",
                (status, event_id),
            )

    # ---- purchases -------------------------------------------------------- #

    def record_purchase(
        self,
        *,
        session_id: str,
        payment_intent: str | None,
        sku: str | None,
        email: str | None,
        price_id: str | None,
        amount: int | None,
        currency: str | None,
        livemode: bool | None,
        repo: str | None = None,
        deadline: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Insert a purchase row. Returns True if newly inserted, False if the
        session was already recorded (idempotent)."""
        now = _now()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO purchases(
                    session_id, payment_intent, sku, email, price_id, amount,
                    currency, livemode, status, repo, deadline, created_at,
                    updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    payment_intent,
                    sku,
                    email,
                    price_id,
                    amount,
                    currency,
                    1 if livemode else 0,
                    repo,
                    deadline,
                    now,
                    now,
                    json.dumps(metadata or {}),
                ),
            )
            return cur.rowcount > 0

    def record_purchase_with_job(
        self,
        *,
        session_id: str,
        payment_intent: str | None,
        sku: str | None,
        email: str | None,
        price_id: str | None,
        amount: int | None,
        currency: str | None,
        livemode: bool | None,
        metadata: dict[str, Any],
        job_type: str,
        job_payload: dict[str, Any],
        dedupe_key: str,
        job_status: str = "pending",
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> tuple[bool, int, bool]:
        """Atomically persist a paid order and its fulfillment/refund work.

        A process crash can therefore never leave a committed charge row without
        a corresponding durable job. The unique session and dedupe keys make a
        replay safe.
        """
        now = _now()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if payment_intent:
                existing_payment = conn.execute(
                    "SELECT id, session_id FROM purchases WHERE payment_intent = ? LIMIT 1",
                    (payment_intent,),
                ).fetchone()
                if existing_payment and existing_payment["session_id"] != session_id:
                    return False, 0, False
            purchase = conn.execute(
                """
                INSERT OR IGNORE INTO purchases(
                    session_id, payment_intent, sku, email, price_id, amount,
                    currency, livemode, status, repo, deadline, created_at,
                    updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    payment_intent,
                    sku,
                    email,
                    price_id,
                    amount,
                    currency,
                    1 if livemode else 0,
                    metadata.get("repo"),
                    metadata.get("deadline"),
                    now,
                    now,
                    json.dumps(metadata),
                ),
            )
            existing = conn.execute(
                "SELECT id FROM jobs WHERE dedupe_key = ?", (dedupe_key,)
            ).fetchone()
            job_created = False
            if existing:
                job_id = int(existing["id"])
            else:
                job = conn.execute(
                    """
                    INSERT INTO jobs(type, payload, status, attempts, max_attempts,
                                     dedupe_key, next_attempt_at, created_at, updated_at)
                    VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_type,
                        json.dumps(job_payload),
                        job_status,
                        max_attempts,
                        dedupe_key,
                        now if job_status == "pending" else None,
                        now,
                        now,
                    ),
                )
                job_id = int(job.lastrowid)
                job_created = True
            return purchase.rowcount > 0, job_id, job_created

    def link_purchase_pr(self, session_id: str, *, pr_url: str, pr_number: int, repo: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE purchases SET pr_url = ?, pr_number = ?, repo = ?, updated_at = ? "
                "WHERE session_id = ?",
                (pr_url, pr_number, repo, _now(), session_id),
            )

    def get_purchase_by_session(self, session_id: str) -> dict[str, Any] | None:
        return self._purchase_query("SELECT * FROM purchases WHERE session_id = ?", (session_id,))

    def get_purchase_by_pr(self, repo: str, pr_number: int) -> dict[str, Any] | None:
        return self._purchase_query(
            "SELECT * FROM purchases WHERE repo = ? AND pr_number = ?", (repo, pr_number)
        )

    def get_purchase_by_payment_intent(self, payment_intent: str) -> dict[str, Any] | None:
        return self._purchase_query(
            "SELECT * FROM purchases WHERE payment_intent = ?", (payment_intent,)
        )

    def mark_refund_failed(self, session_id: str, refund_id: str | None) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE purchases SET status='refund_failed', refund_id=COALESCE(?, refund_id), "
                "updated_at=? WHERE session_id=? AND refunded=0",
                (refund_id, _now(), session_id),
            )

    def mark_refund_pending(self, session_id: str, refund_id: str) -> bool:
        """Bind an order to the exact Stripe refund created for it."""
        if not refund_id:
            return False
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE purchases SET status='refund_pending', refund_id=?, updated_at=? "
                "WHERE session_id=? AND refunded=0 "
                "AND (refund_id IS NULL OR refund_id='' OR refund_id=?)",
                (refund_id, _now(), session_id, refund_id),
            )
            return cur.rowcount > 0

    def _purchase_query(self, sql: str, params: tuple) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    # ---- funnel analytics ------------------------------------------------- #

    def record_event(self, name: str, fields: dict[str, Any]) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO events(ts, name, source, utm_source, utm_medium,
                                   utm_campaign, kit, deadline, sku, path, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _now(),
                    name[:64],
                    _trunc(fields.get("source")),
                    _trunc(fields.get("utm_source")),
                    _trunc(fields.get("utm_medium")),
                    _trunc(fields.get("utm_campaign")),
                    _trunc(fields.get("kit")),
                    _trunc(fields.get("deadline")),
                    _trunc(fields.get("sku")),
                    _trunc(fields.get("path"), 256),
                    json.dumps(fields.get("meta") or {})[:2000],
                ),
            )
            return int(cur.lastrowid)

    # ---- leads ------------------------------------------------------------ #

    def record_lead(
        self,
        *,
        email: str,
        name: str | None = None,
        product: str | None = None,
        source: str | None = None,
        fields: dict[str, Any] | None = None,
    ) -> int:
        """Durably record an inbound lead. The returned id confirms capture even
        if the notification email later fails — this row is the guarantee."""
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO leads(ts, email, name, product, source, fields) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    _now(),
                    str(email)[:200],
                    _trunc(name, 200),
                    _trunc(product),
                    _trunc(source, 200),
                    json.dumps(fields or {})[:4000],
                ),
            )
            return int(cur.lastrowid)

    def recent_leads(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def mark_lead_notified(self, lead_id: int) -> None:
        """Flip a lead to notified=1 only after a confirmed owner alert send."""
        with self.connect() as conn:
            conn.execute("UPDATE leads SET notified = 1 WHERE id = ?", (int(lead_id),))

    def unnotified_leads(self, limit: int = 100) -> list[dict[str, Any]]:
        """Durably-captured leads the owner was NOT yet successfully alerted about —
        the recovery queue for the periodic re-send sweep (self-heals email outages)."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM leads WHERE notified = 0 ORDER BY id ASC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def count_unnotified(self) -> int:
        with self.connect() as conn:
            return int(
                conn.execute("SELECT COUNT(*) AS n FROM leads WHERE notified = 0").fetchone()["n"]
            )

    def event_counts(self, since_days: int = 7) -> dict[str, int]:
        cutoff = (datetime.now(UTC) - timedelta(days=since_days)).isoformat()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT name, COUNT(*) AS n FROM events WHERE ts >= ? GROUP BY name",
                (cutoff,),
            ).fetchall()
            return {row["name"]: int(row["n"]) for row in rows}

    def purge_telemetry(self, *, event_cutoff: str, rate_cutoff: int) -> dict[str, int]:
        """Bound telemetry retention and discard expired abuse-limit buckets.

        Funnel events intentionally contain no visitor identifier, but they still
        describe site activity and must not grow forever. Rate-limit keys are
        server-secret-keyed pseudonyms; two days exceeds every configured window
        while keeping active limits intact.
        """
        with self.connect() as conn:
            events = conn.execute("DELETE FROM events WHERE ts < ?", (event_cutoff,))
            limits = conn.execute(
                "DELETE FROM rate_limits WHERE window_start < ?", (int(rate_cutoff),)
            )
            return {
                "events": int(events.rowcount),
                "rate_limits": int(limits.rowcount),
            }

    def commerce_counts(self, since_days: int = 7) -> dict[str, int]:
        """Return public-safe throughput plus lifetime unresolved money states."""
        cutoff = (datetime.now(UTC) - timedelta(days=since_days)).isoformat()
        with self.connect() as conn:
            purchases = conn.execute(
                "SELECT COUNT(*) AS paid, "
                "SUM(CASE WHEN refunded = 1 THEN 1 ELSE 0 END) AS refunded "
                "FROM purchases WHERE created_at >= ?",
                (cutoff,),
            ).fetchone()
            jobs = conn.execute(
                "SELECT "
                "SUM(CASE WHEN status = 'completed' AND type NOT IN "
                "('refund_payment','cancel_subscription','refund_review','refund_notice') THEN 1 ELSE 0 END) AS fulfilled, "
                "SUM(CASE WHEN status = 'dead_letter' AND type NOT IN "
                "('refund_payment','cancel_subscription','refund_review','refund_notice') THEN 1 ELSE 0 END) AS failed "
                "FROM jobs WHERE created_at >= ?",
                (cutoff,),
            ).fetchone()
            unresolved = conn.execute(
                "SELECT "
                "SUM(CASE WHEN type IN ('refund_payment','cancel_subscription') "
                "AND status IN ('pending','running') THEN 1 ELSE 0 END) AS refunds_pending, "
                "SUM(CASE WHEN (type = 'refund_payment' AND status = 'dead_letter') "
                "OR (type = 'cancel_subscription' AND status = 'dead_letter') "
                "OR (type = 'refund_review' AND status = 'requires_owner') THEN 1 ELSE 0 END) AS refunds_failed, "
                "SUM(CASE WHEN type = 'audit_pdf' AND ("
                "(status IN ('pending','running') AND attempts > 0) "
                "OR status IN ('dead_letter','requires_runner')) THEN 1 ELSE 0 END) "
                "AS fulfillment_at_risk "
                "FROM jobs",
            ).fetchone()
        return {
            "paid": int(purchases["paid"] or 0),
            "refunded": int(purchases["refunded"] or 0),
            "fulfilled": int(jobs["fulfilled"] or 0),
            "failed": int(jobs["failed"] or 0),
            "refunds_pending": int(unresolved["refunds_pending"] or 0),
            "refunds_failed": int(unresolved["refunds_failed"] or 0),
            "fulfillment_at_risk": int(unresolved["fulfillment_at_risk"] or 0),
        }

    def resolve_refund_jobs(self, session_id: str, *, include_cancellation: bool = False) -> int:
        """Resolve only refund jobs whose decoded payload binds to session_id."""
        resolved = 0
        with self.connect() as conn:
            job_types = ["refund_payment", "refund_review"]
            if include_cancellation:
                job_types.append("cancel_subscription")
            placeholders = ",".join("?" for _ in job_types)
            rows = conn.execute(
                f"SELECT id, payload FROM jobs WHERE type IN ({placeholders}) "
                "AND status IN ('pending','running','dead_letter','requires_owner')",
                job_types,
            ).fetchall()
            ids: list[int] = []
            for row in rows:
                try:
                    payload = json.loads(row["payload"])
                except (TypeError, json.JSONDecodeError):
                    continue
                if str(payload.get("sessionId") or "") == session_id:
                    if (
                        not include_cancellation
                        and payload.get("type") == "refund_payment"
                        and payload.get("subscription_id")
                    ):
                        # A full refund does not prove the retired recurring
                        # subscription was cancelled. Its job must retry and
                        # confirm cancellation before becoming terminal.
                        continue
                    ids.append(int(row["id"]))
            for job_id in ids:
                cur = conn.execute(
                    "UPDATE jobs SET status='resolved', updated_at=?, "
                    "last_error=COALESCE(last_error, 'resolved after Stripe verification') "
                    "WHERE id=?",
                    (_now(), job_id),
                )
                resolved += cur.rowcount
        return resolved

    def dead_letter_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Terminal paid jobs inspected by the compensation reconciliation sweep."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status='dead_letter' ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._job_row(row) for row in rows]

    def mark_refunded(self, session_id: str, refund_id: str) -> bool:
        """Mark a purchase refunded. Returns True if this call performed the
        refund transition (i.e. it was not already refunded)."""
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE purchases SET refunded = 1, refund_id = ?, status = 'refunded', "
                "updated_at = ? WHERE session_id = ? AND refunded = 0",
                (refund_id, _now(), session_id),
            )
            return cur.rowcount > 0

    # ---- jobs ------------------------------------------------------------- #

    def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        status: str = "pending",
        dedupe_key: str | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> int:
        """Enqueue a job. If dedupe_key collides with an existing job, returns
        the existing job id instead of inserting a duplicate."""
        now = _now()
        with self.connect() as conn:
            if dedupe_key:
                existing = conn.execute(
                    "SELECT id FROM jobs WHERE dedupe_key = ?", (dedupe_key,)
                ).fetchone()
                if existing:
                    return int(existing["id"])
            cur = conn.execute(
                """
                INSERT INTO jobs(type, payload, status, max_attempts, dedupe_key,
                                 next_attempt_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job_type, json.dumps(payload), status, max_attempts, dedupe_key, now, now, now),
            )
            return int(cur.lastrowid)

    def try_claim(self, job_id: int) -> bool:
        """Atomically transition a job pending -> running. Returns True only for
        the caller that won the claim, so the inline background task and the
        startup drainer never process the same job twice."""
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status = 'running', updated_at = ? "
                "WHERE id = ? AND status = 'pending'",
                (_now(), job_id),
            )
            return cur.rowcount > 0

    def deadletter_if_exhausted(self, job_id: int, error: str) -> bool:
        """Move an already-exhausted pending job through the normal terminal path."""
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status = 'dead_letter', next_attempt_at = NULL, "
                "last_error = ?, updated_at = ? WHERE id = ? AND status = 'pending' "
                "AND attempts >= max_attempts",
                (error[:2000], _now(), job_id),
            )
            return cur.rowcount > 0

    def mark_job(self, job_id: int, status: str, error: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = ?, last_error = COALESCE(?, last_error),
                    attempts = attempts + CASE WHEN ? IS NOT NULL THEN 1 ELSE 0 END
                WHERE id = ? AND status = 'running'
                """,
                (status, _now(), error, error, job_id),
            )

    def mark_dead_letter_compensated(self, job_id: int) -> bool:
        """Finish the one-way terminal compensation transition exactly once."""
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='compensated', updated_at=? "
                "WHERE id=? AND status='dead_letter'",
                (_now(), job_id),
            )
            return cur.rowcount > 0

    def schedule_retry_or_deadletter(self, job_id: int, error: str) -> str:
        """Increment attempts; reschedule with backoff or move to dead_letter
        when max_attempts is exhausted. Returns the resulting status."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT attempts, max_attempts, status FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            if not row:
                return "missing"
            if row["status"] != "running":
                return str(row["status"])
            attempts = int(row["attempts"]) + 1
            max_attempts = int(row["max_attempts"] or DEFAULT_MAX_ATTEMPTS)
            if attempts >= max_attempts:
                status = "dead_letter"
                next_attempt_at = None
            else:
                status = "pending"
                idx = min(attempts, len(JOB_BACKOFF_SECONDS) - 1)
                delay = JOB_BACKOFF_SECONDS[idx]
                next_attempt_at = (datetime.now(UTC) + timedelta(seconds=delay)).isoformat()
            conn.execute(
                "UPDATE jobs SET status = ?, attempts = ?, next_attempt_at = ?, "
                "last_error = ?, updated_at = ? WHERE id = ? AND status = 'running'",
                (status, attempts, next_attempt_at, error[:2000], _now(), job_id),
            )
            return status

    def reclaim_stale_running_jobs(self, cutoff_seconds: int) -> int:
        """Recover jobs orphaned in 'running' by a crash/restart mid-execution.

        ``try_claim`` moves a job pending -> running; if the process dies before
        the job finishes, nothing else ever re-claims it (the drainer only looks
        at 'pending'), so a paid order silently never fulfils. This sweep returns
        any job stuck in 'running' past ``cutoff_seconds`` back to 'pending' so the
        drainer re-runs it. An exhausted reclaimed job is terminally handled by
        ``deadletter_if_exhausted`` before execution, which keeps compensation in
        the application path. ``cutoff_seconds``
        MUST exceed the longest legitimate job runtime (the runner timeout) so a
        job that is merely slow is never double-run.
        """
        cutoff = (datetime.now(UTC) - timedelta(seconds=cutoff_seconds)).isoformat()
        reclaimed = 0
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, attempts, max_attempts FROM jobs "
                "WHERE status = 'running' AND updated_at < ?",
                (cutoff,),
            ).fetchall()
            for row in rows:
                attempts = int(row["attempts"]) + 1
                conn.execute(
                    "UPDATE jobs SET status = 'pending', attempts = ?, next_attempt_at = NULL, "
                    "last_error = 'reclaimed from stale running (likely a prior crash)', "
                    "updated_at = ? WHERE id = ?",
                    (attempts, _now(), row["id"]),
                )
                reclaimed += 1
        return reclaimed

    def claim_pending_jobs(self, limit: int = 25) -> list[dict[str, Any]]:
        """Return jobs that are pending and due (next_attempt_at <= now)."""
        now = _now()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                WHERE status = 'pending'
                  AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                ORDER BY id ASC LIMIT ?
                """,
                (now, limit),
            ).fetchall()
            return [self._job_row(row) for row in rows]

    def recent_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._job_row(row) for row in rows]

    @staticmethod
    def _job_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "type": row["type"],
            "payload": json.loads(row["payload"]),
            "status": row["status"],
            "attempts": row["attempts"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_error": row["last_error"],
        }
