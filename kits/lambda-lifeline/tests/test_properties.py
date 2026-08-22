"""Behavioral properties for the shipped lambda-lifeline CLI.

These tests intentionally invoke only real commands and fail on operational
exit code 2; they never turn an unsupported-command error into a green test.
"""

import subprocess
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

CLI = Path(__file__).resolve().parents[1] / "bin" / "cli.mjs"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(CLI), *args],
        capture_output=True,
        text=True,
        check=False,
    )


@given(
    runtime=st.sampled_from(["nodejs14.x", "nodejs16.x", "nodejs18.x", "nodejs20.x"]),
    handler=st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,30}\.handler", fullmatch=True),
)
@settings(max_examples=30, deadline=None)
def test_iac_apply_changes_only_the_runtime(runtime: str, handler: str) -> None:
    template = f"""Transform: AWS::Serverless-2016-10-31
Resources:
  Function:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: {runtime}
      Handler: {handler}
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          LOG_LEVEL: info
"""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "template.yaml"
        path.write_text(template, encoding="utf-8")

        preview = run_cli("iac", "--path", str(path), "--strict")
        assert preview.returncode == 1, preview.stderr
        assert path.read_text(encoding="utf-8") == template

        applied = run_cli("iac", "--path", str(path), "--apply")
        assert applied.returncode == 0, applied.stderr
        result = path.read_text(encoding="utf-8")
        assert "Runtime: nodejs24.x" in result
        assert f"Handler: {handler}" in result
        assert "MemorySize: 512" in result
        assert "Timeout: 30" in result
        assert "LOG_LEVEL: info" in result


@given(
    variable=st.from_regex(r"[A-Za-z_$][A-Za-z0-9_$]{0,20}", fullmatch=True),
    suffix=st.text(alphabet=" abcdefghijklmnopqrstuvwxyz0123456789;\n", max_size=80),
)
@settings(max_examples=30, deadline=None)
def test_codemod_rewrite_is_idempotent_and_preserves_surrounding_text(
    variable: str, suffix: str
) -> None:
    original = f"import {variable} from './data.json' assert {{ type: 'json' }};\n{suffix}"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "index.mjs"
        path.write_text(original, encoding="utf-8")

        first = run_cli("codemod", "--path", str(path), "--apply")
        assert first.returncode == 0, first.stderr
        once = path.read_text(encoding="utf-8")
        assert f"import {variable} from './data.json' with {{ type: 'json' }};" in once
        assert once.endswith(suffix)

        second = run_cli("codemod", "--path", str(path), "--apply")
        assert second.returncode == 0, second.stderr
        assert path.read_text(encoding="utf-8") == once


def test_missing_path_is_an_operational_error() -> None:
    result = run_cli("iac", "--path", "definitely-does-not-exist", "--strict")
    assert result.returncode == 2
