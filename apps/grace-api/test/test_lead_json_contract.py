"""POST /api/v1/lead keeps its exact contract for every client that is not a
browser form navigation: fetch/XHR (SiteLift's Fit Check reads {"ok": true} and
{"detail": ...}), curl, and server-to-server callers.

Two independent proofs:

* Golden bytes, captured from the production code (e377bd4d), pinned here.
* A differential run: the e377bd4d package is rebuilt from git into a temp
  directory and imported side by side with the current code. Both apps get the
  same raw ASGI requests on fresh databases, and every status line, header list,
  body byte, escaped exception, stored lead row, and owner alert must match.
  Skipped only when the clone has no copy of e377bd4d (e.g. a shallow CI clone).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlencode

import pytest
from leadbus_support import ROOT, call_asgi, fresh_import, install_email_recorder

BASELINE = "e377bd4d"
SITE = "https://apps.toledotechnologies.com"
GOOD = {"email": "visitor@example.com", "name": "Visitor", "message": "Hello", "product": "Apps"}

# ---- request building ------------------------------------------------------- #


def urlencoded(fields: dict[str, str] | list[tuple[str, str]]) -> tuple[str, bytes]:
    return "application/x-www-form-urlencoded", urlencode(fields).encode()


def multipart(
    fields: dict[str, str], *, boundary: str = "leadbusBoundary7MA4YWxk"
) -> tuple[str, bytes]:
    parts = []
    for key, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="attachment"; filename=""\r\n'
        "Content-Type: application/octet-stream\r\n\r\n\r\n"
    )
    parts.append(f"--{boundary}--\r\n")
    return f"multipart/form-data; boundary={boundary}", "".join(parts).encode()


def as_json(value) -> tuple[str, bytes]:
    return "application/json", json.dumps(value).encode()


# (name, content-type or None, body chunks, extra headers)
BODY_CASES: list[tuple[str, str | None, list[bytes], list[tuple[str, str]]]] = []


def _case(name, content_type, body, extra=(), *, chunked=False, length=True):
    chunks = [body[i : i + 4096] for i in range(0, len(body), 4096)] if chunked else [body]
    headers = list(extra)
    if length:
        headers.append(("content-length", str(len(body))))
    BODY_CASES.append((name, content_type, chunks or [b""], headers))


_case("urlencoded ok", *urlencoded(GOOD))
_case("multipart ok", *multipart(GOOD))
_case("json ok", *as_json(GOOD))
_case("bad email", *urlencoded({"email": "not-an-address", "_next": SITE + "/thanks/"}))
_case("missing email", *urlencoded({"name": "No Email"}))
_case("empty body", None, b"")
_case("malformed json", "application/json", b'{"email": ')
_case("json array", *as_json([GOOD]))
_case("honeypot", *urlencoded({**GOOD, "_honey": "i am a bot"}))
_case("allowed next", *urlencoded({**GOOD, "_next": SITE + "/thanks/"}))
_case("relative next", *urlencoded({**GOOD, "_next": "/contact?submitted=true"}))
_case("foreign next", *urlencoded({**GOOD, "_next": "https://evil.example/phish"}))
_case("checkboxes", *urlencoded([("email", "a@b.co"), ("platform", "iOS"), ("platform", "Web")]))
_case("60 KB message", *urlencoded({**GOOD, "message": "m" * 60000}))
_case("70 KB declared", *urlencoded({**GOOD, "message": "m" * 70000}))
_case("70 KB chunked", *urlencoded({**GOOD, "message": "m" * 70000}), chunked=True, length=False)
_case("small chunked", *urlencoded(GOOD), chunked=True, length=False)
_case("bad length", *urlencoded(GOOD), [("content-length", "12abc")], length=False)

# Header profiles for clients that must keep the JSON contract. `None` for the
# content type means "the body's own".
FETCH_PROFILES: dict[str, list[tuple[str, str]]] = {
    "sitelift-fetch": [
        ("sec-fetch-mode", "cors"),
        ("sec-fetch-dest", "empty"),
        ("accept", "application/json"),
        ("origin", "https://sitelift.toledotechnologies.com"),
        ("referer", "https://sitelift.toledotechnologies.com/"),
    ],
    "fetch-default-accept": [
        ("sec-fetch-mode", "cors"),
        ("accept", "*/*"),
        ("origin", SITE),
        ("referer", SITE + "/"),
    ],
    # A fetch() that asks for HTML is still a fetch: Sec-Fetch-Mode decides.
    "fetch-asks-for-html": [
        ("sec-fetch-mode", "cors"),
        ("accept", "text/html"),
        ("origin", SITE),
    ],
    "same-origin-fetch": [("sec-fetch-mode", "same-origin"), ("accept", "*/*")],
    "no-cors-fetch": [("sec-fetch-mode", "no-cors"), ("accept", "*/*"), ("origin", SITE)],
    "curl": [("accept", "*/*"), ("user-agent", "curl/8.5.0")],
    "server-to-server": [("accept", "application/json"), ("user-agent", "python-requests/2")],
    "no-headers": [],
}
# Navigation-looking requests whose body is not form-encoded: still JSON.
NON_FORM_NAVIGATIONS: dict[str, list[tuple[str, str]]] = {
    "navigate-with-json": [
        ("sec-fetch-mode", "navigate"),
        ("accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("content-type", "application/json"),
    ],
    "navigate-with-text-plain": [
        ("sec-fetch-mode", "navigate"),
        ("accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("content-type", "text/plain"),
    ],
}


def _requests(profiles: dict[str, list[tuple[str, str]]]):
    for profile, profile_headers in profiles.items():
        forced_type = dict(profile_headers).get("content-type")
        for name, content_type, chunks, extra in BODY_CASES:
            headers = [(k, v) for k, v in profile_headers if k != "content-type"]
            ctype = forced_type or content_type
            if ctype:
                headers.append(("content-type", ctype))
            yield f"{profile} / {name}", headers + extra, chunks


# ---- golden bytes (always run) ---------------------------------------------- #

JSON = b"application/json"
# (case, status, content-type, body, location) with the SiteLift fetch profile,
# captured from e377bd4d on a fresh database in this order.
GOLDEN = [
    ("urlencoded ok", 200, JSON, b'{"ok":true,"lead_id":1}', None),
    ("multipart ok", 200, JSON, b'{"ok":true,"lead_id":2}', None),
    ("json ok", 200, JSON, b'{"ok":true,"lead_id":3}', None),
    ("bad email", 400, JSON, b'{"detail":"A valid email is required."}', None),
    ("missing email", 400, JSON, b'{"detail":"A valid email is required."}', None),
    ("empty body", 400, JSON, b'{"detail":"A valid email is required."}', None),
    ("malformed json", 400, JSON, b'{"detail":"A valid email is required."}', None),
    ("json array", 400, JSON, b'{"detail":"A valid email is required."}', None),
    ("honeypot", 200, JSON, b'{"ok":true}', None),
    ("allowed next", 303, None, b"", SITE + "/thanks/"),
    (
        "relative next",
        303,
        None,
        b"",
        "https://sitelift.toledotechnologies.com/contact?submitted=true",
    ),
    ("foreign next", 200, JSON, b'{"ok":true,"lead_id":6}', None),
    ("checkboxes", 200, JSON, b'{"ok":true,"lead_id":7}', None),
    ("60 KB message", 200, JSON, b'{"ok":true,"lead_id":8}', None),
    ("70 KB declared", 413, JSON, b'{"detail":"request body too large"}', None),
    ("70 KB chunked", 413, JSON, b'{"detail":"request body too large"}', None),
    ("small chunked", 200, JSON, b'{"ok":true,"lead_id":9}', None),
    ("bad length", 400, JSON, b'{"detail":"invalid content length"}', None),
]


def _headers(result) -> dict[bytes, bytes]:
    return dict(result.headers)


def test_golden_bytes_for_the_sitelift_fetch_client(load_grace):
    mod, _ = load_grace()
    cases = {
        name: (headers, chunks)
        for name, headers, chunks in _requests({"sitelift-fetch": FETCH_PROFILES["sitelift-fetch"]})
    }
    for name, status, content_type, body, location in GOLDEN:
        headers, chunks = cases[f"sitelift-fetch / {name}"]
        result = call_asgi(mod.app, headers=headers, chunks=chunks)
        got = _headers(result)
        assert (result.status, result.body, result.raised) == (status, body, None), name
        assert got.get(b"content-type") == content_type, name
        assert got.get(b"location") == (location.encode() if location else None), name
        assert got[b"content-length"] == str(len(body)).encode(), name
        assert got[b"access-control-allow-origin"] == b"https://sitelift.toledotechnologies.com"
        assert b"content-security-policy" not in got, name


def test_golden_rate_limit_and_server_error_for_fetch_clients(load_grace, monkeypatch):
    mod, _ = load_grace(EOLKITS_LEAD_IP_MINUTE_LIMIT="1")
    content_type, body = urlencoded(GOOD)
    headers = [*FETCH_PROFILES["sitelift-fetch"], ("content-type", content_type)]
    assert call_asgi(mod.app, headers=headers, chunks=[body]).status == 200
    limited = call_asgi(mod.app, headers=headers, chunks=[body])
    assert (limited.status, limited.body) == (
        429,
        b'{"detail":"Too many submissions. Please try again later."}',
    )
    assert _headers(limited)[b"content-type"] == JSON
    assert b"retry-after" not in _headers(limited)

    def broken(**_):
        raise RuntimeError("disk full")

    monkeypatch.setattr(mod.store, "record_lead", broken)
    monkeypatch.setattr(mod, "_consume_lead_capture_allowance", lambda request: True)
    failed = call_asgi(mod.app, headers=headers, chunks=[body])
    assert (failed.status, failed.body, failed.raised) == (
        500,
        b"Internal Server Error",
        "RuntimeError",
    )
    assert _headers(failed)[b"content-type"] == b"text/plain; charset=utf-8"


# ---- differential run against e377bd4d -------------------------------------- #


@pytest.fixture(scope="module")
def baseline_root(tmp_path_factory) -> Path:
    """The e377bd4d `eolkits_grace` package, rebuilt from git as
    `eolkits_grace_baseline` in a temp directory."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not installed")

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [git, "-C", str(ROOT), *args], capture_output=True, timeout=60, check=False
        )

    if run("cat-file", "-e", f"{BASELINE}^{{commit}}").returncode != 0:
        pytest.skip(f"baseline commit {BASELINE} is not in this clone")
    listing = run("ls-tree", "--name-only", BASELINE, "apps/grace-api/eolkits_grace/")
    assert listing.returncode == 0, listing.stderr
    root = tmp_path_factory.mktemp("baseline")
    package = root / "eolkits_grace_baseline"
    package.mkdir()
    for path in listing.stdout.decode().split():
        if path.endswith(".py"):
            shown = run("show", f"{BASELINE}:{path}")
            assert shown.returncode == 0, shown.stderr
            (package / Path(path).name).write_bytes(shown.stdout)
    assert (package / "app.py").is_file()
    assert not (package / "lead_pages.py").exists()  # really the old code
    return root


@pytest.fixture
def pair(baseline_root, grace_env, tmp_path, monkeypatch):
    """Factory: (baseline app module, current app module), each on its own fresh
    database with identical settings and an email recorder."""

    def load(**env: str):
        apps = []
        for label, module, package, root in (
            ("baseline", "eolkits_grace_baseline.app", "eolkits_grace_baseline", baseline_root),
            ("current", "eolkits_grace.app", "eolkits_grace", None),
        ):
            data_dir = tmp_path / label
            data_dir.mkdir()
            grace_env(EOLKITS_DATA_DIR=str(data_dir), **env)
            kwargs = {"package": package, "root": root} if root else {"package": package}
            mod = fresh_import(module, **kwargs)
            mod.store.init()
            mod.sent_emails = install_email_recorder(mod, monkeypatch)
            apps.append(mod)
        return apps[0], apps[1]

    return load


def _lead_rows(mod) -> list[dict]:
    return [
        {k: row[k] for k in ("id", "email", "name", "product", "source", "fields", "notified")}
        for row in mod.store.recent_leads(1000)
    ]


def _assert_same(baseline, current, requests) -> int:
    compared = 0
    for name, headers, chunks in requests:
        old = call_asgi(baseline.app, headers=headers, chunks=chunks)
        new = call_asgi(current.app, headers=headers, chunks=chunks)
        assert new == old, name
        compared += 1
    assert _lead_rows(current) == _lead_rows(baseline)
    assert current.sent_emails == baseline.sent_emails
    return compared


def test_every_non_browser_request_is_byte_identical_to_e377bd4d(pair):
    baseline, current = pair()
    compared = _assert_same(
        baseline, current, _requests({**FETCH_PROFILES, **NON_FORM_NAVIGATIONS})
    )
    assert compared == len(BODY_CASES) * (len(FETCH_PROFILES) + len(NON_FORM_NAVIGATIONS))
    assert len(_lead_rows(current)) > 50  # the run really captured leads...
    assert current.sent_emails  # ...and alerted the owner about them


def test_rate_limited_and_disconnected_requests_match_e377bd4d(pair):
    baseline, current = pair(EOLKITS_LEAD_IP_MINUTE_LIMIT="2")
    content_type, body = urlencoded(GOOD)
    requests = [
        (f"{profile} #{n}", [*headers, ("content-type", content_type)], [body])
        for profile, headers in FETCH_PROFILES.items()
        for n in range(3)
    ]
    _assert_same(baseline, current, requests)
    for app in (baseline.app, current.app):
        assert call_asgi(app, headers=requests[0][1], chunks=[body]).status == 429
    gone = [call_asgi(m.app, headers=requests[0][1], disconnect=True) for m in (baseline, current)]
    assert gone[0] == gone[1] == (None, [], b"", None)


def test_server_errors_match_e377bd4d(pair, monkeypatch):
    baseline, current = pair()

    def broken(**_):
        raise RuntimeError("disk full")

    for mod in (baseline, current):
        monkeypatch.setattr(mod.store, "record_lead", broken)
    requests = []
    for profile, headers in FETCH_PROFILES.items():
        for encode in (urlencoded, multipart, as_json):
            content_type, body = encode(GOOD)
            requests.append(
                (f"{profile} {content_type}", [*headers, ("content-type", content_type)], [body])
            )
    _assert_same(baseline, current, requests)
    assert call_asgi(current.app, headers=requests[0][1], chunks=requests[0][2]).raised == (
        "RuntimeError"
    )


def test_the_harness_does_see_the_intended_browser_change(pair):
    """Guard against a vacuous pass: a real browser form navigation must differ."""
    baseline, current = pair()
    content_type, body = urlencoded({"email": "nope"})
    headers = [
        ("sec-fetch-mode", "navigate"),
        ("accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("origin", SITE),
        ("content-type", content_type),
    ]
    old = call_asgi(baseline.app, headers=headers, chunks=[body])
    new = call_asgi(current.app, headers=headers, chunks=[body])
    assert old.status == new.status == 400
    assert old.body == b'{"detail":"A valid email is required."}'
    assert new.body.startswith(b"<!doctype html>")


def test_other_capped_endpoints_are_untouched_even_for_browser_navigations(pair):
    """The body-size middleware also guards checkout, the Stripe webhook, events
    and admin routes. Only /api/v1/lead may answer a browser with a page: every
    other path must reject exactly as e377bd4d did."""
    baseline, current = pair(
        EOLKITS_MAX_FORM_BYTES="1024",
        EOLKITS_MAX_EVENT_BYTES="256",
        EOLKITS_MAX_WEBHOOK_BYTES="2048",
    )
    navigation = [
        ("sec-fetch-mode", "navigate"),
        ("accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("origin", SITE),
        ("content-type", "application/x-www-form-urlencoded"),
    ]
    paths = [
        "/webhook/stripe",
        "/api/events",
        "/upload/presign",
        "/api/audit/checkout",
        "/api/pack/checkout",
        "/api/license/inquiry",
        "/api/license/validate",
        "/support/ask",
        "/admin/reconcile-refund",
        "/api/v1/lead/",
    ]
    big = b"x" * 4096
    compared = 0
    for path in paths:
        for headers, chunks in (
            ([*navigation, ("content-length", str(len(big)))], [big]),
            (navigation, [big[:1000], big[1000:]]),
            ([*navigation, ("content-length", "12abc")], [b"x"]),
            ([("content-type", "application/json"), ("content-length", "5000")], [b"{}"]),
        ):
            old = call_asgi(baseline.app, path=path, headers=headers, chunks=chunks)
            new = call_asgi(current.app, path=path, headers=headers, chunks=chunks)
            assert new == old, (path, headers)
            assert b"<!doctype" not in new.body
            compared += 1
    assert compared == len(paths) * 4
