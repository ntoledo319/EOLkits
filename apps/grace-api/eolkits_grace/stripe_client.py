from __future__ import annotations

from urllib.parse import urlencode

import requests

from .config import Settings

STRIPE_API_BASE = "https://api.stripe.com"


def _auth_headers(settings: Settings, *, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {settings.stripe_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def stripe_request(
    settings: Settings,
    path: str,
    body: dict[str, str],
    *,
    idempotency_key: str | None = None,
) -> dict:
    response = requests.post(
        f"{STRIPE_API_BASE}{path}",
        headers=_auth_headers(settings, idempotency_key=idempotency_key),
        data=urlencode(body),
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Stripe API error ({response.status_code}): {response.text}")
    return response.json()


def stripe_get(settings: Settings, path: str, params: dict | None = None) -> dict:
    response = requests.get(
        f"{STRIPE_API_BASE}{path}",
        headers={"Authorization": f"Bearer {settings.stripe_key}"},
        params=params,
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Stripe API error ({response.status_code}): {response.text}")
    return response.json()


def create_checkout_session(
    settings: Settings,
    *,
    sku: str,
    email: str,
    price_id: str,
    price_usd: int,
    metadata: dict[str, str],
    success_path: str,
    cancel_path: str,
    mode: str = "payment",
) -> dict:
    # Sandbox/test short-circuit: never call Stripe without a live key.
    if settings.is_demo_stripe:
        query = urlencode({"price": price_usd, "price_id": price_id, "email": email, **metadata})
        return {"url": f"https://checkout.stripe.com/test?{query}", "mode": "test"}

    body = {
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "mode": mode,
        "success_url": f"{settings.public_site_url}{success_path}",
        "cancel_url": f"{settings.public_site_url}{cancel_path}",
        "customer_email": email,
        "client_reference_id": metadata.get("upload_id") or metadata.get("repo") or sku,
        "metadata[project]": "eolkits",
        "metadata[sku]": sku,
        "metadata[email]": email,
        "metadata[price_id]": price_id,
    }
    # Subscription mode doesn't accept payment_intent_data; only tag for payments.
    if mode == "payment":
        body["payment_intent_data[metadata][project]"] = "eolkits"
        body["payment_intent_data[metadata][sku]"] = sku
    for key, value in metadata.items():
        body[f"metadata[{key}]"] = value
    session = stripe_request(settings, "/v1/checkout/sessions", body)
    return {
        "url": session["url"],
        "id": session.get("id"),
        "mode": "live" if settings.stripe_is_live else "test",
    }


def retrieve_checkout_session(settings: Settings, session_id: str) -> dict:
    """Fetch the authoritative session from Stripe (with line items + PI)."""
    return stripe_get(
        settings,
        f"/v1/checkout/sessions/{session_id}",
        params={"expand[]": ["line_items", "payment_intent"]},
    )


def create_refund(
    settings: Settings,
    *,
    payment_intent: str,
    amount: int | None = None,
    reason: str = "requested_by_customer",
    idempotency_key: str,
) -> dict:
    """Issue a refund with an idempotency key so retries never double-refund."""
    body: dict[str, str] = {"payment_intent": payment_intent, "reason": reason}
    if amount is not None:
        body["amount"] = str(amount)
    return stripe_request(
        settings, "/v1/refunds", body, idempotency_key=idempotency_key
    )
