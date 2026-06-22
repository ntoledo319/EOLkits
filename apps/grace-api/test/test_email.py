from __future__ import annotations

import pytest

from eolkits_grace import email as email_mod
from eolkits_grace.config import Settings
from eolkits_grace.email import EmailDeliveryError, send_email


class _Resp:
    def __init__(self, ok, status_code=200, payload=None, text=""):
        self.ok = ok
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def _settings(**overrides) -> Settings:
    base = {"resend_api_key": "re_test", "environment": "test"}
    base.update(overrides)
    return Settings(**base)


def test_send_email_raises_when_no_provider():
    with pytest.raises(EmailDeliveryError) as ei:
        send_email(_settings(resend_api_key=None), to="x@y.com", subject="s", html="<p>h</p>")
    assert ei.value.retryable is True


def test_send_email_returns_payload_on_success(monkeypatch):
    monkeypatch.setattr(email_mod.requests, "post", lambda *a, **k: _Resp(True, 200, payload={"id": "em_1"}))
    out = send_email(_settings(), to="x@y.com", subject="s", html="<p>h</p>")
    assert out["ok"] is True and out["id"] == "em_1"


def test_send_email_raises_retryable_on_5xx(monkeypatch):
    # The exact failure mode the old code silently treated as success.
    monkeypatch.setattr(email_mod.requests, "post", lambda *a, **k: _Resp(False, 500, text="boom"))
    with pytest.raises(EmailDeliveryError) as ei:
        send_email(_settings(), to="x@y.com", subject="s", html="<p>h</p>")
    assert ei.value.retryable is True


def test_send_email_429_is_retryable(monkeypatch):
    monkeypatch.setattr(email_mod.requests, "post", lambda *a, **k: _Resp(False, 429, text="slow down"))
    with pytest.raises(EmailDeliveryError) as ei:
        send_email(_settings(), to="x@y.com", subject="s", html="<p>h</p>")
    assert ei.value.retryable is True


def test_send_email_4xx_is_not_retryable(monkeypatch):
    monkeypatch.setattr(email_mod.requests, "post", lambda *a, **k: _Resp(False, 422, text="bad recipient"))
    with pytest.raises(EmailDeliveryError) as ei:
        send_email(_settings(), to="x@y.com", subject="s", html="<p>h</p>")
    assert ei.value.retryable is False


def test_send_email_transport_error_is_retryable(monkeypatch):
    import requests as _requests

    def _boom(*a, **k):
        raise _requests.ConnectionError("dns down")

    monkeypatch.setattr(email_mod.requests, "post", _boom)
    with pytest.raises(EmailDeliveryError) as ei:
        send_email(_settings(), to="x@y.com", subject="s", html="<p>h</p>")
    assert ei.value.retryable is True
