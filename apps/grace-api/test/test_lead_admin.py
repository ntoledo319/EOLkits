"""The operator CLI: python -m eolkits_grace.lead_admin (delete, purge, list, reclassify)."""

from __future__ import annotations

import io
import json
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest
from leadbus_support import API_ROOT


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


def _cli(fresh_import, *argv: str) -> tuple[int, str]:
    lead_admin = fresh_import("eolkits_grace.lead_admin")
    out = io.StringIO()
    code = lead_admin.main(list(argv), out=out)
    return code, out.getvalue()


def test_delete_by_email_dry_run_then_for_real(load_grace, fresh_import):
    mod, client = load_grace()
    a1 = _seed(mod, "a@example.com", message="private words 9d1c")
    # Stored exactly as typed: surrounding spaces and different case still match.
    a2 = client.post("/api/v1/lead", data={"email": " A@Example.COM "}).json()["lead_id"]
    assert mod.store.recent_leads()[0]["email"] == " A@Example.COM "
    mention = _seed(mod, "colleague@example.com", message="please also reply to a@example.com")
    other = _seed(mod, "c@example.com")

    code, out = _cli(fresh_import, "delete", "--email", "a@example.com", "--dry-run")
    assert code == 0
    assert f"Matched 2 lead row(s) for email a@example.com: id {a1} " in out
    assert "Dry run: nothing was deleted." in out
    assert f"(id {mention})" in out and "were not deleted" in out
    assert "LEAD_NOTIFY_TO mailbox" in out
    assert "private words" not in out  # never prints form contents
    assert _ids(mod) == sorted([a1, a2, mention, other])

    code, out = _cli(fresh_import, "delete", "--email", "A@EXAMPLE.com")
    assert code == 0
    assert "Deleted 2 lead row(s)." in out
    assert "WAL checkpoint complete" in out
    assert "LEAD_NOTIFY_TO mailbox" in out
    assert _ids(mod) == sorted([mention, other])

    code, out = _cli(fresh_import, "delete", "--id", str(mention))
    assert code == 0 and "Deleted 1 lead row(s)." in out
    assert _ids(mod) == [other]

    code, out = _cli(fresh_import, "delete", "--email", "nobody@example.com")
    assert code == 0 and "Matched 0 lead rows" in out and "Deleted 0 lead row(s)." in out
    assert _ids(mod) == [other]


def test_email_matching_folds_case_exactly_like_sqlite(load_grace, fresh_import):
    """SQLite's lower() folds A-Z only. The input is folded the same way, or an
    address with a non-ASCII capital could never match its own row."""
    mod, _ = load_grace()
    stored = _seed(mod, "\u00c4RGER@Example.com")  # an A-umlaut capital
    colleague = _seed(mod, "b@example.com", message="cc \u00c4rger@example.com please")
    code, out = _cli(fresh_import, "delete", "--email", "\u00c4RGER@EXAMPLE.COM")
    assert code == 0 and "Deleted 1 lead row(s)." in out
    assert stored not in _ids(mod)
    # The mention is found although `fields` stores it JSON-escaped.
    assert f"(id {colleague})" in out


def test_delete_overwrites_the_data_on_disk(load_grace, fresh_import, secure_delete_off, db_bytes):
    mod, _ = load_grace()
    marker = "cli-erase-5d20"
    _seed(mod, f"{marker}@example.com", message=f"{marker} " * 600)
    keep = _seed(mod, "keep@example.com", message="keep-this-one")
    code, out = _cli(fresh_import, "delete", "--email", f"{marker}@example.com")
    assert code == 0 and "WAL checkpoint complete" in out
    assert marker.encode() not in db_bytes(mod)
    assert b"keep-this-one" in db_bytes(mod)
    assert _ids(mod) == [keep]


def test_rejects_bad_input_and_a_missing_database(grace_env, fresh_import, tmp_path):
    grace_env()
    assert _cli(fresh_import, "delete", "--email", "not-an-address")[0] == 2
    assert _cli(fresh_import, "delete")[0] == 2
    with pytest.raises(SystemExit) as exc:
        _cli(fresh_import)
    assert exc.value.code == 2

    missing = tmp_path / "no-such-dir"
    grace_env(EOLKITS_DATA_DIR=str(missing))
    code, out = _cli(fresh_import, "delete", "--email", "a@example.com")
    assert code == 1 and "No lead database" in out
    assert not missing.exists()  # did not create an empty database somewhere else


def test_refuses_a_symlinked_database(load_grace, fresh_import, grace_env, tmp_path):
    mod, _ = load_grace()
    _seed(mod, "a@example.com")
    link_dir = tmp_path / "linked"
    link_dir.mkdir()
    (link_dir / "state.sqlite3").symlink_to(mod.settings.db_path)
    grace_env(EOLKITS_DATA_DIR=str(link_dir))
    code, out = _cli(fresh_import, "delete", "--email", "a@example.com")
    assert code == 1 and "No lead database" in out
    assert len(_ids(mod)) == 1


def test_does_not_run_schema_migrations(load_grace, fresh_import, monkeypatch):
    mod, _ = load_grace()
    _seed(mod, "a@example.com")
    lead_admin = fresh_import("eolkits_grace.lead_admin")

    def no_init(self):
        raise AssertionError("the CLI must not run Store.init()")

    monkeypatch.setattr(lead_admin.Store, "init", no_init)
    out = io.StringIO()
    assert lead_admin.main(["delete", "--email", "a@example.com"], out=out) == 0
    assert "Deleted 1 lead row(s)." in out.getvalue()


def test_leaves_the_process_umask_as_it_found_it(load_grace, fresh_import):
    load_grace()
    before = os.umask(0o022)
    os.umask(before)
    _cli(fresh_import, "delete", "--email", "nobody@example.com", "--dry-run")
    after = os.umask(before)
    assert after == before


def test_purge_uses_the_setting_or_explicit_days(load_grace, fresh_import, grace_env):
    mod, _ = load_grace()
    old = _seed(mod, "old@example.com", days_old=100, notified=False)
    new = _seed(mod, "new@example.com", days_old=10)

    code, out = _cli(fresh_import, "purge")
    assert code == 2 and "Lead retention is off" in out

    code, out = _cli(fresh_import, "purge", "--days", "30", "--dry-run")
    assert code == 0 and "Matched 1 lead row(s)" in out and "1 of them were never alerted" in out
    assert _ids(mod) == [old, new]

    grace_env(EOLKITS_LEAD_RETENTION_DAYS="60")
    code, out = _cli(fresh_import, "purge")
    assert code == 0 and "Retention: 60 days (from EOLKITS_LEAD_RETENTION_DAYS)" in out
    assert "Deleted 1 lead row(s)." in out
    assert _ids(mod) == [new]

    for bad in ("0", "-5", "abc"):
        with pytest.raises(SystemExit):
            _cli(fresh_import, "purge", "--days", bad)


def test_runs_as_a_module(load_grace, tmp_path):
    """The exact command the runbook tells the operator to run."""
    mod, _ = load_grace()
    _seed(mod, "person@example.com")
    env = {**os.environ, "PYTHONPATH": str(API_ROOT), "EOLKITS_DATA_DIR": str(tmp_path)}
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "eolkits_grace.lead_admin",
            "delete",
            "--email",
            "person@example.com",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert "Deleted 1 lead row(s)." in run.stdout
    assert "LEAD_NOTIFY_TO mailbox" in run.stdout
    assert _ids(mod) == []


# ---- list and reclassify (lead screening) ----------------------------------- #

MINUTE = timedelta(minutes=1)
T0 = datetime(2026, 7, 4, 18, 39, tzinfo=UTC)
BTC = "IMPORTANT! 1.3426 BTC IS YOURS FOR WITHDRAWAL ACT QUICKLY https://shorto.link/Ab12C"
REDESIGN_PITCH = (
    "Hi, I'm Sam. We help businesses redesign their websites. I took a quick look at your "
    "site and saw a few opportunities to improve it. Grab a time here: https://cal.example/"
)
# (minutes after T0, email, product, form fields): shaped like production's
# leads table before screening, every row already alerted.
HISTORY = [
    *[(0, "bot@example.net", "Contact", {"topic": t, "message": BTC}) for t in "abcde"],
    (60, "bot@forms-bot.example", "Care", {"work_description": "kq3vzr"}),
    (60, "bot@forms-bot.example", "Discovery", {"goal": "w8ptsd"}),
    (
        60,
        "bot@forms-bot.example",
        "Partner",
        {"agency_name": "Transfer of funds to your name >>> graph.org/TRANSACTION-1"},
    ),
    (120, "quote@example.org", "Contact", {"message": "Ciao, volevo sapere il tuo prezzo."}),
    (
        180,
        "sales@toledotechnologies.com",
        "Contact",
        {"message": "Let you know about our new harness. Get yours today, 50% OFF!"},
    ),
    (240, "dana@example.com", "Apps", {"message": "We need a scheduling tool for our clinic."}),
    (300, "sam@agency.example", "Contact", {"message": REDESIGN_PITCH}),
    (301, "sam@agency.example", "Contact", {"context": "Direct contact inquiry"}),
]
EXPECTED = {
    1: ("spam", "link to a known spam host (shorto.link)"),
    2: ("spam", "link to a known spam host (shorto.link)"),
    3: ("spam", "link to a known spam host (shorto.link)"),
    4: ("spam", "link to a known spam host (shorto.link)"),
    5: ("spam", "link to a known spam host (shorto.link)"),
    6: ("suspect", "empty or one-word message"),
    7: ("suspect", "empty or one-word message"),
    8: ("spam", "link to a known spam host (graph.org)"),
    9: ("suspect", "one-line price question"),
    10: ("suspect", "sales pitch wording; sent from the studio's own domain"),
    11: ("ok", None),
    12: ("suspect", "sales pitch wording"),
    13: ("duplicate", "repeat of lead 12 within 10 minutes"),
}
DATA_COLUMNS = "id, ts, email, name, product, source, fields, notified"


def _production_history(grace_env, tmp_path, *, migrate: bool = True):
    """state.sqlite3 with the pre-screening schema and HISTORY in it, then (as
    the API does at startup) migrated. Returns (database path, Store)."""
    data_dir = tmp_path / "prod"
    data_dir.mkdir()
    grace_env(EOLKITS_DATA_DIR=str(data_dir))
    db = data_dir / "state.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE leads (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, "
        "email TEXT NOT NULL, name TEXT, product TEXT, source TEXT, fields TEXT, "
        "notified INTEGER NOT NULL DEFAULT 0)"
    )
    for minutes, email, product, fields in HISTORY:
        conn.execute(
            "INSERT INTO leads(ts, email, product, source, fields, notified) "
            "VALUES (?, ?, ?, 'toledotechnologies.com/contact', ?, 1)",
            ((T0 + minutes * MINUTE).isoformat(), email, product, json.dumps(fields)),
        )
    conn.commit()
    conn.close()
    from eolkits_grace.store import Store

    return db, (Store(db) if migrate else None)


def _rows(db, columns: str = DATA_COLUMNS) -> list[tuple]:
    conn = sqlite3.connect(db)
    try:
        return conn.execute(f"SELECT {columns} FROM leads ORDER BY id").fetchall()
    finally:
        conn.close()


def test_reclassify_dry_run_then_for_real(grace_env, fresh_import, tmp_path):
    db, _ = _production_history(grace_env, tmp_path)
    data_before = _rows(db)
    assert {row[0] for row in _rows(db, "status")} == {"ok"}  # the migration default

    code, out = _cli(fresh_import, "reclassify", "--dry-run")
    assert code == 0
    assert "Checked 13 lead row(s); 12 would change." in out
    # A message-less submission on a different product's form is a new
    # inquiry (flagged, still alerted), not a repeat of the Care form.
    assert (
        "  id 7 | 2026-07-04 19:39 | ok -> suspect | Discovery | empty or one-word message" in out
    )
    assert "By change: ok -> duplicate 1, ok -> spam 6, ok -> suspect 5." in out
    assert "Dry run: nothing was changed." in out
    assert "kq3vzr" not in out and "BTC" not in out  # never the form contents
    assert {row[0] for row in _rows(db, "status")} == {"ok"}

    code, out = _cli(fresh_import, "reclassify")
    assert code == 0
    assert "Checked 13 lead row(s); 12 to change." in out
    assert "Updated the status of 12 lead row(s). No row was deleted" in out
    assert _rows(db) == data_before  # status only: every other value is untouched
    assert {row[0]: (row[1], row[2]) for row in _rows(db, "id, status, status_reason")} == EXPECTED

    code, out = _cli(fresh_import, "reclassify")
    assert code == 0 and "Checked 13 lead row(s); 0 to change." in out


def test_reclassify_reports_leads_that_become_alertable(grace_env, fresh_import, tmp_path):
    db, store = _production_history(grace_env, tmp_path)
    with store.connect() as conn:  # a real lead once held back, never alerted
        conn.execute("UPDATE leads SET status = 'spam', notified = 0 WHERE id = 11")
    code, out = _cli(fresh_import, "reclassify", "--dry-run")
    assert "  id 11 | 2026-07-04 22:39 | spam -> ok | Apps | -" in out
    assert "1 of them were never alerted to the owner and become alertable" in out
    assert store.count_unnotified() == 0
    _cli(fresh_import, "reclassify")
    assert store.count_unnotified() == 1  # the API's re-send sweep picks it up


def test_list_shows_status_and_reason_never_the_message(grace_env, fresh_import, tmp_path):
    _production_history(grace_env, tmp_path)
    _cli(fresh_import, "reclassify")

    code, out = _cli(fresh_import, "list")
    assert code == 0
    assert (
        "id 1 | 2026-07-04 18:39 | spam | Contact | link to a known spam host (shorto.link)" in out
    )
    assert "id 11 | 2026-07-04 22:39 | ok | Apps | -" in out
    assert "Listed 13 lead row(s): ok 1, suspect 5, spam 6, duplicate 1." in out
    assert "add --show-message to see them" in out
    for private in ("BTC", "scheduling tool", "dana@example.com", "prezzo"):
        assert private not in out

    code, out = _cli(fresh_import, "list", "--status", "suspect", "--since", "2026-07-04")
    assert code == 0
    assert [line.split(" | ")[0] for line in out.splitlines() if line.startswith("id ")] == [
        "id 6",
        "id 7",
        "id 9",
        "id 10",
        "id 12",
    ]
    assert "Listed 5 lead row(s) captured on or after 2026-07-04 UTC and with status suspect" in out

    code, out = _cli(fresh_import, "list", "--since", "2026-07-05")
    assert "Listed 0 lead row(s) captured on or after 2026-07-05 UTC." in out

    code, out = _cli(fresh_import, "list", "--status", "ok", "--show-message")
    assert "    message: We need a scheduling tool for our clinic." in out


def test_list_prints_form_text_safely(load_grace, fresh_import):
    mod, _ = load_grace()
    mod.store.record_lead(
        email="a@example.com",
        product="Apps\x1b[2J‮",
        fields={"message": "line one\r\nline two \x1b]0;owned\x07 end"},
    )
    code, out = _cli(fresh_import, "list", "--show-message")
    assert code == 0
    assert "\x1b" not in out and "‮" not in out and "\x07" not in out
    assert "| Apps\\u001b[2J\\u202e |" in out
    assert "    message: line one\n      line two \\u001b]0;owned\\u0007 end" in out


def test_list_and_reclassify_need_the_migrated_schema(grace_env, fresh_import, tmp_path):
    db, _ = _production_history(grace_env, tmp_path, migrate=False)
    schema = _rows(db, "COUNT(*)")
    for argv in (["list"], ["reclassify"], ["reclassify", "--dry-run"]):
        code, out = _cli(fresh_import, *argv)
        assert code == 1 and "no lead screening status yet" in out
    conn = sqlite3.connect(db)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(leads)")]
    conn.close()
    assert "status" not in columns  # the CLI never migrates
    assert _rows(db, "COUNT(*)") == schema
    # purge still works on the old schema.
    code, out = _cli(fresh_import, "purge", "--days", "30", "--dry-run")
    assert code == 0 and "Matched 13 lead row(s)" in out


@pytest.mark.parametrize("value", ["2026-9-1", "yesterday", "2026-02-30", "20260901"])
def test_list_rejects_a_bad_since_date(load_grace, fresh_import, value):
    load_grace()
    with pytest.raises(SystemExit) as exc:
        _cli(fresh_import, "list", "--since", value)
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        _cli(fresh_import, "list", "--status", "maybe")


def test_reclassify_runs_as_a_module(grace_env, tmp_path):
    db, _ = _production_history(grace_env, tmp_path)
    env = {**os.environ, "PYTHONPATH": str(API_ROOT), "EOLKITS_DATA_DIR": str(db.parent)}
    for argv in (["reclassify", "--dry-run"], ["list", "--status", "duplicate"]):
        run = subprocess.run(
            [sys.executable, "-m", "eolkits_grace.lead_admin", *argv],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert run.returncode == 0, run.stderr
    assert "12 would change" not in run.stdout  # the list run
    assert "Listed 0 lead row(s) with status duplicate." in run.stdout
