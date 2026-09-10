"""Test native-wheel audit."""

import builtins
import json
from argparse import Namespace
from pathlib import Path

import pytest
from python_pivot import audit

FIXTURE = Path(__file__).parent / "fixtures" / "requirements.txt"


def _args(path, fmt="table", strict=False):
    return Namespace(path=str(path), format=fmt, strict=strict)


def test_parse_requirements():
    pkgs = audit.parse_requirements(FIXTURE)
    names = [n for n, _ in pkgs]
    assert "numpy" in names
    assert "boto3" in names


def test_detects_outdated_numpy():
    pkgs = audit.parse_requirements(FIXTURE)
    findings = audit.audit_packages(pkgs)
    numpy_finding = next((f for f in findings if f["package"] == "numpy"), None)
    assert numpy_finding is not None
    assert numpy_finding["severity"] == "high"


def test_detects_outdated_python_snappy():
    pkgs = audit.parse_requirements(FIXTURE)
    findings = audit.audit_packages(pkgs)
    snappy = next((f for f in findings if f["package"] == "python-snappy"), None)
    assert snappy is not None
    assert snappy["severity"] == "high"


def test_ignores_clean_requests():
    # requests is NOT in the native wheel table (pure Python) — should not flag
    pkgs = audit.parse_requirements(FIXTURE)
    findings = audit.audit_packages(pkgs)
    assert not any(f["package"] == "requests" for f in findings)


def test_run_strict_exits_nonzero(capsys):
    rc = audit.run(_args(FIXTURE, strict=True))
    assert rc == 1


def test_run_json(capsys):
    rc = audit.run(_args(FIXTURE, fmt="json"))
    assert rc == 0  # non-strict
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert len(parsed) > 0


def test_clean_requirements_pass(tmp_path, capsys):
    clean = tmp_path / "req.txt"
    clean.write_text("numpy==1.26.1\nboto3==1.34.0\nrequests==2.31.0\n")
    rc = audit.run(_args(clean, strict=True))
    assert rc == 0


def test_pyproject_parsing(tmp_path):
    pp = tmp_path / "pyproject.toml"
    pp.write_text(
        """
[project]
dependencies = [
  "numpy==1.24.0",
  "requests>=2.31"
]
"""
    )
    pkgs = audit.parse_pyproject(pp)
    names = [n for n, _ in pkgs]
    assert "numpy" in names
    assert "requests" in names


@pytest.mark.parametrize(
    "declaration",
    [
        "[project]\ndependencies = ['numpy==1.24.0']\n",
        '[project]\ndependencies = ["numpy==1.24.0"]\n',
        "[project.optional-dependencies]\nscience = ['numpy==1.24.0']\n",
        "[project]\ndependencies = [\"numpy[array-api]==1.24.0; python_version < '3.13'\"]\n",
    ],
)
def test_pyproject_all_supported_declarations_are_strict_findings(tmp_path, capsys, declaration):
    path = tmp_path / "pyproject.toml"
    path.write_text(declaration)
    assert audit.run(_args(path, fmt="json", strict=True)) == 1
    result = json.loads(capsys.readouterr().out)
    assert [(item["package"], item["severity"]) for item in result] == [("numpy", "high")]


def test_pyproject_ignores_build_and_unrelated_tool_dependencies(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        """[build-system]
requires = ['numpy==1.24.0']
[project]
dependencies = ['numpy==1.26.1']
[tool.example]
dependencies = ['pandas==1.0.0']
"""
    )
    assert audit.parse_pyproject(path) == [("numpy", "==1.26.1")]
    assert audit.run(_args(path, strict=True)) == 0


def test_pipfile_packages_dev_groups_inline_versions_and_normalized_names(tmp_path, capsys):
    path = tmp_path / "Pipfile"
    path.write_text(
        """[packages]
numpy = '==1.24.0'
requests = '*'
[dev-packages]
Pillow = {version = "==9.5.0", markers = "python_version >= '3.9'"}
scikit_learn = {version = '==1.2.0', extras = ['extra']}
"""
    )
    assert audit.run(_args(path, fmt="json", strict=True)) == 1
    assert {item["package"] for item in json.loads(capsys.readouterr().out)} == {
        "numpy",
        "pillow",
        "scikit-learn",
    }


@pytest.mark.parametrize(
    "filename,content",
    [
        ("pyproject.toml", "[project]\ndependencies = ['numpy==1.24.0'"),
        ("pyproject.toml", "[project]\ndependencies = 'numpy==1.24.0'"),
        ("pyproject.toml", "[project]\ndynamic = ['dependencies']"),
        ("pyproject.toml", "[project]\ndynamic = 'dependencies'"),
        ("pyproject.toml", "[tool.poetry.dependencies]\nnumpy = '==1.24.0'"),
        ("Pipfile", "[packages]\nnumpy = 24"),
        ("requirements.txt", "-r requirements-prod.txt\n"),
        ("requirements.txt", "numpy==1.24.0 \\\n+ --hash=sha256:fixture\n"),
    ],
)
def test_unsupported_or_malformed_manifests_are_errors_not_clean_json(
    tmp_path, capsys, filename, content
):
    path = tmp_path / filename
    path.write_text(content)
    assert audit.run(_args(path, fmt="json", strict=True)) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "Cannot audit" in output.err


def test_requirements_markers_and_comments_do_not_hide_or_inflate_versions(tmp_path):
    path = tmp_path / "requirements.txt"
    path.write_text("numpy==1.24.0; python_version < '3.13' # target\nPillow==10.1.0 # current\n")
    assert audit.parse_requirements(path) == [("numpy", "==1.24.0"), ("pillow", "==10.1.0")]
    assert [item["package"] for item in audit.audit_packages(audit.parse_requirements(path))] == [
        "numpy"
    ]


def test_unknown_packages_do_not_produce_a_universal_compatibility_claim(tmp_path, capsys):
    path = tmp_path / "requirements.txt"
    path.write_text("unknown-package==0.1.0\n")
    assert audit.run(_args(path, strict=True)) == 0
    assert "outside the curated table are not checked" in capsys.readouterr().out


def test_short_release_versions_and_parenthesized_requirements(tmp_path):
    path = tmp_path / "requirements.txt"
    path.write_text("numpy (==1.26)\nPillow>=10.1\n")
    assert audit.run(_args(path, strict=True)) == 0
    assert audit.audit_packages([("numpy", "==1.26.0rc1")])[0]["severity"] == "low"


def test_toml_parser_missing_is_an_actionable_error_without_breaking_requirements(
    tmp_path, monkeypatch, capsys
):
    original_import = builtins.__import__

    def without_toml(name, *args, **kwargs):
        if name in {"tomllib", "tomli"}:
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_toml)
    path = tmp_path / "pyproject.toml"
    path.write_text("[project]\ndependencies = ['numpy==1.24.0']\n")
    assert audit.run(_args(path, fmt="json")) == 2
    assert "Python 3.11+" in capsys.readouterr().err
    flat = tmp_path / "requirements.txt"
    flat.write_text("numpy==1.24.0\n")
    assert audit.run(_args(flat, fmt="json", strict=True)) == 1


def test_direct_reference_contents_are_not_printed_in_audit_findings():
    finding = audit.audit_packages(
        [("numpy", "@ https://fixture-user:fixture-password@example.invalid/archive.zip")]
    )[0]
    assert finding["declared"] == "(direct reference)"
    assert "fixture-password" not in json.dumps(finding)
