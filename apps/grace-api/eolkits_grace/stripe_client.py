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
    idempotency_key: str | None = None,
) -> dict:
    # Sandbox/test short-circuit: never call Stripe without a live key.
    if settings.is_demo_stripe:
        query = urlencode({"price": price_usd, "price_id": price_id, "email": email, **metadata})
        return {"url": f"https://checkout.stripe.com/test?{query}", "mode": "test"}

    body = {
        "payment_method_types[0]": "card",
        "line_items[0][quantity]": "1",
        "mode": mode,
        "success_url": f"{settings.public_site_url}{success_path}",
        "cancel_url": f"{settings.public_site_url}{cancel_path}",
        "customer_email": email,
        "consent_collection[terms_of_service]": "required",
        "client_reference_id": metadata.get("upload_id") or metadata.get("repo") or sku,
        "metadata[project]": "eolkits",
        "metadata[sku]": sku,
        "metadata[email]": email,
        "metadata[price_id]": price_id,
    }
    if settings.stripe_key.startswith(("sk_test_", "rk_test_")):
        # Stripe test/live Price objects are isolated. Inline test price_data lets
        # staging exercise the real hosted checkout without copying a live object
        # into test mode; webhook validation still binds it to canonical $299.
        body.update(
            {
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][unit_amount]": str(price_usd * 100),
                "line_items[0][price_data][product_data][name]": "EOLkits Audit v2 test order",
                "metadata[pricing_mode]": "inline_test",
            }
        )
    else:
        body["line_items[0][price]"] = price_id
    # Subscription mode doesn't accept payment_intent_data; only tag for payments.
    if mode == "payment":
        body["payment_intent_data[metadata][project]"] = "eolkits"
        body["payment_intent_data[metadata][sku]"] = sku
    for key, value in metadata.items():
        body[f"metadata[{key}]"] = value
    session = stripe_request(
        settings,
        "/v1/checkout/sessions",
        body,
        idempotency_key=idempotency_key,
    )
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
        params={
            "expand[]": [
                "line_items",
                "payment_intent",
                "subscription.latest_invoice.payment_intent",
            ]
        },
    )


def retrieve_payment_intent(settings: Settings, payment_intent_id: str) -> dict:
    """Fetch a PaymentIntent with charge/refund state for reconciliation."""
    return stripe_get(
        settings,
        f"/v1/payment_intents/{payment_intent_id}",
        params={"expand[]": ["latest_charge.refunds"]},
    )


def retrieve_refund(settings: Settings, refund_id: str) -> dict:
    """Fetch the current authoritative status and amount of one exact refund."""
    return stripe_get(settings, f"/v1/refunds/{refund_id}")


def retrieve_subscription(settings: Settings, subscription_id: str) -> dict:
    """Fetch subscription state before resolving a recurring-charge incident."""
    return stripe_get(settings, f"/v1/subscriptions/{subscription_id}")


def retrieve_invoice(settings: Settings, invoice_id: str) -> dict:
    """Fetch invoice payment state for refund reconciliation."""
    return stripe_get(
        settings,
        f"/v1/invoices/{invoice_id}",
        params={"expand[]": ["payment_intent", "payments.data.payment.payment_intent"]},
    )


def cancel_subscription(settings: Settings, *, subscription_id: str, idempotency_key: str) -> dict:
    """Cancel a recurring subscription immediately before refunding its invoice."""
    response = requests.delete(
        f"{STRIPE_API_BASE}/v1/subscriptions/{subscription_id}",
        headers=_auth_headers(settings, idempotency_key=idempotency_key),
        timeout=30,
    )
    if response.status_code == 404:
        return {"id": subscription_id, "status": "already_absent"}
    if not response.ok:
        raise RuntimeError(f"Stripe subscription cancellation failed ({response.status_code})")
    return response.json()


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
    return stripe_request(settings, "/v1/refunds", body, idempotency_key=idempotency_key)
