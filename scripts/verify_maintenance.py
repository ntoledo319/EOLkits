#!/usr/bin/env python3
"""Check current documentation, explicit roadmap completion and repository hygiene."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DOCS = (
    "README.md",
    "CONTRIBUTING.md",
    "HANDOFF.md",
    "docs/development.md",
    "docs/MAINTENANCE.md",
    "revenue/PLAN.md",
    "revenue/ASSETS.md",
    "revenue/OPPORTUNITIES.md",
    "revenue/METRICS.md",
    "revenue/HUMAN_QUEUE.md",
    "revenue/DECISIONS.md",
    "kits/python-pivot/README.md",
    "kits/al2023-gate/README.md",
    "deploy/grace/README.md",
)


def unresolved_markers(text: str) -> list[str]:
    return [line for line in text.splitlines() if re.search(r"\b(?:TODO|FIXME|TBD)\b", line)]


def check_links(path: Path) -> list[str]:
    source = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
    failures = []
    for match in re.finditer(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)", source):
        url = urlsplit(match.group(1).strip("<>"))
        if url.scheme or url.netloc or not url.path:
            continue
        target = (path.parent / unquote(url.path)).resolve()
        if not target.is_relative_to(ROOT):
            failures.append(f"{path.relative_to(ROOT)} links outside repository: {url.path}")
        elif not target.exists():
            failures.append(f"{path.relative_to(ROOT)} has missing link: {url.path}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true", help="Check the full active inventory")
    parser.parse_args(argv)
    errors = []
    if (ROOT / "EMERGENCYDDOTHISNOW.md").exists():
        errors.append("The user-requested emergency document deletion is incomplete")
    plan = ROOT / "revenue/PLAN.md"
    # The operating ledger records its owner's workspace. A CI checkout or a
    # contributor clone must not rewrite that historical path just to verify.
    if not Path(plan.read_text().splitlines()[0]).is_absolute():
        errors.append("Revenue plan must start with its recorded absolute WORKSPACE_ROOT")
    for rel in ACTIVE_DOCS:
        path = ROOT / rel
        if not path.resolve().is_relative_to(ROOT) or not path.is_file():
            errors.append(f"Required current documentation missing or unsafe: {rel}")
            continue
        errors.extend(check_links(path))
    for rel in ("kits/python-pivot/README.md", "kits/al2023-gate/README.md"):
        if re.search(r"^- \[ \]", (ROOT / rel).read_text(), re.M):
            errors.append(f"Uncompleted roadmap checkbox in {rel}")
    tracked = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    for rel in tracked:
        path = ROOT / rel
        if not rel.startswith(("apps/", "kits/", "deploy/")) or path.suffix not in {
            ".py",
            ".ts",
            ".mjs",
            ".sh",
        }:
            continue
        if any(part in {"fixtures", "test", "tests", "tmp", "node_modules"} for part in path.parts):
            continue
        if not path.resolve().is_relative_to(ROOT):
            errors.append(f"Source redirects outside repository: {rel}")
        elif path.is_file() and unresolved_markers(path.read_text()):
            errors.append(f"Unresolved implementation marker in {rel}")
    if errors:
        print("\n".join(errors))
        return 1
    print("maintenance inventory verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
