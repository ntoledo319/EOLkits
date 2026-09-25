"""Readable pages for native HTML form posts to ``POST /api/v1/lead``.

The studio sites post their contact forms straight to the lead endpoint. A
visitor whose browser navigated there used to be left on eolkits.com looking at
raw JSON when the submission failed, or when it succeeded without a usable
``_next``. This module recognises that kind of request and renders a small,
self-contained page for it, with the same status code.

Only browser form navigations are answered here. Every other client (fetch/XHR
such as SiteLift's Fit Check, curl, server-to-server) keeps getting exactly the
JSON, redirect, or plain-text response it always got: app.py calls into this
module only after ``is_browser_form_navigation`` says yes.

The page runs no script and loads nothing. Its only link points back to an
allow-listed studio site, and every value placed in it is HTML-escaped.
"""

from __future__ import annotations

import base64
import hashlib
import math
import re
from collections.abc import Iterable, Mapping
from html import escape
from typing import NamedTuple

from starlette.responses import HTMLResponse

# Shared with app.py so the page and the JSON error can never drift apart.
INVALID_EMAIL_DETAIL = "A valid email is required."

FORM_CONTENT_TYPES = frozenset({"application/x-www-form-urlencoded", "multipart/form-data"})

# The origin of an absolute URL, matched the way app._resolve_next matches it:
# everything before the first "/" must equal an allow-listed origin exactly, so
# userinfo, a port, a backslash, "?" or "#" can never smuggle in another host.
_ORIGIN_RE = re.compile(r"^(https?://[^/]+)")
# A Referer is linked back verbatim only when it is plain RFC 3986 URL text
# (browsers send it percent-encoded). Anything else falls back to the site's
# home page.
_LINKABLE_URL_RE = re.compile(r"[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]{1,2048}")


def accept_quality(accept: str, media_type: str) -> float:
    """The quality an Accept header gives ``media_type``, taken from the most
    specific matching range (type/subtype, then type/*, then */*); 0 if none."""
    main_type = media_type.split("/", 1)[0]
    best_rank, best_q = -1, 0.0
    for item in accept.split(","):
        media_range, *params = (part.strip() for part in item.split(";"))
        media_range = media_range.lower()
        if media_range == media_type:
            rank = 2
        elif media_range == f"{main_type}/*":
            rank = 1
        elif media_range == "*/*":
            rank = 0
        else:
            continue
        q = 1.0
        for param in params:
            key, _, value = param.partition("=")
            if key.strip().lower() == "q":
                try:
                    q = float(value.strip())
                except ValueError:
                    q = 0.0
        if not math.isfinite(q):
            q = 0.0
        if rank > best_rank:
            best_rank, best_q = rank, min(max(q, 0.0), 1.0)
    return best_q


def is_browser_form_navigation(headers: Mapping[str, str]) -> bool:
    """True only for a top-level HTML form submission.

    The body must be form-encoded (urlencoded or multipart). Browsers that send
    Fetch Metadata mark a navigation with ``Sec-Fetch-Mode: navigate``, and a
    fetch()/XHR request always carries some other mode, so when that header is
    present it alone decides: a fetch() that asks for HTML still gets JSON.
    Older browsers without Fetch Metadata are recognised by an Accept header
    that ranks text/html above application/json, which is what browsers send for
    a navigation and what no JSON client sends."""
    content_type = (headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if content_type not in FORM_CONTENT_TYPES:
        return False
    mode = (headers.get("sec-fetch-mode") or "").strip().lower()
    if mode:
        return mode == "navigate"
    accept = headers.get("accept") or ""
    return accept_quality(accept, "text/html") > accept_quality(accept, "application/json")


class ReturnLink(NamedTuple):
    href: str = ""
    host: str = ""


def _allowed_origin(url: str, allowed: frozenset[str]) -> str:
    match = _ORIGIN_RE.match(url or "")
    return match.group(1) if match and match.group(1) in allowed else ""


def return_link(
    *, referer: str, origin: str, next_value: str, allowed_origins: Iterable[str]
) -> ReturnLink:
    """Where the page's "Go back" link points. Only ever an allow-listed site.

    The exact page the form was on (Referer) when the browser sent a full one;
    otherwise that site's home page, found from the Referer, Origin, or ``_next``
    in that order. Browsers usually send only the origin across sites
    (strict-origin-when-cross-origin), so the home page is the common case.
    ``_next`` itself is never linked: it is the thank-you page, and linking to
    it after a failure would tell the visitor the message went through."""
    allowed = frozenset(allowed_origins)
    referer_site = _allowed_origin(referer, allowed)
    if referer_site and _LINKABLE_URL_RE.fullmatch(referer):
        return ReturnLink(referer, referer_site.split("://", 1)[1])
    for candidate in (referer, origin, next_value):
        site = _allowed_origin(candidate, allowed)
        if site:
            return ReturnLink(site + "/", site.split("://", 1)[1])
    return ReturnLink()


def kind_for(status_code: int, detail: object) -> str:
    """Which page explains a failed submission with this status and detail."""
    if status_code == 400:
        return "invalid_email" if detail == INVALID_EMAIL_DETAIL else "unreadable"
    if status_code == 413:
        return "too_large"
    if status_code == 429:
        return "rate_limited"
    if status_code >= 500:
        return "server_error"
    return "rejected"


# kind -> (title, heading, what happened, what to do next)
_COPY: dict[str, tuple[str, str, str, str]] = {
    "sent": ("Message sent", "Thank you", "Your message was sent.", ""),
    "invalid_email": (
        "Message not sent: check your email address",
        "Check your email address",
        "The email address was missing or incomplete, so your message was not sent.",
        "Correct your email address and send the form again.",
    ),
    "unreadable": (
        "Message not sent: check the form",
        "Check the form",
        "Some of the form details could not be read, so your message was not sent.",
        "Check your details and send the form again.",
    ),
    "too_large": (
        "Message not sent: too long",
        "Your message is too long",
        "The form was larger than we can accept, so your message was not sent.",
        "Shorten your message and send the form again.",
    ),
    "rate_limited": (
        "Message not sent: too many attempts",
        "Too many attempts",
        "We received too many attempts in a short time, so your message was not sent.",
        "Please wait a while, then try again.",
    ),
    "server_error": (
        "Something went wrong",
        "Something went wrong on our side",
        "Your message may not have been sent.",
        "Please wait a few minutes, then try again.",
    ),
    "rejected": (
        "Message not sent",
        "Your message was not sent",
        "The form could not be accepted.",
        "Check your details and send the form again.",
    ),
}
_TIP = (
    "Your browser's Back button returns you to the form, usually with your answers "
    "still filled in."
)
# Contrast is 4.5:1 or better for every text/background pair in both schemes
# (checked by test_lead_pages.test_page_colours_meet_wcag_contrast).
CSS = (
    ":root{color-scheme:light dark;--bg:#f6f6f3;--card:#fff;--fg:#1b1b19;--muted:#55554e;"
    "--line:#e2e2dc;--accent:#1f4fd1}"
    "@media (prefers-color-scheme:dark){:root{--bg:#131312;--card:#1d1d1b;--fg:#f1f1ec;"
    "--muted:#bdbdb4;--line:#383833;--accent:#a3bdff}}"
    "*{box-sizing:border-box}"
    "body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;"
    "padding:24px 16px;background:var(--bg);color:var(--fg);"
    "font:17px/1.6 system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif}"
    "main{width:100%;max-width:34rem;background:var(--card);border:1px solid var(--line);"
    "border-radius:14px;padding:clamp(24px,6vw,40px)}"
    ".site{margin:0 0 8px;color:var(--muted);font-size:.8125rem;font-weight:600;"
    "letter-spacing:.06em;text-transform:uppercase;overflow-wrap:anywhere}"
    "h1{margin:0 0 16px;font-size:clamp(1.5rem,5vw,1.875rem);line-height:1.2;"
    "letter-spacing:-.015em;font-weight:650}"
    "p{margin:0 0 12px}"
    ".tip{color:var(--muted);font-size:.9375rem}"
    ".back{margin:24px 0 0}"
    "a{color:var(--accent);font-weight:600;text-decoration:underline;"
    "text-underline-offset:3px;overflow-wrap:anywhere}"
    "a:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:3px}"
)
# No scripts, no requests: only the page's own inline <style>, pinned by hash,
# may apply.
CSP = (
    "default-src 'none'; "
    f"style-src 'sha256-{base64.b64encode(hashlib.sha256(CSS.encode()).digest()).decode()}'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def render(
    kind: str,
    status_code: int,
    link: ReturnLink,
    retry_after: str | None = None,
) -> HTMLResponse:
    """The page for ``kind``, served with ``status_code``."""
    title, heading, happened, next_step = _COPY[kind]
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="robots" content="noindex">',
        f"<title>{escape(title)}</title>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        "<main>",
    ]
    if link.host:
        parts.append(f'<p class="site">{escape(link.host)}</p>')
    parts.append(f"<h1>{escape(heading)}</h1>")
    parts.append(f"<p>{escape(happened)}</p>")
    if next_step:
        parts.append(f"<p>{escape(next_step)}</p>")
    if kind != "sent":
        parts.append(f'<p class="tip">{escape(_TIP)}</p>')
    if link.href:
        parts.append(
            f'<p class="back"><a href="{escape(link.href, quote=True)}">'
            f"Go back to {escape(link.host)}</a></p>"
        )
    parts += ["</main>", "</body>", "</html>", ""]
    response = HTMLResponse("\n".join(parts), status_code=status_code)
    if retry_after:
        response.headers["Retry-After"] = retry_after
    response.headers["Content-Security-Policy"] = CSP
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
