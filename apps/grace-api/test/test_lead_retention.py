"""Opt-in lead retention (EOLKITS_LEAD_RETENTION_DAYS), applied by the existing
artifact-retention sweep: once at startup, then hourly from the drain loop."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from datetime import UTC, datetime, timedelta

import pytest


def _seed(
    mod, email: str, *, days_old: float = 0, message: str = "hello", notified: bool = True
) -> int:
    lead_id = mod.store.record_lead(
        email=email,
        name="Someone",
        product="Apps",
        source="test",
        fields={"email": email, "message": message},
    )
    ts = (datetime.now(UTC) - timedelta(days=days_old)).isoformat()
    with mod.store.connect() as conn:
        conn.execute(
            "UPDATE leads SET ts = ?, notified = ? WHERE id = ?",
            (ts, 1 if notified else 0, lead_id),
        )
    return lead_id


def _ids(mod) -> list[int]:
    return sorted(row["id"] for row in mod.store.recent_leads(1000))


def _table_counts(mod) -> dict[str, int]:
    with mod.store.connect() as conn:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("events", "purchases", "jobs", "kv", "rate_limits")
        }


# ---- the setting ------------------------------------------------------------ #


@pytest.mark.parametrize("value", ["abc", "-1", "90d", "1.5", "40000", "3 0"])
def test_malformed_retention_setting_stops_startup(grace_env, fresh_import, value):
    grace_env(EOLKITS_LEAD_RETENTION_DAYS=value)
    with pytest.raises(ValueError, match="EOLKITS_LEAD_RETENTION_DAYS"):
        fresh_import("eolkits_grace.config")


@pytest.mark.parametrize("value,expected", [("", 0), ("0", 0), (" 365 ", 365), ("36500", 36500)])
def test_retention_setting_values(grace_env, fresh_import, value, expected):
    grace_env(EOLKITS_LEAD_RETENTION_DAYS=value)
    assert fresh_import("eolkits_grace.config").settings.lead_retention_days == expected


def test_retention_is_off_by_default_and_never_touches_leads(load_grace, monkeypatch):
    mod, _ = load_grace()
    assert mod.settings.lead_retention_days == 0
    ids = [_seed(mod, "old@example.com", days_old=3000), _seed(mod, "new@example.com")]

    def must_not_run(*args, **kwargs):
        raise AssertionError("retention is off: the leads table must not be touched")

    monkeypatch.setattr(mod.store, "purge_leads_before", must_not_run)
    monkeypatch.setattr(mod.store, "checkpoint_wal", must_not_run)
    assert mod.purge_expired_leads() == 0
    assert mod.cleanup_expired_artifacts()["leads"] == 0
    assert _ids(mod) == ids


# ---- the purge -------------------------------------------------------------- #


def test_retention_purges_only_rows_older_than_the_period(load_grace):
    mod, client = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")
    old = _seed(mod, "old@example.com", days_old=30.01)
    older_unalerted = _seed(mod, "older@example.com", days_old=400, notified=False)
    edge = _seed(mod, "edge@example.com", days_old=29.99)
    fresh = client.post("/api/v1/lead", data={"email": "fresh@example.com"}).json()["lead_id"]
    mod.store.enqueue("audit_pdf", {"sessionId": "cs_keep"})
    before = _table_counts(mod)

    assert mod.purge_expired_leads() == 2
    assert _ids(mod) == sorted([edge, fresh])
    assert old not in _ids(mod) and older_unalerted not in _ids(mod)
    assert _table_counts(mod) == before  # funnel events, jobs, purchases untouched
    assert mod.purge_expired_leads() == 0  # idempotent


def test_the_retention_sweep_applies_the_purge_last(load_grace):
    mod, _ = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")
    _seed(mod, "old@example.com", days_old=31)
    keep = _seed(mod, "new@example.com", days_old=1)
    result = mod.cleanup_expired_artifacts()
    assert result["leads"] == 1
    assert list(result)[-1] == "leads"
    assert _ids(mod) == [keep]


def test_purging_never_alerted_leads_is_logged(load_grace, caplog):
    mod, _ = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")
    _seed(mod, "lost@example.com", days_old=45, notified=False)
    with caplog.at_level(logging.INFO, logger="eolkits_grace"):
        assert mod.purge_expired_leads() == 1
    assert "purged 1 lead row(s) older than 30 days" in caplog.text
    assert "1 purged lead(s) had never been alerted to the owner" in caplog.text


def test_deleted_lead_content_does_not_survive_on_disk(load_grace, secure_delete_off, db_bytes):
    """secure_delete plus a WAL checkpoint: the bytes are gone from the database
    file and the WAL, not just unlinked from the table. A long message spills
    into overflow pages, which must be overwritten too."""
    mod, _ = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")

    # Control: with this SQLite setup, an ordinary DELETE leaves the bytes behind.
    control = _seed(mod, "control-4b1e@example.com", message="control-4b1e")
    with mod.store.connect() as conn:
        conn.execute("DELETE FROM leads WHERE id = ?", (control,))
    assert mod.store.checkpoint_wal()
    assert b"control-4b1e" in db_bytes(mod)

    marker = "erase-me-7f3a91"
    _seed(mod, f"{marker}@example.com", days_old=60, message=f"payload {marker} " * 200)
    keep = _seed(mod, "keep@example.com", message="keep-this-one")
    assert mod.purge_expired_leads() == 1
    assert marker.encode() not in db_bytes(mod)
    assert b"keep-this-one" in db_bytes(mod)
    assert _ids(mod) == [keep]


def test_a_busy_database_defers_the_checkpoint_without_waiting(load_grace, caplog):
    """The WAL checkpoint must never stall other work (a Stripe webhook, a job)
    behind a long reader: it gives up at once and the next sweep retries it."""
    mod, _ = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")
    _seed(mod, "old@example.com", days_old=60)
    keep = _seed(mod, "new@example.com")
    reader = sqlite3.connect(mod.settings.db_path, isolation_level=None)
    try:
        reader.execute("BEGIN")
        assert reader.execute("SELECT COUNT(*) FROM leads").fetchone()[0] == 2
        started = time.monotonic()
        with caplog.at_level(logging.WARNING, logger="eolkits_grace"):
            assert mod.purge_expired_leads() == 1
        assert time.monotonic() - started < 5
        assert "WAL checkpoint deferred" in caplog.text
    finally:
        reader.execute("COMMIT")
        reader.close()
    assert _ids(mod) == [keep]
    assert mod._lead_checkpoint_pending
    # The next sweep deletes nothing new but still owes, and now completes,
    # the checkpoint.
    assert mod.purge_expired_leads() == 0
    assert not mod._lead_checkpoint_pending


# ---- when it runs ----------------------------------------------------------- #


def test_drain_loop_runs_the_purge_on_the_sweep_interval(load_grace, monkeypatch):
    mod, _ = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")
    _seed(mod, "old@example.com", days_old=31)
    keep = _seed(mod, "new@example.com")
    monkeypatch.setattr(mod, "_drain_once", lambda: None)
    monkeypatch.setattr(mod, "DRAIN_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(mod, "ARTIFACT_SWEEP_INTERVAL_SECONDS", 0)

    async def run() -> None:
        try:
            await asyncio.wait_for(mod._drain_loop(), 0.5)
        except TimeoutError:
            pass

    asyncio.run(run())
    assert _ids(mod) == [keep]


def test_startup_applies_retention_outside_tests(load_grace):
    mod, client = load_grace(ENVIRONMENT="staging", EOLKITS_LEAD_RETENTION_DAYS="30")
    _seed(mod, "old@example.com", days_old=31)
    keep = _seed(mod, "new@example.com")
    with client:  # runs the lifespan: the one-shot startup sweep
        for _ in range(200):
            if _ids(mod) == [keep]:
                break
            time.sleep(0.02)
        assert client.get("/health").status_code == 200
    assert _ids(mod) == [keep]
    fields = json.loads(mod.store.recent_leads()[0]["fields"])
    assert fields["email"] == "new@example.com"
