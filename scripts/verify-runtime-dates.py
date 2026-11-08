#!/usr/bin/env python3
"""Diff EOLkits' tracked Lambda runtime dates against AWS's live runtimes table.

Fetches https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html (GET),
parses the supported + deprecated runtime tables, and compares each runtime that
contributes to the /scan/ page's DATA.runtimes (rules/public/deprecations.yml
entries whose name maps to a runtime id, plus the historical block) against:

  - deprecation_date   <-> AWS "Deprecation date"
  - date               <-> AWS "Block function create"
  - block_update_date  <-> AWS "Block function update"

Prints one line per runtime and a final mismatch count; exits non-zero when the
count is non-zero. Stdlib only.

Usage:
  python3 scripts/verify-runtime-dates.py            # live GET
  python3 scripts/verify-runtime-dates.py page.html  # offline check against a saved page
"""

from __future__ import annotations

import re
import sys
import urllib.request
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "web"))

import build  # noqa: E402
import yaml  # noqa: E402

AWS_URL = "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html"


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._in_table = False
        self._in_cell = False
        self._current_table: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
            self._current_table = []
        elif self._in_table and tag == "tr":
            self._current_row = []
        elif self._in_table and tag in ("td", "th"):
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in_cell:
            text = "".join(self._current_cell)
            self._current_row.append(re.sub(r"\s+", " ", text).strip())
            self._in_cell = False
        elif tag == "tr" and self._in_table:
            if self._current_row:
                self._current_table.append(self._current_row)
        elif tag == "table":
            self.tables.append(self._current_table)
            self._in_table = False

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell.append(data)


def _iso(aws_date: str) -> str | None:
    """Convert an AWS table date like 'Jul 29, 2027' to ISO; None if not scheduled."""
    aws_date = aws_date.strip()
    if not aws_date or aws_date.lower().startswith(("not scheduled", "n/a")):
        return None
    return datetime.strptime(aws_date, "%b %d, %Y").date().isoformat()


def aws_runtime_tables(html: str) -> dict[str, dict[str, str | None]]:
    parser = _TableParser()
    parser.feed(html)
    runtimes: dict[str, dict[str, str | None]] = {}
    for table in parser.tables:
        if not table or "Identifier" not in table[0]:
            continue
        for row in table[1:]:
            if len(row) < 6:
                continue
            identifier = row[1].strip()
            if not identifier:
                continue
            runtimes[identifier] = {
                "deprecation_date": _iso(row[3]),
                "date": _iso(row[4]),
                "block_update_date": _iso(row[5]),
            }
    return runtimes


def eolkits_runtime_rows() -> dict[str, dict[str, str | None]]:
    """The DATA.runtimes source: every deprecations.yml row with a runtime id."""
    with open(ROOT / "rules" / "public" / "deprecations.yml", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    rows: dict[str, dict[str, str | None]] = {}
    for group in ("deprecations", "historical"):
        for dep in data.get(group, []):
            runtime = build._runtime_id_from_name(str(dep.get("name", "")))
            if not runtime or runtime in rows:
                continue
            rows[runtime] = {
                "deprecation_date": dep.get("deprecation_date"),
                "date": dep.get("date"),
                "block_update_date": dep.get("block_update_date"),
            }
    return rows


def main() -> int:
    if len(sys.argv) > 1:
        html = Path(sys.argv[1]).read_text(encoding="utf-8")
        source = sys.argv[1]
    else:
        with urllib.request.urlopen(AWS_URL, timeout=60) as response:
            html = response.read().decode("utf-8")
        source = AWS_URL

    aws = aws_runtime_tables(html)
    ours = eolkits_runtime_rows()

    mismatches: list[str] = []
    print(f"AWS table source: {source}")
    print(f"Tracked DATA.runtimes rows: {len(ours)}")
    for runtime in sorted(ours):
        ours_row = ours[runtime]
        aws_row = aws.get(runtime)
        if aws_row is None:
            mismatches.append(f"{runtime}: not present in AWS table")
            print(f"MISMATCH {runtime}: not present in AWS table")
            continue
        diffs = []
        for key, label in (
            ("deprecation_date", "deprecation"),
            ("date", "block function create"),
            ("block_update_date", "block function update"),
        ):
            expected, observed = ours_row[key], aws_row[key]
            if expected != observed:
                diffs.append(f"{label}: eolkits={expected} aws={observed}")
        if diffs:
            mismatches.append(f"{runtime}: " + "; ".join(diffs))
            print(f"MISMATCH {runtime}: " + "; ".join(diffs))
        else:
            print(
                f"OK {runtime}: deprecation={ours_row['deprecation_date']} "
                f"block-create={ours_row['date']} block-update={ours_row['block_update_date']}"
            )

    print(f"\n{len(ours)} rows checked, {len(mismatches)} mismatches")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
