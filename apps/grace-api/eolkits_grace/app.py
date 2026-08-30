from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import shutil
import sys
import threading
import time
import zipfile
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import requests
from fastapi import BackgroundTasks, FastAPI, Form, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response

from . import pricing
from .config import settings
from .email import EmailDeliveryError, render_audit_delivery_email, send_email
from .preflight import validate_runtime_preflight
from .security import sha256_hex, verify_stripe_signature
from .store import Store
from .stripe_client import (
    cancel_subscription,
    create_checkout_session,
    create_refund,
    retrieve_checkout_session,
    retrieve_invoice,
    retrieve_payment_intent,
    retrieve_refund,
    retrieve_subscription,
)

RUNNER_DIR = Path(__file__).resolve().parents[2] / "runner"
if RUNNER_DIR.exists() and str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))

ALLOWED_EXTENSIONS = {
    ".yaml",
    ".yml",
    ".json",
    ".tf",
    ".tfvars",
    ".js",
    ".ts",
    ".tsx",
    ".py",
    ".txt",
    ".toml",
    ".lock",
    ".sh",
    ".zip",
}
AUDIT_REPORT_VERSION = "2.0"
ACTIVE_CHECKOUT_SKUS = {"audit"}
DRAIN_INTERVAL_SECONDS = 30
# How often the drain loop re-attempts owner alerts for durably-captured leads
# whose notification failed — so an email outage self-heals WITHOUT an external
# cron, not only on the next process restart.
LEAD_SWEEP_INTERVAL_SECONDS = 3600
ARTIFACT_SWEEP_INTERVAL_SECONDS = 3600
# A job still in 'running' longer than this is presumed orphaned by a crash and
# is reclaimed by the drainer. MUST exceed the longest legitimate job runtime
# (the 900s runner timeout) so a merely-slow job is never double-run.
STALE_RUNNING_SECONDS = 1800

# Studio microsites + eolkits that POST to /api/v1/lead — used for BOTH the CORS
# allowlist and the 303 redirect allowlist, so the lead endpoint can honor each
# form's `_next` without ever becoming an open redirector.
_SITE_ORIGINS = (
    "https://eolkits.com",
    "https://ntoledo319.github.io",
    "https://toledotechnologies.com",
    "https://web.toledotechnologies.com",
    "https://sitelift.toledotechnologies.com",
    "https://apps.toledotechnologies.com",
    "https://mobile.toledotechnologies.com",
    "https://ai.toledotechnologies.com",
)

store = Store(settings.db_path, initialize=False)
logger = logging.getLogger("eolkits_grace")
_PREFLIGHT_SLOTS = threading.BoundedSemaphore(settings.preflight_concurrency)
_audit_catalog_attested = False


class BoundedRequestBodyMiddleware:
    """Buffer small public request bodies before routing and reject overflow.

    FastAPI resolves ``Form`` dependencies before entering the route function, so
    route-local checks cannot protect form parsing. This pure ASGI middleware
    bounds both Content-Length and chunked bodies, then replays an in-limit body
    to Starlette. Upload bytes retain their separate streaming 10 MiB path.
    """

    def __init__(self, asgi_app: Any) -> None:
        self.app = asgi_app

    @staticmethod
    def _limit(scope: dict[str, Any]) -> int | None:
        if scope.get("method") not in {"POST", "PUT", "PATCH"}:
            return None
        path = str(scope.get("path") or "")
        if path == "/webhook/stripe":
            return settings.max_webhook_bytes
        if path == "/api/events":
            return settings.max_event_bytes
        if path in {
            "/upload/presign",
            "/api/audit/checkout",
            "/api/pack/checkout",
            "/api/v1/lead",
            "/api/license/inquiry",
            "/api/license/validate",
            "/support/ask",
            "/admin/reconcile-refund",
        }:
            return settings.max_form_bytes
        return None

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        limit = self._limit(scope)
        if limit is None:
            await self.app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers") or []}
        raw_length = headers.get(b"content-length")
        if raw_length:
            try:
                if int(raw_length) > limit:
                    await JSONResponse({"detail": "request body too large"}, status_code=413)(
                        scope, receive, send
                    )
                    return
            except ValueError:
                await JSONResponse({"detail": "invalid content length"}, status_code=400)(
                    scope, receive, send
                )
                return

        body = bytearray()
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                return
            if message.get("type") != "http.request":
                continue
            body.extend(message.get("body") or b"")
            if len(body) > limit:
                await JSONResponse({"detail": "request body too large"}, status_code=413)(
                    scope, receive, send
                )
                return
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay() -> dict[str, Any]:
            nonlocal replayed
            if replayed:
                return {"type": "http.request", "body": b"", "more_body": False}
            replayed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_runtime_state()
    drain_task: asyncio.Task | None = None
    # Drain any jobs that were durably queued but not completed before a restart.
    if settings.environment.strip().lower() != "test":
        drain_task = asyncio.create_task(_drain_loop())
        # Heal any leads captured-but-not-alerted during a prior email outage, off the
        # event loop so a slow email provider can't delay startup.
        asyncio.create_task(asyncio.to_thread(resend_unnotified_leads))
        # Privacy policy promises are enforced by code, not by an aspirational
        # document. Sweep once on boot; the drain loop repeats it hourly.
        asyncio.create_task(asyncio.to_thread(cleanup_expired_artifacts))
    try:
        yield
    finally:
        if drain_task:
            drain_task.cancel()


def initialize_runtime_state() -> None:
    """Validate the runtime completely before touching the persistent volume."""
    global _audit_catalog_attested
    result = validate_runtime_preflight(settings)
    _audit_catalog_attested = bool(result["catalog_attested"])
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    store.init()


app = FastAPI(title="EOLkits GRACE API", version="1.0.0", lifespan=lifespan)
app.add_middleware(BoundedRequestBodyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted({settings.public_site_url, *_SITE_ORIGINS}),
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health(response: Response) -> dict[str, Any]:
    commerce = store.commerce_counts(7)
    response.headers["Cache-Control"] = "no-store"
    return {
        "ok": (
            not commerce.get("refunds_pending")
            and not commerce.get("refunds_failed")
            and not commerce.get("fulfillment_at_risk")
        ),
        "env": settings.environment,
        "storage": "filesystem",
        "database": "sqlite",
        "runner": (
            "http"
            if settings.runner_url
            else "inline" if settings.enable_inline_runner else "disabled"
        ),
        "build_sha": settings.build_sha,
        "audit_report_version": AUDIT_REPORT_VERSION,
    }


def _audit_readiness() -> tuple[bool, str]:
    """Single fail-closed gate for every route that can lead to a charge."""
    if not settings.audit_checkout_enabled:
        return False, "checkout paused"
    if not (settings.runner_url or settings.enable_inline_runner):
        return False, "report runner unavailable"
    if not settings.resend_api_key:
        return False, "transactional email unavailable"
    if settings.is_production and not settings.stripe_is_live:
        return False, "payment processor unavailable"
    if not _audit_catalog_attested:
        return False, "payment catalog not attested"
    if not settings.data_dir.exists() or not os.access(settings.data_dir, os.W_OK):
        return False, "artifact storage unavailable"
    commerce = store.commerce_counts(7)
    if commerce.get("refunds_pending") or commerce.get("refunds_failed"):
        return False, "an unresolved customer refund requires attention"
    if commerce.get("fulfillment_at_risk"):
        return False, "paid report delivery is retrying or unavailable"
    return True, "ready"


def _require_audit_ready() -> None:
    ready, reason = _audit_readiness()
    if not ready:
        raise HTTPException(status_code=503, detail=f"Audit checkout unavailable: {reason}")


@app.get("/status")
@app.get("/status.json")
@app.get("/api/status")
async def status(response: Response, x_admin_token: str | None = Header(None)) -> dict[str, Any]:
    is_admin = _admin_ok(x_admin_token)
    response.headers["Cache-Control"] = "private, no-store" if is_admin else "no-store"
    commerce = store.commerce_counts(7)
    data: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "overall": "healthy",
        "environment": settings.environment,
        "components": {
            "storage": {"ok": settings.uploads_dir.exists() and settings.reports_dir.exists()},
            "stripe": {
                "ok": settings.stripe_is_live,
                "mode": "live" if settings.stripe_is_live else "test",
            },
            "email": {
                "ok": bool(settings.resend_api_key),
                "configured": bool(settings.resend_api_key),
            },
            "runner": {
                "ok": bool(settings.runner_url or settings.enable_inline_runner),
                "url": bool(settings.runner_url),
            },
        },
        "capabilities": {
            "audit": _audit_readiness()[0],
            "migration_pack": False,
            "drift_watch": False,
            "org_license": False,
        },
    }
    data["overall"] = (
        "healthy"
        if all(component.get("ok") for component in data["components"].values())
        and not commerce.get("refunds_failed")
        and not commerce.get("refunds_pending")
        and not commerce.get("fulfillment_at_risk")
        else "degraded"
    )
    # Low-volume funnel/commerce counts can reveal an individual visitor or buyer,
    # and recent_jobs carries per-order payloads. Expose all operational metrics
    # only to an authenticated admin — never to an unauthenticated caller.
    if is_admin:
        data["funnel_7d"] = store.event_counts(7)
        data["commerce_7d"] = commerce
        data["recent_jobs"] = store.recent_jobs(20)
    return data


@app.get("/api/capabilities")
async def capabilities(response: Response) -> dict[str, Any]:
    """Public feature handshake used by the static storefront.

    Old backends do not expose this route, so a newly deployed static page keeps
    checkout hidden until the v2 fulfillment backend is actually live.
    """
    response.headers["Cache-Control"] = "no-store"
    audit_ready, audit_reason = _audit_readiness()
    return {
        "audit": {
            "checkout_enabled": audit_ready,
            "reason": audit_reason,
            "report_version": AUDIT_REPORT_VERSION,
            "accepts": ["repository_zip", "single_source_file"],
        },
        "migration_pack": {"checkout_enabled": False, "reason": "private beta"},
        "drift_watch": {"checkout_enabled": False, "reason": "not implemented"},
        "org_license": {"checkout_enabled": False, "reason": "not implemented"},
    }


# ---- uploads ----------------------------------------------------------------- #


@app.post("/upload/presign")
async def upload_presign(request: Request) -> dict[str, Any]:
    _require_audit_ready()
    source_key = _request_source_key(request)
    if not store.allow_rate(
        f"upload-hour:{source_key}",
        limit=settings.upload_presign_hourly_limit,
        window_seconds=3600,
    ) or not store.allow_rate(
        "upload-day:global",
        limit=settings.upload_presign_daily_limit,
        window_seconds=86400,
    ):
        raise HTTPException(status_code=429, detail="upload capacity exceeded; try again later")
    try:
        body = json.loads(await _read_limited_body(request, 16 * 1024))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON object required")
    filename = Path(str(body.get("filename") or "")).name
    size = int(body.get("size") or 0)
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_file_type", "allowed": sorted(ALLOWED_EXTENSIONS)},
        )
    if size <= 0:
        raise HTTPException(status_code=400, detail="positive file size required")
    if size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail={"error": "file_too_large", "maxSize": settings.max_upload_bytes},
        )

    upload_id = secrets.token_urlsafe(18).replace("-", "").replace("_", "")[:24]
    upload_token = secrets.token_urlsafe(32)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(settings.uploads_dir).free - size < settings.min_free_disk_bytes:
        raise HTTPException(status_code=503, detail="upload storage temporarily unavailable")
    if not store.reserve_upload(
        upload_id,
        size,
        ttl_seconds=3600,
        max_total_bytes=settings.max_active_upload_bytes,
    ):
        raise HTTPException(status_code=429, detail="active upload capacity exceeded")
    meta = {
        "filename": filename,
        "contentType": "application/zip" if extension == ".zip" else "text/plain",
        "size": size,
        "uploadedAt": datetime.now(UTC).isoformat(),
        "uploadTokenSha256": sha256_hex(upload_token.encode("utf-8")),
    }
    try:
        store.put_json(f"upload:{upload_id}", meta, ttl_seconds=3600)
    except Exception:
        store.release_upload(upload_id)
        raise
    return {
        "uploadId": upload_id,
        "uploadUrl": f"{settings.public_api_url}/upload/{upload_id}?{urlencode({'token': upload_token})}",
        "expiresIn": 3600,
        "maxSize": settings.max_upload_bytes,
    }


@app.put("/upload/{upload_id}")
async def upload_file(upload_id: str, request: Request, token: str = "") -> dict[str, Any]:
    meta = store.get_json(f"upload:{upload_id}")
    if not meta:
        raise HTTPException(status_code=404, detail="upload not found or expired")
    if meta.get("received"):
        raise HTTPException(status_code=409, detail="upload is immutable after receipt")
    expected_token = str(meta.get("uploadTokenSha256") or "")
    supplied_token = sha256_hex(token.encode("utf-8")) if token else ""
    if not expected_token or not hmac.compare_digest(expected_token, supplied_token):
        raise HTTPException(status_code=403, detail="invalid upload token")
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="file too large")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid content length") from exc
    path = _upload_path(upload_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    received = 0
    try:
        with path.open("xb") as handle:
            async for chunk in request.stream():
                received += len(chunk)
                if received > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="file too large")
                digest.update(chunk)
                handle.write(chunk)
        if received != int(meta["size"]):
            raise HTTPException(status_code=400, detail="uploaded size does not match presign")
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail="upload is immutable after receipt") from exc
    except Exception:
        if path.is_file() and not path.is_symlink():
            path.unlink()
        raise
    meta.update(
        {
            "received": True,
            "receivedAt": datetime.now(UTC).isoformat(),
            "sha256": digest.hexdigest(),
            "bytes": received,
        }
    )
    meta.pop("uploadTokenSha256", None)
    store.put_json(f"upload:{upload_id}", meta, ttl_seconds=3600 * 24)
    store.extend_upload_reservation(upload_id, 3600 * 24)
    return {"success": True, "uploadId": upload_id, "sha256": meta["sha256"]}


@app.get("/upload/{upload_id}")
async def get_upload(upload_id: str, expires: int = 0, signature: str = "") -> FileResponse:
    if not _valid_internal_upload_signature(upload_id, expires, signature):
        raise HTTPException(status_code=403, detail="invalid or expired upload signature")
    meta = store.get_json(f"upload:{upload_id}")
    path = _upload_path(upload_id)
    if not meta or not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(
        path,
        media_type=meta.get("contentType") or "application/octet-stream",
        filename=meta.get("filename") or "upload",
        headers={
            "Cache-Control": "private, no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/upload/report/{report_id}")
async def get_report(report_id: str, expires: int = 0, signature: str = "") -> FileResponse:
    if not _valid_sha(report_id):
        raise HTTPException(status_code=400, detail="invalid report id")
    if not _valid_report_signature(report_id, expires, signature):
        raise HTTPException(status_code=403, detail="invalid or expired report signature")
    report_meta = store.get_json(f"report:{report_id}")
    path = settings.reports_dir / f"{report_id}.pdf"
    if not report_meta or not path.exists():
        raise HTTPException(status_code=404, detail="report not found")
    evidence_hash = str(report_meta.get("evidenceFingerprint") or report_id)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"eolkits-audit-{evidence_hash[:8]}.pdf",
        headers={
            "Cache-Control": "private, no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ---- checkout ---------------------------------------------------------------- #


@app.post("/api/audit/checkout")
async def audit_checkout(
    request: Request,
    email: str = Form(...),
    deadline: str | None = Form(None),
    upload_id: str | None = Form(None),
    upload_url: str | None = Form(None),
    source: str | None = Form(None),
    utm_source: str | None = Form(None),
    utm_medium: str | None = Form(None),
    utm_campaign: str | None = Form(None),
    kit: str | None = Form(None),
) -> Response:
    _require_audit_ready()
    deadline = _safe_deadline(deadline)
    # SSRF hardening: never trust an arbitrary upload_url. Accept an upload_id
    # (preferred) or extract one only from a URL that points at our own host,
    # then validate the upload actually exists locally.
    resolved_id = _resolve_upload_id(upload_id, upload_url)
    if not resolved_id:
        raise HTTPException(status_code=400, detail="upload_id required")
    meta = store.get_json(f"upload:{resolved_id}")
    path = _upload_path(resolved_id)
    if not meta or not meta.get("received") or not path.is_file():
        raise HTTPException(status_code=400, detail="upload has not completed")

    source_key = _request_source_key(request)
    if not store.allow_rate(
        f"checkout-hour:{source_key}", limit=10, window_seconds=3600
    ) or not store.allow_rate("checkout-day:global", limit=500, window_seconds=86400):
        raise HTTPException(status_code=429, detail="checkout capacity exceeded")
    try:
        preflight = await _preflight_upload(path, str(meta.get("filename") or "uploaded-input"))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(
            status_code=400, detail=f"Upload cannot be audited: {str(exc)[:240]}"
        ) from exc
    stored_hash = str(meta.get("sha256") or "")
    if not stored_hash or not hmac.compare_digest(
        stored_hash, str(preflight.get("input_hash") or "")
    ):
        raise HTTPException(status_code=400, detail="Uploaded bytes no longer match the receipt")
    retain_seconds = 3600 * 48
    meta["preflight"] = {
        "scannedFiles": preflight["scanned_files"],
        "skippedFiles": preflight["skipped_files"],
    }
    meta["retainUntil"] = (datetime.now(UTC) + timedelta(seconds=retain_seconds)).isoformat()
    store.put_json(f"upload:{resolved_id}", meta, ttl_seconds=retain_seconds)
    store.extend_upload_reservation(resolved_id, retain_seconds)
    claim = store.reserve_checkout(resolved_id, source_key)
    if not claim["owner"]:
        if claim.get("state") == "ready" and claim.get("session_url"):
            return _checkout_response(request, str(claim["session_url"]), 299, "existing")
        raise HTTPException(
            status_code=409, detail="checkout session is being created; retry shortly"
        )

    tier = pricing.audit_price_for_deadline(deadline, stripe_price_id=settings.audit_price_id)
    price_id = tier["stripe_price_id"]
    price = int(tier["price_usd"])
    attribution = _attribution(source, utm_source, utm_medium, utm_campaign, kit)
    try:
        session = create_checkout_session(
            settings,
            sku="audit",
            email=email,
            price_id=price_id,
            price_usd=price,
            metadata={
                "upload_id": resolved_id,
                "upload_sha256": str(meta.get("sha256") or ""),
                "deadline": deadline or "",
                **attribution,
            },
            success_path="/success/?sku=audit",
            cancel_path="/audit/?cancelled=1",
            idempotency_key=f"eolkits-audit-{resolved_id}",
        )
        store.complete_checkout(
            resolved_id,
            session_url=str(session["url"]),
            session_id=str(session.get("id") or "") or None,
        )
    except Exception:
        store.release_checkout(resolved_id)
        raise
    store.record_event("checkout_started", {"sku": "audit", "deadline": deadline, **attribution})
    return _checkout_response(request, session["url"], price, session["mode"])


@app.post("/api/pack/checkout")
async def pack_checkout(
    request: Request,
    email: str = Form(...),
    repo: str = Form(...),
    installation_id: str | None = Form(None),
    source: str | None = Form(None),
    utm_source: str | None = Form(None),
    utm_medium: str | None = Form(None),
    utm_campaign: str | None = Form(None),
    kit: str | None = Form(None),
) -> Response:
    # The public GitHub App is unavailable and the migration/refund path has not
    # passed a sandbox E2E. Refuse charges at the API even if an old form or raw
    # link is still cached somewhere.
    raise HTTPException(
        status_code=410,
        detail="Migration Pack is a private beta and is not available for purchase.",
    )


@app.post("/api/drift/checkout")
async def drift_checkout() -> Response:
    # The retired concept has no fulfillment path. Keep stale clients from
    # reaching any payment flow by refusing the request at the API boundary.
    raise HTTPException(
        status_code=410,
        detail="Drift Watch is not available for purchase.",
    )


@app.post("/api/events")
async def record_event(request: Request, response: Response) -> dict[str, Any]:
    """Bounded, first-party aggregate signal with no visitor identifier."""
    if _event_database_bytes() >= settings.max_event_db_bytes:
        raise HTTPException(status_code=503, detail="telemetry capacity exceeded")
    source_key = _request_source_key(request)
    if not store.allow_rate(
        f"event-hour:{source_key}", limit=settings.event_hourly_limit, window_seconds=3600
    ) or not store.allow_rate(
        "event-day:global", limit=settings.event_daily_limit, window_seconds=86400
    ):
        raise HTTPException(status_code=429, detail="event capacity exceeded")
    try:
        body = json.loads(await _read_limited_body(request, settings.max_event_bytes))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="invalid event JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="event object required")
    name = str(body.get("event") or body.get("name") or "")[:64]
    allowed_names = {"view", "widget_view", "scan_completed", "checkout_click"}
    if name not in allowed_names:
        raise HTTPException(status_code=400, detail="unsupported event")
    store.record_event(
        name,
        {
            "source": _event_token(body.get("source")),
            "utm_source": _event_token(body.get("utm_source")),
            "utm_medium": _event_token(body.get("utm_medium")),
            "utm_campaign": _event_token(body.get("utm_campaign")),
            "kit": _event_token(body.get("kit")),
            "deadline": _safe_deadline(body.get("deadline")),
            "sku": _event_token(body.get("sku")),
            "path": _canonical_event_path(body.get("path")),
            "meta": (
                {
                    "finding_count": _event_count(body["meta"].get("finding_count")),
                    "file_count": _event_count(body["meta"].get("file_count")),
                }
                if name == "scan_completed" and isinstance(body.get("meta"), dict)
                else None
            ),
        },
    )
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True}


@app.post("/admin/reconcile-refund")
async def reconcile_refund(
    request: Request, x_admin_token: str | None = Header(None)
) -> dict[str, Any]:
    """Resolve an owner-review refund only after Stripe proves it happened."""
    if not _admin_ok(x_admin_token):
        raise HTTPException(status_code=403, detail="admin token required")
    try:
        body = json.loads(await _read_limited_body(request, settings.max_form_bytes))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc
    session_id = str(body.get("session_id") or "") if isinstance(body, dict) else ""
    if not re.fullmatch(r"(?:cs_[A-Za-z0-9_]+|invoice_in_[A-Za-z0-9_]+)", session_id):
        raise HTTPException(status_code=400, detail="valid Stripe order id required")
    purchase = store.get_purchase_by_session(session_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="purchase not found")
    if session_id.startswith("invoice_"):
        invoice = retrieve_invoice(settings, session_id.removeprefix("invoice_"))
        payment_intent_id = _invoice_payment_intent_id(invoice) or purchase.get("payment_intent")
        subscription_id = _invoice_subscription_id(invoice)
    else:
        session = retrieve_checkout_session(settings, session_id)
        payment_intent_id = _payment_intent_id(session) or purchase.get("payment_intent")
        subscription_id = _subscription_id(session)
    if not payment_intent_id:
        raise HTTPException(status_code=409, detail="Stripe session has no payment intent")
    payment_intent = retrieve_payment_intent(settings, str(payment_intent_id))
    charge = payment_intent.get("latest_charge") or {}
    if not isinstance(charge, dict) or not charge.get("refunded"):
        raise HTTPException(status_code=409, detail="Stripe does not report a full refund")
    cancellation_verified = not subscription_id
    if subscription_id:
        subscription = retrieve_subscription(settings, subscription_id)
        cancellation_verified = subscription.get("status") in {"canceled", "incomplete_expired"}
        if not cancellation_verified:
            raise HTTPException(status_code=409, detail="Stripe subscription is still active")
    refund_id = str(
        ((charge.get("refunds") or {}).get("data") or [{}])[0].get("id") or "stripe-confirmed"
    )
    store.mark_refunded(session_id, refund_id)
    _enqueue_refund_notice(purchase)
    resolved = store.resolve_refund_jobs(
        session_id, include_cancellation=bool(cancellation_verified)
    )
    return {"ok": True, "session_id": session_id, "resolved_jobs": resolved}


# ---- generic lead capture (studio microsites + any product) ------------------ #

# Inbound forms use heterogeneous field names; these are the priority orders for
# the two identity columns. Everything else is preserved verbatim in `fields`.
_EMAIL_KEYS = ("email", "Email", "e-mail", "your-email", "your_email")
_NAME_KEYS = (
    "name",
    "Name",
    "full_name",
    "fullname",
    "contact",
    "company",
    "Business",
    "agency_name",
)

# Pragmatic email shape check — rejects obvious junk without trying to be RFC 5322.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_LEAD_RATE_MAX = settings.lead_ip_minute_limit


def _consume_lead_capture_allowance(request: Request) -> bool:
    """Durable per-source and global storage limits that survive restarts."""
    source_key = _request_source_key(request)
    return (
        store.allow_rate(
            f"lead-minute:{source_key}",
            limit=settings.lead_ip_minute_limit,
            window_seconds=60,
        )
        and store.allow_rate(
            f"lead-day:{source_key}",
            limit=settings.lead_ip_daily_limit,
            window_seconds=86400,
        )
        and store.allow_rate(
            "lead-day:global",
            limit=settings.lead_global_daily_limit,
            window_seconds=86400,
        )
    )


def _admin_ok(token: str | None) -> bool:
    expected = settings.admin_token
    if not expected or not token:
        return False
    import hmac as _hmac

    return _hmac.compare_digest(expected, token)


def _esc(value: Any) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _lead_email_html(product: str, source: str, fields: dict[str, str]) -> str:
    rows = "".join(
        f"<tr><td style='padding:4px 12px 4px 0;color:#6b7280;font-size:13px;vertical-align:top'>{_esc(k)}</td>"
        f"<td style='padding:4px 0;font-size:13px'><strong>{_esc(v)}</strong></td></tr>"
        for k, v in fields.items()
    )
    return (
        '<!doctype html><html><body style="font-family:system-ui,-apple-system,sans-serif;'
        'max-width:600px;margin:0 auto;padding:24px;line-height:1.5">'
        f"<h2 style=\"margin:0 0 4px\">New lead &mdash; {_esc(product) or 'studio'}</h2>"
        f"<p style=\"margin:0 0 16px;color:#6b7280;font-size:13px\">via {_esc(source) or 'website'}</p>"
        f'<table style="border-collapse:collapse;width:100%">{rows}</table>'
        '<p style="font-size:12px;color:#9ca3af;margin-top:24px">Captured by the GRACE lead bus '
        "(/api/v1/lead). Reply directly to reach the prospect.</p></body></html>"
    )


def _send_lead_notification(
    lead_id: int, product: str, source: str, fields: dict[str, str]
) -> None:
    """Owner alert for a captured lead. The lead ROW is already durable; this only
    flips `notified=1` after a CONFIRMED send. It retries transient failures and, if
    every attempt fails, logs LOUDLY and leaves `notified=0` so the row surfaces in
    the recovery queue — instead of silently dropping the way FormSubmit did one layer
    up. `resend_unnotified_leads` then self-heals once email recovers. Never raises."""
    recipients = [a.strip() for a in (settings.lead_notify_to or "").split(",") if a.strip()]
    if not recipients:
        logger.error("LEAD %s captured but LEAD_NOTIFY_TO is empty — OWNER NOT ALERTED", lead_id)
        return
    html = _lead_email_html(product, source, fields)
    subject = f"New lead: {product or 'studio inquiry'}"
    sent = 0
    for to in recipients:
        if not store.allow_rate(
            "email-lead-day:global",
            limit=settings.lead_notification_daily_limit,
            window_seconds=86400,
        ):
            logger.warning(
                "LEAD %s captured but notification budget is reserved for commerce mail; queued",
                lead_id,
            )
            break
        for attempt in (1, 2):
            try:
                send_email(
                    settings,
                    to=to,
                    subject=subject,
                    html=html,
                    idempotency_key=(
                        f"eolkits-lead-{lead_id}-" f"{hashlib.sha256(to.encode()).hexdigest()[:12]}"
                    ),
                )
                sent += 1
                break
            except EmailDeliveryError as exc:
                logger.warning(
                    "LEAD %s notify to %s attempt %d failed: %s", lead_id, to, attempt, exc
                )
                if not exc.retryable:
                    break  # permanent failure (e.g. bad recipient) — a retry won't help
            except Exception as exc:  # noqa: BLE001 — alert path must never raise
                logger.warning(
                    "LEAD %s notify to %s attempt %d failed: %s", lead_id, to, attempt, exc
                )
    if sent:
        try:
            store.mark_lead_notified(lead_id)
        except Exception:
            logger.exception("LEAD %s alert sent but failed to mark notified", lead_id)
    else:
        logger.error(
            "LEAD %s captured but ALL notify attempts failed (recipients=%s) — durable row kept; "
            "will retry via the re-send sweep",
            lead_id,
            recipients,
        )


def resend_unnotified_leads(max_batch: int = 50) -> dict[str, int]:
    """Re-attempt owner alerts for any durably-captured lead not yet confirmed-sent.
    Idempotent; runs once at startup and then on a cadence from the drain loop
    (LEAD_SWEEP_INTERVAL_SECONDS) — no external cron required. Self-heals a transient
    email outage without ever touching the (already durable) lead rows."""
    pending = store.unnotified_leads(limit=max_batch)
    for row in pending:
        try:
            fields = json.loads(row.get("fields") or "{}")
        except Exception:
            fields = {}
        _send_lead_notification(
            int(row["id"]), row.get("product") or "", row.get("source") or "", fields
        )
    remaining = store.count_unnotified()
    if remaining:
        logger.error("re-send sweep: %d lead(s) STILL unnotified after retry", remaining)
    elif pending:
        logger.info("re-send sweep: healed %d previously-unnotified lead(s)", len(pending))
    return {"attempted": len(pending), "still_unnotified": remaining}


def _resolve_next(next_url: str, request: Request) -> str:
    """Return a safe absolute redirect target, or "" for none (caller sends JSON).

    An absolute http(s) `_next` is honored only when its origin is allow-listed; a
    site-relative `/path` is prefixed with the request Origin (also allow-listed).
    This preserves each form's prior FormSubmit `_next` UX — including forms whose
    `_next` is relative — without the endpoint becoming an open redirector."""
    if not next_url:
        return ""
    if next_url.lower().startswith(("http://", "https://")):
        m = re.match(r"^(https?://[^/]+)", next_url)
        return next_url if (m and m.group(1) in _SITE_ORIGINS) else ""
    if next_url.startswith("/") and not next_url.startswith("//"):
        origin = request.headers.get("origin") or ""
        if not origin:
            m = re.match(r"^(https?://[^/]+)", request.headers.get("referer") or "")
            origin = m.group(1) if m else ""
        if origin in _SITE_ORIGINS:
            return origin + next_url
    return ""


def _respond(target: str, payload: dict[str, Any]) -> Response:
    return RedirectResponse(target, status_code=303) if target else JSONResponse(payload)


@app.post("/api/v1/lead")
async def capture_lead(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Generic lead capture for the studio microsites and any product.

    Accepts a native HTML form POST (urlencoded/multipart) or JSON, records the
    lead durably, fires an owner notification over the working email path, and
    303-redirects to `_next` (preserving the prior FormSubmit UX) — or returns
    JSON when no redirect target is given. Replaces FormSubmit, which silently
    dropped every submission at mxroute."""
    raw: dict[str, str] = {}
    try:
        form = await request.form()
        for k, v in form.multi_items():
            k, v = str(k), str(v)
            raw[k] = f"{raw[k]}, {v}" if k in raw else v  # join checkbox arrays
    except Exception:
        raw = {}
    if not raw:
        try:
            body = await request.json()
            if isinstance(body, dict):
                raw = {str(k): str(v) for k, v in body.items()}
        except Exception:
            raw = {}

    target = _resolve_next(raw.get("_next") or raw.get("next") or "", request)
    # Honeypot: bots fill the hidden _honey field. Accept silently; record nothing.
    if raw.get("_honey") or raw.get("_gotcha"):
        return _respond(target, {"ok": True})

    fields = {k: v for k, v in raw.items() if not k.startswith("_") and str(v).strip()}
    email = next((fields[k] for k in _EMAIL_KEYS if fields.get(k)), "")
    name = next((fields[k] for k in _NAME_KEYS if fields.get(k)), "")
    product = (raw.get("product") or raw.get("_subject") or "").strip()[:120]
    source = (raw.get("source") or _safe_referrer_source(request) or "").strip()[:200]
    for control in ("product", "source", "next"):
        fields.pop(control, None)
    if not email or not _EMAIL_RE.match(email.strip()):
        raise HTTPException(status_code=400, detail="A valid email is required.")
    if not _consume_lead_capture_allowance(request):
        raise HTTPException(status_code=429, detail="Too many submissions. Please try again later.")

    lead_id = store.record_lead(
        email=email, name=name, product=product, source=source, fields=fields
    )
    store.record_event("lead", {"source": source, "sku": product, "meta": {"lead_id": lead_id}})
    background_tasks.add_task(_send_lead_notification, lead_id, product, source, fields)
    return _respond(target, {"ok": True, "lead_id": lead_id})


# ---- webhooks ---------------------------------------------------------------- #


@app.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str | None = Header(None),
) -> Response:
    payload = await _read_limited_body(request, settings.max_webhook_bytes)
    if not verify_stripe_signature(payload, stripe_signature, settings.stripe_webhook_secret):
        raise HTTPException(status_code=400, detail="invalid signature")
    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid event JSON") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="invalid event")
    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="missing event id")

    # Durable idempotency: record the event atomically. A duplicate delivery
    # short-circuits without re-fulfilling.
    if not store.record_stripe_event(event_id, event.get("type") or "unknown", event):
        if store.stripe_event_status(event_id) in {"processed", "rejected"}:
            return Response("Already processed", media_type="text/plain")
        return Response(
            "Event is already being processed", status_code=503, media_type="text/plain"
        )

    try:
        if event.get("type") in {
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
        }:
            session_obj = event.get("data", {}).get("object", {})
            session_id = session_obj.get("id")
            if session_id:
                _ingest_paid_session(session_id, background_tasks)
        elif event.get("type") in {"invoice.paid", "invoice.payment_succeeded"}:
            invoice = event.get("data", {}).get("object", {})
            if isinstance(invoice, dict):
                _ingest_paid_invoice(invoice, background_tasks)
        elif event.get("type") in {"refund.updated", "refund.failed"}:
            refund = event.get("data", {}).get("object", {})
            if isinstance(refund, dict):
                _ingest_refund_event(refund)
        store.mark_stripe_event(event_id, "processed")
    except HTTPException:
        store.mark_stripe_event(event_id, "rejected")
        raise
    except Exception as exc:  # pragma: no cover - defensive
        store.mark_stripe_event(event_id, "error")
        logger.exception("Stripe webhook processing failed for event %s", event_id)
        raise HTTPException(status_code=500, detail="Stripe event processing failed") from exc
    return Response("OK", media_type="text/plain")


@app.post("/webhook/github")
async def github_webhook() -> Response:
    raise HTTPException(
        status_code=410,
        detail="The EOLkits GitHub App is closed; remove this webhook endpoint.",
    )


# ---- GitHub App install flow ------------------------------------------------- #


@app.get("/pack/install")
async def pack_install() -> Response:
    # Never send a customer into an unpublished/owner-only GitHub App manifest
    # flow. The Pack can return only after a public App and full paid E2E exist.
    return JSONResponse(
        {"available": False, "reason": "Migration Pack is currently a private beta."},
        status_code=410,
    )


@app.get("/pack/setup")
async def pack_setup() -> Response:
    raise HTTPException(status_code=410, detail="The EOLkits GitHub App is closed.")


# ---- license / verify / support (unchanged behavior) ------------------------- #


@app.post("/api/license/inquiry")
async def license_inquiry() -> None:
    raise HTTPException(
        status_code=410,
        detail="The organization-license research program is closed.",
    )


@app.get("/api/license/verify")
async def verify_license(key: str) -> dict[str, Any]:
    data = store.get_json(f"license:{key}")
    if not data:
        raise HTTPException(
            status_code=404, detail={"valid": False, "error": "Invalid license key"}
        )
    if datetime.fromisoformat(data["expiresAt"]) < datetime.now(UTC):
        raise HTTPException(
            status_code=403,
            detail={"valid": False, "error": "License expired", "expiredAt": data["expiresAt"]},
        )
    return {
        "valid": True,
        "company": data["company"],
        "expiresAt": data["expiresAt"],
        "features": ["legacy_key_verification"],
    }


@app.post("/api/license/validate")
async def validate_license(request: Request) -> dict[str, Any]:
    body = await request.json()
    key = body.get("key")
    if not key:
        raise HTTPException(
            status_code=400, detail={"valid": False, "error": "Missing license key"}
        )
    result = await verify_license(key)
    store.put_json(
        f"license:usage:{key}:{datetime.now(UTC).timestamp()}",
        {"action": body.get("action") or "validate", "timestamp": datetime.now(UTC).isoformat()},
        ttl_seconds=86400 * 365,
    )
    return {
        "valid": True,
        "action": body.get("action") or "validate",
        "timestamp": datetime.now(UTC).isoformat(),
        **result,
    }


@app.get("/verify/{sha}")
async def verify_report(sha: str) -> dict[str, Any]:
    data = store.get_json(f"verify:{sha}")
    if not data:
        raise HTTPException(status_code=404, detail={"valid": False, "error": "Hash not found"})
    return {"valid": True, "sha256": sha, **data}


@app.get("/api/verify/{sha}")
async def verify_report_api(sha: str) -> dict[str, Any]:
    return await verify_report(sha)


@app.post("/support/ask")
async def support_ask(request: Request) -> dict[str, Any]:
    body = await request.json()
    question = str(body.get("question") or "").lower()
    if not question:
        raise HTTPException(status_code=400, detail="Missing question")
    canned = {
        "pricing": "See https://eolkits.com/#pricing for current availability. The CLI is free (MIT). Audit v2 is the only prepared self-serve paid product and remains readiness-gated; Migration Pack, Org License, and Drift Watch are not for sale.",
        "refund": "Audit purchases have a 30-day money-back guarantee. Email hello@toledotechnologies.com from the purchase address. Terms: https://eolkits.com/legal/terms.html",
        "install": "Install any kit from https://github.com/ntoledo319/EOLkits. Each kit README has package-specific setup.",
        "license": "CLI code is MIT licensed. The only prepared paid product is the readiness-gated repository evidence report.",
        "support": "Use GitHub Discussions at https://github.com/ntoledo319/EOLkits/discussions.",
    }
    for keyword, answer in canned.items():
        if keyword in question:
            return {"answer": answer, "source": "canned", "confidence": "high"}
    return {
        "answer": "See the EOLkits docs at https://eolkits.com/ or ask on GitHub Discussions: https://github.com/ntoledo319/EOLkits/discussions",
        "source": "canned_fallback",
    }


# ---- partners ---------------------------------------------------------------- #


@app.post("/partners/signup")
async def partner_signup() -> None:
    raise HTTPException(
        status_code=410,
        detail="The white-label partner program is closed and is not accepting accounts.",
    )


@app.post("/partners/verify/{slug}")
async def partner_verify(slug: str) -> None:
    raise HTTPException(status_code=410, detail="The white-label partner program is closed.")


@app.post("/partners/{slug}/audit")
async def partner_audit(
    slug: str,
) -> None:
    raise HTTPException(status_code=410, detail="The white-label partner program is closed.")


# ---- helpers ----------------------------------------------------------------- #


def cleanup_expired_artifacts(
    upload_retention_hours: int = 24,
    report_retention_days: int = 30,
    event_retention_days: int = 30,
) -> dict[str, int]:
    """Enforce upload/report retention without recursive or symlink traversal."""
    upload_cutoff = time.time() - (upload_retention_hours * 3600)
    report_cutoff = time.time() - (report_retention_days * 86400)
    removed_uploads = 0
    removed_reports = 0

    if settings.uploads_dir.exists():
        for upload_dir in settings.uploads_dir.iterdir():
            try:
                if upload_dir.is_symlink():
                    if upload_dir.lstat().st_mtime < upload_cutoff:
                        upload_dir.unlink()
                        removed_uploads += 1
                    continue
                if not upload_dir.is_dir():
                    continue
                upload_file = upload_dir / "file"
                if not upload_file.is_file() or upload_file.is_symlink():
                    continue
                meta = store.get_json(f"upload:{upload_dir.name}") or {}
                retain_until = meta.get("retainUntil")
                if retain_until:
                    try:
                        if datetime.fromisoformat(str(retain_until)) > datetime.now(UTC):
                            continue
                    except ValueError:
                        pass
                if upload_file.stat().st_mtime >= upload_cutoff:
                    continue
                upload_file.unlink()
                # Only remove the generated one-file directory. Unexpected
                # contents are left for operator review rather than traversed.
                try:
                    upload_dir.rmdir()
                except OSError:
                    pass
                store.delete(f"upload:{upload_dir.name}")
                store.release_upload(upload_dir.name)
                removed_uploads += 1
            except FileNotFoundError:
                continue

    if settings.reports_dir.exists():
        for report in settings.reports_dir.iterdir():
            try:
                if report.suffix != ".pdf":
                    continue
                if report.is_symlink():
                    if report.lstat().st_mtime < report_cutoff:
                        report.unlink()
                        removed_reports += 1
                    continue
                if report.is_file() and report.stat().st_mtime < report_cutoff:
                    report.unlink()
                    store.delete(f"report:{report.stem}")
                    removed_reports += 1
            except FileNotFoundError:
                continue

    expired_kv = store.purge_expired_kv()
    telemetry = store.purge_telemetry(
        event_cutoff=(datetime.now(UTC) - timedelta(days=event_retention_days)).isoformat(),
        rate_cutoff=int(time.time()) - (2 * 86400),
    )
    return {
        "uploads": removed_uploads,
        "reports": removed_reports,
        "expired_kv": expired_kv,
        **telemetry,
    }


def _upload_path(upload_id: str) -> Path:
    if "/" in upload_id or "\\" in upload_id or not upload_id:
        raise HTTPException(status_code=400, detail="invalid upload id")
    return settings.uploads_dir / upload_id / "file"


async def _read_limited_body(request: Request, max_bytes: int) -> bytes:
    """Read a request without allowing an unauthenticated body to exhaust RAM."""
    declared = request.headers.get("content-length")
    if declared:
        try:
            if int(declared) > max_bytes:
                raise HTTPException(status_code=413, detail="request body too large")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid content length") from exc
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise HTTPException(status_code=413, detail="request body too large")
    return bytes(body)


def _request_source_key(request: Request) -> str:
    """Return a pseudonymous stable key for abuse-rate enforcement.

    Forwarded addresses are considered only when the direct peer is a local or
    private reverse proxy. Production uses a keyed digest so the stored value
    cannot be reversed by enumerating the public IP address space.
    """
    peer = request.client.host if request.client else "unknown"
    candidate = peer
    try:
        peer_ip = ipaddress.ip_address(peer)
        if peer_ip.is_loopback or peer_ip.is_private:
            forwarded = request.headers.get("x-forwarded-for", "")
            for value in reversed(forwarded.split(",")):
                value = value.strip()
                try:
                    forwarded_ip = ipaddress.ip_address(value)
                except ValueError:
                    continue
                candidate = forwarded_ip.compressed
                break
    except ValueError:
        pass
    key = settings.internal_url_secret.encode("utf-8") or b"eolkits-nonproduction-only"
    return hmac.new(key, candidate.encode("utf-8"), hashlib.sha256).hexdigest()[:24]


def _safe_referrer_source(request: Request) -> str:
    """Reduce an implicit Referer to origin + path; never retain query/fragment."""
    value = request.headers.get("referer") or ""
    try:
        parsed = urlparse(value)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path if parsed.path.startswith("/") else ""
    return f"{parsed.scheme}://{parsed.netloc}{path}"[:200]


def _run_audit_preflight(path: Path, filename: str) -> dict[str, Any]:
    from audit_pdf import preflight_audit_input

    return preflight_audit_input(upload_path=str(path), filename=filename)


async def _preflight_upload(path: Path, filename: str) -> dict[str, Any]:
    """Run one bounded archive validation without queueing unbounded memory work.

    The permit is released inside the worker, so a disconnected/cancelled request
    cannot release it while decompression is still consuming memory.
    """
    if not _PREFLIGHT_SLOTS.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="Audit preflight is busy; retry shortly")

    def work() -> dict[str, Any]:
        try:
            return _run_audit_preflight(path, filename)
        finally:
            _PREFLIGHT_SLOTS.release()

    task = asyncio.create_task(asyncio.to_thread(work))
    return await asyncio.shield(task)


def _resolve_upload_id(upload_id: str | None, upload_url: str | None) -> str | None:
    """Return a safe, local upload id. An upload_url is only honored when it
    points at our own host; arbitrary URLs are rejected (SSRF)."""
    if upload_id:
        candidate = Path(upload_id).name
        return candidate or None
    if not upload_url:
        return None
    parsed = urlparse(upload_url)
    own_hosts = {
        urlparse(settings.public_api_url).netloc,
        urlparse(settings.public_site_url).netloc,
    }
    if parsed.netloc and parsed.netloc not in own_hosts:
        raise HTTPException(status_code=400, detail="upload_url must reference an eolkits upload")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[-2] == "upload":
        return parts[-1]
    return None


def _attribution(
    source: str | None,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    kit: str | None,
) -> dict[str, str]:
    """Build the non-empty attribution metadata that rides along on the Stripe
    session so source/utm/kit survive into the purchase row and analytics."""
    fields = {
        "source": source,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
        "kit": kit,
    }
    return {
        key: clean for key, value in fields.items() if (clean := _event_token(value)) is not None
    }


def _event_token(value: Any) -> str | None:
    """Return a compact non-PII attribution token or discard it."""
    if value is None:
        return None
    token = str(value).strip().lower()
    return token if re.fullmatch(r"[a-z0-9._-]{1,64}", token) else None


def _safe_deadline(value: Any) -> str | None:
    candidate = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return None
    try:
        datetime.strptime(candidate, "%Y-%m-%d")
    except ValueError:
        return None
    return candidate


def _canonical_event_path(value: Any) -> str:
    """Collapse page paths to a small route taxonomy; never store query data."""
    candidate = str(value or "")
    if not candidate.startswith("/") or any(c in candidate for c in "?#\r\n"):
        return "/other/"
    if candidate == "/EOLkits" or candidate.startswith("/EOLkits/"):
        candidate = candidate[len("/EOLkits") :] or "/"
    segment = candidate.strip("/").split("/", 1)[0]
    allowed = {
        "audit",
        "blog",
        "eol-checker",
        "fix",
        "license",
        "migrate",
        "scan",
        "status",
        "verify",
    }
    if not segment:
        return "/"
    return f"/{segment}/" if segment in allowed else "/other/"


def _event_count(value: Any) -> int:
    try:
        return max(0, min(int(value or 0), 10000))
    except (TypeError, ValueError, OverflowError):
        return 0


def _event_database_bytes() -> int:
    """Include SQLite sidecars so telemetry stops before exhausting shared disk."""
    total = 0
    for suffix in ("", "-wal", "-shm"):
        path = Path(str(settings.db_path) + suffix)
        try:
            total += path.stat().st_size
        except FileNotFoundError:
            pass
    return total


def _valid_sha(sha: str) -> bool:
    return len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)


def _signed_upload_url(upload_id: str, lifetime_seconds: int = 900) -> str:
    """Create a short-lived, runner-only URL for customer source bytes."""
    expires = int(time.time()) + lifetime_seconds
    message = f"{upload_id}:{expires}".encode("utf-8")
    signature = hmac.new(
        settings.internal_url_secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    query = urlencode({"expires": expires, "signature": signature})
    return f"{settings.public_api_url.rstrip('/')}/upload/{upload_id}?{query}"


def _valid_internal_upload_signature(upload_id: str, expires: int, signature: str) -> bool:
    if not settings.internal_url_secret or not signature:
        return False
    now = int(time.time())
    if expires < now or expires > now + 1200:
        return False
    expected = hmac.new(
        settings.internal_url_secret.encode("utf-8"),
        f"{upload_id}:{expires}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _signed_report_url(sha: str, lifetime_seconds: int = 86400 * 30) -> str:
    """Create a buyer-facing, expiring report URL."""
    expires = int(time.time()) + lifetime_seconds
    signature = hmac.new(
        settings.internal_url_secret.encode("utf-8"),
        f"report:{sha}:{expires}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    query = urlencode({"expires": expires, "signature": signature})
    return f"{settings.public_api_url.rstrip('/')}/upload/report/{sha}?{query}"


def _valid_report_signature(sha: str, expires: int, signature: str) -> bool:
    if not settings.internal_url_secret or not signature:
        return False
    now = int(time.time())
    if expires < now or expires > now + (86400 * 31):
        return False
    expected = hmac.new(
        settings.internal_url_secret.encode("utf-8"),
        f"report:{sha}:{expires}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _checkout_response(request: Request, url: str, price: int, mode: str) -> Response:
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse(url, status_code=303)
    return JSONResponse({"url": url, "price": price, "mode": mode})


# ---- payment validation + fulfillment ---------------------------------------- #


def _validate_paid_session(
    session: dict[str, Any], expected_sku: str | None = None
) -> dict[str, Any]:
    """Verify an authoritative Stripe session before fulfilling. Raises 400 on
    any mismatch so we never fulfill (or refund-link) an unpaid/forged order."""
    if session.get("status") not in (None, "complete"):
        raise HTTPException(status_code=400, detail="session not complete")
    if session.get("payment_status") not in ("paid", "no_payment_required"):
        raise HTTPException(status_code=400, detail="session not paid")
    metadata = session.get("metadata") or {}
    if metadata.get("project") != "eolkits":
        raise HTTPException(status_code=400, detail="session not an eolkits order")
    price_id = _session_price_id(session) or metadata.get("price_id")
    # Historical raw Payment Links omitted metadata[sku]. Recover only from an
    # exact configured Price ID; never guess from amount or product copy.
    sku = metadata.get("sku") or (
        pricing.sku_for_price_id(price_id, active_audit_price_id=settings.audit_price_id)
        if price_id
        else None
    )
    if not sku:
        raise HTTPException(status_code=400, detail="missing or unrecognized sku")
    if expected_sku and sku != expected_sku:
        raise HTTPException(status_code=400, detail="unexpected sku")
    if session.get("currency") not in ("usd", None):
        raise HTTPException(status_code=400, detail="unexpected currency")
    # In production the charge must be livemode.
    livemode = session.get("livemode")
    if settings.is_production and livemode is False:
        raise HTTPException(status_code=400, detail="test-mode session rejected in production")

    allowed = pricing.allowed_price_ids(sku, active_audit_price_id=settings.audit_price_id)
    configured_price_id = metadata.get("price_id")
    inline_test_price = (
        not settings.is_production
        and livemode is False
        and metadata.get("pricing_mode") == "inline_test"
        and configured_price_id in allowed
    )
    if not inline_test_price and (not price_id or not allowed or price_id not in allowed):
        raise HTTPException(status_code=400, detail="price id not recognized for sku")
    amount_total = session.get("amount_total")
    expected_amount = pricing.expected_amount_cents(
        sku,
        configured_price_id if inline_test_price else price_id,
        active_audit_price_id=settings.audit_price_id,
    )
    if expected_amount is None or amount_total is None or amount_total != expected_amount:
        raise HTTPException(status_code=400, detail="amount mismatch")
    payment_intent = _payment_intent_id(session)
    if expected_amount > 0 and not payment_intent:
        raise HTTPException(status_code=400, detail="paid session has no refundable payment intent")

    return {
        "sku": sku,
        "price_id": price_id,
        "amount_total": amount_total,
        "currency": session.get("currency"),
        "livemode": bool(livemode),
        "payment_intent": payment_intent,
        "email": session.get("customer_email") or metadata.get("email"),
        "metadata": metadata,
    }


def _session_price_id(session: dict[str, Any]) -> str | None:
    line_items = (session.get("line_items") or {}).get("data") or []
    if line_items:
        return ((line_items[0] or {}).get("price") or {}).get("id")
    return None


def _payment_intent_id(session: dict[str, Any]) -> str | None:
    pi = session.get("payment_intent")
    if isinstance(pi, dict):
        return pi.get("id")
    if pi:
        return str(pi)
    subscription = session.get("subscription")
    if isinstance(subscription, dict):
        invoice = subscription.get("latest_invoice")
        if isinstance(invoice, dict):
            invoice_pi = invoice.get("payment_intent")
            if isinstance(invoice_pi, dict):
                return invoice_pi.get("id")
            if invoice_pi:
                return str(invoice_pi)
    return None


def _subscription_id(session: dict[str, Any]) -> str | None:
    subscription = session.get("subscription")
    if isinstance(subscription, dict):
        return subscription.get("id")
    return str(subscription) if subscription else None


def _ingest_paid_session(session_id: str, background_tasks: BackgroundTasks) -> None:
    """Retrieve the authoritative session, validate it, durably record the
    purchase, and durably queue fulfillment."""
    if settings.is_demo_stripe:
        return  # No live Stripe in sandbox; fulfillment is exercised via tests.
    session = retrieve_checkout_session(settings, session_id)
    try:
        info = _validate_paid_session(session)
    except HTTPException as exc:
        # A Stripe-hosted link created by this project can still charge even if
        # its metadata is stale. If it is unquestionably a live, paid EOLkits
        # session, durably refund it instead of rejecting the webhook after the
        # customer has already paid.
        metadata = session.get("metadata") or {}
        payment_intent = _payment_intent_id(session)
        subscription_id = _subscription_id(session)
        price_id = _session_price_id(session) or metadata.get("price_id")
        known_sku = (
            pricing.sku_for_price_id(price_id, active_audit_price_id=settings.audit_price_id)
            if price_id
            else None
        )
        if (
            (metadata.get("project") == "eolkits" or known_sku is not None)
            and session.get("status") in (None, "complete")
            and session.get("payment_status") in ("paid", "no_payment_required")
            and session.get("currency") in ("usd", None)
            and (not settings.is_production or session.get("livemode") is not False)
            and known_sku
        ):
            if payment_intent:
                job_type, job_status = "refund_payment", "pending"
            elif subscription_id:
                job_type, job_status = "cancel_subscription", "pending"
            else:
                job_type, job_status = "refund_review", "requires_owner"
            job = {
                "type": job_type,
                "sessionId": session_id,
                "payment_intent": payment_intent,
                "subscription_id": subscription_id,
                "amount": session.get("amount_total"),
                "email": session.get("customer_email") or metadata.get("email"),
                "reason": f"unfulfillable Stripe session: {exc.detail}",
            }
            _, job_id, job_created = store.record_purchase_with_job(
                session_id=session_id,
                payment_intent=payment_intent,
                sku=known_sku,
                email=job["email"],
                price_id=price_id,
                amount=session.get("amount_total"),
                currency=session.get("currency"),
                livemode=bool(session.get("livemode")),
                metadata=metadata,
                job_type=job_type,
                job_payload=job,
                job_status=job_status,
                dedupe_key=f"refund:{session_id}",
                max_attempts=12,
            )
            if job_created and job_status == "pending":
                background_tasks.add_task(_run_job, job_id, job)
            return
        raise
    metadata = info["metadata"]
    sku = info["sku"]
    blocker = _paid_fulfillment_blocker(sku, metadata)
    if blocker:
        subscription_id = _subscription_id(session)
        if info["payment_intent"]:
            job_type, job_status = "refund_payment", "pending"
        elif subscription_id:
            job_type, job_status = "cancel_subscription", "pending"
        else:
            job_type, job_status = "refund_review", "requires_owner"
        dedupe_key = f"refund:{session_id}"
        job = {
            "type": job_type,
            "sessionId": session_id,
            "payment_intent": info["payment_intent"],
            "subscription_id": subscription_id,
            "amount": info["amount_total"],
            "email": info["email"],
            "reason": blocker,
        }
        max_attempts = 12
    else:
        job_type = "audit_pdf"
        job_status = "pending"
        dedupe_key = f"fulfill:{session_id}"
        job = {
            "type": "audit_pdf",
            "sessionId": session_id,
            "email": info["email"],
            "upload_id": metadata.get("upload_id"),
            "upload_sha256": metadata.get("upload_sha256"),
            "deadline": metadata.get("deadline"),
        }
        max_attempts = 6
    purchase_created, job_id, job_created = store.record_purchase_with_job(
        session_id=session_id,
        payment_intent=info["payment_intent"],
        sku=sku,
        email=info["email"],
        price_id=info["price_id"],
        amount=info["amount_total"],
        currency=info["currency"],
        livemode=info["livemode"],
        metadata=metadata,
        job_type=job_type,
        job_payload=job,
        job_status=job_status,
        dedupe_key=dedupe_key,
        max_attempts=max_attempts,
    )
    if purchase_created:
        store.record_event(
            "purchase_paid",
            {
                "sku": sku,
                "source": metadata.get("source"),
                "utm_source": metadata.get("utm_source"),
                "utm_medium": metadata.get("utm_medium"),
                "utm_campaign": metadata.get("utm_campaign"),
                "kit": metadata.get("kit"),
                "deadline": metadata.get("deadline"),
            },
        )
    if job_created and job_status == "pending":
        background_tasks.add_task(_run_job, job_id, job)


def _ingest_paid_invoice(invoice: dict[str, Any], background_tasks: BackgroundTasks) -> None:
    """Cancel/refund renewals from retired recurring products.

    Checkout completion handles the first subscription invoice. This handler
    closes the later-renewal gap if an old Org/Drift subscription still exists.
    """
    invoice_id = str(invoice.get("id") or "")
    if invoice.get("billing_reason") not in {"subscription_cycle", "subscription_update"}:
        return
    price_id = None
    sku = None
    for candidate in _invoice_price_ids(invoice):
        candidate_sku = pricing.sku_for_price_id(
            candidate, active_audit_price_id=settings.audit_price_id
        )
        if candidate_sku in {"org_license", "drift_watch"}:
            price_id, sku = candidate, candidate_sku
            break
    if not invoice_id or sku not in {"org_license", "drift_watch"}:
        return
    if invoice.get("status") not in {"paid", None}:
        return
    if invoice.get("currency") not in {"usd", None}:
        return
    if settings.is_production and invoice.get("livemode") is False:
        return
    subscription_id = _invoice_subscription_id(invoice)
    payment_intent = _invoice_payment_intent_id(invoice)
    amount = invoice.get("amount_paid")
    email = invoice.get("customer_email")
    session_id = f"invoice_{invoice_id}"
    if payment_intent:
        job_type, job_status = "refund_payment", "pending"
    elif subscription_id:
        job_type, job_status = "cancel_subscription", "pending"
    else:
        job_type, job_status = "refund_review", "requires_owner"
    job = {
        "type": job_type,
        "sessionId": session_id,
        "invoice_id": invoice_id,
        "payment_intent": payment_intent,
        "subscription_id": subscription_id,
        "amount": amount,
        "email": email,
        "reason": f"renewal for retired {sku}",
    }
    _, job_id, created = store.record_purchase_with_job(
        session_id=session_id,
        payment_intent=payment_intent,
        sku=sku,
        email=email,
        price_id=price_id,
        amount=amount,
        currency=invoice.get("currency"),
        livemode=bool(invoice.get("livemode")),
        metadata={"invoice_id": invoice_id, "subscription_id": subscription_id},
        job_type=job_type,
        job_payload=job,
        job_status=job_status,
        dedupe_key=f"refund-invoice:{invoice_id}",
        max_attempts=12,
    )
    if created and job_status == "pending":
        background_tasks.add_task(_run_job, job_id, job)


def _invoice_price_ids(invoice: dict[str, Any]) -> list[str]:
    lines = (invoice.get("lines") or {}).get("data") or []
    price_ids: list[str] = []
    for raw_line in lines:
        line = raw_line or {}
        price = line.get("price") or {}
        value = str(price.get("id") or "") if isinstance(price, dict) else str(price or "")
        if not value:
            details = (line.get("pricing") or {}).get("price_details") or {}
            nested = details.get("price")
            value = str(nested.get("id") or "") if isinstance(nested, dict) else str(nested or "")
        if value and value not in price_ids:
            price_ids.append(value)
    return price_ids


def _invoice_subscription_id(invoice: dict[str, Any]) -> str | None:
    direct = invoice.get("subscription")
    if isinstance(direct, dict):
        return str(direct.get("id") or "") or None
    if direct:
        return str(direct)
    nested = ((invoice.get("parent") or {}).get("subscription_details") or {}).get("subscription")
    if isinstance(nested, dict):
        return str(nested.get("id") or "") or None
    return str(nested) if nested else None


def _invoice_payment_intent_id(invoice: dict[str, Any]) -> str | None:
    direct = invoice.get("payment_intent")
    if isinstance(direct, dict):
        return str(direct.get("id") or "") or None
    if direct:
        return str(direct)
    payments = (invoice.get("payments") or {}).get("data") or []
    for item in payments:
        value = ((item or {}).get("payment") or {}).get("payment_intent")
        if isinstance(value, dict) and value.get("id"):
            return str(value["id"])
        if value:
            return str(value)
    return None


def _ingest_refund_event(refund: dict[str, Any]) -> None:
    """Reconcile only the exact full refund previously created by this app."""
    payment_intent = refund.get("payment_intent")
    if isinstance(payment_intent, dict):
        payment_intent = payment_intent.get("id")
    if not payment_intent:
        return
    purchase = store.get_purchase_by_payment_intent(str(payment_intent))
    if not purchase:
        return
    status = str(refund.get("status") or "")
    refund_id = str(refund.get("id") or "")
    session_id = str(purchase["session_id"])
    expected_refund_id = str(purchase.get("refund_id") or "")
    if (
        not refund_id
        or not expected_refund_id
        or not hmac.compare_digest(refund_id, expected_refund_id)
    ):
        return
    if status == "succeeded":
        expected_amount = purchase.get("amount")
        try:
            actual_amount = int(refund.get("amount"))
            full_amount = int(expected_amount)
        except (TypeError, ValueError):
            return
        if actual_amount != full_amount or full_amount <= 0:
            return
        store.mark_refunded(session_id, refund_id)
        _enqueue_refund_notice(purchase)
        store.resolve_refund_jobs(session_id, include_cancellation=False)
        return
    if status in {"failed", "canceled"}:
        store.mark_refund_failed(session_id, refund_id or None)
        store.enqueue(
            "refund_review",
            {
                "type": "refund_review",
                "sessionId": session_id,
                "payment_intent": str(payment_intent),
                "refund_id": refund_id,
                "reason": f"Stripe refund entered terminal status {status}",
            },
            status="requires_owner",
            dedupe_key=f"refund-review:{session_id}",
        )


def _paid_fulfillment_blocker(sku: str | None, metadata: dict[str, Any]) -> str | None:
    if sku not in ACTIVE_CHECKOUT_SKUS:
        return f"{sku or 'unknown'} is not available for purchase"
    if sku == "audit":
        upload_id = metadata.get("upload_id")
        if not upload_id:
            return "audit purchase did not include a server-gated upload"
        meta = store.get_json(f"upload:{upload_id}")
        if not meta or not meta.get("received") or not _upload_path(upload_id).is_file():
            return "audit upload is missing or incomplete"
        upload_sha = str(metadata.get("upload_sha256") or "")
        stored_sha = str(meta.get("sha256") or "")
        if not upload_sha or not stored_sha or not hmac.compare_digest(upload_sha, stored_sha):
            return "audit upload hash does not match checkout metadata"
    return None


# ---- job queue / drainer ----------------------------------------------------- #


def _enqueue_job(
    job: dict[str, Any], background_tasks: BackgroundTasks, dedupe_key: str | None = None
) -> int:
    job_id = store.enqueue(str(job.get("type") or "unknown"), job, dedupe_key=dedupe_key)
    background_tasks.add_task(_run_job, job_id, job)
    return job_id


def _run_job(job_id: int, job: dict[str, Any]) -> None:
    # Only one of {inline background task, startup drainer} processes a job.
    if store.deadletter_if_exhausted(
        job_id, "reclaimed job exceeded max attempts after a process crash"
    ):
        _compensate_dead_letter(job, "job exceeded max attempts after a process crash")
        store.mark_dead_letter_compensated(job_id)
        return
    if not store.try_claim(job_id):
        return
    try:
        _execute_job(job_id, job)
        store.mark_job(job_id, "completed")
    except Exception as exc:
        status = store.schedule_retry_or_deadletter(job_id, str(exc))
        if status == "dead_letter":
            _compensate_dead_letter(job, str(exc))
            store.mark_dead_letter_compensated(job_id)


def _compensate_dead_letter(job: dict[str, Any], error: str) -> None:
    session_id = str(job.get("sessionId") or "")
    if not session_id:
        return
    purchase = store.get_purchase_by_session(session_id)
    if not purchase or purchase.get("refunded"):
        return
    if job.get("type") == "refund_payment":
        store.enqueue(
            "refund_review",
            {
                "type": "refund_review",
                "sessionId": session_id,
                "email": purchase.get("email"),
                "reason": f"automatic refund failed after retries: {error[:300]}",
            },
            status="requires_owner",
            dedupe_key=f"refund-review:{session_id}",
        )
        return
    payment_intent = purchase.get("payment_intent")
    refund_type = "refund_payment" if payment_intent else "refund_review"
    refund_status = "pending" if payment_intent else "requires_owner"
    store.enqueue(
        refund_type,
        {
            "type": refund_type,
            "sessionId": session_id,
            "payment_intent": payment_intent,
            "amount": purchase.get("amount"),
            "email": purchase.get("email"),
            "reason": f"paid fulfillment failed after retries: {error[:300]}",
        },
        status=refund_status,
        dedupe_key=f"refund:{session_id}",
        max_attempts=12,
    )


def _execute_job(job_id: int, job: dict[str, Any]) -> None:
    if job.get("type") == "refund_payment":
        _execute_refund_job(job)
        return
    if job.get("type") == "cancel_subscription":
        _execute_subscription_cancellation(job)
        return
    if job.get("type") == "refund_notice":
        _execute_refund_notice(job)
        return
    if job.get("type") != "audit_pdf" or job.get("transfer"):
        raise RuntimeError("this legacy fulfillment product is no longer available")
    session_id = str(job.get("sessionId") or "")
    delivery = store.get_json(f"delivery:{session_id}") if session_id else None
    if delivery:
        if delivery.get("status") == "delivered":
            _delete_upload_artifact(job.get("upload_id"))
            return
        if delivery.get("status") == "prepared":
            _deliver_prepared_audit(delivery, job)
            return
    result = _dispatch_runner(job)
    _fulfill_audit(result, job)


def _execute_subscription_cancellation(job: dict[str, Any]) -> None:
    session_id = str(job.get("sessionId") or "")
    subscription_id = str(job.get("subscription_id") or "")
    if not session_id or not subscription_id:
        raise RuntimeError("subscription cancellation job missing identifiers")
    if not settings.is_demo_stripe:
        cancel_subscription(
            settings,
            subscription_id=subscription_id,
            idempotency_key=f"cancel:{session_id}",
        )
    store.enqueue(
        "refund_review",
        {
            "type": "refund_review",
            "sessionId": session_id,
            "email": job.get("email"),
            "reason": "recurring charge cancelled; payment intent requires operator lookup",
        },
        status="requires_owner",
        dedupe_key=f"refund-review:{session_id}",
    )


def _execute_refund_job(job: dict[str, Any]) -> None:
    session_id = str(job.get("sessionId") or "")
    payment_intent = str(job.get("payment_intent") or "")
    if not session_id or not payment_intent:
        raise RuntimeError("refund job missing session or payment intent")
    purchase = store.get_purchase_by_session(session_id)
    if not purchase:
        raise RuntimeError("refund job purchase is missing")
    subscription_id = str(job.get("subscription_id") or "")
    if subscription_id and not settings.is_demo_stripe:
        cancellation = cancel_subscription(
            settings,
            subscription_id=subscription_id,
            idempotency_key=f"cancel:{session_id}",
        )
        if str(cancellation.get("status") or "") not in {
            "canceled",
            "already_absent",
            "incomplete_expired",
        }:
            raise RuntimeError("Stripe subscription cancellation was not confirmed")
    # A matching succeeded webhook may have completed the refund while this job
    # was sleeping. Cancellation is deliberately checked first for subscriptions.
    purchase = store.get_purchase_by_session(session_id)
    if purchase and purchase.get("refunded"):
        _enqueue_refund_notice(purchase)
        return
    if settings.is_demo_stripe:
        refund_id = "re_demo"
        refund_amount = int(purchase.get("amount") or 0)
    else:
        existing_refund_id = str(purchase.get("refund_id") or "")
        if existing_refund_id:
            refund = retrieve_refund(settings, existing_refund_id)
            refund_id = str(refund.get("id") or "")
            if not refund_id or not hmac.compare_digest(refund_id, existing_refund_id):
                raise RuntimeError("Stripe returned the wrong refund during reconciliation")
        else:
            refund = create_refund(
                settings,
                payment_intent=payment_intent,
                amount=int(job["amount"]) if job.get("amount") is not None else None,
                idempotency_key=f"refund:{session_id}",
            )
            refund_id = str(refund.get("id") or "")
            if not refund_id or not store.mark_refund_pending(session_id, refund_id):
                raise RuntimeError("Stripe refund could not be bound to this purchase")
        refund_status = str(refund.get("status") or "")
        if refund_status != "succeeded":
            refund = retrieve_refund(settings, refund_id)
            if str(refund.get("id") or "") != refund_id:
                raise RuntimeError("Stripe returned the wrong refund during reconciliation")
            refund_status = str(refund.get("status") or "")
        if refund_status != "succeeded":
            raise RuntimeError(
                f"Stripe refund is not complete (status={refund_status or 'unknown'})"
            )
        try:
            refund_amount = int(refund.get("amount"))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Stripe refund response has no verifiable amount") from exc
    expected_amount = int(purchase.get("amount") or 0)
    if expected_amount <= 0 or refund_amount != expected_amount:
        raise RuntimeError("Stripe refund is not the full recorded purchase amount")
    changed = store.mark_refunded(session_id, refund_id)
    if changed:
        store.record_event(
            "purchase_refunded",
            {
                "sku": purchase.get("sku") if purchase else None,
                "meta": {"reason": job.get("reason")},
            },
        )
    if changed:
        _enqueue_refund_notice(purchase)


def _enqueue_refund_notice(purchase: dict[str, Any]) -> int | None:
    session_id = str(purchase.get("session_id") or "")
    email = str(purchase.get("email") or "")
    if not session_id or not email:
        return None
    return store.enqueue(
        "refund_notice",
        {
            "type": "refund_notice",
            "sessionId": session_id,
            "email": email,
        },
        dedupe_key=f"refund-notice:{session_id}",
        max_attempts=12,
    )


def _execute_refund_notice(job: dict[str, Any]) -> None:
    session_id = str(job.get("sessionId") or "")
    email = str(job.get("email") or "")
    if not session_id or not email:
        raise RuntimeError("refund notice is missing order identity")
    purchase = store.get_purchase_by_session(session_id)
    if not purchase or not purchase.get("refunded"):
        raise RuntimeError("refund notice cannot precede a confirmed full refund")
    send_email(
        settings,
        to=email,
        subject="Your EOLkits purchase was automatically refunded",
        html=(
            "<p>We could not safely fulfill this purchase, so the full charge was "
            "automatically refunded.</p><p>No action is required. If you have questions, "
            "email hello@toledotechnologies.com.</p>"
        ),
        idempotency_key=f"eolkits-refund-{session_id}",
    )


async def _drain_loop() -> None:
    # Start the clock now so the first PERIODIC lead sweep runs one interval after
    # the one-shot startup sweep, instead of stacking on top of it.
    last_lead_sweep = time.monotonic()
    last_artifact_sweep = time.monotonic()
    while True:
        try:
            await asyncio.get_running_loop().run_in_executor(None, _drain_once)
        except Exception:  # pragma: no cover - never let the loop die
            logger.exception("drain loop iteration failed")
        # Self-heal unnotified leads on a cadence, so an email outage recovers without
        # an external cron (it previously only recovered on a full process restart).
        now = time.monotonic()
        if now - last_lead_sweep >= LEAD_SWEEP_INTERVAL_SECONDS:
            last_lead_sweep = now
            try:
                await asyncio.to_thread(resend_unnotified_leads)
            except Exception:  # pragma: no cover - the sweep must never kill the loop
                logger.exception("periodic lead re-send sweep failed")
        if now - last_artifact_sweep >= ARTIFACT_SWEEP_INTERVAL_SECONDS:
            last_artifact_sweep = now
            try:
                await asyncio.to_thread(cleanup_expired_artifacts)
            except Exception:  # pragma: no cover - report health, never kill the loop
                logger.exception("artifact-retention sweep failed")
        await asyncio.sleep(DRAIN_INTERVAL_SECONDS)


def _drain_once() -> None:
    # Recover jobs orphaned in 'running' by a prior crash BEFORE claiming new work,
    # so a paid order interrupted mid-fulfillment is retried rather than lost.
    reclaimed = store.reclaim_stale_running_jobs(STALE_RUNNING_SECONDS)
    if reclaimed:
        logger.warning("reclaimed %d job(s) stuck in 'running' (likely a prior crash)", reclaimed)
    # Dead-letter and compensation are separate durable operations. Reconcile on
    # every drain so a crash between them cannot strand a paid order forever.
    for terminal in store.dead_letter_jobs():
        try:
            job = terminal.get("payload") or {}
            session_id = str(job.get("sessionId") or "")
            if session_id:
                purchase = store.get_purchase_by_session(session_id)
                if purchase and not purchase.get("refunded"):
                    _compensate_dead_letter(job, str(terminal.get("last_error") or "terminal job"))
            store.mark_dead_letter_compensated(int(terminal["id"]))
        except Exception:
            logger.exception("failed to reconcile terminal job %s", terminal.get("id"))
    for job_row in store.claim_pending_jobs():
        _run_job(int(job_row["id"]), job_row["payload"])


def _dispatch_runner(job: dict[str, Any]) -> dict[str, Any]:
    job = _attach_runner_upload_ref(job)
    if settings.runner_url:
        response = requests.post(
            settings.runner_url,
            headers={
                "Content-Type": "application/json",
                **(
                    {"Authorization": f"Bearer {settings.runner_token}"}
                    if settings.runner_token
                    else {}
                ),
            },
            json=job,
            timeout=900,
            stream=True,
            allow_redirects=False,
        )
        if 300 <= response.status_code < 400:
            raise RuntimeError("runner redirects are not allowed")
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            raise RuntimeError("runner returned a non-JSON response")
        body = bytearray()
        for chunk in response.iter_content(64 * 1024):
            body.extend(chunk)
            if len(body) > 27 * 1024 * 1024:
                raise RuntimeError("runner response exceeds delivery limit")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise RuntimeError("runner returned an invalid response")
        if data.get("success") is False:
            raise RuntimeError(json.dumps(data))
        return data.get("result") or {}
    if settings.enable_inline_runner:
        from main import run_job

        return run_job(job)
    store.enqueue(str(job.get("type") or "unknown"), job, status="requires_runner")
    return {"queued": True}


def _attach_runner_upload_ref(job: dict[str, Any]) -> dict[str, Any]:
    """Convert an upload_id into a runner-consumable reference WITHOUT trusting
    a client-supplied URL. Inline runner gets a local path; an HTTP runner gets
    a server-derived URL on our own host."""
    upload_id = job.get("upload_id")
    if not upload_id:
        return job
    job = dict(job)
    meta = store.get_json(f"upload:{upload_id}") or {}
    job["filename"] = meta.get("filename") or "uploaded-input"
    if not settings.runner_url:
        job["upload_path"] = str(_upload_path(upload_id))
    else:
        job["upload_url"] = _signed_upload_url(str(upload_id))
    return job


def _fulfill_audit(result: dict[str, Any], job: dict[str, Any]) -> None:
    # The paid order—not a remote runner response—is authoritative for recipient.
    email = job.get("email")
    input_hash = result.get("input_hash")
    evidence_hash = result.get("evidence_hash")
    pdf_base64 = result.get("pdf_base64")
    rule_pack_version = result.get("rule_pack_version")
    report_version = result.get("report_version")
    generated_at = result.get("generated_at")
    if not all(
        [
            email,
            input_hash,
            evidence_hash,
            pdf_base64,
            rule_pack_version,
            report_version,
            generated_at,
        ]
    ):
        raise RuntimeError("audit result missing delivery fields")
    if not _valid_sha(str(input_hash)) or not _valid_sha(str(evidence_hash)):
        raise RuntimeError("audit result contains an invalid hash")
    if str(report_version) != AUDIT_REPORT_VERSION:
        raise RuntimeError("audit runner returned an unsupported report version")
    upload_meta = store.get_json(f"upload:{job.get('upload_id')}") or {}
    expected_input_hash = str(upload_meta.get("sha256") or "")
    if not expected_input_hash or not hmac.compare_digest(expected_input_hash, str(input_hash)):
        raise RuntimeError("audit result does not match the uploaded input")
    checkout_input_hash = str(job.get("upload_sha256") or "")
    if not checkout_input_hash or not hmac.compare_digest(checkout_input_hash, str(input_hash)):
        raise RuntimeError("audit result does not match the checkout-bound input")
    if len(str(pdf_base64)) > 25 * 1024 * 1024:
        raise RuntimeError("audit report payload exceeds delivery limit")

    pdf_bytes = base64.b64decode(pdf_base64, validate=True)
    if not pdf_bytes.startswith(b"%PDF"):
        raise RuntimeError("audit runner did not return a PDF")
    session_id = str(job.get("sessionId") or "")
    if not session_id or not settings.internal_url_secret:
        raise RuntimeError("audit delivery is missing its order-bound secret")
    report_id = hmac.new(
        settings.internal_url_secret.encode("utf-8"),
        f"delivery:{session_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    report_path = settings.reports_dir / f"{report_id}.pdf"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    _atomic_write_bytes(report_path, pdf_bytes)
    store.put_json(
        f"report:{report_id}",
        {
            "evidenceFingerprint": evidence_hash,
            "sessionId": session_id,
            "pdfSha256": pdf_sha256,
            "pdfBytes": len(pdf_bytes),
        },
        ttl_seconds=86400 * 30,
    )
    store.put_json(
        f"verify:{evidence_hash}",
        {
            "generatedAt": generated_at,
            "rulePackVersion": rule_pack_version,
            "reportVersion": report_version,
            "inputSha256": input_hash,
            "evidenceFingerprint": evidence_hash,
            "findingsCount": int(result.get("findings_count") or 0),
            "evidenceCount": int(result.get("evidence_count") or 0),
            "scannedFiles": int(result.get("scanned_files") or 0),
        },
        ttl_seconds=86400 * 30,
    )
    pdf_url = _signed_report_url(report_id)
    verify_url = f"{settings.public_site_url}/verify/?hash={evidence_hash}"
    delivery = {
        "status": "prepared",
        "sessionId": session_id,
        "reportId": report_id,
        "pdfUrl": pdf_url,
        "email": email,
        "verifyUrl": verify_url,
        "rulePackVersion": rule_pack_version,
        "inputSha256": input_hash,
        "evidenceFingerprint": evidence_hash,
        "findingsCount": int(result.get("findings_count") or 0),
        "pdfSha256": pdf_sha256,
        "pdfBytes": len(pdf_bytes),
    }
    store.put_json(f"delivery:{session_id}", delivery, ttl_seconds=86400 * 30)
    _deliver_prepared_audit(delivery, job)


def _deliver_prepared_audit(delivery: dict[str, Any], job: dict[str, Any]) -> None:
    session_id = str(delivery.get("sessionId") or job.get("sessionId") or "")
    report_id = str(delivery.get("reportId") or "")
    email = str(delivery.get("email") or job.get("email") or "")
    if not session_id or not report_id or not email:
        raise RuntimeError("prepared audit delivery is incomplete")
    report_path = settings.reports_dir / f"{report_id}.pdf"
    if not report_path.is_file():
        raise RuntimeError("prepared audit report is missing")
    actual_sha, actual_size = _file_sha256_size(report_path)
    expected_sha = str(delivery.get("pdfSha256") or "")
    expected_size = int(delivery.get("pdfBytes") or 0)
    if (
        not expected_sha
        or not hmac.compare_digest(actual_sha, expected_sha)
        or expected_size <= 0
        or actual_size != expected_size
    ):
        raise RuntimeError("prepared audit report failed its integrity check")
    response = send_email(
        settings,
        to=email,
        subject="Your EOLkits Audit is ready",
        html=render_audit_delivery_email(
            pdf_url=str(delivery.get("pdfUrl") or ""),
            verify_url=str(delivery.get("verifyUrl") or ""),
            rule_pack_version=str(delivery.get("rulePackVersion") or ""),
            input_sha=str(delivery.get("inputSha256") or ""),
            evidence_sha=str(delivery.get("evidenceFingerprint") or ""),
            findings_count=int(delivery.get("findingsCount") or 0),
        ),
        idempotency_key=f"eolkits-audit-{session_id}",
    )
    delivery = {
        **delivery,
        "status": "delivered",
        "deliveredAt": datetime.now(UTC).isoformat(),
        "providerMessageId": str(response.get("id") or ""),
    }
    store.put_json(f"delivery:{session_id}", delivery, ttl_seconds=86400 * 30)
    _delete_upload_artifact(job.get("upload_id"))


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    """Durably publish a paid artifact before committing its prepared ledger."""
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _file_sha256_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _delete_upload_artifact(upload_id: Any) -> None:
    if not upload_id:
        return
    path = _upload_path(str(upload_id))
    if path.is_file() and not path.is_symlink():
        path.unlink()
    try:
        path.parent.rmdir()
    except OSError:
        pass
    store.delete(f"upload:{upload_id}")
    store.release_upload(str(upload_id))
