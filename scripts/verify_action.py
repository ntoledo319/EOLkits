#!/usr/bin/env python3
"""Exercise the real Action entrypoint with clean and finding fixtures, offline."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    target = ROOT / "tmp/verify/action"
    assert target.resolve().is_relative_to(ROOT)
    target.mkdir(parents=True, exist_ok=True)
    for name, expected in (("clean", "false"), ("findings", "true")):
        output = target / (name + ".txt")
        output.write_text("")
        env = os.environ.copy()
        env.update(
            {
                "GITHUB_ACTION_PATH": str(ROOT),
                "GITHUB_WORKSPACE": str(ROOT),
                "GITHUB_OUTPUT": str(output),
                "TMPDIR": str(target),
                "PIP_CACHE_DIR": str(target / "pip-cache"),
                "npm_config_cache": str(target / "npm-cache"),
                "INPUT_KIT": "lambda-lifeline",
                "INPUT_FAIL_ON": "any",
                "INPUT_PATH": f"apps/github-action/test/fixtures/{name}",
            }
        )
        subprocess.run(["bash", "apps/github-action/run.sh"], cwd=ROOT, env=env, check=True)
        result = dict(line.split("=", 1) for line in output.read_text().splitlines() if "=" in line)
        assert result["has_findings"] == expected
        assert result["should_fail"] == expected
        report = Path(result["report_path"]).resolve()
        assert report.is_relative_to(ROOT)
        content = report.read_text()
        assert ("audit-interest.yml" in content) == (expected == "true")
        if expected == "true":
            assert "https://ntoledo319.github.io/EOLkits/audit/" in content
            assert "one-repository evidence report ($299)" in content
        assert "https://eolkits.com/audit" not in content
    print("action fixtures verified")


if __name__ == "__main__":
    main()
