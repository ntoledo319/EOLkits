"""Generated-site internal-link integrity tests."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

import build

DOCS = Path(__file__).resolve().parents[2] / "docs"


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.values.append(value)


def _target(link: str) -> Path | None:
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    if parsed.path.startswith(("/api/", "/upload/")):
        return None
    relative = unquote(parsed.path).lstrip("/")
    candidate = DOCS / relative
    return candidate / "index.html" if parsed.path.endswith("/") else candidate


def test_generated_internal_links_resolve() -> None:
    missing: list[str] = []
    for page in sorted(DOCS.rglob("*.html")):
        parser = _Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for link in parser.values:
            target = _target(link)
            if target is not None and not target.exists():
                missing.append(f"{page.relative_to(DOCS)} -> {link}")
    assert not missing, "broken generated links:\n" + "\n".join(missing)


def test_every_generated_rule_has_a_public_source() -> None:
    deprecations = build.load_deprecations().get("deprecations", [])
    fixes = build.load_fixes()
    assert deprecations
    assert fixes
    assert all(str(item["url"]).startswith("https://") for item in deprecations)
    assert all(str(item["source_url"]).startswith("https://") for item in fixes)


def test_sitemap_locations_use_the_canonical_host() -> None:
    root = ElementTree.parse(DOCS / "sitemap.xml").getroot()
    locations = [
        element.text for element in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    assert locations
    assert all(location and location.startswith(f"{build.SITE_URL}/") for location in locations)


def test_project_pages_links_receive_the_repository_prefix(monkeypatch) -> None:
    monkeypatch.setattr(build, "PROJECT_BASE_PATH", "/EOLkits")
    monkeypatch.setattr(build, "API_URL", "https://eolkits.com")
    html = (
        '<a href="/audit/">Audit</a>'
        '<script src="/track.js"></script>'
        '<form action="/api/events"></form>'
        '<script>fetch("/api/capabilities")</script>'
        '<script>navigator.sendBeacon("/api/events")</script>'
        '<a href="https://eolkits.com/scan/">Scanner</a>'
    )

    normalized = build.normalize_project_links(html)

    assert 'href="/EOLkits/audit/"' in normalized
    assert 'src="/EOLkits/track.js"' in normalized
    assert 'action="https://eolkits.com/api/events"' in normalized
    assert 'fetch("https://eolkits.com/api/capabilities")' in normalized
    assert 'sendBeacon("https://eolkits.com/api/events")' in normalized
    assert 'href="https://eolkits.com/scan/"' in normalized


def test_project_pages_keep_live_api_calls_on_the_api_origin(monkeypatch) -> None:
    monkeypatch.setattr(build, "SITE_URL", "https://ntoledo319.github.io/EOLkits")
    monkeypatch.setattr(build, "API_URL", "https://eolkits.com")

    status = build.build_status_page()
    widget = build.build_widget_js()
    scanner = build.build_scan_page(build.load_deprecations())

    assert "fetch('https://eolkits.com/api/status'" in status
    assert "sendBeacon('https://eolkits.com/api/events'" in widget
    assert 'const SITE_BASE = "https://ntoledo319.github.io/EOLkits"' in scanner
    assert 'const API_BASE = "https://eolkits.com"' in scanner
    assert "sendBeacon('/api/" not in scanner


def test_retired_generated_surfaces_are_not_publishable() -> None:
    retired = [
        DOCS / "feed" / "manifest.json",
        DOCS / "feed" / "private-stub" / "index.json",
        DOCS / "feed" / "public" / "deprecations.yml",
        DOCS / "status" / "benchmark.json",
    ]
    retired.extend((DOCS / "blog").glob("ops-*.html"))
    assert not [path for path in retired if path.exists()]


def test_tracking_does_not_retain_full_referrer() -> None:
    track = (DOCS / "track.js").read_text(encoding="utf-8")
    assert "document.referrer" not in track
    for page in DOCS.rglob("*.html"):
        assert "ref: ref.slice" not in page.read_text(encoding="utf-8")


def test_false_imds_deadline_and_unbuilt_drift_offer_stay_retired() -> None:
    imds = (DOCS / "migrate" / "imdsv1-enforcement" / "index.html").read_text(encoding="utf-8")
    drift = (DOCS / "drift" / "index.html").read_text(encoding="utf-8")

    assert 'name="robots" content="noindex,follow"' in imds
    assert "universal December 31, 2025 enforcement date that AWS does not document" in imds
    assert 'name="robots" content="noindex,follow"' in drift
    assert "No checkout · no subscription · no waitlist" in drift
    assert "$19" not in drift
    assert "auto-opened migration PR" not in drift


def test_closed_product_pages_collect_no_speculative_leads() -> None:
    for relative in ("pack/index.html", "license/index.html", "partners/index.html"):
        page = (DOCS / relative).read_text(encoding="utf-8")
        assert 'name="robots" content="noindex,follow"' in page
        assert "No checkout · no account · no waitlist" in page
        assert "/api/v1/lead" not in page
        assert "<form" not in page


def test_node_22_timeline_is_tracked_with_aws_source() -> None:
    page = (DOCS / "migrate" / "lambda-node.js-22-phase-1" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "Lambda Node.js 22 projected restrictions" in page
    assert "2027-06-01" in page
    assert "2027-07-01" in page
    assert "docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html" in page


def test_generated_text_has_no_trailing_whitespace() -> None:
    offenders = []
    for path in sorted(item for item in DOCS.rglob("*") if item.is_file()):
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.endswith((" ", "\t")):
                offenders.append(f"{path.relative_to(DOCS)}:{line_number}")
    assert not offenders, "generated trailing whitespace:\n" + "\n".join(offenders)
