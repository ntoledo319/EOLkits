"""Test Python Lambda runtime scanner."""

import json
from argparse import Namespace
from datetime import date
from pathlib import Path

from python_pivot import runtimes, scan

FIXTURE = Path(__file__).parent / "fixtures" / "lambda-inventory.json"


def _args(**kw):
    base = dict(
        fixture=str(FIXTURE),
        regions=None,
        profile=None,
        format="table",
        out=None,
        strict=False,
    )
    base.update(kw)
    return Namespace(**base)


def test_loads_all_six():
    findings = scan.scan_fixture(str(FIXTURE))
    assert len(findings) == 6


class _Nov10(date):
    """Freeze "today" so day counts in these assertions do not drift."""

    @classmethod
    def today(cls):
        return cls(2026, 11, 10)


def test_identifies_eol_runtimes(monkeypatch):
    monkeypatch.setattr(runtimes, "date", _Nov10)
    findings = scan.scan_fixture(str(FIXTURE))
    by_rt = {f.runtime: f for f in findings}
    # 3.7 is long past EOL (AWS: deprecated 2023-12-04)
    assert by_rt["python3.7"].severity == "critical-eol"
    assert by_rt["python3.7"].days_to_eol == -1072
    # 3.8 is past EOL
    assert by_rt["python3.8"].severity == "critical-eol"
    # 3.12 is the target. AWS deprecates it on 2028-10-31: "low", not flagged for migration.
    assert by_rt["python3.12"].severity == "low"
    assert by_rt["python3.12"].days_to_eol == 721
    assert not runtimes.is_eol_or_soon("python3.12")


def test_run_table_format(capsys):
    rc = scan.run(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "payment-webhook" in out
    assert "python3.9" in out


def test_run_json(capsys):
    rc = scan.run(_args(format="json"))
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert len(parsed) == 6
    assert any(x["function_name"] == "payment-webhook" for x in parsed)


def test_run_csv_has_header(capsys):
    rc = scan.run(_args(format="csv"))
    assert rc == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("function_name")


def test_run_markdown(capsys):
    rc = scan.run(_args(format="md"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "| Function |" in out


def test_strict_mode_exits_1_with_eol():
    rc = scan.run(_args(strict=True))
    assert rc == 1


def test_run_out_file(tmp_path):
    outfile = tmp_path / "f.json"
    rc = scan.run(_args(format="json", out=str(outfile)))
    assert rc == 0
    assert outfile.exists()
    data = json.loads(outfile.read_text())
    assert len(data) == 6


def test_eol_delta_labels_past_and_future_dates():
    assert scan.eol_delta(-250) == "250d ago"
    assert scan.eol_delta(70) == "in 70d"


# Every Python row of https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html,
# re-read 2026-11-10: (deprecation, block function create, block function update).
# None = "Not scheduled".
AWS_PYTHON_ROWS = {
    "python3.15": (None, None, None),
    "python3.14": (date(2029, 6, 30), date(2029, 7, 31), date(2029, 8, 31)),
    "python3.13": (date(2029, 6, 30), date(2029, 7, 31), date(2029, 8, 31)),
    "python3.12": (date(2028, 10, 31), date(2028, 11, 30), date(2029, 1, 10)),
    "python3.11": (date(2027, 6, 30), date(2027, 7, 29), date(2027, 8, 31)),
    "python3.10": (date(2026, 10, 31), date(2027, 7, 29), date(2027, 8, 31)),
    "python3.9": (date(2025, 12, 15), date(2027, 7, 29), date(2027, 8, 31)),
    "python3.8": (date(2024, 10, 14), date(2027, 7, 29), date(2027, 8, 31)),
    "python3.7": (date(2023, 12, 4), date(2024, 1, 9), date(2027, 8, 31)),
    "python3.6": (date(2022, 7, 18), date(2022, 7, 18), date(2022, 8, 29)),
    "python2.7": (date(2021, 7, 15), date(2021, 7, 15), date(2022, 5, 30)),
}


def test_every_python_row_matches_the_aws_runtimes_table():
    assert set(runtimes.RUNTIME_TABLE) == set(AWS_PYTHON_ROWS)
    for runtime, expected in AWS_PYTHON_ROWS.items():
        info = runtimes.RUNTIME_TABLE[runtime]
        got = (info.deprecation_phase1, info.block_create, info.block_update)
        assert got == expected, runtime


def test_newer_runtimes_are_never_told_to_move_back_to_312():
    for runtime in ("python3.13", "python3.14", "python3.15"):
        assert runtimes.RUNTIME_TABLE[runtime].recommended_target == runtime


def test_retired_runtimes_are_flagged_not_ok():
    for runtime in ("python2.7", "python3.6"):
        assert runtimes.severity_for(runtime) == "critical-eol"
        assert runtimes.is_eol_or_soon(runtime)
