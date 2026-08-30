"""Mutation-free runtime preflight for deployment and application startup."""

from __future__ import annotations

import json

from .config import Settings, settings
from .stripe_client import attest_live_audit_price


def validate_runtime_preflight(runtime_settings: Settings) -> dict[str, object]:
    """Validate secrets and, when enabled, the live Stripe catalog via GET only."""
    runtime_settings.require_runtime_secrets()
    catalog_attested = False
    if runtime_settings.audit_checkout_enabled:
        runtime_settings.require_audit_price_configuration()
        if runtime_settings.is_production:
            attest_live_audit_price(runtime_settings)
        catalog_attested = True
    return {
        "ok": True,
        "environment": runtime_settings.environment,
        "checkout_enabled": runtime_settings.audit_checkout_enabled,
        "catalog_attested": catalog_attested,
    }


def main() -> None:
    # Output only booleans/mode. Secret and catalog identifiers are never printed.
    print(json.dumps(validate_runtime_preflight(settings), sort_keys=True))


if __name__ == "__main__":
    main()
