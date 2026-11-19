#!/usr/bin/env python3
"""Daily AWS runtime & Amazon Linux deprecation drift watchdog.

Compares rules/public/deprecations.yml against live upstream lifecycle feeds
(endoflife.date/api/aws-lambda.json and amazon-linux.json) so any AWS schedule
shift is surfaced immediately with a machine-readable JSON receipt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPRECATIONS_FILE = ROOT / "rules" / "public" / "deprecations.yml"
LAMBDA_FEED_URL = "https://endoflife.date/api/aws-lambda.json"
AL_FEED_URL = "https://endoflife.date/api/amazon-linux.json"


def _runtime_id(name: str) -> str | None:
    n = (name or "").lower()
    if "provided.al2" in n:
        return "provided.al2"
    m = re.search(r"python\s*(\d+)\.(\d+)", n)
    if m:
        return f"python{m.group(1)}.{m.group(2)}"
    m = re.search(r"node(?:\.|\s)?js\s*(\d+)", n)
    if m:
        return f"nodejs{m.group(1)}.x"
    m = re.search(r"(?:\.net|dotnet)\s*(\d+)", n)
    if m:
        return f"dotnet{m.group(1)}"
    m = re.search(r"ruby\s*(\d+)\.(\d+)", n)
    if m:
        return f"ruby{m.group(1)}.{m.group(2)}"
    return None


def _fetch_json(url: str) -> list[dict]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "eolkits-freshness-watch/1.0 (+https://eolkits.com/about/)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_freshness() -> dict:
    local_data = yaml.safe_load(DEPRECATIONS_FILE.read_text(encoding="utf-8")) or {}
    entries = local_data.get("deprecations", [])
    lambda_feed = {str(item.get("cycle")): item for item in _fetch_json(LAMBDA_FEED_URL)}
    al_feed = {str(item.get("cycle")): item for item in _fetch_json(AL_FEED_URL)}

    drifts: list[dict] = []
    checked = 0

    for entry in entries:
        name = str(entry.get("name", ""))
        rt = _runtime_id(name)
        if rt:
            checked += 1
            upstream = lambda_feed.get(rt)
            if not upstream:
                drifts.append({"target": rt, "reason": "missing_in_upstream_feed"})
                continue
            up_dep = str(upstream.get("support") or "")
            up_eol = str(upstream.get("eol") or "")
            loc_dep = str(entry.get("deprecation_date") or "")
            loc_upd = str(entry.get("block_update_date") or "")
            if up_dep and loc_dep and up_dep != loc_dep:
                drifts.append(
                    {
                        "target": rt,
                        "field": "deprecation_date",
                        "local": loc_dep,
                        "upstream": up_dep,
                    }
                )
            if up_eol and loc_upd and up_eol != loc_upd:
                drifts.append(
                    {
                        "target": rt,
                        "field": "block_update_date",
                        "local": loc_upd,
                        "upstream": up_eol,
                    }
                )
        elif "amazon linux 2" in name.lower():
            checked += 1
            al2 = al_feed.get("2")
            if al2:
                up_eol = str(al2.get("eol") or "")
                loc_eol = str(entry.get("date") or "")
                if up_eol and loc_eol and up_eol != loc_eol:
                    drifts.append(
                        {
                            "target": "amazon-linux-2",
                            "field": "date",
                            "local": loc_eol,
                            "upstream": up_eol,
                        }
                    )

    return {
        "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "ok" if not drifts else "drift_detected",
        "checked_targets": checked,
        "drift_count": len(drifts),
        "drifts": drifts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="Write JSON verification receipt to path")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if drift is detected")
    args = parser.parse_args()

    try:
        report = check_freshness()
    except Exception as exc:
        report = {
            "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "fetch_error",
            "error": str(exc),
            "checked_targets": 0,
            "drift_count": 0,
            "drifts": [],
        }
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"eol_freshness_watch: fetch_error: {exc}", file=sys.stderr)
        return 1 if args.strict else 0

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report))
    if args.strict and report["drift_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
