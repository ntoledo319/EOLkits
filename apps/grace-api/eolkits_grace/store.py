from __future__ import annotations

import json
import logging
import re
import sqlite3
import string
import time
import unicodedata
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, NamedTuple

# Exponential backoff schedule (seconds) for retryable jobs; index == attempts.
JOB_BACKOFF_SECONDS = [0, 30, 120, 600, 1800, 7200]
DEFAULT_MAX_ATTEMPTS = 6

logger = logging.getLogger("eolkits_grace")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _trunc(value: Any, limit: int = 120) -> str | None:
    if value is None:
        return None
    return str(value)[:limit]


# ---- lead screening --------------------------------------------------------- #
#
# Every submission to POST /api/v1/lead is stored, whatever these rules say, and
# the visitor gets the same response either way. The rules only decide whether
# the owner is emailed about it:
#
#   ok         normal alert
#   suspect    alert, with the subject prefixed "Likely spam: "
#   spam       stored, no alert
#   duplicate  stored, no alert: the same address sent the same text again, or
#              a submission with no text of its own, within 10 minutes
#
# A wrong "spam" or "duplicate" costs the owner an alert (the row itself stays
# and `lead_admin list` shows it), so those need a host or wording that only
# spam uses, or a true repeat. The looser signals only ever make a lead
# "suspect", which still alerts. The patterns come from the submissions the
# lead bus received from June to September 2026.

LEAD_STATUSES = ("ok", "suspect", "spam", "duplicate")
LEAD_ALERT_STATUSES = ("ok", "suspect")
LEAD_DUPLICATE_WINDOW = timedelta(minutes=10)
LIKELY_SPAM_PREFIX = "Likely spam: "

# Form field names, in priority order, that app.py reads the email and name
# columns from. Screening leaves them out of the text it treats as the message.
LEAD_EMAIL_KEYS = ("email", "Email", "e-mail", "your-email", "your_email")
LEAD_NAME_KEYS = (
    "name",
    "Name",
    "full_name",
    "fullname",
    "contact",
    "company",
    "Business",
    "agency_name",
)
_EMAIL_FIELDS = frozenset(key.casefold() for key in LEAD_EMAIL_KEYS)
_IDENTITY_FIELDS = _EMAIL_FIELDS | {key.casefold() for key in LEAD_NAME_KEYS}
# Hidden fields the page fills in itself (the form's label, the service name,
# the offer terms). They say nothing about what the visitor wrote.
_SITE_FILLED_FIELDS = frozenset({"context", "service", "offer"})
# Visitors do not write from the studio's own domains; pitch bots do.
_OWN_DOMAINS = ("toledotechnologies.com", "eolkits.com")

# Hosts that carried nothing but prize and crypto spam: link shorteners and
# Telegraph pages. Each entry also matches its subdomains.
SPAM_LINK_HOSTS = (
    "telegra.ph",
    "graph.org",
    "shorto.link",
    "short.vird.co",
    "shortmylink.co",
    "lmy.de",
    "alstr.in",
    "gnosis.link",
    "myip.kr",
    "g9.yt",
    "come.ac",
    "1hut.ru",
    "link.firststudyhub.com",
    "1borsa.com",
    "lnkz.at",
    "clickto.cc",
    "cut.gl",
    "tau.lu",
    "nordwit.com",
    "resizelink.com",
    "bpl.kr",
    "url.in.th",
)

_HOST_RE = re.compile(
    r"(?<![\w.@-])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24})(?![\w-])",
    re.IGNORECASE,
)
# A link: a URL with a scheme or "www.", or a bare host followed by a path
# ("graph.org/BALANCE-..."). A bare host alone is not a link here.
_LINK_RE = re.compile(
    r"(?:https?://|\bwww\.)[^\s<>\"]+|(?<![\w.@-])(?:[a-z0-9-]+\.)+[a-z]{2,24}/",
    re.IGNORECASE,
)
# Link markup pointing at another site: an HTML anchor or a forum [url=] tag
# with an absolute address, the way link spam posts it. A relative link, as in
# a visitor quoting their own page's HTML, is not this. Bounded so a long run
# of "<a " cannot make the search quadratic.
_MARKUP_RE = re.compile(
    r"<a\s[^>]{0,200}?\bhref\s*=\s*[\"']?\s*(?:https?:)?//|\[url=\s*[\"']?\s*(?:https?:)?//",
    re.IGNORECASE,
)

_MONEY = r"\$\s?\d{1,3}(?:,\d{3})+"  # $1,000 and up, written with commas
_BIG_MONEY = r"\$\s?\d{2,3}(?:,\d{3})+"  # $10,000 and up
# Anchored to the start of a number so a long digit run stays linear.
_COIN_AMOUNT = r"(?<![\d.,])\d+(?:[.,]\d+)?\s*(?:btc|usdt|eth)\b"
# An arrow pointing straight at a link ("-> graph.org/...", "=>> https://..."),
# not an arrow in a described flow ("sign up -> pay -> done").
_ARROW_TO_LINK = r"\s*[-=]*>+\s*(?=https?://|www\.|(?:[a-z0-9-]+\.)+[a-z]{2,24}/)"
# The campaigns' own phrases, each of which the spam put in front of its link.
# They count only when a link follows in the same field (see `_spam_wording`).
# Each is a phrase from those campaigns, never a topic word: a genuine lead may
# well write about crypto, fund transfers, prizes, raffles, promo codes or
# loans, and link its own site next to that.
_SPAM_WORDING: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (kind, re.compile(pattern, re.IGNORECASE))
    for kind, pattern in (
        # "The $27,000,000 Jackpot Is a Route to Riches", "Go all in with a
        # $25,000 promo code": a slogan with a five-figure-plus amount.
        ("prize", rf"{_BIG_MONEY}\s+(?:jackpot|promo code)\b"),
        ("prize", r"\bbe the (?:random|sweepstakes) winner of\b"),
        ("prize", r"\bnanosecond from winning\b"),
        # "The PlayStation 5 Pro 2TB is the fantastic reward", "The Lamborghini
        # Aventador is the astonishing premium", "An PlayStation 5 Pro 2TB award
        # is being presented".
        (
            "prize",
            r"\b(?:playstation\s*5|lamborghini)\b[^\n]{0,24}?"
            r"\b(?:is the \w+ (?:reward|premium)|award is being presented)\b",
        ),
        # "Earn $1,500 per day or more by validating transactions on PoS chains",
        # "... through crypto options trading", "... from decentralized voting
        # rights", "... from multiple blockchain networks", "... usage".
        (
            "crypto",
            rf"{_MONEY}\s+per day or more\s+(?:usage\b|(?:through|by|from)\s+"
            r"(?:crypto|validating|decentrali[sz]ed|multiple blockchain)\b)",
        ),
        ("crypto", rf"{_COIN_AMOUNT}\s+is yours for withdrawal\b"),
        ("crypto", rf"\btake the benefit of your {_COIN_AMOUNT}"),
        # "Top Up 169.30 USDT -> graph.org/...", "Transaction to you.Continue >
        # graph.org/...", "Transfer of funds to your name. RECEIVE >>> graph.org/...",
        # "Transfer No E1234 from Coinbase. GET =>> ...": each arrow points at the link.
        ("crypto", rf"\btop up {_COIN_AMOUNT}{_ARROW_TO_LINK}"),
        ("crypto", rf"\btransaction to you\.\s*\w{{0,12}}{_ARROW_TO_LINK}"),
        (
            "crypto",
            rf"\btransfer of funds to your name\W{{0,4}}receive\b[^\n>]{{0,24}}{_ARROW_TO_LINK}",
        ),
        (
            "crypto",
            r"\btransfer\s*(?:№|no\.?|#)\s*\w{0,12}\d\w{0,12}\s+from\s+(?:coinbase|binance)\b"
            rf"[^\n>]{{0,12}}{_ARROW_TO_LINK}",
        ),
        ("loan-offer", r"\btake advantage of our (?:limited\W{0,3}time )?loan offer\b"),
    )
)


def _spam_wording(texts: Iterable[str]) -> str | None:
    """The kind of campaign wording ("prize", "crypto", "loan-offer") in any
    one of `texts` (one per form field) that has a link after it in the same
    field. A phrase in one field and a link in another (the Website field, say)
    do not count."""
    for text in texts:
        for kind, pattern in _SPAM_WORDING:
            match = pattern.search(text)
            if match and _LINK_RE.search(text, match.end()):
                return kind
    return None


# Sales-pitch wording. A "strong" cue is something a prospect does not write to
# a studio; a "weak" cue is outreach mechanics a prospect might use too. A lead
# is a pitch with one strong cue plus any other cue. Weak cues alone never make
# one: "I visited your site, can we book a call? Let us know" is how a real
# prospect writes too, and every pitch received had a strong cue.
_PITCH_STRONG = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:order|get|grab) yours\b|\b(?:order|get|grab) (?:it|one) (?:now|today)\b",
        r"\blet you know about our new\b",
        r"\bdo you have any use for\b",
        r"\bfreelance (?:writer|copywriter)\b",
        r"\bno cost,? no obligation\b",
        r"\b(?:loan offer|instant (?:loan )?approval|no collateral|flexible repayment)\b",
        r"\buse contact (?:forms?|pages?) to share\b",
        r"\bwe only use chat\b",
        r"\b(?:saw|see|noticed|found) (?:a few|some|several) (?:opportunities|ways|areas)"
        r" to improve\b",
        r"\bhappy to share (?:a few )?(?:quick )?ideas\b",
        r"\bvetted (?:development|software) (?:companies|agencies|partners)\b",
    )
)
_PITCH_WEAK = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bvisited (?:your (?:web ?)?site|[a-z0-9-]+\.[a-z]{2,})",
        r"\b(?:took|had) a (?:quick )?look at your (?:web ?)?site\b",
        r"\b(?:book|grab|schedule) a (?:time|call|meeting|demo|slot)\b|\bcalendly\.com\b",
        r"\b(?:t\.me|wa\.me)/|\bwhatsapp\b|\btelegram\b",
        r"\b\d{1,2}\s?% off\b|\bfree shipping\b",
        r"\btoday only\b|\blimited\W?time\b|\bdon'?t miss (?:out|this)\b",
        r"\blooking for new (?:opportunities|clients|projects)\b",
        r"\bkindly reply\b",
        r"\bsee how it works\b",
        r"\blet us know if (?:this|you)\b",
        r"\bhope (?:this|my) (?:email|message|note) finds you\b|\bhope you'?re doing well\b",
        r"\bwe help (?:businesses|companies|brands|business owners)\b",
        r"\bunsubscribe\b|\bopt[- ]out\b",
    )
)

# "What is your price" in many languages, for the one-line template that
# arrives in a new language every week. Short stems carry their inflections.
_PRICE_WORD_RE = re.compile(
    r"(?<!\w)(?:"
    r"prices?|pricing|costs?|quotes?|rates|"
    r"precios?|preços?|preco|prezz[oi]|prezo|preu|prix|tarifs?|pre[țţt](?:ul)?|pretium|"
    r"preise?|prijs|prys|pris(?:en)?|"
    r"cen[aeuyęėo]|cenas|cijen[aeu]|цен[аеуы]|цін[аиу]|kain(?:a|ą|os|as)|"
    r"hinta|hinnan|hintaa|hind|hinda|hinnad|ár(?:a|at|ak)?|fiyat\w*|qiym[əe]t\w*|"
    r"giá|harga|presyo|çmim\w*|verð\w*|"
    r"τιμ\w*|ფას\w*|գին\w*|מחיר\w*|\w*سعر\w*|قیمت\w*|कीमत|मूल्य|दाम|দাম"
    r")(?!\w)"
    r"|价格|價格|价钱|値段|価格|料金|가격|ราคา",
    re.IGNORECASE,
)
# Anything that gives a price question something to price.
_PROJECT_WORD_RE = re.compile(
    r"\b(?:web ?sites?|sites?|apps?|applications?|stores?|shops?|e-?commerce|online|"
    r"wordpress|shopify|squarespace|wix|webflow|migrat\w*|redesign\w*|audit\w*|seo|"
    r"mobile|ios|android|software|platforms?|integrations?|api|pages?|logo|brand\w*|"
    r"design\w*|develop\w*|build\w*|rebuild\w*|fix\w*|bugs?|support|maintenance|"
    r"hosting|domains?|automat\w*|chatbots?|crm|dashboards?|databases?|plugins?|"
    r"projects?|mvp|saas|portals?|booking|care plans?|kits?|reports?|"
    r"sitio|página|pagina|tienda|aplicaci\w*|sito|negozio|loja)\b",
    re.IGNORECASE,
)
# Scripts written without spaces between words.
_UNSPACED_SCRIPTS = ("CJK", "HIRAGANA", "KATAKANA", "HANGUL", "THAI", "LAO", "KHMER", "MYANMAR")
# A file input in a multipart form is stored as the text of Starlette's upload
# object (for example an empty <input type="file">). Not something typed.
_UPLOAD_PLACEHOLDER_RE = re.compile(r"UploadFile\(filename=")


class LeadScreen(NamedTuple):
    status: str
    reason: str


class RecordedLead(NamedTuple):
    id: int
    status: str
    reason: str


def _screen_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value if value is not None else ""))
    return text.replace("\u2019", "'").replace("\u2018", "'")


def _is_message_text(text: str) -> bool:
    """True for something the visitor wrote, as opposed to a picked option
    ("15k-50k", "not-sure") or a lone word or random token ("hello", "kq3vzr")."""
    if " " in text or len(text) >= 25 or _HOST_RE.search(text):
        return True
    return any(unicodedata.name(ch, "").startswith(_UNSPACED_SCRIPTS) for ch in text)


def lead_message_parts(fields: Mapping[str, Any]) -> list[str]:
    """The text the visitor wrote, one entry per field, whitespace collapsed.
    Leaves out the identity fields, the fields the page fills in itself, and
    picked options."""
    parts = []
    for key, value in fields.items():
        folded = str(key).strip().casefold()
        if folded in _IDENTITY_FIELDS or folded in _SITE_FILLED_FIELDS:
            continue
        text = " ".join(_screen_text(value).split())
        if text and _is_message_text(text) and not _UPLOAD_PLACEHOLDER_RE.match(text):
            parts.append(text)
    return parts


def lead_message_key(stored_fields: str | None) -> tuple[str, bool]:
    """(comparison key, has text) for a `fields` value as stored. Two
    submissions carry the same message when their keys are equal. A value cut
    at 4,000 characters is no longer JSON; its raw text is compared instead."""
    try:
        data = json.loads(stored_fields or "{}")
    except (TypeError, ValueError):
        data = None
    if isinstance(data, dict):
        parts = lead_message_parts(data)
        return "\x1f".join(sorted(part.casefold() for part in parts)), bool(parts)
    text = " ".join(str(stored_fields).split()).casefold()
    return text, bool(text)


def _spam_host(text: str) -> str | None:
    for match in _HOST_RE.finditer(text):
        host = match.group(1).lower()
        for spam_host in SPAM_LINK_HOSTS:
            if host == spam_host or host.endswith("." + spam_host):
                return spam_host
    return None


def _is_pitch(text: str) -> bool:
    strong = sum(1 for pattern in _PITCH_STRONG if pattern.search(text))
    weak = sum(1 for pattern in _PITCH_WEAK if pattern.search(text))
    return strong >= 1 and strong + weak >= 2


def _is_price_template(text: str) -> bool:
    return (
        len(text) <= 80
        and len(text.split()) <= 10
        and bool(_PRICE_WORD_RE.search(text))
        and not any(ch.isdigit() for ch in text)
        and not _HOST_RE.search(text)
        and not _PROJECT_WORD_RE.search(text)
    )


def _own_domain(email: str) -> bool:
    domain = str(email).strip().rsplit("@", 1)[-1].strip().casefold()
    return any(domain == own or domain.endswith("." + own) for own in _OWN_DOMAINS)


def screen_lead_content(*, email: str, fields: Mapping[str, Any] | str) -> LeadScreen:
    """Judge one submission on its content alone: 'spam', 'suspect' or 'ok'.
    (A 'duplicate' needs the earlier rows; see `Store.record_screened_lead`.)

    `fields` is the form as captured, or the raw stored text when the stored
    JSON was cut short. The reason names the rule, never the visitor's text."""
    if isinstance(fields, Mapping):
        values = [
            _screen_text(value)
            for key, value in fields.items()
            if str(key).strip().casefold() not in _EMAIL_FIELDS
        ]
        parts = lead_message_parts(fields)
    else:
        values = [_screen_text(fields)]
        parts = [" ".join(values[0].split())] if values[0].strip() else []
    scanned = "\n".join(values)

    if _MARKUP_RE.search(scanned):
        return LeadScreen("spam", "HTML link markup")
    host = _spam_host(scanned)
    if host:
        return LeadScreen("spam", f"link to a known spam host ({host})")
    kind = _spam_wording(values)
    if kind:
        return LeadScreen("spam", f"link with {kind} spam wording")

    message = "\n".join(parts)
    reasons = []
    if not parts:
        reasons.append("empty or one-word message")
    elif _is_pitch(message):
        reasons.append("sales pitch wording")
    elif _is_price_template(message):
        reasons.append("one-line price question")
    if _own_domain(email):
        reasons.append("sent from the studio's own domain")
    if reasons:
        return LeadScreen("suspect", "; ".join(reasons))
    return LeadScreen("ok", "")


def _duplicate_reason(earlier_id: int) -> str:
    minutes = int(LEAD_DUPLICATE_WINDOW.total_seconds() // 60)
    return f"repeat of lead {earlier_id} within {minutes} minutes"


def _parse_ts(value: Any) -> datetime | None:
    """A stored `ts` as an aware UTC datetime (None if unreadable)."""
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


class Store:
    def __init__(self, db_path: Path, *, initialize: bool = True):
        self.db_path = db_path
        if initialize:
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
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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
                -- `status` is the screening result (ok/suspect/spam/duplicate);
                -- it only decides the owner alert, never whether a row is kept.
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    email TEXT NOT NULL,
                    name TEXT,
                    product TEXT,
                    source TEXT,
                    fields TEXT,
                    notified INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'ok',
                    status_reason TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_leads_ts ON leads(ts);
                CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
                """
            )
            # Add columns to pre-existing `jobs` tables BEFORE creating any index
            # that references them (an old prod DB has jobs without dedupe_key).
            self._migrate_jobs_columns(conn)
            # An old prod `leads` table (created before notify-hardening) lacks
            # `notified`; one created before lead screening lacks `status`.
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
        # Lead screening. Additive only: rows captured before it keep every value
        # and read as 'ok' (the column default), which is how they were alerted.
        # `lead_admin reclassify` applies the rules to them when the operator
        # chooses to.
        if "status" not in existing:
            conn.execute("ALTER TABLE leads ADD COLUMN status TEXT NOT NULL DEFAULT 'ok'")
        if "status_reason" not in existing:
            conn.execute("ALTER TABLE leads ADD COLUMN status_reason TEXT")

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
        return self.record_screened_lead(
            email=email, name=name, product=product, source=source, fields=fields
        ).id

    def record_screened_lead(
        self,
        *,
        email: str,
        name: str | None = None,
        product: str | None = None,
        source: str | None = None,
        fields: dict[str, Any] | None = None,
    ) -> RecordedLead:
        """Record a lead exactly as `record_lead` always has, plus its screening
        status (see "lead screening" above). The row is written whatever the
        rules say; a rule that fails leaves the lead 'ok' so it still alerts.

        The duplicate check and the insert share one IMMEDIATE transaction, so
        a burst of identical submissions is judged one at a time."""
        stored_fields = json.dumps(fields or {})[:4000]
        try:
            status, reason = screen_lead_content(email=email, fields=fields or {})
        except Exception:  # noqa: BLE001 — screening must never cost a lead
            logger.exception("lead screening failed; keeping the lead as 'ok'")
            status, reason = "ok", "not screened (rule error)"
        now = datetime.now(UTC)
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if status != "spam":
                try:
                    earlier = self._earlier_submission(conn, email, stored_fields, now)
                except Exception:  # noqa: BLE001 — as above
                    logger.exception("lead duplicate check failed; judging the lead alone")
                    earlier = None
                if earlier is not None:
                    status, reason = "duplicate", _duplicate_reason(earlier)
            cur = conn.execute(
                "INSERT INTO leads(ts, email, name, product, source, fields, status, "
                "status_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    now.isoformat(),
                    str(email)[:200],
                    _trunc(name, 200),
                    _trunc(product),
                    _trunc(source, 200),
                    stored_fields,
                    status,
                    reason or None,
                ),
            )
            return RecordedLead(int(cur.lastrowid), status, reason)

    def _earlier_submission(
        self,
        conn: sqlite3.Connection,
        email: str,
        stored_fields: str | None,
        when: datetime,
        *,
        before_id: int | None = None,
    ) -> int | None:
        """The id of an earlier lead that makes this one a duplicate: the same
        address within LEAD_DUPLICATE_WINDOW before `when`, and either the same
        message or no message of its own (a bot hitting several forms, an empty
        re-send). A different message from the same address is not a duplicate,
        even on another form: it may be a real follow-up."""
        email_key = self._email_key(email)
        if not email_key:
            return None
        message_key, has_message = lead_message_key(stored_fields)
        sql = f"SELECT id, fields FROM leads WHERE ts >= ? AND {self._LEAD_EMAIL_KEY} = ?"
        params: list[Any] = [(when - LEAD_DUPLICATE_WINDOW).isoformat(), email_key]
        if before_id is not None:
            sql += " AND id < ?"
            params.append(int(before_id))
        for row in conn.execute(sql + " ORDER BY id DESC LIMIT 50", params).fetchall():
            if not has_message or lead_message_key(row["fields"])[0] == message_key:
                return int(row["id"])
        return None

    def lead_screen(self, lead_id: int) -> LeadScreen:
        """The screening status stored with a lead ('ok' if the row is gone)."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status, status_reason FROM leads WHERE id = ?", (int(lead_id),)
            ).fetchone()
        if row is None:
            return LeadScreen("ok", "")
        return LeadScreen(row["status"] or "ok", row["status_reason"] or "")

    def recent_leads(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def mark_lead_notified(self, lead_id: int) -> None:
        """Flip a lead to notified=1 only after a confirmed owner alert send."""
        with self.connect() as conn:
            conn.execute("UPDATE leads SET notified = 1 WHERE id = ?", (int(lead_id),))

    # Leads the owner is alerted about. Spam and duplicates are never alerted,
    # so they are never "owed" an alert either.
    _ALERTABLE = "status IN ('ok', 'suspect')"

    def unnotified_leads(self, limit: int = 100) -> list[dict[str, Any]]:
        """Durably-captured leads the owner was NOT yet successfully alerted about —
        the recovery queue for the periodic re-send sweep (self-heals email outages).
        Spam and duplicates are not in it."""
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM leads WHERE notified = 0 AND {self._ALERTABLE} "
                "ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def count_unnotified(self) -> int:
        with self.connect() as conn:
            return int(
                conn.execute(
                    f"SELECT COUNT(*) AS n FROM leads WHERE notified = 0 AND {self._ALERTABLE}"
                ).fetchone()["n"]
            )

    # ---- lead screening: operator views ------------------------------------ #

    def has_lead_status(self) -> bool:
        """True once the API has added the screening columns (at its startup)."""
        with self.connect() as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(leads)")}
        return {"status", "status_reason"} <= columns

    def iter_leads(
        self, *, since: str | None = None, status: str | None = None, with_fields: bool = False
    ) -> Iterator[dict[str, Any]]:
        """Lead rows oldest first, one at a time, optionally from a UTC date or
        time (`ts` text order is time order) and with one screening status. The
        form contents (`fields`) are read only when asked for."""
        clauses: list[str] = []
        params: list[Any] = []
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)} " if clauses else ""
        columns = "id, ts, product, source, notified, status, status_reason"
        if with_fields:
            columns += ", fields"
        with self.connect() as conn:
            for row in conn.execute(f"SELECT {columns} FROM leads {where}ORDER BY id", params):
                yield dict(row)

    def reclassify_leads(self, *, dry_run: bool = False) -> dict[str, Any]:
        """Apply the screening rules to every stored lead, oldest first, exactly
        as they apply at capture: a duplicate is judged against the rows before
        it within LEAD_DUPLICATE_WINDOW of its own time.

        Changes `status` and `status_reason` only; never deletes a row or changes
        what it holds. A row changes only if its status is still what was read,
        so a concurrent change is never overwritten. Returns every change (id,
        ts, product, source, notified, old/new status, reason) and, unless
        `dry_run`, how many were written."""
        changes: list[dict[str, Any]] = []
        checked = 0
        with self.connect() as conn:
            for row in conn.execute(
                "SELECT id, ts, email, product, source, fields, notified, status, "
                "status_reason FROM leads ORDER BY id"
            ):
                checked += 1
                status, reason = self._rescreen(conn, row)
                old_status = row["status"] or "ok"
                if (status, reason or None) != (old_status, row["status_reason"] or None):
                    changes.append(
                        {
                            "id": int(row["id"]),
                            "ts": row["ts"],
                            "product": row["product"],
                            "source": row["source"],
                            "notified": int(row["notified"] or 0),
                            "old_status": old_status,
                            "status": status,
                            "reason": reason,
                        }
                    )
        updated = 0
        if changes and not dry_run:
            with self.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                for change in changes:
                    cur = conn.execute(
                        "UPDATE leads SET status = ?, status_reason = ? "
                        "WHERE id = ? AND status = ?",
                        (
                            change["status"],
                            change["reason"] or None,
                            change["id"],
                            change["old_status"],
                        ),
                    )
                    updated += cur.rowcount
        return {"checked": checked, "changes": changes, "updated": updated}

    def _rescreen(self, conn: sqlite3.Connection, row: sqlite3.Row) -> LeadScreen:
        """The status `record_screened_lead` would give this row had it just
        arrived, with the rows stored before it."""
        stored = row["fields"]
        try:
            data = json.loads(stored or "{}")
        except (TypeError, ValueError):
            data = None
        try:
            verdict = screen_lead_content(
                email=row["email"] or "", fields=data if isinstance(data, dict) else str(stored)
            )
        except Exception:  # noqa: BLE001 — same fallback as at capture
            logger.exception("lead screening failed for lead %s", row["id"])
            verdict = LeadScreen("ok", "not screened (rule error)")
        when = _parse_ts(row["ts"])
        if verdict.status == "spam" or when is None:
            return verdict
        earlier = self._earlier_submission(
            conn, row["email"] or "", stored, when, before_id=int(row["id"])
        )
        if earlier is not None:
            return LeadScreen("duplicate", _duplicate_reason(earlier))
        return verdict

    # ---- lead retention and deletion -------------------------------------- #
    #
    # Deletes of personal data run with `secure_delete` on, so SQLite overwrites
    # the freed row content instead of leaving it in free pages, inside one
    # IMMEDIATE transaction so the rows reported are exactly the rows removed.
    # In WAL mode the old page images stay in the database file until a
    # checkpoint copies the overwritten pages over them; callers that erase
    # rows call `checkpoint_wal()` afterwards.

    @contextmanager
    def _erasing(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as conn:
            conn.execute("PRAGMA secure_delete = ON")
            conn.execute("BEGIN IMMEDIATE")
            yield conn

    def checkpoint_wal(self) -> bool:
        """Copy the WAL into the database file and truncate it, without waiting.

        The busy timeout is 0 for this one connection, so the checkpoint never
        stalls other work (a Stripe webhook, a job) behind a reader: it either
        completes at once or reports False, and the caller retries later."""
        with self.connect() as conn:
            conn.execute("PRAGMA busy_timeout = 0")
            try:
                busy, _log_frames, _checkpointed = conn.execute(
                    "PRAGMA wal_checkpoint(TRUNCATE)"
                ).fetchone()
            except sqlite3.OperationalError:
                return False
        return int(busy) == 0

    def purge_leads_before(self, cutoff_iso: str, *, dry_run: bool = False) -> dict[str, int]:
        """Delete lead rows captured before `cutoff_iso` (a UTC isoformat string,
        the format `ts` is written in, so text order is time order).
        `unnotified` counts matched rows whose owner alert never went out (spam
        and duplicates are never alerted, so they are not counted)."""
        sql_where = "FROM leads WHERE ts < ?"
        manager = self.connect() if dry_run else self._erasing()
        with manager as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(leads)")}
            # The CLI may open a database the API has not migrated yet.
            owed = f"notified = 0 AND {self._ALERTABLE}" if "status" in columns else "notified = 0"
            row = conn.execute(
                f"SELECT COUNT(*) AS n, COALESCE(SUM({owed}), 0) AS unnotified " + sql_where,
                (cutoff_iso,),
            ).fetchone()
            deleted = 0
            if not dry_run and int(row["n"]):
                deleted = int(conn.execute("DELETE " + sql_where, (cutoff_iso,)).rowcount)
        return {"matched": int(row["n"]), "deleted": deleted, "unnotified": int(row["unnotified"])}

    # Stored emails are the raw form value (not trimmed), so one person's rows
    # are matched on a trimmed, lower-cased copy. SQLite's lower() folds A-Z
    # only; the input is folded exactly the same way (not with str.lower(),
    # which folds all of Unicode) so both sides always agree.
    _LEAD_EMAIL_KEY = "lower(trim(email, char(32, 9, 10, 13)))"
    _ASCII_LOWER = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)

    @classmethod
    def _email_key(cls, email: str) -> str:
        return str(email).strip(" \t\r\n").translate(cls._ASCII_LOWER)

    def delete_leads(
        self,
        *,
        email: str | None = None,
        ids: list[int] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Delete the lead rows for one person (by email) and/or by row id.

        Returns the matched rows (id, ts, product, source, notified; never the
        form contents) and how many were deleted (0 on a dry run)."""
        clauses: list[str] = []
        params: list[Any] = []
        if email is not None:
            clauses.append(f"{self._LEAD_EMAIL_KEY} = ?")
            params.append(self._email_key(email))
        if ids:
            clauses.append(f"id IN ({', '.join('?' for _ in ids)})")
            params.extend(int(i) for i in ids)
        if not clauses:
            raise ValueError("delete_leads needs an email or at least one id")
        where = " OR ".join(clauses)
        manager = self.connect() if dry_run else self._erasing()
        with manager as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    f"SELECT id, ts, product, source, notified FROM leads WHERE {where} "
                    "ORDER BY id",
                    params,
                ).fetchall()
            ]
            deleted = 0
            if rows and not dry_run:
                deleted = int(conn.execute(f"DELETE FROM leads WHERE {where}", params).rowcount)
        return {"matched": rows, "deleted": deleted}

    def lead_ids_mentioning(self, email: str, *, exclude_ids: list[int] | None = None) -> list[int]:
        """Ids of lead rows whose name or form fields contain `email` although the
        row's own email is someone else's: candidates for a human to review.
        `fields` is stored as JSON, so non-ASCII text there is \\u-escaped; both
        spellings of the address are searched."""
        needle = self._email_key(email)
        if not needle:
            return []
        escaped = json.dumps(needle)[1:-1]
        exclude = [int(i) for i in exclude_ids or []]
        sql = (
            "SELECT id FROM leads WHERE "
            f"{self._LEAD_EMAIL_KEY} != ? AND ("
            "instr(lower(COALESCE(fields, '')), ?) > 0 "
            "OR instr(lower(COALESCE(fields, '')), ?) > 0 "
            "OR instr(lower(COALESCE(name, '')), ?) > 0)"
        )
        params: list[Any] = [needle, needle, escaped, needle]
        if exclude:
            sql += f" AND id NOT IN ({', '.join('?' for _ in exclude)})"
            params.extend(exclude)
        with self.connect() as conn:
            return [int(row["id"]) for row in conn.execute(sql + " ORDER BY id", params).fetchall()]

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
