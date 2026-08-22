from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import socket
import zipfile
from pathlib import Path

import pytest
from jinja2 import Environment, select_autoescape

RUNNER_DIR = Path(__file__).resolve().parents[1]


def _load(name: str):
    target = RUNNER_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"eolkits_test_{name}", target)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _zip_bytes(files: dict[str, str]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in files.items():
            archive.writestr(name, body)
    return output.getvalue()


def test_scan_reports_exact_files_and_lines_without_sdk_v3_false_positive():
    audit = _load("audit_pdf")
    sources = [
        ("infra/template.yaml", "Resources:\n  Runtime: nodejs20.x\n"),
        (
            "src/index.js",
            "const v3 = require('@aws-sdk/client-lambda');\n" "const v2 = require('aws-sdk');\n",
        ),
    ]

    findings = {finding["id"]: finding for finding in audit._scan_sources(sources)}

    assert findings["lambda-nodejs20"]["locations"] == [
        {"file": "infra/template.yaml", "line": 2, "evidence": "Runtime: nodejs20.x"}
    ]
    assert findings["aws-sdk-v2"]["locations"] == [
        {"file": "src/index.js", "line": 2, "evidence": "const v2 = require('aws-sdk');"}
    ]
    assert findings["aws-sdk-v2"]["occurrences"] == 1


def test_zip_scan_is_in_memory_sorted_and_skips_binary_or_unsupported_files():
    audit = _load("audit_pdf")
    payload = _zip_bytes(
        {
            "z/template.yaml": "Runtime: python3.9\n",
            "a/main.py": "from distutils import core\n",
            "image.png": "\x00binary",
            "notes.md": "Runtime: nodejs18.x\n",
        }
    )

    sources, skipped = audit._source_files(payload, "repo.zip")

    assert [name for name, _ in sources] == ["a/main.py", "z/template.yaml"]
    assert skipped == 2
    assert {finding["id"] for finding in audit._scan_sources(sources)} >= {
        "python-distutils",
        "lambda-python39",
    }


def test_zip_rejects_traversal_and_excessive_compression():
    audit = _load("audit_pdf")
    with pytest.raises(ValueError, match="unsafe path"):
        audit._source_files(_zip_bytes({"../outside.py": "import imp\n"}), "repo.zip")

    compressed = _zip_bytes({"huge.py": "a" * (1024 * 1024 + 1)})
    with pytest.raises(ValueError, match="compression ratio"):
        audit._source_files(compressed, "repo.zip")


def test_zip_rejects_too_many_members(monkeypatch):
    audit = _load("audit_pdf")
    monkeypatch.setattr(audit, "MAX_SOURCE_FILES", 1)
    with pytest.raises(ValueError, match="more than 1 files"):
        audit._source_files(_zip_bytes({"one.py": "x", "two.py": "y"}), "repo.zip")


def test_preflight_rejects_fake_zip_binary_and_empty_source_archive(tmp_path):
    audit = _load("audit_pdf")
    fake_zip = tmp_path / "repo.zip"
    fake_zip.write_bytes(b"not actually a zip")
    with pytest.raises(ValueError, match="not a valid ZIP"):
        audit.preflight_audit_input(str(fake_zip), "repo.zip")

    binary = tmp_path / "settings.json"
    binary.write_bytes(b"{\x00binary}")
    with pytest.raises(ValueError, match="binary files"):
        audit.preflight_audit_input(str(binary), "settings.json")

    unsupported = tmp_path / "unsupported.zip"
    unsupported.write_bytes(_zip_bytes({"diagram.png": "not source"}))
    with pytest.raises(ValueError, match="no supported"):
        audit.preflight_audit_input(str(unsupported), "unsupported.zip")


def test_preflight_applies_separate_expanded_archive_limit(tmp_path, monkeypatch):
    audit = _load("audit_pdf")
    monkeypatch.setattr(audit, "MAX_EXPANDED_BYTES", 32)
    archive = tmp_path / "repo.zip"
    archive.write_bytes(_zip_bytes({"main.py": "x" * 33}))
    with pytest.raises(ValueError, match="expands beyond"):
        audit.preflight_audit_input(str(archive), "repo.zip")


def test_paid_dependency_rules_cover_browser_scanner_tables():
    audit = _load("audit_pdf")
    web_path = RUNNER_DIR.parent / "web" / "build.py"
    spec = importlib.util.spec_from_file_location("eolkits_test_web_build", web_path)
    assert spec and spec.loader
    web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web)

    assert {name: rule.get("min") for name, rule in audit.NODE_NATIVE_PACKAGES.items()} == {
        name: rule.get("min") for name, rule in web._NATIVE_PACKAGES.items()
    }
    assert {name: rule.get("min") for name, rule in audit.PY312_WHEELS.items()} == {
        name: rule.get("min") for name, rule in web._PY312_WHEELS.items()
    }

    findings = {
        finding["id"]: finding
        for finding in audit._scan_sources(
            [
                ("requirements.txt", "numpy==1.25.0\n"),
                ("package.json", '{"dependencies":{"bcrypt":"4.0.0"}}'),
            ]
        )
    }
    assert findings["dependency-python-numpy"]["locations"][0]["line"] == 1
    assert findings["dependency-node-bcrypt"]["locations"][0]["line"] == 1


def test_evidence_fingerprint_is_deterministic_and_input_bound():
    audit = _load("audit_pdf")
    sources = [("template.yaml", "Runtime: nodejs20.x\n")]
    findings = audit._scan_sources(sources)
    rule_version = "rules-test"
    input_hash = hashlib.sha256(sources[0][1].encode()).hexdigest()

    first = audit._evidence_fingerprint(input_hash, rule_version, findings)
    second = audit._evidence_fingerprint(input_hash, rule_version, findings)
    changed = audit._evidence_fingerprint("f" * 64, rule_version, findings)

    assert first == second
    assert len(first) == 64
    assert changed != first


def test_report_template_escapes_uploaded_names_and_evidence():
    audit = _load("audit_pdf")
    template = Environment(
        autoescape=select_autoescape(default=True, default_for_string=True)
    ).from_string(audit.PDF_TEMPLATE)
    html = template.render(
        generated_at="now",
        report_version="2.0",
        rule_pack_version="rules",
        input_name="<script>alert(1)</script>.yaml",
        input_hash="a" * 64,
        evidence_hash="b" * 64,
        total_findings=1,
        findings=[
            {
                "severity": "high",
                "title": "test",
                "description": "test",
                "remediation": "test",
                "source_url": "https://example.com",
                "affected_files": 1,
                "occurrences": 1,
                "locations": [{"file": "<img>.yaml", "line": 1, "evidence": "<svg>"}],
                "omitted_locations": 0,
            }
        ],
        categories=[],
        affected_files=1,
        scanned_files=1,
        scanned_bytes=5,
        skipped_files=0,
        evidence_lines=1,
        deadline=None,
        upcoming_deprecations=[],
        verify_url="https://eolkits.com/verify/?hash=" + "b" * 64,
    )

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;svg&gt;" in html


def test_download_rejects_redirect_after_public_host_validation(monkeypatch):
    audit = _load("audit_pdf")
    monkeypatch.setattr(audit, "ALLOWED_UPLOAD_ORIGIN", "https://uploads.example")
    monkeypatch.setattr(
        audit.socket,
        "getaddrinfo",
        lambda *_: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))],
    )

    class Response:
        status_code = 302

        def raise_for_status(self):
            raise AssertionError("redirect must be rejected before raise_for_status")

    observed: dict[str, object] = {}

    def fake_get(url, **kwargs):
        observed.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr(audit.requests, "get", fake_get)
    with pytest.raises(ValueError, match="redirects are not allowed"):
        audit._download_input("https://uploads.example/repo.zip")
    assert observed["allow_redirects"] is False


def test_generate_audit_package_renders_a_real_pdf(tmp_path):
    audit = _load("audit_pdf")
    source = tmp_path / "template.yaml"
    source.write_text("Resources:\n  Runtime: nodejs20.x\n", encoding="utf-8")

    package = audit.generate_audit_package(
        upload_url=None,
        email="buyer@example.com",
        upload_path=str(source),
        filename="template.yaml",
    )
    pdf = base64.b64decode(package["pdf_base64"], validate=True)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 10_000
    assert package["report_version"] == "2.0"
    assert package["input_hash"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert package["findings_count"] >= 1


def test_runner_http_auth_rejects_bad_token(monkeypatch):
    from io import BytesIO

    runner = _load("main")
    writes: list[tuple[str, object]] = []
    handler = object.__new__(runner.RunnerHandler)
    handler.path = "/job"
    handler.headers = {"Authorization": "Bearer wrong", "Content-Length": "2"}
    handler.rfile = BytesIO(b"{}")
    monkeypatch.setenv("RUNNER_TOKEN", "expected")
    monkeypatch.setattr(handler, "send_response", lambda status: writes.append(("status", status)))
    monkeypatch.setattr(handler, "send_header", lambda key, value: None)
    monkeypatch.setattr(handler, "end_headers", lambda: None)
    handler.wfile = type(
        "Writer", (), {"write": lambda _self, data: writes.append(("body", data))}
    )()

    handler.do_POST()

    assert ("status", 401) in writes
    assert b"unauthorized" in dict(writes)["body"]


def test_runner_http_requires_a_configured_token(monkeypatch):
    from io import BytesIO

    runner = _load("main")
    writes: list[tuple[str, object]] = []
    handler = object.__new__(runner.RunnerHandler)
    handler.path = "/job"
    handler.headers = {"Content-Length": "2"}
    handler.rfile = BytesIO(b"{}")
    monkeypatch.delenv("RUNNER_TOKEN", raising=False)
    monkeypatch.setattr(handler, "send_response", lambda status: writes.append(("status", status)))
    monkeypatch.setattr(handler, "send_header", lambda key, value: None)
    monkeypatch.setattr(handler, "end_headers", lambda: None)
    handler.wfile = type(
        "Writer", (), {"write": lambda _self, data: writes.append(("body", data))}
    )()

    handler.do_POST()

    assert ("status", 503) in writes
    assert b"runner_not_configured" in dict(writes)["body"]


def test_runner_http_rejects_work_above_capacity(monkeypatch):
    from io import BytesIO

    runner = _load("main")
    writes: list[tuple[str, object]] = []
    handler = object.__new__(runner.RunnerHandler)
    handler.path = "/job"
    handler.headers = {"Authorization": "Bearer expected", "Content-Length": "2"}
    handler.rfile = BytesIO(b"{}")
    handler.wfile = type(
        "Writer", (), {"write": lambda _self, data: writes.append(("body", data))}
    )()
    monkeypatch.setenv("RUNNER_TOKEN", "expected")
    monkeypatch.setattr(
        runner,
        "RUNNER_SLOTS",
        type("NoSlot", (), {"acquire": lambda _self, blocking=False: False})(),
    )
    monkeypatch.setattr(handler, "send_response", lambda status: writes.append(("status", status)))
    monkeypatch.setattr(handler, "send_header", lambda key, value: None)
    monkeypatch.setattr(handler, "end_headers", lambda: None)

    handler.do_POST()

    assert ("status", 503) in writes
    assert b"runner_capacity_exhausted" in dict(writes)["body"]
