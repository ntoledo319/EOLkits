from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app(tmp_path, monkeypatch, **env_overrides):
    root = Path(__file__).resolve().parents[3]
    api_root = root / "apps" / "grace-api"
    runner_root = root / "apps" / "runner"
    for path in (api_root, runner_root):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    env = {
        "ENVIRONMENT": "test",
        "EOLKITS_DATA_DIR": str(tmp_path),
        "STRIPE_KEY": "sk_test_dummy",
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "PUBLIC_SITE_URL": "https://eolkits.com",
        "PUBLIC_API_URL": "https://eolkits.com",
        "EOLKITS_INLINE_RUNNER": "0",
    }
    env.update(env_overrides)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    for name in list(sys.modules):
        if name == "eolkits_grace" or name.startswith("eolkits_grace."):
            del sys.modules[name]
    mod = importlib.import_module("eolkits_grace.app")
    return mod, TestClient(mod.app)


def test_lead_json_records_and_returns_id(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post(
        "/api/v1/lead",
        json={"email": "buyer@acme.com", "name": "Dana", "product": "SiteLift Fit Check"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    leads = mod.store.recent_leads()
    assert len(leads) == 1
    assert leads[0]["email"] == "buyer@acme.com"
    assert leads[0]["product"] == "SiteLift Fit Check"


def test_lead_form_post_redirects_to_next(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post(
        "/api/v1/lead",
        data={
            "email": "lead@example.com",
            "name": "Pat",
            "product": "ToledoWeb Migration Audit",
            "_next": "https://web.toledotechnologies.com/thanks/",
            "_subject": "ignored when product present",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "https://web.toledotechnologies.com/thanks/"
    assert mod.store.recent_leads()[0]["email"] == "lead@example.com"


def test_lead_relative_next_resolved_against_origin(tmp_path, monkeypatch):
    # Forms whose _next is site-relative (e.g. ToledoTechnologies /contact?submitted=true)
    # redirect back to the submitting site via the Origin header.
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post(
        "/api/v1/lead",
        data={"email": "a@b.com", "_next": "/contact?submitted=true"},
        headers={"origin": "https://toledotechnologies.com"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "https://toledotechnologies.com/contact?submitted=true"


def test_lead_rejects_open_redirect(tmp_path, monkeypatch):
    # A hostile _next to an off-allowlist origin must NOT be honored (no open redirect);
    # the lead is still captured and a JSON 200 is returned instead.
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post(
        "/api/v1/lead",
        data={"email": "a@b.com", "_next": "https://evil.example.com/phish"},
        follow_redirects=False,
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert mod.store.recent_leads()[0]["email"] == "a@b.com"


def test_lead_honeypot_drops_silently(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post(
        "/api/v1/lead",
        data={"email": "bot@spam.com", "_honey": "i am a bot"},
        follow_redirects=False,
    )
    assert r.status_code == 200  # accepted, but...
    assert mod.store.recent_leads() == []  # ...nothing recorded


def test_lead_requires_a_valid_email(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post("/api/v1/lead", data={"name": "No Email"})
    assert r.status_code == 400
    assert mod.store.recent_leads() == []


def test_lead_notify_success_marks_notified(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, LEAD_NOTIFY_TO="owner@toledo.test")
    monkeypatch.setattr(mod, "send_email", lambda *a, **k: None)  # send succeeds
    r = client.post("/api/v1/lead", json={"email": "warm@lead.com", "product": "ToledoWeb Migration Audit"})
    assert r.status_code == 200
    lead = mod.store.recent_leads()[0]
    assert lead["notified"] == 1               # confirmed-sent -> flagged
    assert mod.store.count_unnotified() == 0


def test_lead_notify_failure_is_durable_and_recoverable(tmp_path, monkeypatch):
    # Resend outage: the lead must still be captured, left notified=0 (not silently
    # dropped), and then self-heal when the re-send sweep runs after email recovers.
    mod, client = _load_app(tmp_path, monkeypatch, LEAD_NOTIFY_TO="owner@toledo.test")

    def _boom(*a, **k):
        raise RuntimeError("resend down")

    monkeypatch.setattr(mod, "send_email", _boom)
    r = client.post("/api/v1/lead", json={"email": "atrisk@lead.com", "product": "Site Rescue"})
    assert r.status_code == 200
    assert r.json()["ok"] is True              # buyer still gets success
    lead = mod.store.recent_leads()[0]
    assert lead["email"] == "atrisk@lead.com"  # durable row kept
    assert lead["notified"] == 0               # owner NOT silently told it's fine
    assert mod.store.count_unnotified() == 1

    monkeypatch.setattr(mod, "send_email", lambda *a, **k: None)  # email recovers
    result = mod.resend_unnotified_leads()
    assert result == {"attempted": 1, "still_unnotified": 0}
    assert mod.store.recent_leads()[0]["notified"] == 1
    assert mod.store.count_unnotified() == 0


def test_leads_migration_backfills_existing_as_notified(tmp_path, monkeypatch):
    # An OLD prod leads table (no `notified` column) with existing rows must migrate so
    # those rows are notified=1 (already-handled) — preventing duplicate-alert spam on
    # deploy — while NEW inserts still start unnotified and earn the sweep's protection.
    import sqlite3

    _load_app(tmp_path, monkeypatch)  # sets sys.path + env
    from eolkits_grace.store import Store

    old_db = tmp_path / "old.sqlite3"
    conn = sqlite3.connect(old_db)
    conn.execute(
        "CREATE TABLE leads (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, "
        "email TEXT NOT NULL, name TEXT, product TEXT, source TEXT, fields TEXT)"
    )
    conn.execute("INSERT INTO leads(ts,email,fields) VALUES('2026-06-01','old1@x.com','{}')")
    conn.execute("INSERT INTO leads(ts,email,fields) VALUES('2026-06-02','old2@x.com','{}')")
    conn.commit()
    conn.close()

    s = Store(old_db)  # __init__ runs init() -> the leads migration + backfill
    assert s.count_unnotified() == 0  # both pre-existing rows backfilled to notified=1
    assert all(row["notified"] == 1 for row in s.recent_leads())
    s.record_lead(email="new@x.com", product="ToledoWeb Migration Audit")
    assert s.count_unnotified() == 1  # only the NEW lead is unnotified


def test_lead_preserves_heterogeneous_and_checkbox_fields(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    # ToledoMobile-style: repeated checkbox `platform`, custom field names, no `name`.
    r = client.post(
        "/api/v1/lead",
        data={
            "email": "founder@startup.io",
            "company": "Startup Inc",
            "platform": ["iOS native", "Android native"],  # repeated checkbox
            "summary": "Need an MVP in 8 weeks",
            "_captcha": "false",
        },
    )
    assert r.status_code == 200
    lead = mod.store.recent_leads()[0]
    assert lead["email"] == "founder@startup.io"
    assert lead["name"] == "Startup Inc"  # falls back to company
    import json as _json
    fields = _json.loads(lead["fields"])
    assert fields["platform"] == "iOS native, Android native"  # checkboxes joined
    assert fields["summary"] == "Need an MVP in 8 weeks"
    assert "_captcha" not in fields  # control fields stripped
