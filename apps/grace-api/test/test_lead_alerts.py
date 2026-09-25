"""Owner alerts for captured leads.

e377bd4d already counts an alert as sent only when Resend accepts it
(send_email raises EmailDeliveryError otherwise; see test_hardening's
test_lead_notify_survives_real_http_failure), so that part of the old
5361cb23 fix is not repeated here. What was still broken: the re-send sweep
for a long lead."""

from __future__ import annotations

import json

import pytest

GOOD = {"email": "visitor@example.com", "name": "Visitor", "message": "Hello", "product": "Apps"}


def test_resend_of_a_long_lead_still_carries_the_contact_details(load_grace, monkeypatch):
    mod, client = load_grace()
    from eolkits_grace.email import EmailDeliveryError

    def outage(settings, **_):
        raise EmailDeliveryError("provider down", retryable=True)

    monkeypatch.setattr(mod, "send_email", outage)
    long_lead = {**GOOD, "email": "long@example.com", "name": "Dana", "message": "word " * 2000}
    assert client.post("/api/v1/lead", data=long_lead).json()["ok"] is True
    stored = mod.store.unnotified_leads()[0]["fields"]
    with pytest.raises(json.JSONDecodeError):
        json.loads(stored)  # cut at 4000 characters when stored

    captured: list[str] = []

    def accept(settings, *, to, subject, html, idempotency_key=None, attachments=None):
        captured.append(html)
        return {"ok": True, "id": "em_1"}

    monkeypatch.setattr(mod, "send_email", accept)
    assert mod.resend_unnotified_leads() == {"attempted": 1, "still_unnotified": 0}
    assert len(captured) == 1
    html = captured[0]
    assert "long@example.com" in html and "Dana" in html
    assert "details (shortened when stored)" in html
    assert "word word word" in html


def test_resend_of_a_normal_lead_is_unchanged(load_grace, monkeypatch):
    mod, client = load_grace()
    from eolkits_grace.email import EmailDeliveryError

    def outage(settings, **_):
        raise EmailDeliveryError("provider down", retryable=True)

    monkeypatch.setattr(mod, "send_email", outage)
    client.post("/api/v1/lead", data=GOOD)
    first_html = mod._lead_email_html(
        "Apps", "", {"email": GOOD["email"], "name": "Visitor", "message": "Hello"}
    )

    captured: list[str] = []
    monkeypatch.setattr(
        mod, "send_email", lambda settings, **kw: captured.append(kw["html"]) or {"ok": True}
    )
    mod.resend_unnotified_leads()
    assert captured == [first_html]
    assert "shortened" not in captured[0]


def test_rejected_alert_is_still_not_marked_as_sent(load_grace, monkeypatch):
    """Regression guard for the accounting e377bd4d already has."""
    mod, client = load_grace()
    from eolkits_grace.email import EmailDeliveryError

    calls: list[str] = []

    def rejected(settings, *, to, **_):
        calls.append(to)
        raise EmailDeliveryError(
            "email provider returned 403: domain not verified", retryable=False
        )

    monkeypatch.setattr(mod, "send_email", rejected)
    assert client.post("/api/v1/lead", data=GOOD).status_code == 200
    assert calls == ["owner@toledo.test"]  # a permanent rejection is not retried
    assert mod.store.count_unnotified() == 1
