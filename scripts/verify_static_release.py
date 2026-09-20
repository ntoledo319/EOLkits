#!/usr/bin/env python3
"""Validate an isolated custom-domain static release before rsync can touch a host."""

from __future__ import annotations

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://eolkits.com"
MARKERS = {
    "index.html": "repository evidence report is the only paid product",
    "audit/index.html": '<form id="auditForm" hidden>',
    "pack/index.html": "Migration Pack is unavailable",
    "drift/index.html": "Drift Watch is unavailable",
    "success/index.html": "This page does not confirm a payment",
}


class ReleaseError(ValueError):
    """A release is incomplete, unsafe, or built for the wrong origin."""


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.policy = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.links.extend(value for name, value in attrs if name in {"href", "src"} and value)
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"] or "")
        if tag == "meta" and (values.get("http-equiv") or "").lower() == "content-security-policy":
            self.policy = values.get("content") or ""


def validate(directory: Path) -> int:
    directory = directory.resolve()
    if directory == ROOT or not directory.is_relative_to(ROOT):
        raise ReleaseError("Release directory must be a child of the repository")
    if not directory.is_dir():
        raise ReleaseError("Release directory is missing")
    paths = sorted(directory.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ReleaseError("Release contains a symlink")
    for path in [directory, *paths]:
        mode = path.stat().st_mode
        required = 0o005 if path.is_dir() else 0o004
        if mode & required != required or mode & 0o002:
            raise ReleaseError(f"Unsafe public-asset permissions: {path.relative_to(directory)}")
    allowed = {
        ".html",
        ".css",
        ".js",
        ".txt",
        ".xml",
        ".svg",
        ".png",
        ".json",
        ".pdf",
        ".zip",
        ".ics",
    }
    for path in paths:
        if path.is_file() and path.suffix not in allowed:
            raise ReleaseError(f"Unexpected deployment file: {path.relative_to(directory)}")
    for relative, marker in MARKERS.items():
        if marker not in (directory / relative).read_text(encoding="utf-8"):
            raise ReleaseError(f"Missing release contract: {relative}")
    audit = (directory / "audit/index.html").read_text(encoding="utf-8")
    if "Checkout stays closed unless the live API confirms report engine 2.0." not in audit:
        raise ReleaseError("Audit capability gate is missing")
    pages = [path for path in paths if path.suffix == ".html"]
    for path in pages:
        relative = path.relative_to(directory).as_posix()
        html = path.read_text(encoding="utf-8")
        if any(marker in html for marker in ("{API_URL}", "ntoledo319.github.io", '="/EOLkits/')):
            raise ReleaseError(f"Wrong origin or unresolved template: {relative}")
        page = Page()
        page.feed(html)
        if (
            "script-src 'self' 'unsafe-inline'" not in page.policy
            or "connect-src 'self' https://eolkits.com" not in page.policy
        ):
            raise ReleaseError(f"Missing privacy CSP: {relative}")
        if any(urlsplit(value).scheme or urlsplit(value).netloc for value in page.scripts):
            raise ReleaseError(f"Absolute or third-party script: {relative}")
        for link in page.links:
            parsed = urlsplit(urljoin(f"{ORIGIN}/{relative}", link))
            if parsed.netloc != "eolkits.com" or parsed.scheme not in {"http", "https"}:
                continue
            target_path = unquote(parsed.path)
            if target_path.startswith(("/api/", "/upload/")):
                continue
            target = (directory / target_path.lstrip("/")).resolve()
            if not target.is_relative_to(directory):
                raise ReleaseError(f"Link escapes release: {relative}")
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                raise ReleaseError(f"Broken release link: {relative} -> {parsed.path}")
    if f"Sitemap: {ORIGIN}/sitemap.xml" not in (directory / "robots.txt").read_text():
        raise ReleaseError("Incorrect robots sitemap origin")
    sitemap = ElementTree.parse(directory / "sitemap.xml").getroot()
    locations = [
        item.text for item in sitemap.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    if not locations or any(not item or not item.startswith(ORIGIN + "/") for item in locations):
        raise ReleaseError("Incorrect sitemap origin")
    sample = directory / "audit/sample"
    manifest = json.loads((sample / "eolkits-sample-report.json").read_text())
    if (
        manifest.get("fictional") is not True
        or manifest.get("engine_sample_mode") is not True
        or manifest.get("verification_registered") is not False
    ):
        raise ReleaseError("Sample provenance is missing")
    for kind, name in (("pdf", "eolkits-sample-report.pdf"), ("input", "fictional-repository.zip")):
        if manifest.get(kind + "_file") != name:
            raise ReleaseError("Unexpected sample artifact name")
        data = (sample / name).read_bytes()
        if len(data) != manifest.get(kind + "_bytes") or hashlib.sha256(
            data
        ).hexdigest() != manifest.get(kind + "_sha256"):
            raise ReleaseError(f"Sample artifact differs from its manifest: {name}")
    return len(pages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.directory)
    except (OSError, ValueError, ElementTree.ParseError) as exc:
        parser.exit(1, f"Static release rejected: {exc}\n")
    print(
        f"Static release verified: {count} HTML pages, local links, CSP, origin and sample hashes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
