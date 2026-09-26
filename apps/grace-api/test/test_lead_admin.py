"""The operator deletion CLI: python -m eolkits_grace.lead_admin."""

from __future__ import annotations

import io
import os
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
