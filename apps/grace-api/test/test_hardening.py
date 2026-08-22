from __future__ import annotations

import hashlib
import hmac
import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request


def _load_app(tmp_path, monkeypatch, **env_overrides):
    root = Path(__file__).resolve().parents[3]
    for path in (root / "apps" / "grace-api", root / "apps" / "runner"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    env = {
        "ENVIRONMENT": "test",
        "EOLKITS_DATA_DIR": str(tmp_path),
        "STRIPE_KEY": "sk_test_dummy",
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "PUBLIC_SITE_URL": "https://eolkits.com",
        "PUBLIC_API_URL": "https://eolkits.com",
        "EOLKITS_INLINE_RUNNER": "1",
        "EOLKITS_AUDIT_CHECKOUT_ENABLED": "1",
        "RESEND_API_KEY": "re_test",
        "LEAD_NOTIFY_TO": "",
    }
    env.update(env_overrides)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    for name in list(sys.modules):
        if name == "eolkits_grace" or name.startswith("eolkits_grace."):
            del sys.modules[name]
    mod = importlib.import_module("eolkits_grace.app")
    return mod, TestClient(mod.app)


def _force_running(store, job_id, *, attempts=0, updated_at="2000-01-01T00:00:00+00:00"):
    with store.connect() as conn:
        conn.execute(
            "UPDATE jobs SET status='running', attempts=?, updated_at=? WHERE id=?",
            (attempts, updated_at, job_id),
        )


def test_reaper_recovers_job_orphaned_in_running(tmp_path, monkeypatch):
    # A crash mid-fulfillment used to leave a paid job stuck in 'running' forever.
    mod, _ = _load_app(tmp_path, monkeypatch)
    job_id = mod.store.enqueue("audit_pdf", {"sessionId": "cs_1"})
    _force_running(mod.store, job_id)

    reclaimed = mod.store.reclaim_stale_running_jobs(60)
    assert reclaimed == 1
    job = next(j for j in mod.store.recent_jobs() if j["id"] == job_id)
    assert job["status"] == "pending"  # back on the queue for the drainer
    assert job["attempts"] == 1  # counted, so it can't loop forever


def test_reaper_deadletters_a_poison_pill(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch)
    job_id = mod.store.enqueue("audit_pdf", {"sessionId": "cs_2"}, max_attempts=2)
    _force_running(mod.store, job_id, attempts=1)

    mod.store.reclaim_stale_running_jobs(60)
    mod._run_job(job_id, {"type": "audit_pdf", "sessionId": "cs_2"})
    job = next(j for j in mod.store.recent_jobs() if j["id"] == job_id)
    assert job["status"] == "compensated"  # terminal state cannot starve newer failures


def test_reaper_leaves_a_fresh_running_job_alone(tmp_path, monkeypatch):
    # A job that is merely slow (claimed just now) must never be double-run.
    from datetime import UTC, datetime

    mod, _ = _load_app(tmp_path, monkeypatch)
    job_id = mod.store.enqueue("audit_pdf", {"sessionId": "cs_3"})
    _force_running(mod.store, job_id, updated_at=datetime.now(UTC).isoformat())
    assert mod.store.reclaim_stale_running_jobs(1800) == 0


def test_lead_endpoint_rate_limited_after_burst(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    for i in range(mod._LEAD_RATE_MAX):
        r = client.post("/api/v1/lead", json={"email": f"a{i}@b.com"})
        assert r.status_code == 200
    blocked = client.post("/api/v1/lead", json={"email": "flood@b.com"})
    assert blocked.status_code == 429


def test_rate_window_is_anchored_to_first_request(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch)
    store_module = sys.modules["eolkits_grace.store"]
    now = [59]
    monkeypatch.setattr(store_module.time, "time", lambda: now[0])

    assert mod.store.allow_rate("boundary", limit=2, window_seconds=60)
    assert mod.store.allow_rate("boundary", limit=2, window_seconds=60)
    now[0] = 60
    assert not mod.store.allow_rate("boundary", limit=2, window_seconds=60)
    now[0] = 119
    assert mod.store.allow_rate("boundary", limit=2, window_seconds=60)


def test_lead_endpoint_rejects_malformed_email(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post("/api/v1/lead", json={"email": "not-an-email"})
    assert r.status_code == 400
    assert mod.store.recent_leads() == []


def test_request_source_key_is_secret_keyed_and_referrer_query_is_dropped(tmp_path, monkeypatch):
    secret = "s" * 32
    mod, _ = _load_app(tmp_path, monkeypatch, EOLKITS_INTERNAL_URL_SECRET=secret)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"referer", b"https://example.com/landing?token=secret#frag")],
            "client": ("203.0.113.8", 1234),
        }
    )
    expected = hmac.new(secret.encode(), b"203.0.113.8", hashlib.sha256).hexdigest()[:24]
    assert mod._request_source_key(request) == expected
    assert mod._safe_referrer_source(request) == "https://example.com/landing"


def test_public_bodies_and_event_names_are_bounded(tmp_path, monkeypatch):
    mod, client = _load_app(
        tmp_path,
        monkeypatch,
        EOLKITS_MAX_EVENT_BYTES="256",
        EOLKITS_MAX_FORM_BYTES="64",
    )
    assert client.post("/api/events", content=b"x" * 257).status_code == 413
    assert client.post("/api/v1/lead", content=b"x" * 65).status_code == 413
    unsupported = client.post("/api/events", json={"event": "purchase_success"})
    assert unsupported.status_code == 400

    recorded = client.post(
        "/api/events",
        json={
            "event": "scan_completed",
            "meta": {"finding_count": 2, "file_count": 3, "session_id": "must-not-store"},
        },
    )
    assert recorded.status_code == 200
    with mod.store.connect() as conn:
        meta = conn.execute("SELECT meta FROM events").fetchone()["meta"]
    assert "session_id" not in meta


def test_status_hides_recent_jobs_without_admin_token(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, EOLKITS_ADMIN_TOKEN="s3cret")
    mod.store.enqueue("audit_pdf", {"sessionId": "cs_4"})

    anon = client.get("/status").json()
    assert "recent_jobs" not in anon  # per-order payloads not leaked
    assert "funnel_7d" in anon  # aggregate metrics stay public

    authed = client.get("/status", headers={"X-Admin-Token": "s3cret"}).json()
    assert "recent_jobs" in authed
    assert any(j["type"] == "audit_pdf" for j in authed["recent_jobs"])


def test_lead_notify_survives_real_http_failure(tmp_path, monkeypatch):
    # Regression for the headline bug: a Resend 500 must NOT be mistaken for a
    # successful send. The lead stays notified=0 and lands in the recovery queue.
    mod, client = _load_app(
        tmp_path, monkeypatch, LEAD_NOTIFY_TO="owner@toledo.test", RESEND_API_KEY="re_test"
    )
    from eolkits_grace import email as email_mod

    class _Resp:
        ok = False
        status_code = 500
        text = "resend 500"

        def json(self):
            return {}

    monkeypatch.setattr(email_mod.requests, "post", lambda *a, **k: _Resp())

    r = client.post("/api/v1/lead", json={"email": "atrisk@lead.com", "product": "Site Rescue"})
    assert r.status_code == 200
    lead = mod.store.recent_leads()[0]
    assert lead["notified"] == 0
    assert mod.store.count_unnotified() == 1
