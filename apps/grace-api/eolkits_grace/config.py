from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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
    github_webhook_secret: str | None = os.environ.get("GITHUB_WEBHOOK_SECRET")
    github_app_id: str | None = os.environ.get("GITHUB_APP_ID")
    github_app_private_key: str | None = os.environ.get("GITHUB_APP_PRIVATE_KEY")
    github_app_slug: str | None = os.environ.get("GITHUB_APP_SLUG")
    resend_api_key: str | None = os.environ.get("RESEND_API_KEY")
    # Where inbound leads (/api/v1/lead) are emailed. Comma-separated. Defaults to
    # the studio inbox; set to a guaranteed-deliverable address in prod so leads
    # never route back through the dead FormSubmit/mxroute path. The durable
    # `leads` row is the real guarantee regardless of this.
    lead_notify_to: str = os.environ.get("LEAD_NOTIFY_TO", "hello@toledotechnologies.com")

    runner_url: str | None = os.environ.get("RUNNER_URL")
    runner_token: str | None = os.environ.get("RUNNER_TOKEN")
    enable_inline_runner: bool = _bool_env("EOLKITS_INLINE_RUNNER", True)

    # Secret used to sign short-lived internal upload URLs handed to the runner
    # (SSRF mitigation — see app._signed_upload_url / audit_pdf._download_input).
    internal_url_secret: str = os.environ.get("EOLKITS_INTERNAL_URL_SECRET", "")

    max_upload_bytes: int = int(os.environ.get("EOLKITS_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

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
        if not self.github_webhook_secret:
            missing.append("GITHUB_WEBHOOK_SECRET")
        if not self.github_app_id or not self.github_app_private_key:
            missing.append("GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY")
        if not self.resend_api_key:
            missing.append("RESEND_API_KEY (email provider)")
        if not self.internal_url_secret:
            missing.append("EOLKITS_INTERNAL_URL_SECRET")
        return missing

    def require_runtime_secrets(self) -> None:
        """Fail closed: abort startup in production when live secrets are absent."""
        if not self.is_production:
            return
        missing = self.missing_production_secrets()
        if missing:
            raise RuntimeError(
                "Refusing to start in ENVIRONMENT=production without required secrets: "
                + ", ".join(missing)
            )


settings = Settings()
