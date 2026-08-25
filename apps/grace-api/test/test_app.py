from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import importlib
import json
import sys
from pathlib import Path

import pytest
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
        "EOLKITS_INTERNAL_URL_SECRET": "test-internal-secret",
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


def test_health_reports_grace_native_primitives(tmp_path, monkeypatch):
    _, client = _load_app(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["storage"] == "filesystem"
    assert data["database"] == "sqlite"
    assert response.headers["cache-control"] == "no-store"
    assert "unnotified_leads" not in data
    assert "refunds_pending" not in data


def test_upload_checkout_verify_flow_uses_local_state(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)

    presign = client.post(
        "/upload/presign",
        json={"filename": "template.yaml", "contentType": "text/yaml", "size": 19},
    )
    assert presign.status_code == 200
    upload_url = presign.json()["uploadUrl"]
    uploaded = client.put(
        upload_url.removeprefix("https://eolkits.com"),
        content=b"Runtime: nodejs20.x",
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["success"] is True

    checkout = client.post(
        "/api/audit/checkout",
        data={"email": "buyer@example.com", "upload_url": upload_url},
        headers={"accept": "application/json"},
    )
    assert checkout.status_code == 200
    assert checkout.json()["url"].startswith("https://checkout.stripe.com/test")

    sha = "a" * 64
    mod.store.put_json("verify:" + sha, {"generatedAt": "now", "rulePackVersion": "test"})
    verify = client.get(f"/verify/{sha}")
    assert verify.status_code == 200
    assert verify.json()["valid"] is True


def test_github_pack_install_is_closed(tmp_path, monkeypatch):
    _, client = _load_app(tmp_path, monkeypatch)
    response = client.get("/pack/install")
    assert response.status_code == 410


def test_stripe_webhook_rejects_bad_signature(tmp_path, monkeypatch):
    _, client = _load_app(tmp_path, monkeypatch)
    response = client.post(
        "/webhook/stripe",
        content=json.dumps({"id": "evt_1", "type": "checkout.session.completed"}),
        headers={"stripe-signature": "bad"},
    )
    assert response.status_code == 400


def test_partner_account_and_fulfillment_are_closed(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)

    signup = client.post(
        "/partners/signup",
        data={
            "email": "partner@example.com",
            "display_name": "Acme Partners",
            "domain": "example.com",
        },
    )
    assert signup.status_code == 410
    audit = client.post(
        "/partners/acme-partners/audit",
        data={
            "buyer_email": "buyer@example.com",
            "upload_id": "unused",
            "stripe_session_id": "cs_123",
        },
    )
    assert audit.status_code == 410
    inquiry = client.post(
        "/api/license/inquiry",
        data={"email": "buyer@example.com", "company": "Acme", "repos": "5"},
    )
    assert inquiry.status_code == 410
    assert mod.store.recent_jobs() == []


def test_production_startup_fails_closed_without_secrets(tmp_path, monkeypatch):
    """ENVIRONMENT=production with sandbox/dummy secrets must refuse to start."""
    import importlib
    import sys as _sys

    root = Path(__file__).resolve().parents[3]
    for path in (root / "apps" / "grace-api", root / "apps" / "runner"):
        if str(path) not in _sys.path:
            _sys.path.insert(0, str(path))
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("EOLKITS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STRIPE_KEY", "sk_test_dummy")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    for name in list(_sys.modules):
        if name == "eolkits_grace" or name.startswith("eolkits_grace."):
            del _sys.modules[name]
    cfg = importlib.import_module("eolkits_grace.config")
    settings = cfg.Settings()
    assert settings.is_production
    missing = settings.missing_production_secrets()
    assert any("STRIPE_KEY" in m for m in missing)
    with pytest.raises(RuntimeError):
        settings.require_runtime_secrets()


def test_audit_checkout_defaults_closed(monkeypatch):
    monkeypatch.delenv("EOLKITS_AUDIT_CHECKOUT_ENABLED", raising=False)
    for name in list(sys.modules):
        if name == "eolkits_grace.config":
            del sys.modules[name]
    cfg = importlib.import_module("eolkits_grace.config")
    assert cfg.Settings().audit_checkout_enabled is False


def test_stripe_webhook_is_idempotent_and_validates(tmp_path, monkeypatch):
    """A valid, signed checkout.session.completed fulfills exactly once; a
    duplicate delivery is a no-op; an unpaid session is rejected."""
    # A live-style key takes the non-demo validation/ingest path; we stub the
    # authoritative session retrieval + signature check below.
    mod, client = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")

    presign = client.post(
        "/upload/presign",
        json={"filename": "template.yaml", "contentType": "text/yaml", "size": 19},
    )
    upload_id = presign.json()["uploadId"]
    client.put(
        presign.json()["uploadUrl"].removeprefix("https://eolkits.com"),
        content=b"Runtime: nodejs20.x",
    )
    upload_sha = hashlib.sha256(b"Runtime: nodejs20.x").hexdigest()

    paid_session = {
        "id": "cs_live_1",
        "status": "complete",
        "payment_status": "paid",
        "currency": "usd",
        "amount_total": 29900,
        "livemode": False,
        "customer_email": "buyer@example.com",
        "payment_intent": "pi_1",
        "metadata": {
            "project": "eolkits",
            "sku": "audit",
            "upload_id": upload_id,
            "upload_sha256": upload_sha,
            "price_id": "price_1TRoGjDL3cQl851oiIWR5JIa",
        },
        "line_items": {"data": [{"price": {"id": "price_1TRoGjDL3cQl851oiIWR5JIa"}}]},
    }
    monkeypatch.setattr(mod, "retrieve_checkout_session", lambda settings, sid: paid_session)
    monkeypatch.setattr(mod, "verify_stripe_signature", lambda *a, **k: True)
    # Don't actually run the runner during the webhook background task.
    monkeypatch.setattr(mod, "_run_job", lambda *a, **k: None)

    event = json.dumps(
        {
            "id": "evt_paid_1",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_live_1"}},
        }
    )
    r1 = client.post("/webhook/stripe", content=event, headers={"stripe-signature": "ok"})
    assert r1.status_code == 200
    assert r1.text == "OK"
    purchase = mod.store.get_purchase_by_session("cs_live_1")
    assert purchase and purchase["sku"] == "audit" and purchase["amount"] == 29900

    # Duplicate delivery -> already processed, no second purchase row mutation.
    r2 = client.post("/webhook/stripe", content=event, headers={"stripe-signature": "ok"})
    assert r2.status_code == 200
    assert r2.text == "Already processed"

    # An unpaid session is rejected.
    unpaid = dict(paid_session, id="cs_live_2", payment_status="unpaid")
    monkeypatch.setattr(mod, "retrieve_checkout_session", lambda settings, sid: unpaid)
    bad_event = json.dumps(
        {
            "id": "evt_unpaid",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_live_2"}},
        }
    )
    r3 = client.post("/webhook/stripe", content=bad_event, headers={"stripe-signature": "ok"})
    assert r3.status_code == 400


def test_events_beacon_records_funnel(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, EOLKITS_ADMIN_TOKEN="test-admin")
    r = client.post(
        "/api/events",
        json={"event": "view", "sku": "audit", "utm_source": "migrate", "kit": "al2023-gate"},
    )
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert mod.store.event_counts(7).get("view") == 1
    status = client.get("/status", headers={"X-Admin-Token": "test-admin"}).json()
    assert status["funnel_7d"].get("view") == 1


def test_drift_checkout_refuses_the_charge(tmp_path, monkeypatch):
    """The retired Drift route must never reach a payment flow."""
    mod, client = _load_app(tmp_path, monkeypatch)
    r = client.post(
        "/api/drift/checkout",
        data={"email": "buyer@example.com", "repo": "owner/repo", "utm_source": "home"},
        headers={"accept": "application/json"},
    )
    assert r.status_code == 410
    assert mod.store.event_counts(7).get("checkout_started") is None


def test_audit_checkout_propagates_attribution_metadata(tmp_path, monkeypatch):
    """source/utm/kit must ride along on the Stripe metadata (demo URL echoes it)."""
    mod, client = _load_app(tmp_path, monkeypatch)
    presign = client.post(
        "/upload/presign",
        json={"filename": "template.yaml", "contentType": "text/yaml", "size": 19},
    )
    upload_id = presign.json()["uploadId"]
    client.put(
        presign.json()["uploadUrl"].removeprefix("https://eolkits.com"),
        content=b"Runtime: nodejs20.x",
    )
    r = client.post(
        "/api/audit/checkout",
        data={
            "email": "buyer@example.com",
            "upload_id": upload_id,
            "deadline": "2026-06-30",
            "utm_source": "migrate",
            "kit": "lambda-lifeline",
        },
        headers={"accept": "application/json"},
    )
    assert r.status_code == 200
    url = r.json()["url"]
    assert "utm_source=migrate" in url and "kit=lambda-lifeline" in url


def test_store_migrates_legacy_jobs_table(tmp_path):
    """A pre-existing DB with the old `jobs` schema (no dedupe_key) must migrate
    cleanly — regression for the production redeploy that crash-looped on
    `no such column: dedupe_key`."""
    import sqlite3

    from eolkits_grace.store import Store

    db = tmp_path / "state.sqlite3"
    legacy = sqlite3.connect(db)
    legacy.executescript(
        """
        CREATE TABLE jobs(id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            payload TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_error TEXT);
        CREATE TABLE kv(key TEXT PRIMARY KEY, value TEXT, expires_at TEXT);
        """
    )
    legacy.commit()
    legacy.close()

    store = Store(db)  # must not raise
    jid = store.enqueue("audit_pdf", {"x": 1}, dedupe_key="k1")
    assert store.enqueue("audit_pdf", {"x": 1}, dedupe_key="k1") == jid  # dedupe works


def test_audit_price_is_stable_across_deadlines(tmp_path, monkeypatch):
    _load_app(tmp_path, monkeypatch)
    from eolkits_grace import pricing

    tiers = [
        pricing.audit_price_for_deadline(deadline)
        for deadline in (None, "2020-01-01", "2026-08-22", "2035-12-31", "invalid")
    ]
    assert {tier["price_usd"] for tier in tiers} == {299}
    assert {tier["stripe_price_id"] for tier in tiers} == {"price_1TRoGjDL3cQl851oiIWR5JIa"}


def test_only_audit_is_an_active_paid_sku(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch)
    for sku in ("migration_pack", "org_license", "drift_watch", "unknown"):
        assert "not available" in mod._paid_fulfillment_blocker(sku, {})


def test_capability_handshake_and_status_fail_closed(tmp_path, monkeypatch):
    _, client = _load_app(tmp_path, monkeypatch)

    capabilities = client.get("/api/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.headers["cache-control"] == "no-store"
    assert capabilities.json()["audit"] == {
        "checkout_enabled": True,
        "reason": "ready",
        "report_version": "2.0",
        "accepts": ["repository_zip", "single_source_file"],
    }
    assert capabilities.json()["migration_pack"]["checkout_enabled"] is False

    status = client.get("/api/status").json()
    assert set(status["components"]) == {"storage", "stripe", "email", "runner"}
    assert status["overall"] == "degraded"
    assert "commerce_7d" not in status


def test_upload_is_immutable_and_get_requires_short_lived_signature(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    presign = client.post(
        "/upload/presign",
        json={"filename": "repo.zip", "contentType": "application/zip", "size": 5},
    ).json()
    upload_id = presign["uploadId"]
    upload_path = presign["uploadUrl"].removeprefix("https://eolkits.com")
    assert client.put(f"/upload/{upload_id}", content=b"first").status_code == 403
    assert client.put(upload_path, content=b"first").status_code == 200
    assert client.put(upload_path, content=b"other").status_code == 409
    assert client.get(f"/upload/{upload_id}").status_code == 403

    signed = mod._signed_upload_url(upload_id)
    signed_path = signed.removeprefix("https://eolkits.com")
    response = client.get(signed_path)
    assert response.status_code == 200
    assert response.content == b"first"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_paid_audit_with_missing_upload_is_durably_refunded(tmp_path, monkeypatch):
    from fastapi import BackgroundTasks

    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    paid_session = {
        "id": "cs_missing_upload",
        "status": "complete",
        "payment_status": "paid",
        "currency": "usd",
        "amount_total": 29900,
        "livemode": False,
        "customer_email": "buyer@example.com",
        "payment_intent": "pi_missing_upload",
        "metadata": {
            "project": "eolkits",
            "sku": "audit",
            "upload_id": "gone",
            "price_id": "price_1TRoGjDL3cQl851oiIWR5JIa",
        },
        "line_items": {"data": [{"price": {"id": "price_1TRoGjDL3cQl851oiIWR5JIa"}}]},
    }
    monkeypatch.setattr(mod, "retrieve_checkout_session", lambda settings, sid: paid_session)
    mod._ingest_paid_session("cs_missing_upload", BackgroundTasks())

    purchase = mod.store.get_purchase_by_session("cs_missing_upload")
    assert purchase and purchase["amount"] == 29900
    queued = mod.store.recent_jobs()
    assert queued[0]["type"] == "refund_payment"
    assert queued[0]["payload"]["payment_intent"] == "pi_missing_upload"
    assert "missing or incomplete" in queued[0]["payload"]["reason"]


@pytest.mark.parametrize(
    ("price_id", "amount"),
    [
        ("price_1TRoEZDL3cQl851o9DFh1DIz", 59900),
        ("price_1TRoGiDL3cQl851ouqnljzMx", 39900),
    ],
)
def test_retired_audit_payment_links_are_refund_only(tmp_path, monkeypatch, price_id, amount):
    from fastapi import BackgroundTasks

    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    session = {
        "id": f"cs_retired_{amount}",
        "status": "complete",
        "payment_status": "paid",
        "currency": "usd",
        "amount_total": amount,
        "livemode": False,
        "customer_email": "buyer@example.com",
        "payment_intent": f"pi_retired_{amount}",
        "metadata": {},
        "line_items": {"data": [{"price": {"id": price_id}}]},
    }
    monkeypatch.setattr(mod, "retrieve_checkout_session", lambda *_: session)

    mod._ingest_paid_session(session["id"], BackgroundTasks())

    purchase = mod.store.get_purchase_by_session(session["id"])
    assert purchase and purchase["sku"] == "audit"
    job = mod.store.recent_jobs()[0]
    assert job["type"] == "refund_payment"
    assert "unfulfillable Stripe session" in job["payload"]["reason"]


def test_stripe_event_errors_are_retryable_but_successes_dedupe(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch)
    payload = {"id": "evt_retry"}

    assert mod.store.record_stripe_event("evt_retry", "checkout.session.completed", payload)
    assert not mod.store.record_stripe_event("evt_retry", "checkout.session.completed", payload)
    with mod.store.connect() as conn:
        conn.execute(
            "UPDATE stripe_events SET received_at='2000-01-01T00:00:00+00:00' WHERE event_id='evt_retry'"
        )
    assert mod.store.record_stripe_event("evt_retry", "checkout.session.completed", payload)
    mod.store.mark_stripe_event("evt_retry", "error")
    assert mod.store.record_stripe_event("evt_retry", "checkout.session.completed", payload)
    mod.store.mark_stripe_event("evt_retry", "processed")
    assert not mod.store.record_stripe_event("evt_retry", "checkout.session.completed", payload)


def test_audit_delivery_is_input_bound_and_deletes_source_after_email(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, RESEND_API_KEY="re_test")
    source = b"Runtime: nodejs20.x\n"
    presign = client.post(
        "/upload/presign",
        json={"filename": "template.yaml", "contentType": "text/yaml", "size": len(source)},
    ).json()
    upload_id = presign["uploadId"]
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=source)
    expected_input_hash = hashlib.sha256(source).hexdigest()
    result = {
        "email": "buyer@example.com",
        "input_hash": "f" * 64,
        "evidence_hash": "e" * 64,
        "pdf_base64": base64.b64encode(b"%PDF-1.7\n%%EOF").decode(),
        "rule_pack_version": "audit-v2+test",
        "report_version": "2.0",
        "generated_at": "2026-08-21T12:00:00Z",
        "findings_count": 1,
        "evidence_count": 1,
        "scanned_files": 1,
    }
    job = {
        "type": "audit_pdf",
        "sessionId": "cs_delivery",
        "upload_id": upload_id,
        "upload_sha256": expected_input_hash,
        "email": "buyer@example.com",
    }

    with pytest.raises(RuntimeError, match="does not match"):
        mod._fulfill_audit(result, job)
    assert mod._upload_path(upload_id).is_file()

    result["input_hash"] = expected_input_hash
    sent: dict = {}
    monkeypatch.setattr(
        mod,
        "send_email",
        lambda settings, **kwargs: sent.update(kwargs) or {"ok": True},
    )
    mod._fulfill_audit(result, job)

    assert sent["to"] == "buyer@example.com"
    assert "signature=" in sent["html"]
    assert not mod._upload_path(upload_id).exists()
    assert mod.store.get_json(f"upload:{upload_id}") is None
    report_id = hmac.new(
        mod.settings.internal_url_secret.encode(),
        b"delivery:cs_delivery",
        hashlib.sha256,
    ).hexdigest()
    assert (mod.settings.reports_dir / f"{report_id}.pdf").is_file()
    assert client.get(f"/upload/report/{report_id}").status_code == 403
    signed_report = mod._signed_report_url(report_id).removeprefix("https://eolkits.com")
    report_response = client.get(signed_report)
    assert report_response.status_code == 200
    assert report_response.headers["cache-control"] == "private, no-store"
    assert report_response.headers["pragma"] == "no-cache"
    assert report_response.headers["x-content-type-options"] == "nosniff"
    verification = mod.store.get_json(f"verify:{'e' * 64}")
    assert verification["inputSha256"] == expected_input_hash


def test_checkout_double_submit_reuses_one_stripe_session(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    source = b"Runtime: nodejs20.x"
    presign = client.post(
        "/upload/presign", json={"filename": "template.yaml", "size": len(source)}
    ).json()
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=source)
    calls: list[dict] = []

    def create(*args, **kwargs):
        calls.append(kwargs)
        return {"id": "cs_once", "url": "https://checkout.stripe.com/c/pay/once", "mode": "live"}

    monkeypatch.setattr(mod, "create_checkout_session", create)
    form = {"email": "buyer@example.com", "upload_id": presign["uploadId"]}
    first = client.post("/api/audit/checkout", data=form, headers={"accept": "application/json"})
    second = client.post("/api/audit/checkout", data=form, headers={"accept": "application/json"})

    assert first.status_code == second.status_code == 200
    assert first.json()["url"] == second.json()["url"]
    assert len(calls) == 1
    assert calls[0]["idempotency_key"] == f"eolkits-audit-{presign['uploadId']}"
    assert calls[0]["success_path"] == "/success/?sku=audit"
    assert "CHECKOUT_SESSION_ID" not in calls[0]["success_path"]


def test_prepared_delivery_retry_is_byte_identical_and_skips_runner(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, RESEND_API_KEY="re_test")
    source = b"Runtime: nodejs20.x\n"
    presign = client.post(
        "/upload/presign", json={"filename": "template.yaml", "size": len(source)}
    ).json()
    upload_id = presign["uploadId"]
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=source)
    input_hash = hashlib.sha256(source).hexdigest()
    result = {
        "email": "buyer@example.com",
        "input_hash": input_hash,
        "evidence_hash": "e" * 64,
        "pdf_base64": base64.b64encode(b"%PDF-1.7\n%%EOF").decode(),
        "rule_pack_version": "audit-v2+test",
        "report_version": "2.0",
        "generated_at": "2026-08-21T12:00:00Z",
        "findings_count": 1,
        "evidence_count": 1,
        "scanned_files": 1,
    }
    job = {
        "type": "audit_pdf",
        "sessionId": "cs_retry_delivery",
        "upload_id": upload_id,
        "upload_sha256": input_hash,
        "email": "buyer@example.com",
    }
    attempts: list[dict] = []

    def accepted_then_timeout(settings, **kwargs):
        attempts.append(kwargs)
        raise mod.EmailDeliveryError("timeout after provider accepted", retryable=True)

    monkeypatch.setattr(mod, "send_email", accepted_then_timeout)
    with pytest.raises(mod.EmailDeliveryError):
        mod._fulfill_audit(result, job)
    prepared = mod.store.get_json("delivery:cs_retry_delivery")
    assert prepared["status"] == "prepared"
    assert mod._upload_path(upload_id).is_file()

    monkeypatch.setattr(
        mod,
        "send_email",
        lambda settings, **kwargs: attempts.append(kwargs) or {"ok": True, "id": "email_1"},
    )
    monkeypatch.setattr(
        mod,
        "_dispatch_runner",
        lambda *_: pytest.fail("a prepared delivery must not rerun the report engine"),
    )
    mod._execute_job(1, job)

    assert attempts[0]["html"] == attempts[1]["html"]
    assert attempts[0]["idempotency_key"] == attempts[1]["idempotency_key"]
    assert mod.store.get_json("delivery:cs_retry_delivery")["status"] == "delivered"
    assert not mod._upload_path(upload_id).exists()


def test_prepared_delivery_never_emails_a_truncated_report(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, RESEND_API_KEY="re_test")
    source = b"Runtime: nodejs20.x\n"
    presign = client.post(
        "/upload/presign", json={"filename": "template.yaml", "size": len(source)}
    ).json()
    upload_id = presign["uploadId"]
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=source)
    input_hash = hashlib.sha256(source).hexdigest()
    job = {
        "type": "audit_pdf",
        "sessionId": "cs_corrupt_delivery",
        "upload_id": upload_id,
        "upload_sha256": input_hash,
        "email": "buyer@example.com",
    }
    result = {
        "email": "attacker@example.com",
        "input_hash": input_hash,
        "evidence_hash": "d" * 64,
        "pdf_base64": base64.b64encode(b"%PDF-1.7\nreal report\n%%EOF").decode(),
        "rule_pack_version": "audit-v2+test",
        "report_version": "2.0",
        "generated_at": "2026-08-21T12:00:00Z",
        "findings_count": 1,
        "evidence_count": 1,
        "scanned_files": 1,
    }
    monkeypatch.setattr(
        mod,
        "send_email",
        lambda *a, **k: (_ for _ in ()).throw(
            mod.EmailDeliveryError("provider timeout", retryable=True)
        ),
    )
    with pytest.raises(mod.EmailDeliveryError):
        mod._fulfill_audit(result, job)
    delivery = mod.store.get_json("delivery:cs_corrupt_delivery")
    report_path = mod.settings.reports_dir / f"{delivery['reportId']}.pdf"
    report_path.write_bytes(b"%PDF-truncated")
    sends: list[dict] = []
    monkeypatch.setattr(mod, "send_email", lambda settings, **kwargs: sends.append(kwargs))

    with pytest.raises(RuntimeError, match="integrity check"):
        mod._deliver_prepared_audit(delivery, job)

    assert sends == []
    assert mod._upload_path(upload_id).exists()


def test_stale_subscription_charge_is_cancelled_before_refund(tmp_path, monkeypatch):
    from fastapi import BackgroundTasks

    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    session = {
        "id": "cs_stale_subscription",
        "status": "complete",
        "payment_status": "paid",
        "currency": "usd",
        "amount_total": 1900,
        "livemode": False,
        "customer_email": "buyer@example.com",
        "metadata": {},
        "subscription": {
            "id": "sub_stale",
            "latest_invoice": {"payment_intent": {"id": "pi_stale"}},
        },
        "line_items": {"data": [{"price": {"id": "price_1TRoGmDL3cQl851ofGZyxs6q"}}]},
    }
    monkeypatch.setattr(mod, "retrieve_checkout_session", lambda *_: session)
    mod._ingest_paid_session(session["id"], BackgroundTasks())
    job = mod.store.recent_jobs()[0]["payload"]
    assert job["type"] == "refund_payment"
    assert job["subscription_id"] == "sub_stale"

    actions: list[str] = []
    monkeypatch.setattr(
        mod,
        "cancel_subscription",
        lambda *a, **k: actions.append("cancel") or {"status": "canceled"},
    )
    monkeypatch.setattr(
        mod,
        "create_refund",
        lambda *a, **k: actions.append("refund")
        or {"id": "re_stale", "status": "succeeded", "amount": 1900},
    )
    mod._execute_refund_job(job)

    assert actions == ["cancel", "refund"]
    assert mod.store.get_purchase_by_session(session["id"])["refunded"] == 1


def test_subscription_without_payment_intent_requires_review_after_cancel(tmp_path, monkeypatch):
    from fastapi import BackgroundTasks

    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    session = {
        "id": "cs_subscription_no_pi",
        "status": "complete",
        "payment_status": "paid",
        "currency": "usd",
        "amount_total": 1900,
        "livemode": False,
        "metadata": {},
        "subscription": {"id": "sub_no_pi", "latest_invoice": {}},
        "line_items": {"data": [{"price": {"id": "price_1TRoGmDL3cQl851ofGZyxs6q"}}]},
    }
    monkeypatch.setattr(mod, "retrieve_checkout_session", lambda *_: session)
    mod._ingest_paid_session(session["id"], BackgroundTasks())
    job = mod.store.recent_jobs()[0]["payload"]
    assert job["type"] == "cancel_subscription"
    monkeypatch.setattr(mod, "cancel_subscription", lambda *a, **k: {"status": "canceled"})

    mod._execute_subscription_cancellation(job)

    review = mod.store.recent_jobs()[0]
    assert review["type"] == "refund_review"
    assert review["status"] == "requires_owner"
    assert mod.store.commerce_counts()["refunds_failed"] == 1


def test_retired_subscription_renewal_is_cancelled_and_refunded(tmp_path, monkeypatch):
    from fastapi import BackgroundTasks

    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    invoice = {
        "id": "in_retired_renewal",
        "billing_reason": "subscription_cycle",
        "status": "paid",
        "currency": "usd",
        "amount_paid": 1900,
        "livemode": False,
        "customer_email": "buyer@example.com",
        "subscription": "sub_retired_renewal",
        "payment_intent": "pi_retired_renewal",
        "lines": {"data": [{"price": {"id": "price_1TRoGmDL3cQl851ofGZyxs6q"}}]},
    }
    tasks = BackgroundTasks()
    mod._ingest_paid_invoice(invoice, tasks)
    job = mod.store.recent_jobs()[0]["payload"]
    assert job["type"] == "refund_payment"
    assert job["subscription_id"] == "sub_retired_renewal"
    actions: list[str] = []
    monkeypatch.setattr(
        mod,
        "cancel_subscription",
        lambda *a, **k: actions.append("cancel") or {"status": "canceled"},
    )
    monkeypatch.setattr(
        mod,
        "create_refund",
        lambda *a, **k: actions.append("refund")
        or {"id": "re_renewal", "status": "succeeded", "amount": 1900},
    )

    mod._execute_refund_job(job)

    assert actions == ["cancel", "refund"]
    assert mod.store.get_purchase_by_session("invoice_in_retired_renewal")["refunded"] == 1


def test_failed_automatic_refund_stays_visible_for_owner(tmp_path, monkeypatch):
    mod, client = _load_app(
        tmp_path,
        monkeypatch,
        STRIPE_KEY="sk_live_dummytest",
        EOLKITS_ADMIN_TOKEN="test-admin",
    )
    mod.store.record_purchase(
        session_id="cs_refund_failure",
        payment_intent="pi_refund_failure",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
    )
    payload = {
        "type": "refund_payment",
        "sessionId": "cs_refund_failure",
        "payment_intent": "pi_refund_failure",
        "amount": 29900,
    }
    job_id = mod.store.enqueue(
        "refund_payment", payload, max_attempts=1, dedupe_key="refund:cs_refund_failure"
    )
    monkeypatch.setattr(
        mod, "create_refund", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("Stripe down"))
    )

    mod._run_job(job_id, payload)

    jobs = mod.store.recent_jobs()
    assert any(j["type"] == "refund_review" and j["status"] == "requires_owner" for j in jobs)
    status = client.get("/api/status").json()
    assert "commerce_7d" not in status
    status = client.get("/api/status", headers={"X-Admin-Token": "test-admin"}).json()
    assert status["commerce_7d"]["refunds_failed"] == 1
    assert status["overall"] == "degraded"


def test_checkout_preflight_rejects_fake_zip_before_stripe(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    body = b"not a zip archive"
    presign = client.post(
        "/upload/presign", json={"filename": "repo.zip", "size": len(body)}
    ).json()
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=body)
    stripe_calls: list[dict] = []
    monkeypatch.setattr(
        mod,
        "create_checkout_session",
        lambda *args, **kwargs: stripe_calls.append(kwargs),
    )

    response = client.post(
        "/api/audit/checkout",
        data={"email": "buyer@example.com", "upload_id": presign["uploadId"]},
        headers={"accept": "application/json"},
    )

    assert response.status_code == 400
    assert "not a valid ZIP" in response.text
    assert stripe_calls == []


def test_checkout_preflight_rejects_post_upload_byte_mutation(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    source = b"Runtime: nodejs20.x"
    presign = client.post(
        "/upload/presign", json={"filename": "template.yaml", "size": len(source)}
    ).json()
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=source)
    mod._upload_path(presign["uploadId"]).write_bytes(b"Runtime: nodejs18.x")
    calls: list[dict] = []
    monkeypatch.setattr(mod, "create_checkout_session", lambda *a, **k: calls.append(k))

    response = client.post(
        "/api/audit/checkout",
        data={"email": "buyer@example.com", "upload_id": presign["uploadId"]},
        headers={"accept": "application/json"},
    )

    assert response.status_code == 400
    assert "no longer match" in response.text
    assert calls == []


def test_store_uses_full_wal_durability_and_minimizes_stripe_events(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch)
    with mod.store.connect() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2

    payload = {
        "id": "evt_private",
        "data": {
            "object": {
                "id": "cs_private",
                "customer_email": "private@example.com",
                "customer_details": {"address": {"line1": "secret"}},
            }
        },
    }
    assert mod.store.record_stripe_event("evt_private", "checkout.session.completed", payload)
    with mod.store.connect() as conn:
        stored = conn.execute(
            "SELECT payload FROM stripe_events WHERE event_id='evt_private'"
        ).fetchone()["payload"]
    assert json.loads(stored) == {"object_id": "cs_private"}
    assert "private@example.com" not in stored and "secret" not in stored


def test_store_scrubs_legacy_stripe_payloads_on_migration(tmp_path, monkeypatch):
    _load_app(tmp_path, monkeypatch)
    from eolkits_grace.store import Store

    db = tmp_path / "legacy-events.sqlite3"
    first = Store(db)
    with first.connect() as conn:
        conn.execute(
            "INSERT INTO stripe_events(event_id,type,received_at,payload,status) "
            "VALUES('evt_old','invoice.paid','now',?,'processed')",
            (json.dumps({"data": {"object": {"id": "in_old", "email": "pii@x.test"}}}),),
        )
    migrated = Store(db)
    with migrated.connect() as conn:
        stored = conn.execute(
            "SELECT payload FROM stripe_events WHERE event_id='evt_old'"
        ).fetchone()["payload"]
    assert json.loads(stored) == {"object_id": "in_old"}


def test_pending_refund_reconciles_exact_full_refund_and_ignores_other_events(
    tmp_path, monkeypatch
):
    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    mod.store.record_purchase(
        session_id="cs_pending",
        payment_intent="pi_pending",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
    )
    job = {
        "type": "refund_payment",
        "sessionId": "cs_pending",
        "payment_intent": "pi_pending",
        "amount": 29900,
        "email": "buyer@example.com",
    }
    job_id = mod.store.enqueue("refund_payment", job, dedupe_key="refund:cs_pending")
    monkeypatch.setattr(
        mod,
        "create_refund",
        lambda *a, **k: {"id": "re_expected", "status": "pending", "amount": 29900},
    )
    monkeypatch.setattr(
        mod,
        "retrieve_refund",
        lambda *a, **k: {"id": "re_expected", "status": "pending", "amount": 29900},
    )
    with pytest.raises(RuntimeError, match="not complete"):
        mod._execute_refund_job(job)
    purchase = mod.store.get_purchase_by_session("cs_pending")
    assert purchase["refunded"] == 0 and purchase["status"] == "refund_pending"

    mod._ingest_refund_event(
        {"id": "re_other", "payment_intent": "pi_pending", "status": "succeeded", "amount": 29900}
    )
    mod._ingest_refund_event(
        {"id": "re_expected", "payment_intent": "pi_pending", "status": "succeeded", "amount": 100}
    )
    assert mod.store.get_purchase_by_session("cs_pending")["refunded"] == 0

    mod._ingest_refund_event(
        {
            "id": "re_expected",
            "payment_intent": "pi_pending",
            "status": "succeeded",
            "amount": 29900,
        }
    )
    assert mod.store.get_purchase_by_session("cs_pending")["refunded"] == 1
    jobs = mod.store.recent_jobs()
    assert next(item for item in jobs if item["id"] == job_id)["status"] == "resolved"
    assert sum(item["type"] == "refund_notice" for item in jobs) == 1


def test_refund_retry_get_closes_webhook_before_bind_race(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    mod.store.record_purchase(
        session_id="cs_race",
        payment_intent="pi_race",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
    )
    # This can arrive before Stripe's create-refund HTTP response; it is safely
    # ignored until the exact refund id has been bound locally.
    mod._ingest_refund_event(
        {"id": "re_race", "payment_intent": "pi_race", "status": "succeeded", "amount": 29900}
    )
    assert mod.store.get_purchase_by_session("cs_race")["refunded"] == 0
    assert mod.store.mark_refund_pending("cs_race", "re_race")
    monkeypatch.setattr(
        mod,
        "retrieve_refund",
        lambda *a, **k: {"id": "re_race", "status": "succeeded", "amount": 29900},
    )

    mod._execute_refund_job(
        {
            "type": "refund_payment",
            "sessionId": "cs_race",
            "payment_intent": "pi_race",
            "amount": 29900,
            "email": "buyer@example.com",
        }
    )

    assert mod.store.get_purchase_by_session("cs_race")["refunded"] == 1
    assert sum(j["type"] == "refund_notice" for j in mod.store.recent_jobs()) == 1


def test_subscription_refund_success_still_requires_cancellation(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    mod.store.record_purchase(
        session_id="cs_sub_refund",
        payment_intent="pi_sub_refund",
        sku="drift_watch",
        email="buyer@example.com",
        price_id="price_1TRoGmDL3cQl851ofGZyxs6q",
        amount=1900,
        currency="usd",
        livemode=False,
    )
    mod.store.mark_refund_pending("cs_sub_refund", "re_sub_refund")
    payload = {
        "type": "refund_payment",
        "sessionId": "cs_sub_refund",
        "payment_intent": "pi_sub_refund",
        "subscription_id": "sub_refund",
        "amount": 1900,
        "email": "buyer@example.com",
    }
    job_id = mod.store.enqueue("refund_payment", payload, dedupe_key="refund:cs_sub_refund")
    mod._ingest_refund_event(
        {
            "id": "re_sub_refund",
            "payment_intent": "pi_sub_refund",
            "status": "succeeded",
            "amount": 1900,
        }
    )
    assert next(j for j in mod.store.recent_jobs() if j["id"] == job_id)["status"] == "pending"
    actions: list[str] = []
    monkeypatch.setattr(
        mod,
        "cancel_subscription",
        lambda *a, **k: actions.append("cancel") or {"status": "canceled"},
    )
    monkeypatch.setattr(mod, "create_refund", lambda *a, **k: pytest.fail("must not re-refund"))

    mod._run_job(job_id, payload)

    assert actions == ["cancel"]
    assert next(j for j in mod.store.recent_jobs() if j["id"] == job_id)["status"] == "completed"


def test_atomic_purchase_heals_legacy_missing_job_and_blocks_cross_session_pi(
    tmp_path, monkeypatch
):
    mod, _ = _load_app(tmp_path, monkeypatch)
    assert mod.store.record_purchase(
        session_id="cs_legacy_gap",
        payment_intent="pi_legacy_gap",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
    )
    kwargs = dict(
        session_id="cs_legacy_gap",
        payment_intent="pi_legacy_gap",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
        metadata={"upload_id": "u1"},
        job_type="audit_pdf",
        job_payload={"type": "audit_pdf", "sessionId": "cs_legacy_gap"},
        dedupe_key="fulfill:cs_legacy_gap",
    )
    created, job_id, job_created = mod.store.record_purchase_with_job(**kwargs)
    assert not created and job_created and job_id > 0
    assert mod.store.record_purchase_with_job(**kwargs) == (False, job_id, False)
    blocked = mod.store.record_purchase_with_job(
        **{**kwargs, "session_id": "cs_other", "dedupe_key": "fulfill:cs_other"}
    )
    assert blocked == (False, 0, False)


def test_readiness_pauses_new_sales_on_retried_paid_fulfillment(tmp_path, monkeypatch):
    mod, client = _load_app(tmp_path, monkeypatch)
    job_id = mod.store.enqueue("audit_pdf", {"type": "audit_pdf", "sessionId": "cs_risk"})
    with mod.store.connect() as conn:
        conn.execute("UPDATE jobs SET attempts=1 WHERE id=?", (job_id,))

    assert client.get("/api/capabilities").json()["audit"]["checkout_enabled"] is False
    assert (
        client.post("/upload/presign", json={"filename": "template.yaml", "size": 10}).status_code
        == 503
    )
    with mod.store.connect() as conn:
        conn.execute("UPDATE jobs SET status='completed' WHERE id=?", (job_id,))
    assert client.get("/api/capabilities").json()["audit"]["checkout_enabled"] is True


def test_checkout_extends_upload_retention_past_session_window(tmp_path, monkeypatch):
    import os

    mod, client = _load_app(tmp_path, monkeypatch)
    source = b"Runtime: nodejs20.x"
    presign = client.post(
        "/upload/presign", json={"filename": "template.yaml", "size": len(source)}
    ).json()
    client.put(presign["uploadUrl"].removeprefix("https://eolkits.com"), content=source)
    upload_path = mod._upload_path(presign["uploadId"])
    old = 1_600_000_000
    os.utime(upload_path, (old, old))

    assert (
        client.post(
            "/api/audit/checkout",
            data={"email": "buyer@example.com", "upload_id": presign["uploadId"]},
            headers={"accept": "application/json"},
        ).status_code
        == 200
    )
    assert mod.cleanup_expired_artifacts(upload_retention_hours=1)["uploads"] == 0
    assert upload_path.exists()


def test_terminal_compensation_is_one_way_and_idempotent(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch)
    mod.store.record_purchase(
        session_id="cs_terminal",
        payment_intent="pi_terminal",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
    )
    payload = {"type": "audit_pdf", "sessionId": "cs_terminal"}
    job_id = mod.store.enqueue("audit_pdf", payload, max_attempts=1)
    with mod.store.connect() as conn:
        conn.execute("UPDATE jobs SET status='dead_letter' WHERE id=?", (job_id,))

    mod._drain_once()
    mod._drain_once()

    jobs = mod.store.recent_jobs()
    assert next(j for j in jobs if j["id"] == job_id)["status"] == "compensated"
    assert sum(j["type"] == "refund_payment" for j in jobs) == 1


def test_preflight_concurrency_rejects_excess_without_releasing_worker_early(tmp_path, monkeypatch):
    import threading

    mod, _ = _load_app(tmp_path, monkeypatch, EOLKITS_PREFLIGHT_CONCURRENCY="1")
    started = threading.Event()
    release = threading.Event()

    def blocking_preflight(path, filename):
        started.set()
        assert release.wait(timeout=5)
        return {
            "input_hash": "a" * 64,
            "scanned_files": 1,
            "skipped_files": 0,
            "decoded_bytes": 1,
        }

    monkeypatch.setattr(mod, "_run_audit_preflight", blocking_preflight)

    async def scenario():
        first = asyncio.create_task(mod._preflight_upload(tmp_path / "one", "one.py"))
        assert await asyncio.to_thread(started.wait, 2)
        with pytest.raises(Exception) as exc_info:
            await mod._preflight_upload(tmp_path / "two", "two.py")
        assert getattr(exc_info.value, "status_code", None) == 503
        release.set()
        assert (await first)["scanned_files"] == 1

    asyncio.run(scenario())


def test_retired_invoice_scans_every_line_and_ignores_initial_invoice(tmp_path, monkeypatch):
    from fastapi import BackgroundTasks

    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    invoice = {
        "id": "in_multiline",
        "billing_reason": "subscription_create",
        "status": "paid",
        "currency": "usd",
        "amount_paid": 1900,
        "livemode": False,
        "subscription": "sub_multiline",
        "payment_intent": "pi_multiline",
        "lines": {
            "data": [
                {"price": {"id": "price_unrelated"}},
                {"price": {"id": "price_1TRoGmDL3cQl851ofGZyxs6q"}},
            ]
        },
    }
    mod._ingest_paid_invoice(invoice, BackgroundTasks())
    assert mod.store.recent_jobs() == []

    invoice["billing_reason"] = "subscription_cycle"
    mod._ingest_paid_invoice(invoice, BackgroundTasks())
    purchase = mod.store.get_purchase_by_session("invoice_in_multiline")
    assert purchase and purchase["sku"] == "drift_watch"
    assert mod.store.recent_jobs()[0]["type"] == "refund_payment"


def test_matching_failed_refund_requires_owner_but_unrelated_failure_is_ignored(
    tmp_path, monkeypatch
):
    mod, client = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_live_dummytest")
    mod.store.record_purchase(
        session_id="cs_refund_event_failure",
        payment_intent="pi_refund_event_failure",
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        amount=29900,
        currency="usd",
        livemode=False,
    )
    mod.store.mark_refund_pending("cs_refund_event_failure", "re_expected_failure")
    mod._ingest_refund_event(
        {
            "id": "re_unrelated",
            "payment_intent": "pi_refund_event_failure",
            "status": "failed",
            "amount": 29900,
        }
    )
    assert (
        mod.store.get_purchase_by_session("cs_refund_event_failure")["status"] == "refund_pending"
    )

    mod._ingest_refund_event(
        {
            "id": "re_expected_failure",
            "payment_intent": "pi_refund_event_failure",
            "status": "failed",
            "amount": 29900,
        }
    )
    assert mod.store.get_purchase_by_session("cs_refund_event_failure")["status"] == "refund_failed"
    assert any(
        job["type"] == "refund_review" and job["status"] == "requires_owner"
        for job in mod.store.recent_jobs()
    )
    assert client.get("/health").json()["ok"] is False


def test_admin_reconciles_invoice_refund_and_queues_notice(tmp_path, monkeypatch):
    mod, client = _load_app(
        tmp_path,
        monkeypatch,
        STRIPE_KEY="sk_live_dummytest",
        EOLKITS_ADMIN_TOKEN="test-admin-token",
    )
    mod.store.record_purchase(
        session_id="invoice_in_admin",
        payment_intent="pi_admin",
        sku="drift_watch",
        email="buyer@example.com",
        price_id="price_1TRoGmDL3cQl851ofGZyxs6q",
        amount=1900,
        currency="usd",
        livemode=False,
    )
    mod.store.enqueue(
        "refund_review",
        {"type": "refund_review", "sessionId": "invoice_in_admin"},
        status="requires_owner",
        dedupe_key="refund-review:invoice_in_admin",
    )
    monkeypatch.setattr(
        mod,
        "retrieve_invoice",
        lambda *a, **k: {"payment_intent": "pi_admin", "subscription": "sub_admin"},
    )
    monkeypatch.setattr(
        mod,
        "retrieve_payment_intent",
        lambda *a, **k: {
            "latest_charge": {
                "refunded": True,
                "refunds": {"data": [{"id": "re_admin"}]},
            }
        },
    )
    monkeypatch.setattr(mod, "retrieve_subscription", lambda *a, **k: {"status": "canceled"})

    response = client.post(
        "/admin/reconcile-refund",
        json={"session_id": "invoice_in_admin"},
        headers={"X-Admin-Token": "test-admin-token"},
    )

    assert response.status_code == 200
    assert mod.store.get_purchase_by_session("invoice_in_admin")["refunded"] == 1
    assert sum(j["type"] == "refund_notice" for j in mod.store.recent_jobs()) == 1


def test_real_test_mode_checkout_uses_inline_price_and_validates_webhook(tmp_path, monkeypatch):
    mod, _ = _load_app(tmp_path, monkeypatch, STRIPE_KEY="sk_test_real_mode")
    from eolkits_grace import stripe_client

    captured: dict = {}

    def request(settings, path, body, **kwargs):
        captured.update(body)
        return {"id": "cs_test_inline", "url": "https://checkout.stripe.test/session"}

    monkeypatch.setattr(stripe_client, "stripe_request", request)
    session_result = stripe_client.create_checkout_session(
        mod.settings,
        sku="audit",
        email="buyer@example.com",
        price_id="price_1TRoGjDL3cQl851oiIWR5JIa",
        price_usd=299,
        metadata={"upload_id": "upload1"},
        success_path="/success",
        cancel_path="/audit",
    )
    assert session_result["id"] == "cs_test_inline"
    assert "line_items[0][price]" not in captured
    assert captured["line_items[0][price_data][unit_amount]"] == "29900"
    assert captured["metadata[pricing_mode]"] == "inline_test"

    validated = mod._validate_paid_session(
        {
            "id": "cs_test_inline",
            "status": "complete",
            "payment_status": "paid",
            "currency": "usd",
            "amount_total": 29900,
            "livemode": False,
            "payment_intent": "pi_test_inline",
            "customer_email": "buyer@example.com",
            "metadata": {
                "project": "eolkits",
                "sku": "audit",
                "price_id": "price_1TRoGjDL3cQl851oiIWR5JIa",
                "pricing_mode": "inline_test",
            },
            "line_items": {"data": [{"price": {"id": "price_dynamic_test"}}]},
        }
    )
    assert validated["amount_total"] == 29900
