from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .pricing import RETIRED_PRICE_SKUS


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Marker for explicit demo/sandbox mode. Tests set STRIPE_KEY to this value to
# exercise the checkout/fulfillment flow without hitting Stripe. It is NEVER a
# valid value in ENVIRONMENT=production (startup aborts — see require_runtime_secrets).
DUMMY_STRIPE_KEY = "sk_test_dummy"


@dataclass(frozen=True)
class Settings:
    environment: str = os.environ.get("ENVIRONMENT", "production")
    public_site_url: str = os.environ.get("PUBLIC_SITE_URL", "https://eolkits.com")
    public_api_url: str = os.environ.get("PUBLIC_API_URL", "https://eolkits.com")
    data_dir: Path = Path(os.environ.get("EOLKITS_DATA_DIR", "/data/eolkits"))

    # No live-credential defaults: an unset secret must read as empty so that
    # production startup fails closed instead of silently running with fakes.
    stripe_key: str = os.environ.get("STRIPE_KEY", "")
    stripe_webhook_secret: str = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    resend_api_key: str | None = os.environ.get("RESEND_API_KEY")
    # Where inbound leads (/api/v1/lead) are emailed. Comma-separated. Defaults to
    # the studio inbox; set it to an operator-verified address in production.
    # The durable `leads` row is the source of truth when notification fails.
    lead_notify_to: str = os.environ.get("LEAD_NOTIFY_TO", "hello@toledotechnologies.com")

    runner_url: str | None = os.environ.get("RUNNER_URL")
    runner_token: str | None = os.environ.get("RUNNER_TOKEN")
    enable_inline_runner: bool = _bool_env("EOLKITS_INLINE_RUNNER", True)

    # Optional bearer for the detailed /status fields (recent jobs + funnel). When
    # unset, /status exposes only high-level health — never internal job/funnel data.
    admin_token: str | None = os.environ.get("EOLKITS_ADMIN_TOKEN")

    # Secret used to sign short-lived internal upload URLs handed to an HTTP
    # runner. Upload bytes are never available from an unsigned GET request.
    internal_url_secret: str = os.environ.get("EOLKITS_INTERNAL_URL_SECRET", "")

    max_upload_bytes: int = int(os.environ.get("EOLKITS_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    upload_presign_hourly_limit: int = int(
        os.environ.get("EOLKITS_UPLOAD_PRESIGN_HOURLY_LIMIT", "10")
    )
    upload_presign_daily_limit: int = int(
        os.environ.get("EOLKITS_UPLOAD_PRESIGN_DAILY_LIMIT", "50")
    )
    max_active_upload_bytes: int = int(
        os.environ.get("EOLKITS_MAX_ACTIVE_UPLOAD_BYTES", str(512 * 1024 * 1024))
    )
    min_free_disk_bytes: int = int(
        os.environ.get("EOLKITS_MIN_FREE_DISK_BYTES", str(512 * 1024 * 1024))
    )
    max_webhook_bytes: int = int(os.environ.get("EOLKITS_MAX_WEBHOOK_BYTES", str(256 * 1024)))
    max_form_bytes: int = int(os.environ.get("EOLKITS_MAX_FORM_BYTES", str(64 * 1024)))
    max_event_bytes: int = int(os.environ.get("EOLKITS_MAX_EVENT_BYTES", str(2 * 1024)))
    max_event_db_bytes: int = int(
        os.environ.get("EOLKITS_MAX_EVENT_DB_BYTES", str(128 * 1024 * 1024))
    )
    preflight_concurrency: int = max(1, int(os.environ.get("EOLKITS_PREFLIGHT_CONCURRENCY", "1")))
    event_hourly_limit: int = int(os.environ.get("EOLKITS_EVENT_HOURLY_LIMIT", "60"))
    event_daily_limit: int = int(os.environ.get("EOLKITS_EVENT_DAILY_LIMIT", "2000"))
    lead_ip_minute_limit: int = int(os.environ.get("EOLKITS_LEAD_IP_MINUTE_LIMIT", "8"))
    lead_ip_daily_limit: int = int(os.environ.get("EOLKITS_LEAD_IP_DAILY_LIMIT", "20"))
    lead_global_daily_limit: int = int(os.environ.get("EOLKITS_LEAD_GLOBAL_DAILY_LIMIT", "500"))
    # Lead alerts are deliberately capped below the provider's free daily quota.
    # Paid delivery/refund mail is uncapped and therefore always has priority.
    lead_notification_daily_limit: int = int(
        os.environ.get("EOLKITS_LEAD_NOTIFICATION_DAILY_LIMIT", "20")
    )
    # Audit v2 is the only paid capability implemented end-to-end. This kill
    # switch is intentionally server-side so an operator can stop new charges
    # without waiting for a static-site deploy.
    audit_checkout_enabled: bool = _bool_env("EOLKITS_AUDIT_CHECKOUT_ENABLED", False)
    # A new v2-only Product/Price pair is supplied at deployment time. Keeping
    # retired IDs out of the repository prevents a rollback from reviving them.
    audit_price_id: str = os.environ.get("EOLKITS_AUDIT_PRICE_ID", "")
    audit_product_id: str = os.environ.get("EOLKITS_AUDIT_PRODUCT_ID", "")
    build_sha: str = os.environ.get("EOLKITS_BUILD_SHA", "unknown")[:64]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "state.sqlite3"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def is_demo_stripe(self) -> bool:
        """True when running without real Stripe credentials (tests/sandbox)."""
        return not self.stripe_key or self.stripe_key.startswith(DUMMY_STRIPE_KEY)

    @property
    def stripe_is_live(self) -> bool:
        return self.stripe_key.startswith(("sk_live", "rk_live"))

    def missing_production_secrets(self) -> list[str]:
        """Return the list of required secrets that are absent/insecure for prod."""
        missing: list[str] = []
        if not self.stripe_is_live:
            missing.append("STRIPE_KEY (must be a live sk_live_/rk_live_ key)")
        if not self.stripe_webhook_secret or self.stripe_webhook_secret == "whsec_test":
            missing.append("STRIPE_WEBHOOK_SECRET")
        if not self.resend_api_key:
            missing.append("RESEND_API_KEY (email provider)")
        if len(self.internal_url_secret.encode("utf-8")) < 32:
            missing.append("EOLKITS_INTERNAL_URL_SECRET (minimum 32 bytes)")
        if self.runner_url and len((self.runner_token or "").encode("utf-8")) < 32:
            missing.append("RUNNER_TOKEN (minimum 32 bytes when RUNNER_URL is set)")
        if self.runner_url and urlparse(self.runner_url).scheme != "https":
            missing.append("RUNNER_URL (must use HTTPS in production)")
        if self.admin_token and len(self.admin_token.encode("utf-8")) < 32:
            missing.append("EOLKITS_ADMIN_TOKEN (minimum 32 bytes when configured)")
        if self.audit_checkout_enabled:
            missing.extend(self.audit_price_configuration_errors())
        return missing

    def audit_price_configuration_errors(self) -> list[str]:
        """Reject missing, malformed, or retired production catalog identities."""
        if not self.audit_checkout_enabled:
            return []
        errors: list[str] = []
        if not re.fullmatch(r"price_[A-Za-z0-9_]{8,}", self.audit_price_id):
            errors.append("EOLKITS_AUDIT_PRICE_ID (new v2-only Stripe Price required)")
        elif self.audit_price_id in RETIRED_PRICE_SKUS:
            errors.append("EOLKITS_AUDIT_PRICE_ID (retired Stripe Price is forbidden)")
        if not re.fullmatch(r"prod_[A-Za-z0-9_]{8,}", self.audit_product_id):
            errors.append("EOLKITS_AUDIT_PRODUCT_ID (new v2-only Stripe Product required)")
        return errors

    def require_audit_price_configuration(self) -> None:
        errors = self.audit_price_configuration_errors()
        if errors:
            raise RuntimeError("Refusing to enable Audit checkout: " + ", ".join(errors))

    def require_runtime_secrets(self) -> None:
        """Fail closed: abort startup in production when live secrets are absent."""
        if not self.is_production:
            if self.stripe_is_live:
                raise RuntimeError(
                    "Refusing to start a non-production environment with a live Stripe key"
                )
            return
        missing = self.missing_production_secrets()
        if missing:
            raise RuntimeError(
                "Refusing to start in ENVIRONMENT=production without required secrets: "
                + ", ".join(missing)
            )


settings = Settings()
