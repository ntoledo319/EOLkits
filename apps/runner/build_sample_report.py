#!/usr/bin/env python3
"""Build or verify the public fictional Audit v2 sample artifacts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import stat
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = RUNNER_DIR.parents[1]
SAMPLE_DIR = REPOSITORY_ROOT / "docs" / "audit" / "sample"
TMP_DIR = REPOSITORY_ROOT / "tmp" / "sample-report"
INPUT_PATH = SAMPLE_DIR / "fictional-repository.zip"
PDF_PATH = SAMPLE_DIR / "eolkits-sample-report.pdf"
MANIFEST_PATH = SAMPLE_DIR / "eolkits-sample-report.json"
PUBLIC_SITE_URL = "https://ntoledo319.github.io/EOLkits"
GENERATED_AT = datetime(2026, 8, 22, 21, 0, tzinfo=UTC)
SAMPLE_BUILDER_VERSION = 1
SAMPLE_PDF_PAGES = 4
RENDERER_VARIANT_MANIFEST_FIELDS = frozenset({"pdf_bytes", "pdf_sha256"})

sys.path.insert(0, str(RUNNER_DIR))
import audit_pdf  # noqa: E402, I001


FICTIONAL_FILES: dict[str, str] = {
    "README.md": (
        "# Fictional EOLkits sample\n\n"
        "This archive contains invented source created only to demonstrate the report format.\n"
    ),
    "images/Dockerfile": "FROM amazonlinux:2\nRUN amazon-linux-extras enable epel\n",
    "infra/template.yaml": (
        "Resources:\n"
        "  LegacyFunction:\n"
        "    Type: AWS::Serverless::Function\n"
        "    Properties:\n"
        "      Runtime: python3.9\n"
    ),
    "serverless.yml": "provider:\n  name: aws\n  runtime: python3.9\n",
    "src/compat.py": "from distutils import core\n",
}


def _assert_jailed_path(path: Path, *, require_file: bool = False) -> None:
    """Reject path escapes, symlinks, and non-regular checked-in artifacts."""
    try:
        relative = path.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise RuntimeError(f"sample path escapes the repository: {path}") from exc
    cursor = REPOSITORY_ROOT
    missing = False
    for index, part in enumerate(relative.parts):
        cursor /= part
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            missing = True
            continue
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"sample path must not contain a symlink: {cursor}")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(mode):
            raise RuntimeError(f"sample path parent is not a directory: {cursor}")
    if require_file:
        if missing:
            raise RuntimeError(f"sample artifact is missing: {path}")
        if not stat.S_ISREG(path.lstat().st_mode):
            raise RuntimeError(f"sample artifact is not a regular file: {path}")


def build_fictional_input() -> bytes:
    """Return a byte-stable ZIP containing only published fictional source."""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(FICTIONAL_FILES):
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, FICTIONAL_FILES[name].encode("utf-8"))
    return output.getvalue()


def build_sample_assets() -> dict[Path, bytes]:
    """Render the sample with the production engine and return its public assets."""
    input_bytes = build_fictional_input()
    _assert_jailed_path(TMP_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    temporary_input = TMP_DIR / "fictional-repository.zip"
    _assert_jailed_path(temporary_input)
    temporary_input.write_bytes(input_bytes)

    original_site_url = audit_pdf.PUBLIC_SITE_URL
    audit_pdf.PUBLIC_SITE_URL = PUBLIC_SITE_URL
    try:
        package = audit_pdf.generate_audit_package(
            upload_url=None,
            email="sample@example.invalid",
            upload_path=str(temporary_input),
            filename="fictional-repository.zip",
            report_time=GENERATED_AT,
            illustrative_sample=True,
        )
    finally:
        audit_pdf.PUBLIC_SITE_URL = original_site_url

    pdf_bytes = base64.b64decode(package["pdf_base64"], validate=True)
    if not pdf_bytes.startswith(b"%PDF"):
        raise RuntimeError("report engine did not return a PDF")

    manifest = _expected_manifest(input_bytes, pdf_bytes)
    package_fields = {
        "engine_sample_mode": package["illustrative_sample"],
        "evidence_count": package["evidence_count"],
        "evidence_fingerprint": package["evidence_hash"],
        "findings_count": package["findings_count"],
        "generated_at": package["generated_at"],
        "input_sha256": package["input_hash"],
        "pdf_pages": package["pdf_pages"],
        "report_version": package["report_version"],
        "rule_pack_version": package["rule_pack_version"],
        "scanned_files": package["scanned_files"],
        "skipped_files": package["skipped_files"],
    }
    for key, value in package_fields.items():
        if manifest[key] != value:
            raise RuntimeError(f"report engine metadata disagrees with sample manifest: {key}")
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return {INPUT_PATH: input_bytes, PDF_PATH: pdf_bytes, MANIFEST_PATH: manifest_bytes}


def _expected_manifest(input_bytes: bytes, pdf_bytes: bytes) -> dict[str, object]:
    sources, skipped_files = audit_pdf._source_files(input_bytes, INPUT_PATH.name)
    findings = audit_pdf._scan_sources(sources)
    rule_pack_version = audit_pdf._rule_pack_version()
    input_hash = hashlib.sha256(input_bytes).hexdigest()
    return {
        "artifact": "EOLkits Audit v2 illustrative sample",
        "sample_builder_version": SAMPLE_BUILDER_VERSION,
        "fictional": True,
        "engine_sample_mode": True,
        "verification_registered": False,
        "generated_at": GENERATED_AT.isoformat().replace("+00:00", "Z"),
        "report_version": audit_pdf.REPORT_VERSION,
        "report_template_sha256": hashlib.sha256(
            audit_pdf.PDF_TEMPLATE.encode("utf-8")
        ).hexdigest(),
        "rule_pack_version": rule_pack_version,
        "input_file": INPUT_PATH.name,
        "input_sha256": input_hash,
        "input_bytes": len(input_bytes),
        "source_files": sorted(FICTIONAL_FILES),
        "scanned_files": len(sources),
        "skipped_files": skipped_files,
        "findings_count": len(findings),
        "evidence_count": sum(finding["occurrences"] for finding in findings),
        "evidence_fingerprint": audit_pdf._evidence_fingerprint(
            input_hash, rule_pack_version, findings
        ),
        "pdf_file": PDF_PATH.name,
        "pdf_pages": SAMPLE_PDF_PAGES,
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "pdf_bytes": len(pdf_bytes),
        "limitations": (
            "Fictional static-source sample only; no customer repository or AWS account was used."
        ),
    }


def validate_checked_in_assets() -> list[str]:
    """Validate portable sample invariants without re-rendering system-font PDF bytes."""
    errors: list[str] = []
    try:
        for path in (INPUT_PATH, PDF_PATH, MANIFEST_PATH):
            _assert_jailed_path(path, require_file=True)
    except RuntimeError as exc:
        return [str(exc)]
    expected_input = build_fictional_input()
    if INPUT_PATH.read_bytes() != expected_input:
        errors.append("fictional input ZIP differs from the canonical fixture")

    pdf_bytes = PDF_PATH.read_bytes()
    if not pdf_bytes.startswith(b"%PDF"):
        errors.append("sample PDF does not have a PDF header")

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        errors.append("sample manifest is missing or invalid JSON")
        return errors

    expected_manifest = _expected_manifest(expected_input, pdf_bytes)
    if manifest != expected_manifest:
        errors.append("sample manifest schema or content is stale")
    return errors


def validate_engine_compatibility() -> list[str]:
    """Verify engine semantics while allowing platform-specific PDF serialization.

    WeasyPrint delegates font shaping and PDF serialization to native libraries.
    The checked-in PDF therefore has one exact published hash, but a fresh render
    on another supported Linux image can be semantically identical without being
    byte-identical. All engine-derived manifest fields except the resulting PDF
    byte count and hash must still match.
    """
    try:
        fresh_assets = build_sample_assets()
    except (OSError, RuntimeError, ValueError) as exc:
        return [f"fresh report-engine render failed: {exc}"]

    checked_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    fresh_manifest = json.loads(fresh_assets[MANIFEST_PATH].decode("utf-8"))
    checked_semantics = {
        key: value
        for key, value in checked_manifest.items()
        if key not in RENDERER_VARIANT_MANIFEST_FIELDS
    }
    fresh_semantics = {
        key: value
        for key, value in fresh_manifest.items()
        if key not in RENDERER_VARIANT_MANIFEST_FIELDS
    }
    errors: list[str] = []
    if fresh_assets[INPUT_PATH] != INPUT_PATH.read_bytes():
        errors.append("fresh engine fixture differs from the checked-in fictional input")
    if checked_semantics != fresh_semantics:
        errors.append("fresh report-engine metadata differs from the published sample")
    if not fresh_assets[PDF_PATH].startswith(b"%PDF"):
        errors.append("fresh report-engine output does not have a PDF header")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the public sample assets")
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify checked-in input, manifest semantics, and published PDF hash",
    )
    args = parser.parse_args()

    if args.check:
        errors = validate_checked_in_assets()
        if not errors:
            errors.extend(validate_engine_compatibility())
        if errors:
            print("Sample report assets are stale: " + "; ".join(errors), file=sys.stderr)
            return 1
        print(
            "Sample PDF hash, fictional input, and renderer-independent Audit v2 "
            "engine metadata are valid."
        )
        return 0

    expected = build_sample_assets()
    for path, content in expected.items():
        _assert_jailed_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        print(f"Wrote {path.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
