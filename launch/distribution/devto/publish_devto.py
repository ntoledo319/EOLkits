#!/usr/bin/env python3
"""Auto-publish EOLkits articles to dev.to.

Own account, own content, every article carries `canonical_url` back to
eolkits.com — so dev.to's authority flows TO the site (backlink) instead of
competing with it. This is the highest-ROI distribution lever: it directly
fixes the "new domain, zero backlinks" ceiling on the revenue projection.

Idempotent: skips any title already on the account. Dry-run by default.
Uses curl (system CA store) to avoid Python-framework SSL issues.

Usage:
  DEVTO_API_KEY=... python3 publish_devto.py            # dry run (shows what would post)
  DEVTO_API_KEY=... python3 publish_devto.py --apply    # actually publish

Get the key: dev.to -> Settings -> Extensions -> "DEV Community API Keys" -> Generate.
Runs anywhere with curl (your Mac, or the GRACE box where the cron lives).
"""
import os
import sys
import json
import glob
import re
import subprocess
import pathlib

API = "https://dev.to/api/articles"
KEY = os.environ.get("DEVTO_API_KEY", "")
DIR = pathlib.Path(__file__).parent


def _curl(method, url, payload=None):
    cmd = ["curl", "-s", "-m", "30", "-X", method, url,
           "-H", f"api-key: {KEY}", "-H", "Content-Type: application/json"]
    if payload is not None:
        cmd += ["--data", json.dumps(payload)]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except Exception:
        return out


def _parse(path):
    txt = pathlib.Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
    meta, body = {}, txt
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2).lstrip("\n")
    return meta, body


def main():
    if not KEY:
        print("ERROR: set DEVTO_API_KEY (dev.to -> Settings -> Extensions -> Generate API Key)")
        sys.exit(1)
    apply = "--apply" in sys.argv
    mine = _curl("GET", "https://dev.to/api/articles/me?per_page=100")
    existing = {a.get("title") for a in mine if isinstance(a, dict)} if isinstance(mine, list) else set()
    for path in sorted(glob.glob(str(DIR / "*.md"))):
        meta, body = _parse(path)
        title = meta.get("title")
        if not title:
            continue
        if title in existing:
            print(f"  skip (already published): {title}")
            continue
        article = {
            "title": title,
            "body_markdown": body,
            "published": True,
            "canonical_url": meta.get("canonical_url", ""),
            "description": meta.get("description", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()][:4],
        }
        if not apply:
            print(f"  DRY: would publish '{title}'  (canonical -> {article['canonical_url']})")
            continue
        r = _curl("POST", API, {"article": article})
        print(f"  published: {r.get('url') if isinstance(r, dict) else r}")
    if not apply:
        print("\nDry run only. Re-run with --apply once DEVTO_API_KEY is set.")


if __name__ == "__main__":
    main()
