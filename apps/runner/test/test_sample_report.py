"""Regression checks for the public, fictional Audit v2 sample artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parents[1]
ROOT = RUNNER_DIR.parents[1]


def _load_sample_builder():
    target = RUNNER_DIR / "build_sample_report.py"
    spec = importlib.util.spec_from_file_location("eolkits_sample_builder", target)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checked_in_sample_matches_the_production_report_engine() -> None:
    builder = _load_sample_builder()
    assert builder.validate_checked_in_assets() == []
    assert builder.INPUT_PATH.is_relative_to(ROOT)
    assert builder.PDF_PATH.is_relative_to(ROOT)
    assert builder.MANIFEST_PATH.is_relative_to(ROOT)

    manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    pdf = builder.PDF_PATH.read_bytes()
    source = builder.INPUT_PATH.read_bytes()

    assert manifest["fictional"] is True
    assert manifest["engine_sample_mode"] is True
    assert manifest["verification_registered"] is False
    assert manifest["sample_builder_version"] == 1
    assert manifest["generated_at"] == "2026-08-22T21:00:00Z"
    assert manifest["report_version"] == "2.0"
    assert manifest["pdf_pages"] == 4
    assert manifest["scanned_files"] == 4
    assert manifest["skipped_files"] == 1
    assert manifest["findings_count"] == 4
    assert manifest["evidence_count"] == 5
    assert hashlib.sha256(pdf).hexdigest() == manifest["pdf_sha256"]
    assert hashlib.sha256(source).hexdigest() == manifest["input_sha256"]
    assert pdf.startswith(b"%PDF")
    with zipfile.ZipFile(builder.INPUT_PATH) as archive:
        assert sorted(archive.namelist()) == manifest["source_files"]
        assert all((item.external_attr >> 16) & 0o170000 == 0o100000 for item in archive.infolist())


def test_sample_validator_rejects_extra_manifest_fields(tmp_path, monkeypatch) -> None:
    builder = _load_sample_builder()
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()
    input_path = sample_dir / builder.INPUT_PATH.name
    pdf_path = sample_dir / builder.PDF_PATH.name
    manifest_path = sample_dir / builder.MANIFEST_PATH.name
    input_path.write_bytes(builder.INPUT_PATH.read_bytes())
    pdf_path.write_bytes(builder.PDF_PATH.read_bytes())
    manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["unreviewed_field"] = True
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(builder, "INPUT_PATH", input_path)
    monkeypatch.setattr(builder, "PDF_PATH", pdf_path)
    monkeypatch.setattr(builder, "MANIFEST_PATH", manifest_path)

    assert builder.validate_checked_in_assets() == ["sample manifest schema or content is stale"]


def test_sample_validator_rejects_symlinked_artifacts(tmp_path, monkeypatch) -> None:
    builder = _load_sample_builder()
    target = tmp_path / "target.zip"
    target.write_bytes(builder.build_fictional_input())
    symlink = tmp_path / builder.INPUT_PATH.name
    symlink.symlink_to(target)
    monkeypatch.setattr(builder, "INPUT_PATH", symlink)

    errors = builder.validate_checked_in_assets()

    assert len(errors) == 1
    assert "must not contain a symlink" in errors[0]
