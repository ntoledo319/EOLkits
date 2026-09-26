"""POST /api/v1/lead from a native HTML form: a browser navigation that fails
(400, 413, 429, 5xx), or succeeds without a usable `_next`, gets a small,
accessible page with the same status code instead of raw JSON."""

from __future__ import annotations

import base64
import hashlib
import re
from html.parser import HTMLParser
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

SITE = "https://apps.toledotechnologies.com"
# What Chrome sends for a top-level form POST from a Toledo site. The Referer is
# origin-only because the sites use strict-origin-when-cross-origin.
CHROME_NAV = {
    "sec-fetch-mode": "navigate",
    "sec-fetch-dest": "document",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
    "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "origin": SITE,
    "referer": SITE + "/",
}
# A browser without Fetch Metadata (older Safari): recognised by Accept alone.
LEGACY_NAV = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "origin": SITE,
    "referer": SITE + "/",
}
GOOD = {"email": "visitor@example.com", "name": "Visitor", "message": "Hello", "product": "Apps"}
FORM = "application/x-www-form-urlencoded"


class _PageAudit(HTMLParser):
    """Collects what the accessibility and no-third-party checks need."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.attrs: dict[str, list[dict[str, str | None]]] = {}
        self.text: dict[str, str] = {}
        self.styles: list[str] = []
        self._current: str | None = None

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.setdefault(tag, []).append(dict(attrs))
        self._current = tag

    def handle_endtag(self, tag):
        self._current = None

    def handle_data(self, data):
        if self._current == "style":
            self.styles.append(data)
        elif self._current:
            self.text[self._current] = self.text.get(self._current, "") + data


def _audit_page(response) -> _PageAudit:
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    page = _PageAudit()
    page.feed(response.text)
    # An accessible, self-contained document.
    assert response.text.startswith("<!doctype html>")
    assert page.attrs["html"][0].get("lang") == "en"
    assert page.text.get("title", "").strip()
    assert any(m.get("name") == "viewport" for m in page.attrs.get("meta", []))
    assert page.tags.count("h1") == 1 and page.tags.count("main") == 1
    # No scripts and no subresources of any kind, third-party or not.
    for banned in ("script", "img", "iframe", "link", "form", "object", "embed", "svg", "base"):
        assert banned not in page.tags, banned
    assert "<script" not in response.text.lower()
    every_attrs = [attrs for attr_list in page.attrs.values() for attrs in attr_list]
    loading = {"src", "srcset", "style", "action", "formaction", "background", "poster"}
    assert not any(loading & set(attrs) for attrs in every_attrs)
    assert not any(name.startswith("on") for attrs in every_attrs for name in attrs)
    # The only style block is exactly the one the CSP hash allows.
    assert len(page.styles) == 1
    digest = base64.b64encode(hashlib.sha256(page.styles[0].encode()).digest()).decode()
    csp = response.headers["content-security-policy"]
    assert f"style-src 'sha256-{digest}'" in csp
    assert "default-src 'none'" in csp and "script-src" not in csp
    assert "frame-ancestors 'none'" in csp and "form-action 'none'" in csp
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    return page


def _links(page: _PageAudit) -> list[str]:
    return [a.get("href") or "" for a in page.attrs.get("a", [])]


# ---- failures get a page with the same status -------------------------------- #


def test_invalid_email_gets_an_accessible_400_page(load_grace):
    mod, client = load_grace()
    r = client.post(
        "/api/v1/lead",
        data={"email": "not-an-address", "_next": SITE + "/thanks/"},
        headers=CHROME_NAV,
    )
    assert r.status_code == 400
    page = _audit_page(r)
    assert page.text["h1"] == "Check your email address"
    assert "email address was missing or incomplete" in r.text
    assert "was not sent" in r.text
    # "Go back" goes to the site the visitor came from, never to `_next`
    # (the thank-you page would claim the message went through).
    assert _links(page) == [SITE + "/"]
    assert "Go back to apps.toledotechnologies.com</a>" in r.text
    assert "/thanks/" not in r.text
    assert mod.store.recent_leads() == []
    assert mod.sent_emails == []


def test_missing_email_multipart_from_a_browser_without_fetch_metadata(load_grace):
    _, client = load_grace()
    r = client.post(
        "/api/v1/lead",
        data={"email": ""},
        files={"attachment": ("", b"", "application/octet-stream")},  # multipart body
        headers=LEGACY_NAV,
    )
    assert r.status_code == 400
    assert _audit_page(r).text["h1"] == "Check your email address"


def test_declared_oversized_body_gets_a_413_page(load_grace):
    mod, client = load_grace(EOLKITS_MAX_FORM_BYTES="2048")
    r = client.post("/api/v1/lead", data={**GOOD, "message": "x" * 5000}, headers=CHROME_NAV)
    assert r.status_code == 413
    page = _audit_page(r)
    assert page.text["h1"] == "Your message is too long"
    assert "Shorten your message" in r.text
    assert _links(page) == [SITE + "/"]
    assert mod.store.recent_leads() == []


def test_streamed_oversized_body_gets_a_413_page(load_grace):
    mod, client = load_grace(EOLKITS_MAX_FORM_BYTES="2048")

    def chunks():
        yield b"email=a%40example.com&message="
        for _ in range(10):
            yield b"x" * 1000

    r = client.post("/api/v1/lead", content=chunks(), headers={**CHROME_NAV, "content-type": FORM})
    assert "content-length" not in r.request.headers
    assert r.status_code == 413
    assert _audit_page(r).text["h1"] == "Your message is too long"
    assert mod.store.recent_leads() == []


def test_unreadable_content_length_gets_a_400_page(load_grace, asgi):
    mod, _ = load_grace()
    headers = [*CHROME_NAV.items(), ("content-type", FORM), ("content-length", "12abc")]
    result = asgi(mod.app, headers=headers, chunks=[urlencode(GOOD).encode()])
    assert result.status == 400
    assert b"<h1>Check the form</h1>" in result.body
    assert dict(result.headers)[b"content-type"] == b"text/html; charset=utf-8"


def test_rate_limited_browser_gets_a_429_page(load_grace):
    mod, client = load_grace(EOLKITS_LEAD_IP_MINUTE_LIMIT="1")
    first = client.post("/api/v1/lead", data=GOOD, headers=CHROME_NAV)
    assert first.status_code == 200
    r = client.post("/api/v1/lead", data=GOOD, headers=CHROME_NAV)
    assert r.status_code == 429
    page = _audit_page(r)
    assert page.text["h1"] == "Too many attempts"
    assert "wait a while, then try again" in r.text
    assert "retry-after" not in r.headers  # the endpoint sends none today
    assert len(mod.store.recent_leads()) == 1


def test_retry_after_is_kept_when_a_429_carries_one(load_grace, monkeypatch):
    mod, client = load_grace()

    def throttled(**_):
        raise HTTPException(429, "Too many submissions.", headers={"Retry-After": "60"})

    monkeypatch.setattr(mod.store, "record_lead", throttled)
    r = client.post("/api/v1/lead", data=GOOD, headers=CHROME_NAV)
    assert r.status_code == 429
    assert r.headers["retry-after"] == "60"
    _audit_page(r)


def test_server_failure_gets_a_500_page_without_internals(load_grace, monkeypatch, caplog):
    mod, client = load_grace()

    def broken(**_):
        raise RuntimeError("disk full at /data/eolkits")

    monkeypatch.setattr(mod.store, "record_lead", broken)
    r = client.post("/api/v1/lead", data=GOOD, headers=CHROME_NAV)
    assert r.status_code == 500
    page = _audit_page(r)
    assert page.text["h1"] == "Something went wrong on our side"
    assert "may not have been sent" in r.text
    assert "disk full" not in r.text and "/data" not in r.text
    assert "lead capture failed during a native form submission" in caplog.text


# ---- success ----------------------------------------------------------------- #


def test_success_without_next_gets_a_confirmation_page(load_grace):
    mod, client = load_grace()
    r = client.post("/api/v1/lead", data=GOOD, headers=CHROME_NAV)
    assert r.status_code == 200
    page = _audit_page(r)
    assert page.text["h1"] == "Thank you"
    assert "Your message was sent." in r.text
    assert "Back button" not in r.text
    assert _links(page) == [SITE + "/"]
    assert [lead["email"] for lead in mod.store.recent_leads()] == ["visitor@example.com"]
    assert [e["to"] for e in mod.sent_emails] == ["owner@toledo.test"]

    # The honeypot looks identical to a bot and records nothing.
    bot = client.post("/api/v1/lead", data={**GOOD, "_honey": "x"}, headers=CHROME_NAV)
    assert (bot.status_code, bot.text) == (200, r.text)
    assert len(mod.store.recent_leads()) == 1


@pytest.mark.parametrize(
    "next_url,location",
    [
        (SITE + "/thanks/", SITE + "/thanks/"),
        ("/contact?submitted=true", SITE + "/contact?submitted=true"),
    ],
)
def test_success_with_a_usable_next_still_redirects(load_grace, next_url, location):
    mod, client = load_grace()
    r = client.post("/api/v1/lead", data={**GOOD, "_next": next_url}, headers=CHROME_NAV)
    assert r.status_code == 303
    assert r.headers["location"] == location
    assert len(mod.store.recent_leads()) == 1


def test_success_with_a_foreign_next_gets_the_confirmation_page(load_grace):
    _, client = load_grace()
    data = {**GOOD, "_next": "https://evil.example/phish"}
    r = client.post("/api/v1/lead", data=data, headers=CHROME_NAV)
    assert r.status_code == 200
    page = _audit_page(r)
    assert page.text["h1"] == "Thank you"
    assert _links(page) == [SITE + "/"] and "evil" not in r.text


# ---- the "Go back" link ------------------------------------------------------ #


def test_full_referer_on_an_allowed_site_is_the_go_back_target(load_grace):
    _, client = load_grace()
    headers = {**CHROME_NAV, "referer": SITE + "/contact/?plan=pro"}
    r = client.post("/api/v1/lead", data={"email": "x"}, headers=headers)
    assert _links(_audit_page(r)) == [SITE + "/contact/?plan=pro"]


@pytest.mark.parametrize(
    "origin,referer,next_url",
    [
        ("https://evil.example", "https://evil.example/", "https://evil.example/phish"),
        ("null", "", "//evil.example/x"),
        (
            "",
            "https://apps.toledotechnologies.com.evil.example/",
            "https://evil.example@apps.toledotechnologies.com/",
        ),
        ("", "https://apps.toledotechnologies.com@evil.example/", "javascript:alert(1)"),
        ("", "http://apps.toledotechnologies.com/", "https://apps.toledotechnologies.com:8443/"),
        ("https://APPS.toledotechnologies.com", "", "HTTPS://apps.toledotechnologies.com/"),
    ],
)
def test_go_back_link_is_never_an_open_redirect(load_grace, origin, referer, next_url):
    _, client = load_grace()
    headers = {**CHROME_NAV, "origin": origin, "referer": referer}
    r = client.post("/api/v1/lead", data={"email": "x", "_next": next_url}, headers=headers)
    assert r.status_code == 400
    page = _audit_page(r)
    assert _links(page) == []  # no allow-listed site known: no link at all
    assert "evil" not in r.text and "javascript" not in r.text
    assert "Back button" in r.text  # the visitor is still told how to return


def test_next_on_an_allowed_site_identifies_the_site_when_headers_do_not(load_grace):
    _, client = load_grace()
    headers = {**CHROME_NAV, "origin": "null", "referer": ""}
    r = client.post(
        "/api/v1/lead",
        data={"email": "x", "_next": "https://mobile.toledotechnologies.com/?submitted=true"},
        headers=headers,
    )
    assert _links(_audit_page(r)) == ["https://mobile.toledotechnologies.com/"]
    assert "submitted" not in r.text


@pytest.mark.parametrize(
    "referer",
    [
        SITE + '/c?a="><script>alert(1)</script>&b=<img/src=x/onerror=alert(1)>',
        SITE + "\\@evil.example/",  # a browser reads the backslash as "/"
        SITE + "/c d",
        SITE + "/caf\u00e9",
    ],
)
def test_unusual_referers_fall_back_to_the_site_home_page(load_grace, asgi, referer):
    mod, _ = load_grace()
    headers = {**CHROME_NAV, "content-type": FORM, "referer": referer}
    # Sent as raw header bytes (UTF-8 where the value is not ASCII), the way a
    # hand-made request could send them.
    raw = [(k, v.encode("utf-8").decode("latin-1")) for k, v in headers.items()]
    result = asgi(mod.app, headers=raw, chunks=[urlencode({"email": "x"}).encode()])
    assert result.status == 400
    text = result.body.decode()
    page = _PageAudit()
    page.feed(text)
    assert "<script" not in text and "<img" not in text and "evil" not in text
    assert _links(page) == [SITE + "/"]
    assert "Go back to apps.toledotechnologies.com</a>" in text


def test_link_markup_is_escaped(load_grace):
    _, client = load_grace()
    referer = SITE + "/c?a=1&b='x'"
    r = client.post("/api/v1/lead", data={"email": "x"}, headers={**CHROME_NAV, "referer": referer})
    assert 'href="https://apps.toledotechnologies.com/c?a=1&amp;b=&#x27;x&#x27;"' in r.text
    assert _links(_audit_page(r)) == [referer]


def test_every_allow_listed_site_can_be_linked_and_nothing_else(load_grace):
    mod, client = load_grace()
    for origin in mod._SITE_ORIGINS:
        headers = {**CHROME_NAV, "origin": origin, "referer": origin + "/"}
        r = client.post("/api/v1/lead", data={"email": "x"}, headers=headers)
        assert _links(_audit_page(r)) == [origin + "/"]


# ---- which requests count as a browser form navigation ---------------------- #


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({"content-type": FORM, "sec-fetch-mode": "navigate"}, True),
        ({"content-type": "multipart/form-data; boundary=x", "sec-fetch-mode": "Navigate"}, True),
        ({"content-type": FORM, "accept": LEGACY_NAV["accept"]}, True),
        ({"content-type": FORM + "; charset=UTF-8", "accept": LEGACY_NAV["accept"]}, True),
        # fetch()/XHR always carry a non-navigate mode; that alone decides.
        ({"content-type": FORM, "sec-fetch-mode": "cors", "accept": "text/html"}, False),
        ({"content-type": FORM, "sec-fetch-mode": "no-cors", "accept": "text/html"}, False),
        ({"content-type": FORM, "sec-fetch-mode": "same-origin", "accept": "text/html"}, False),
        # No Fetch Metadata and no preference for HTML: not a browser navigation.
        ({"content-type": FORM, "accept": "*/*"}, False),
        ({"content-type": FORM, "accept": "application/json"}, False),
        ({"content-type": FORM}, False),
        # Not a form body, whatever the other headers say.
        ({"content-type": "application/json", "sec-fetch-mode": "navigate"}, False),
        ({"content-type": "text/plain", "sec-fetch-mode": "navigate"}, False),
        ({"sec-fetch-mode": "navigate", "accept": LEGACY_NAV["accept"]}, False),
    ],
)
def test_browser_form_navigation_detection(load_grace, headers, expected):
    load_grace()
    from eolkits_grace import lead_pages

    assert lead_pages.is_browser_form_navigation(headers) is expected


@pytest.mark.parametrize(
    "accept,prefers_html",
    [
        (CHROME_NAV["accept"], True),
        ("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", True),
        ("text/*, application/json;q=0.2", True),
        ("*/*", False),
        ("", False),
        ("application/json", False),
        ("application/json, text/html", False),
        ("text/html;q=0.5, application/json", False),
        ("text/html;q=nan, */*", False),
        ("text/html;q=inf, */*;q=0.1", False),
        ("TEXT/HTML, */*;q=0.1", True),
        ("garbage;;;,,", False),
    ],
)
def test_accept_preference(load_grace, accept, prefers_html):
    load_grace()
    from eolkits_grace import lead_pages

    html_q = lead_pages.accept_quality(accept, "text/html")
    json_q = lead_pages.accept_quality(accept, "application/json")
    assert (html_q > json_q) is prefers_html


# ---- the page's own design -------------------------------------------------- #


def _luminance(hex_colour: str) -> float:
    hex_colour = hex_colour.lstrip("#")
    if len(hex_colour) == 3:
        hex_colour = "".join(c * 2 for c in hex_colour)
    channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_page_colours_meet_wcag_contrast(load_grace):
    load_grace()
    from eolkits_grace import lead_pages

    light, dark = re.findall(r":root\{([^}]*)\}", lead_pages.CSS)
    for scheme in (light, dark):
        tokens = dict(re.findall(r"--(\w+):(#[0-9a-fA-F]{3,6})", scheme))
        for text in ("fg", "muted", "accent"):
            for background in ("card", "bg"):
                ratio = _contrast(tokens[text], tokens[background])
                assert ratio >= 4.5, (text, background, round(ratio, 2))
