"""Canonical offer amounts loaded from the repo-root pricing.yml.

The repository owns the amount and product scope. The production Stripe Price
and Product IDs are deployment configuration because retired IDs must never be
made chargeable by a rollback. Checkout and webhook validation bind the runtime
IDs to the amount in this file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Public Payment Links using these former prices may survive in bookmarks or git
# history. They are recognized only so paid sessions can enter the durable refund
# path; they are never accepted by ``allowed_price_ids`` for fulfillment.
RETIRED_PRICE_SKUS = {
    "price_1TRoGjDL3cQl851oiIWR5JIa": "audit",  # retired $299 v1 price
    "price_1TRoEZDL3cQl851o9DFh1DIz": "audit",  # former $599 surge tier
    "price_1TRoGiDL3cQl851ouqnljzMx": "audit",  # former $399 surge tier
}


def _pricing_path() -> Path:
    override = os.environ.get("EOLKITS_PRICING_FILE")
    if override:
        return Path(override)
    # apps/grace-api/eolkits_grace/pricing.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3] / "pricing.yml"


@lru_cache(maxsize=1)
def load_pricing() -> dict[str, Any]:
    path = _pricing_path()
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _skus() -> dict[str, Any]:
    return load_pricing().get("skus", {})


def audit_tiers() -> list[dict[str, Any]]:
    tiers = _skus().get("audit", {}).get("tiers", [])
    # Ascending max_days so the first match is the tightest applicable tier.
    return sorted(tiers, key=lambda t: t.get("max_days", 9999))


def _standard_tier() -> dict[str, Any]:
    tiers = audit_tiers()
    if not tiers:
        raise RuntimeError("Audit pricing has no configured tier")
    for tier in tiers:
        if tier.get("name") == "standard":
            return tier
    return tiers[-1]


def audit_price_for_deadline(
    deadline: str | None, *, stripe_price_id: str | None = None
) -> dict[str, Any]:
    # Deadline remains report context, never a customer-controlled price lever.
    tier = dict(_standard_tier())
    tier["stripe_price_id"] = stripe_price_id
    return tier


def allowed_price_ids(sku: str, *, active_audit_price_id: str | None = None) -> set[str]:
    """The set of Stripe Price IDs that are legitimate for a given SKU."""
    skus = _skus()
    if sku == "audit":
        return {active_audit_price_id} if active_audit_price_id else set()
    entry = skus.get(sku, {})
    pid = entry.get("stripe_price_id")
    return {pid} if pid else set()


def price_id_for_sku(sku: str) -> str | None:
    return _skus().get(sku, {}).get("stripe_price_id")


def product_for_sku(sku: str) -> str | None:
    return _skus().get(sku, {}).get("stripe_product")


def expected_amount_cents(
    sku: str,
    price_id: str | None = None,
    *,
    active_audit_price_id: str | None = None,
) -> int | None:
    """Expected charge amount in cents for validation."""
    if sku == "audit":
        if not active_audit_price_id or price_id != active_audit_price_id:
            return None
        return int(_standard_tier()["price_usd"]) * 100
    usd = _skus().get(sku, {}).get("price_usd")
    return int(usd) * 100 if usd is not None else None


def sku_for_price_id(price_id: str, *, active_audit_price_id: str | None = None) -> str | None:
    if active_audit_price_id and price_id == active_audit_price_id:
        return "audit"
    for sku, entry in _skus().items():
        if entry.get("stripe_price_id") == price_id:
            return sku
    return RETIRED_PRICE_SKUS.get(price_id)
