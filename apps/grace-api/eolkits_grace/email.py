from __future__ import annotations

import requests

from .config import Settings


RESEND_API = "https://api.resend.com/emails"


class EmailDeliveryError(RuntimeError):
    """Raised when an email could NOT be delivered.

    Every caller drives retry / durable-recovery off an exception (the lead
    re-send sweep, the job-queue backoff). A failed send must therefore surface
    as a raised exception — never as a quietly-returned ``{"ok": False}`` that
    looks like success and silently drops the message. ``retryable`` marks the
    transient cases (no provider yet, 429, 5xx) worth re-attempting."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


def render_audit_delivery_email(
    *,
    pdf_url: str,
    verify_url: str,
    rule_pack_version: str,
    input_sha: str,
) -> str:
    return f"""<!doctype html>
<html><body style="font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:24px;line-height:1.6">
<h2 style="margin:0 0 12px">Your EOLkits Audit is ready</h2>
<p>The audit you requested has been generated and signed.</p>
<p><a href="{pdf_url}" style="display:inline-block;background:#2563eb;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none">Download PDF</a></p>
<h3 style="margin-top:24px;font-size:14px;color:#374151">Verification</h3>
<ul style="font-size:13px;color:#4b5563">
<li>Input SHA-256: <code>{input_sha}</code></li>
<li>Rule pack version: <code>{rule_pack_version}</code></li>
<li>Verify authenticity: <a href="{verify_url}">{verify_url}</a></li>
</ul>
<div style="background:#ecfdf5;border:1px solid #059669;border-radius:8px;padding:16px;margin-top:24px">
<h3 style="margin:0 0 6px;font-size:15px;color:#065f46">Want it fixed, not just found?</h3>
<p style="margin:0 0 10px;font-size:13px;color:#065f46">Upgrade to a <strong>Migration Pack</strong> within 48 hours and we credit this $299 audit toward the $1,499 — a real PR with codemods, IaC patches, a canary plan, and an automatic refund if your CI fails.</p>
<a href="https://eolkits.com/pack/?utm_source=audit_email&utm_medium=email&utm_campaign=audit48h" style="display:inline-block;background:#059669;color:#fff;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px">Apply my $299 credit</a>
</div>
<p style="font-size:12px;color:#6b7280;margin-top:32px">This is a transactional message. You are receiving it because you purchased an Audit PDF on EOLkits.</p>
</body></html>"""


def send_email(
    settings: Settings,
    *,
    to: str,
    subject: str,
    html: str,
    attachments: list[dict] | None = None,
) -> dict:
    """Send one email via Resend. Returns the provider payload on success and
    RAISES :class:`EmailDeliveryError` on any failure (no provider configured,
    transport error, or a non-2xx response) so callers never mistake a failed
    send for a delivered one."""
    if not settings.resend_api_key:
        raise EmailDeliveryError(
            "no email provider configured (RESEND_API_KEY unset)", retryable=True
        )
    payload: dict = {
        "from": "EOLkits <noreply@eolkits.com>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if attachments:
        payload["attachments"] = attachments
    try:
        response = requests.post(
            RESEND_API,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise EmailDeliveryError(f"email transport error: {exc}", retryable=True) from exc
    if response.ok:
        try:
            return {"ok": True, **response.json()}
        except ValueError:
            return {"ok": True}
    retryable = response.status_code == 429 or response.status_code >= 500
    raise EmailDeliveryError(
        f"email provider returned {response.status_code}: {response.text[:500]}",
        retryable=retryable,
    )

