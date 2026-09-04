"""Cross-product runtime dates must agree with the cited public rule pack."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parents[2]
PYTHON_PIVOT_SRC = ROOT / "kits" / "python-pivot" / "src"
if str(PYTHON_PIVOT_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_PIVOT_SRC))

from python_pivot.runtimes import RUNTIME_TABLE  # noqa: E402


def _public_runtime_dates() -> dict[str, dict[str, str]]:
    dates: dict[str, dict[str, str]] = {}
    for entry in build.load_deprecations()["deprecations"]:
        runtime = build._runtime_id_from_name(entry["name"])
        if runtime:
            dates[runtime] = {
                "phase1": entry["deprecation_date"],
                "block_create": entry["date"],
                "block_update": entry["block_update_date"],
            }
    return dates


def test_lambda_lifeline_dates_match_the_public_rule_pack() -> None:
    fixture = ROOT / "kits" / "lambda-lifeline" / "test" / "fixtures" / "runtime-parity.json"
    cli = ROOT / "kits" / "lambda-lifeline" / "bin" / "cli.mjs"
    result = subprocess.run(
        ["node", str(cli), "scan", "--fixture", str(fixture), "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    observed = {item["runtime"]: item["deprecation_dates"] for item in json.loads(result.stdout)}

    assert observed == _public_runtime_dates()


def test_python_pivot_dates_match_the_public_rule_pack() -> None:
    expected = {
        runtime: dates
        for runtime, dates in _public_runtime_dates().items()
        if runtime.startswith("python")
    }
    observed = {
        runtime: {
            "phase1": info.deprecation_phase1.isoformat(),
            "block_create": info.block_create.isoformat(),
            "block_update": info.block_update.isoformat(),
        }
        for runtime, info in RUNTIME_TABLE.items()
        if runtime in expected
    }

    assert observed == expected
