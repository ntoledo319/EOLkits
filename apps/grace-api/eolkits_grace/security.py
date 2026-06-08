from __future__ import annotations

import hashlib
import hmac
import time


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_stripe_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    if not signature:
        return False
    pieces: dict[str, list[str]] = {}
    for part in signature.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        pieces.setdefault(key, []).append(value)
    timestamp = pieces.get("t", [None])[0]
    if not timestamp:
        return False
    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - timestamp_int) > 300:
        return False
    signed = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in pieces.get("v1", []))


def verify_github_signature(payload: bytes, signature: str | None, secret: str | None) -> bool:
    # Fail closed: a missing/empty secret must NEVER bypass verification.
    # Production startup aborts when GITHUB_WEBHOOK_SECRET is unset (see config),
    # so reaching here without a secret means the request cannot be trusted.
    if not secret:
        return False
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def sign_internal_url(secret: str, upload_id: str, expires_at: int) -> str:
    """HMAC token authorizing the runner to fetch a specific local upload.

    Mitigates SSRF: the runner is handed an internal URL it can prove is
    server-issued for a known upload_id, instead of an arbitrary attacker-
    controlled upload_url.
    """
    message = f"{upload_id}.{expires_at}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_internal_url(secret: str, upload_id: str, expires_at: int, token: str | None) -> bool:
    if not secret or not token:
        return False
    if expires_at < int(time.time()):
        return False
    expected = sign_internal_url(secret, upload_id, expires_at)
    return hmac.compare_digest(expected, token)

