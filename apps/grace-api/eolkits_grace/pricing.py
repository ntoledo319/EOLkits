"""Canonical pricing loaded from the repo-root pricing.yml.

This is the single source of truth for SKU -> Stripe Price IDs, amounts, and the
deadline-driven audit surge tiers. Both the checkout path and the webhook
validation path use it so the price we charge always matches a real, approved
Stripe Price object (verified live: surge_7d $599, surge_30d $399, standard
$299, migration_pack $1499, org_license $14999, drift_watch $19).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


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


def days_until_deadline(deadline: str | None) -> int:
    """Canonical day count used by BOTH the static site and the API so the
    displayed price equals the checkout price. Accepts YYYY-MM-DD or ISO 8601."""
    if not deadline:
        return 999
    text = deadline.strip()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return 999
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return (parsed - datetime.now(UTC)).days


def audit_tiers() -> list[dict[str, Any]]:
    tiers = _skus().get("audit", {}).get("tiers", [])
    # Ascending max_days so the first match is the tightest applicable tier.
    return sorted(tiers, key=lambda t: t.get("max_days", 9999))


def _standard_tier() -> dict[str, Any]:
    tiers = audit_tiers()
    for tier in tiers:
        if tier.get("name") == "standard":
            return tier
    return tiers[-1]


def audit_tier(days_until: int) -> dict[str, Any]:
    """Return the tier dict for a NON-NEGATIVE days-until-deadline.

    Selection rule (identical to the static site's compute_urgency): the first
    tier whose ``max_days`` >= days_until. Callers that may pass a negative
    (already-passed) deadline should use ``audit_price_for_deadline``, which
    matches the site by pricing a passed deadline at the standard tier rather
    than the surge tier — so the displayed price always equals the charged price.
    """
    for tier in audit_tiers():
        if days_until <= int(tier.get("max_days", 9999)):
            return tier
    return _standard_tier()


def audit_price_for_deadline(deadline: str | None) -> dict[str, Any]:
    days = days_until_deadline(deadline)
    # Passed deadline -> standard pricing (mirrors build.py compute_urgency,
    # which shows base price + "deadline passed" messaging).
    if days < 0:
        return _standard_tier()
    return audit_tier(days)


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
    return None
