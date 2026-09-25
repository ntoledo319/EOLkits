"""Helpers shared by the lead-bus tests (imported by conftest.py and the test
modules). Outbound email is always replaced by a recorder and RESEND_API_KEY is
unset by the fixtures, so no test can reach Resend."""

from __future__ import annotations

import asyncio
import importlib
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "grace-api"
RUNNER_ROOT = ROOT / "apps" / "runner"

BASE_ENV = {
    "ENVIRONMENT": "test",
    "STRIPE_KEY": "sk_test_dummy",
    "STRIPE_WEBHOOK_SECRET": "whsec_test",
    "PUBLIC_SITE_URL": "https://eolkits.com",
    "PUBLIC_API_URL": "https://eolkits.com",
    "EOLKITS_INLINE_RUNNER": "1",
    "EOLKITS_PRICING_FILE": str(ROOT / "pricing.yml"),
    "LEAD_NOTIFY_TO": "owner@toledo.test",
    # Roomy limits so a test's own requests never trip the abuse limits by
    # accident; tests about those limits set them explicitly.
    "EOLKITS_LEAD_IP_MINUTE_LIMIT": "1000",
    "EOLKITS_LEAD_IP_DAILY_LIMIT": "1000",
    "EOLKITS_LEAD_GLOBAL_DAILY_LIMIT": "1000",
    "EOLKITS_LEAD_NOTIFICATION_DAILY_LIMIT": "1000",
}
# Cleared unless a test sets them, so the ambient environment cannot leak in.
CLEARED_ENV = (
    "RESEND_API_KEY",
    "EOLKITS_LEAD_RETENTION_DAYS",
    "EOLKITS_MAX_FORM_BYTES",
    "EOLKITS_INTERNAL_URL_SECRET",
    "EOLKITS_ADMIN_TOKEN",
    "EOLKITS_AUDIT_CHECKOUT_ENABLED",
    "RUNNER_URL",
)


def fresh_import(module: str, *, package: str = "eolkits_grace", root: Path = API_ROOT):
    """Import ``module`` with settings re-read from the current environment."""
    for path in (root, RUNNER_ROOT):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    for name in list(sys.modules):
        if name == package or name.startswith(package + "."):
            del sys.modules[name]
    return importlib.import_module(module)


def install_email_recorder(mod, monkeypatch) -> list[dict[str, Any]]:
    """Replace the module's send_email with a recorder that reports success."""
    sent: list[dict[str, Any]] = []

    def fake_send_email(settings, *, to, subject, html, attachments=None, idempotency_key=None):
        sent.append({"to": to, "subject": subject, "html": html, "key": idempotency_key})
        return {"ok": True, "id": f"test-{len(sent)}"}

    monkeypatch.setattr(mod, "send_email", fake_send_email)
    return sent


class AsgiResult(NamedTuple):
    status: int | None
    headers: list[tuple[bytes, bytes]]
    body: bytes
    raised: str | None


def call_asgi(
    app,
    *,
    headers: Iterable[tuple[str, str]] = (),
    chunks: Iterable[bytes] = (b"",),
    method: str = "POST",
    path: str = "/api/v1/lead",
    client: tuple[str, int] = ("203.0.113.7", 50000),
    disconnect: bool = False,
) -> AsgiResult:
    """Drive the ASGI app directly and return exactly what it sent: the status,
    the raw header list in order, the body bytes, and the name of any exception
    that escaped. No HTTP client sits in between to normalise anything."""
    chunk_list = list(chunks)
    pending: list[dict[str, Any]] = (
        [{"type": "http.disconnect"}]
        if disconnect
        else [
            {"type": "http.request", "body": chunk, "more_body": index < len(chunk_list) - 1}
            for index, chunk in enumerate(chunk_list)
        ]
    )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "server": ("eolkits.com", 443),
        "client": client,
        "root_path": "",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers],
    }
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return pending.pop(0) if pending else {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    async def run() -> str | None:
        try:
            await app(scope, receive, send)
        except Exception as exc:  # noqa: BLE001 - reported, then compared
            return type(exc).__name__
        return None

    raised = asyncio.run(run())
    start = [m for m in sent if m["type"] == "http.response.start"]
    assert len(start) <= 1
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return AsgiResult(
        start[0]["status"] if start else None,
        [tuple(pair) for pair in start[0].get("headers", [])] if start else [],
        body,
        raised,
    )
