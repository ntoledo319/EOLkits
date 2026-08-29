from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import socket
import zipfile
from datetime import UTC, datetime
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
        (
            "infra/template.yaml",
            "Resources:\n"
            "  Job:\n"
            "    Type: AWS::Lambda::Function\n"
            "    Properties:\n"
            "      Runtime: nodejs20.x\n",
        ),
        (
            "src/index.js",
            "const v3 = require('@aws-sdk/client-lambda');\n" "const v2 = require('aws-sdk');\n",
        ),
    ]

    findings = {finding["id"]: finding for finding in audit._scan_sources(sources)}

    assert findings["lambda-nodejs20"]["locations"] == [
        {"file": "infra/template.yaml", "line": 5, "evidence": "Runtime: nodejs20.x"}
    ]
    assert findings["aws-sdk-v2"]["locations"] == [
        {"file": "src/index.js", "line": 2, "evidence": "const v2 = require('aws-sdk');"}
    ]
    assert findings["aws-sdk-v2"]["occurrences"] == 1


def test_zip_scan_is_in_memory_sorted_and_skips_binary_or_unsupported_files():
    audit = _load("audit_pdf")
    payload = _zip_bytes(
        {
            "z/template.yaml": (
                "Resources:\n"
                "  Legacy:\n"
                "    Type: AWS::Serverless::Function\n"
                "    Properties:\n"
                "      Runtime: python3.9\n"
            ),
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


def test_python_runtime_rules_require_lambda_configuration_context():
    audit = _load("audit_pdf")
    findings = {
        finding["id"]: finding
        for finding in audit._scan_sources(
            [
                (
                    "template.yaml",
                    "Resources:\n"
                    "  Python38:\n"
                    "    Type: AWS::Serverless::Function\n"
                    "    Properties:\n"
                    "      Runtime: python3.8\n"
                    "  Python39:\n"
                    "    Type: AWS::Lambda::Function\n"
                    "    Properties:\n"
                    "      Runtime: python3.9\n",
                ),
                (
                    "main.tf",
                    'resource "aws_lambda_function" "job" {\n' '  runtime = "python3.10"\n' "}\n",
                ),
                ("stack.ts", "runtime: lambda.Runtime.PYTHON_3_11\n"),
                (
                    "stack.py",
                    "from aws_cdk.aws_lambda import Runtime\n"
                    "function = lambda_config(runtime=Runtime.PYTHON_3_11)\n",
                ),
                (
                    "commands.sh",
                    "aws lambda update-function-configuration --runtime python3.8\n",
                ),
                (
                    "Dockerfile",
                    "RUN amazon-linux-extras enable python3.8\n",
                ),
                ("requirements.txt", "python3.9==1.0\n"),
                (
                    "mixed.yaml",
                    "Resources:\n"
                    "  RealLambda:\n"
                    "    Type: AWS::Serverless::Function\n"
                    "    Properties:\n"
                    "      Runtime: nodejs20.x\n"
                    "custom_app:\n"
                    "  runtime: python3.9\n",
                ),
                (
                    "serverless.yml",
                    "provider:\n"
                    "  name: aws\n"
                    "  runtime: nodejs20.x\n"
                    "custom:\n"
                    "  runtime: python3.10\n",
                ),
                (
                    "generic-stack.ts",
                    "import * as lambda from 'aws-cdk-lib/aws-lambda';\n"
                    "const localConfig = {runtime: 'python3.11'};\n"
                    "const TARGET = Runtime.PYTHON_3_11;\n",
                ),
                ("generic-command.sh", "mytool deploy --runtime python3.8\n"),
            ]
        )
    }

    assert findings["lambda-python38"]["occurrences"] == 2
    assert findings["lambda-python39"]["occurrences"] == 1
    assert findings["lambda-python310"]["occurrences"] == 1
    assert findings["lambda-python311"]["occurrences"] == 2
    assert all(
        location["file"]
        not in {
            "Dockerfile",
            "generic-command.sh",
            "generic-stack.ts",
            "mixed.yaml",
            "requirements.txt",
            "serverless.yml",
        }
        for rule_id in (
            "lambda-python38",
            "lambda-python39",
            "lambda-python310",
            "lambda-python311",
        )
        for location in findings[rule_id]["locations"]
    )


def test_lambda_context_lexer_is_bounded_and_rejects_lookalikes():
    audit = _load("audit_pdf")
    deeply_nested = "\n".join(" " * depth + f"level{depth}:" for depth in range(1100))
    hostile_sources = [
        (
            "cycle.yaml",
            "anchor: &loop\n  self: *loop\n  runtime: python3.9\n",
        ),
        ("deep.yaml", deeply_nested + "\n" + " " * 1100 + "runtime: python3.10\n"),
        (
            "globals.yaml",
            "Globals:\n  Function:\n    Runtime: python3.9\n",
        ),
        (
            "generic.json",
            '{"FunctionName":"not-lambda","runtime":"python3.10"}',
        ),
        (
            "nested.tf",
            'resource "aws_lambda_function" "job" {\n'
            "  environment {\n"
            '    variables = { runtime = "python3.11" }\n'
            "  }\n"
            "}\n",
        ),
        (
            "multi.yaml",
            "---\napp:\n  runtime: python3.8\n---\nother:\n  runtime: python3.9\n",
        ),
    ]

    findings = audit._scan_sources(hostile_sources)

    assert not any(finding["id"].startswith("lambda-python") for finding in findings)


def test_lambda_context_supports_bounded_json_yaml_and_cdk_forms():
    audit = _load("audit_pdf")
    fixtures = [
        (
            "minified_cfn.json",
            '{"Resources":{"Fn":{"Type":"AWS::Lambda::Function",'
            '"Properties":{"Runtime":"python3.9"}}}}\n',
        ),
        (
            "yaml_flow.yml",
            "Resources: {Fn: {Type: AWS::Lambda::Function, " "Properties: {Runtime: python3.9}}}\n",
        ),
        (
            "sam_transform_list.yml",
            "Transform:\n"
            "  - AWS::Serverless-2016-10-31\n"
            "Globals:\n"
            "  Function:\n"
            "    Runtime: python3.9\n",
        ),
        (
            "sam_comment.yml",
            "Resources:\n"
            "  Fn:\n"
            "    Type: AWS::Serverless::Function # Lambda\n"
            "    Properties:\n"
            "      Runtime: python3.9\n",
        ),
        (
            "python_named_cdk.py",
            "from aws_cdk.aws_lambda import Runtime\n"
            "config = dict(runtime=Runtime.PYTHON_3_11)\n",
        ),
    ]

    findings = {finding["id"]: finding for finding in audit._scan_sources(fixtures)}

    assert findings["lambda-python39"]["occurrences"] == 4
    assert findings["lambda-python311"]["occurrences"] == 1


def test_sam_globals_require_transform_and_serverless_requires_aws_provider():
    audit = _load("audit_pdf")
    findings = {
        finding["id"]: finding
        for finding in audit._scan_sources(
            [
                (
                    "sam.yaml",
                    "Transform: AWS::Serverless-2016-10-31\n"
                    "Globals:\n"
                    "  Function:\n"
                    "    Runtime: python3.8\n",
                ),
                (
                    "serverless.yml",
                    "provider:\n"
                    "  name: aws\n"
                    "functions:\n"
                    "  real:\n"
                    "    runtime: python3.9\n",
                ),
                (
                    "not-aws.yml",
                    "provider:\n"
                    "  name: other\n"
                    "functions:\n"
                    "  fake:\n"
                    "    runtime: python3.10\n",
                ),
            ]
        )
    }

    assert findings["lambda-python38"]["occurrences"] == 1
    assert findings["lambda-python39"]["occurrences"] == 1
    assert "lambda-python310" not in findings


def test_yaml_lambda_context_does_not_cross_document_boundaries():
    audit = _load("audit_pdf")
    sources = [
        (
            "resources.yml",
            "Resources:\n"
            "  Same:\n"
            "    Type: AWS::Lambda::Function\n"
            "    Properties:\n"
            "      Runtime: nodejs20.x\n"
            "---\n"
            "Resources:\n"
            "  Same:\n"
            "    Type: Other::Thing\n"
            "    Properties:\n"
            "      Runtime: python3.9\n",
        ),
        (
            "provider.yml",
            "provider:\n" "  name: aws\n" "---\n" "provider:\n" "  runtime: python3.10\n",
        ),
        (
            "globals.yml",
            "Transform: AWS::Serverless-2016-10-31\n"
            "---\n"
            "Globals:\n"
            "  Function:\n"
            "    Runtime: python3.11\n",
        ),
    ]

    findings = {finding["id"]: finding for finding in audit._scan_sources(sources)}

    assert findings["lambda-nodejs20"]["occurrences"] == 1
    assert not any(
        finding_id in findings
        for finding_id in ("lambda-python39", "lambda-python310", "lambda-python311")
    )


def test_terraform_runtime_depth_ignores_braces_in_strings_and_supports_one_line():
    audit = _load("audit_pdf")
    findings = {
        finding["id"]: finding
        for finding in audit._scan_sources(
            [
                (
                    "strings.tf",
                    'resource "aws_lambda_function" "job" {\n'
                    '  description = "literal } in text"\n'
                    '  runtime = "python3.10"\n'
                    "}\n",
                ),
                (
                    "one-line.tf",
                    'resource "aws_lambda_function" "job" { runtime = "python3.10" }\n',
                ),
            ]
        )
    }

    assert findings["lambda-python310"]["occurrences"] == 2


def test_terraform_runtime_depth_ignores_heredoc_braces():
    audit = _load("audit_pdf")
    findings = {
        finding["id"]: finding
        for finding in audit._scan_sources(
            [
                (
                    "heredoc.tf",
                    'resource "aws_lambda_function" "job" {\n'
                    "  description = <<EOT\n"
                    "}\n"
                    "EOT\n"
                    '  runtime = "python3.10"\n'
                    "}\n",
                )
            ]
        )
    }

    assert findings["lambda-python310"]["occurrences"] == 1


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


def test_zip_member_limit_counts_directories(monkeypatch):
    audit = _load("audit_pdf")
    monkeypatch.setattr(audit, "MAX_SOURCE_FILES", 2)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("one/", b"")
        archive.writestr("two/", b"")
        archive.writestr("main.py", b"print('ok')\n")

    with pytest.raises(ValueError, match="files or directories"):
        audit._source_files(output.getvalue(), "repo.zip")


def test_zip_rejects_duplicate_normalized_source_paths():
    audit = _load("audit_pdf")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("infra\\template.yaml", "app:\n  runtime: python3.9\n")
        archive.writestr(
            "infra/template.yaml",
            "Resources:\n"
            "  Fn:\n"
            "    Type: AWS::Lambda::Function\n"
            "    Properties:\n"
            "      Runtime: python3.9\n",
        )

    with pytest.raises(ValueError, match="duplicate normalized"):
        audit._source_files(output.getvalue(), "repo.zip")


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


def test_preflight_runs_the_same_detector_used_for_the_paid_report(tmp_path, monkeypatch):
    audit = _load("audit_pdf")
    source = tmp_path / "template.yaml"
    source.write_text(
        "Resources:\n"
        "  Legacy:\n"
        "    Type: AWS::Serverless::Function\n"
        "    Properties:\n"
        "      Runtime: python3.9\n",
        encoding="utf-8",
    )
    observed: list[list[tuple[str, str]]] = []
    real_scan = audit._scan_sources

    def recording_scan(sources):
        observed.append(sources)
        return real_scan(sources)

    monkeypatch.setattr(audit, "_scan_sources", recording_scan)
    result = audit.preflight_audit_input(str(source), source.name)

    assert len(observed) == 1
    assert result["findings_count"] == 1
    assert result["evidence_count"] == 1


def test_scan_rejects_excessive_lines_and_mapping_records(monkeypatch):
    audit = _load("audit_pdf")
    monkeypatch.setattr(audit, "MAX_SCAN_LINES", 3)
    with pytest.raises(ValueError, match="line analysis limit"):
        audit._scan_sources([("large.yml", "a:\nb:\nc:\nd:\n")])

    monkeypatch.setattr(audit, "MAX_SCAN_LINES", 100)
    monkeypatch.setattr(audit, "MAX_SCAN_LINE_CHARS", 8)
    with pytest.raises(ValueError, match="character analysis limit"):
        audit._scan_sources([("large.yml", "runtime: python3.9\n")])

    monkeypatch.setattr(audit, "MAX_SCAN_LINE_CHARS", 256 * 1024)
    monkeypatch.setattr(audit, "MAX_CONFIG_RECORDS", 3)
    with pytest.raises(ValueError, match="record analysis limit"):
        audit._scan_sources([("large.yml", "a:\nb:\nc:\nd:\nruntime: python3.9\n")])

    monkeypatch.setattr(audit, "MAX_CONFIG_RECORDS", 100)
    monkeypatch.setattr(audit, "MAX_FLOW_LINE_CHARS", 128)
    with pytest.raises(ValueError, match="flow-mapping line"):
        audit._scan_sources(
            [
                (
                    "flow.yml",
                    "{"
                    + " Type: AWS::Lambda::Function," * 8
                    + " Properties: {Runtime: python3.9}}\n",
                )
            ]
        )

    monkeypatch.setattr(audit, "MAX_HCL_STRUCTURE_EVENTS", 100000)
    monkeypatch.setattr(audit, "MAX_EVIDENCE_PER_RULE", 2)
    with pytest.raises(ValueError, match="finding exceeds"):
        audit._scan_sources([("legacy.py", "import imp\nimport imp\nimport imp\n")])

    monkeypatch.setattr(audit, "MAX_FLOW_LINE_CHARS", 8192)
    monkeypatch.setattr(audit, "MAX_FLOW_RESOURCE_MATCHES", 2)
    with pytest.raises(ValueError, match="flow mapping"):
        audit._scan_sources(
            [
                (
                    "flow.yml",
                    "\n".join(
                        "Resource: {Type: AWS::Lambda::Function, "
                        "Properties: {Runtime: python3.9}}"
                        for _ in range(3)
                    ),
                )
            ]
        )

    monkeypatch.setattr(audit, "MAX_FLOW_RESOURCE_MATCHES", 100)
    monkeypatch.setattr(audit, "MAX_HCL_STRUCTURE_EVENTS", 4)
    with pytest.raises(ValueError, match="Terraform structure"):
        audit._scan_sources(
            [
                (
                    "large.tf",
                    'resource "aws_lambda_function" "job" { '
                    'runtime = "python3.10" {{{{ }}}} }\n',
                )
            ]
        )


def test_dependency_manifest_fields_are_bounded_and_root_is_an_object(monkeypatch):
    audit = _load("audit_pdf")
    with pytest.raises(ValueError, match="root must be an object"):
        audit._scan_sources([("package.json", "[]")])

    oversized = '{"dependencies":{"sharp":"' + ("1." * 200) + '"}}'
    monkeypatch.setattr(audit, "MAX_DEPENDENCY_SPEC_CHARS", 64)
    with pytest.raises(ValueError, match="at most 64 characters"):
        audit._scan_sources([("package.json", oversized)])

    monkeypatch.setattr(audit, "MAX_MANIFEST_BYTES", 32)
    with pytest.raises(ValueError, match="dependency analysis limit"):
        audit._scan_sources([("requirements.txt", "numpy==1.25.0\n" * 3)])

    monkeypatch.setattr(audit, "MAX_MANIFEST_BYTES", 1024 * 1024)
    with pytest.raises(ValueError, match="dependency findings exceed"):
        audit._scan_dependency_manifests(
            [("requirements.txt", "numpy==1.25.0\n")], evidence_budget=0
        )


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
    sources = [
        (
            "template.yaml",
            "Resources:\n"
            "  Job:\n"
            "    Type: AWS::Lambda::Function\n"
            "    Properties:\n"
            "      Runtime: nodejs20.x\n",
        )
    ]
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
        sample_manifest_url="https://eolkits.com/audit/sample/eolkits-sample-report.json",
        illustrative_sample=False,
    )

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;svg&gt;" in html


def test_report_template_labels_fictional_sample_and_pluralizes_scope():
    audit = _load("audit_pdf")
    template = Environment(
        autoescape=select_autoescape(default=True, default_for_string=True)
    ).from_string(audit.PDF_TEMPLATE)
    html = template.render(
        illustrative_sample=True,
        generated_at="now",
        report_version="2.0",
        rule_pack_version="rules",
        input_name="fictional.zip",
        input_hash="a" * 64,
        evidence_hash="b" * 64,
        total_findings=0,
        findings=[],
        categories=[],
        affected_files=0,
        scanned_files=1,
        scanned_bytes=5,
        skipped_files=1,
        evidence_lines=0,
        deadline=None,
        upcoming_deprecations=[],
        verify_url="https://eolkits.com/verify/",
        sample_manifest_url="https://eolkits.com/audit/sample/eolkits-sample-report.json",
    )

    assert "Illustrative fictional sample — EOLkits" in html
    assert "Illustrative fictional sample — AWS" in html
    assert "1 supported text file;" in html
    assert "1 unsupported/binary file was skipped" in html
    assert "eolkits-sample-report.json" in html


def test_upcoming_deprecations_use_the_report_time(monkeypatch, tmp_path):
    audit = _load("audit_pdf")
    rules = tmp_path / "deprecations.yml"
    rules.write_text(
        "deprecations:\n"
        "  - name: Before\n"
        "    date: '2026-08-21'\n"
        "    url: https://example.com/before\n"
        "  - name: On date\n"
        "    date: '2026-08-22'\n"
        "    url: https://example.com/on\n"
        "  - name: After\n"
        "    date: '2026-08-23'\n"
        "    url: https://example.com/after\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "_rules_file", lambda: rules)

    items = audit._upcoming_deprecations(datetime(2026, 8, 22, 21, tzinfo=UTC))

    assert [item["name"] for item in items] == ["On date", "After"]


def test_real_lambda_lifecycle_labels_match_the_date_kind():
    audit = _load("audit_pdf")

    items = audit._upcoming_deprecations(datetime(2026, 8, 22, 21, tzinfo=UTC))

    assert [(item["name"], item["date"]) for item in items] == [
        ("Lambda Python 3.10 — projected deprecation", "2026-10-31"),
        ("Lambda Node.js 16 — block new functions", "2027-02-01"),
        ("Lambda Node.js 18 — block new functions", "2027-02-01"),
        ("Lambda Node.js 20 — block new functions", "2027-02-01"),
        ("Lambda Python 3.8 — block new functions", "2027-02-01"),
        ("Lambda Python 3.9 — block new functions", "2027-02-01"),
        ("Lambda Node.js 22 — projected deprecation", "2027-04-30"),
        ("Lambda Python 3.11 — projected deprecation", "2027-06-30"),
    ]


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
    source.write_text(
        "Resources:\n"
        "  Job:\n"
        "    Type: AWS::Lambda::Function\n"
        "    Properties:\n"
        "      Runtime: nodejs20.x\n",
        encoding="utf-8",
    )

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
    assert package["pdf_pages"] >= 1
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
