"""Canonical pricing loaded from the repo-root pricing.yml.

This is the single source of truth for SKU -> Stripe Price IDs and amounts.
Audit uses one price: charging more for identical automated output based on a
buyer-entered date was removed. Both checkout and webhook validation use this
file so the displayed and charged amount stay aligned.
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


def audit_price_for_deadline(deadline: str | None) -> dict[str, Any]:
    # Deadline remains report context, never a customer-controlled price lever.
    return _standard_tier()


def allowed_price_ids(sku: str) -> set[str]:
    """The set of Stripe Price IDs that are legitimate for a given SKU."""
    skus = _skus()
    if sku == "audit":
        return {t["stripe_price_id"] for t in audit_tiers() if t.get("stripe_price_id")}
    entry = skus.get(sku, {})
    pid = entry.get("stripe_price_id")
    return {pid} if pid else set()


def price_id_for_sku(sku: str) -> str | None:
    return _skus().get(sku, {}).get("stripe_price_id")


def product_for_sku(sku: str) -> str | None:
    return _skus().get(sku, {}).get("stripe_product")


def expected_amount_cents(sku: str, price_id: str | None = None) -> int | None:
    """Expected charge amount in cents for validation."""
    if sku == "audit":
        for tier in audit_tiers():
            if tier.get("stripe_price_id") == price_id:
                return int(tier["price_usd"]) * 100
        return None
    usd = _skus().get(sku, {}).get("price_usd")
    return int(usd) * 100 if usd is not None else None


def sku_for_price_id(price_id: str) -> str | None:
    for tier in audit_tiers():
        if tier.get("stripe_price_id") == price_id:
            return "audit"
    for sku, entry in _skus().items():
        if entry.get("stripe_price_id") == price_id:
            return sku
    return RETIRED_PRICE_SKUS.get(price_id)
