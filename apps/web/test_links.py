"""Generated-site internal-link integrity tests."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

import build

DOCS = Path(__file__).resolve().parents[2] / "docs"
ROOT = DOCS.parent


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.values.append(value)


def _target(link: str) -> Path | None:
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    path = parsed.path
    project_base = build.PROJECT_BASE_PATH.rstrip("/")
    if project_base and (path == project_base or path.startswith(project_base + "/")):
        path = path[len(project_base) :] or "/"
    if path.startswith(("/api/", "/upload/")):
        return None
    relative = unquote(path).lstrip("/")
    candidate = DOCS / relative
    return candidate / "index.html" if path.endswith("/") else candidate


def test_generated_internal_links_resolve() -> None:
    missing: list[str] = []
    for page in sorted(DOCS.rglob("*.html")):
        parser = _Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for link in parser.values:
            target = _target(link)
            if target is not None and not target.exists():
                missing.append(f"{page.relative_to(DOCS)} -> {link}")
    assert not missing, "broken generated links:\n" + "\n".join(missing)


def test_every_generated_rule_has_a_public_source() -> None:
    deprecations = build.load_deprecations().get("deprecations", [])
    fixes = build.load_fixes()
    assert deprecations
    assert fixes
    assert all(str(item["url"]).startswith("https://") for item in deprecations)
    assert all(str(item["source_url"]).startswith("https://") for item in fixes)


def test_sitemap_locations_use_the_canonical_host() -> None:
    root = ElementTree.parse(DOCS / "sitemap.xml").getroot()
    locations = [
        element.text for element in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    assert locations
    assert all(location and location.startswith(f"{build.SITE_URL}/") for location in locations)


def test_sitemap_dates_change_only_for_materially_updated_pages() -> None:
    root = ElementTree.parse(DOCS / "sitemap.xml").getroot()
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    observed = {
        item.findtext(f"{namespace}loc"): item.findtext(f"{namespace}lastmod")
        for item in root.findall(f"{namespace}url")
    }

    assert observed[f"{build.SITE_URL}/"] == "2026-08-31"
    assert observed[f"{build.SITE_URL}/audit/"] == "2026-09-04"
    assert observed[f"{build.SITE_URL}/lambda-runtime-deprecation-schedule/"] == "2026-09-04"


def test_indexnow_key_verifies_the_entire_sitemap_scope() -> None:
    candidates = [
        path
        for path in DOCS.glob("*.txt")
        if re.fullmatch(r"[A-Za-z0-9-]{8,128}", path.stem)
        and path.read_text(encoding="utf-8").strip() == path.stem
    ]
    assert len(candidates) == 1

    root = ElementTree.parse(DOCS / "sitemap.xml").getroot()
    locations = [
        element.text for element in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    key_location = f"{build.SITE_URL}/{candidates[0].name}"
    assert key_location.startswith(f"{build.SITE_URL}/")
    assert locations
    assert all(location and location.startswith(f"{build.SITE_URL}/") for location in locations)


def test_indexnow_submission_is_scoped_to_both_verified_hosts() -> None:
    workflow = (ROOT / ".github" / "workflows" / "submit-indexnow.yml").read_text(encoding="utf-8")

    assert "branches: [main, marketing-machine-v2]" in workflow
    assert "main)\n              site_base='https://ntoledo319.github.io/EOLkits'" in workflow
    assert "marketing-machine-v2)\n              site_base='https://eolkits.com'" in workflow
    assert 'key_location="$site_base/$key.txt"' in workflow
    assert '--arg host "$site_host"' in workflow
    assert '"$site_base/sitemap.xml"' in workflow
    assert "repository evidence report is the only paid product" in workflow
    assert "Checkout stays closed unless the live API confirms report engine 2.0." in workflow
    assert "Refusing to notify search engines about retired commercial copy" in workflow
    assert "Refusing to notify search engines while an external script is injected" in workflow

    grace_verifier = (ROOT / ".github" / "workflows" / "verify-grace-static.yml").read_text(
        encoding="utf-8"
    )
    assert 'http-equiv="Content-Security-Policy"' in grace_verifier
    assert "script-src 'self' 'unsafe-inline'" in grace_verifier
    assert "An unreviewed cross-origin script is injected" in grace_verifier


def test_project_pages_links_receive_the_repository_prefix(monkeypatch) -> None:
    monkeypatch.setattr(build, "PROJECT_BASE_PATH", "/EOLkits")
    monkeypatch.setattr(build, "API_URL", "https://eolkits.com")
    html = (
        '<a href="/audit/">Audit</a>'
        '<script src="/track.js"></script>'
        '<form action="/api/events"></form>'
        '<script>fetch("/api/capabilities")</script>'
        '<script>navigator.sendBeacon("/api/events")</script>'
        '<a href="https://eolkits.com/scan/">Scanner</a>'
    )

    normalized = build.normalize_project_links(html)

    assert 'href="/EOLkits/audit/"' in normalized
    assert 'src="/EOLkits/track.js"' in normalized
    assert 'action="https://eolkits.com/api/events"' in normalized
    assert 'fetch("https://eolkits.com/api/capabilities")' in normalized
    assert 'sendBeacon("https://eolkits.com/api/events")' in normalized
    assert 'href="https://eolkits.com/scan/"' in normalized


def test_project_pages_keep_live_api_calls_on_the_api_origin(monkeypatch) -> None:
    monkeypatch.setattr(build, "SITE_URL", "https://ntoledo319.github.io/EOLkits")
    monkeypatch.setattr(build, "API_URL", "https://eolkits.com")

    status = build.build_status_page()
    widget = build.build_widget_js()
    scanner = build.build_scan_page(build.load_deprecations())

    assert "fetch('https://eolkits.com/api/status'" in status
    assert "/api/events" not in widget
    assert "meta.repo" not in widget
    assert "textContent = repo" in widget
    assert 'const SITE_BASE = "https://ntoledo319.github.io/EOLkits"' in scanner
    assert "API_BASE" not in scanner
    assert "sendBeacon('/api/" not in scanner


def test_retired_generated_surfaces_are_not_publishable() -> None:
    retired = [
        DOCS / "feed" / "manifest.json",
        DOCS / "feed" / "private-stub" / "index.json",
        DOCS / "feed" / "public" / "deprecations.yml",
        DOCS / "status" / "benchmark.json",
    ]
    retired.extend((DOCS / "blog").glob("ops-*.html"))
    assert not [path for path in retired if path.exists()]


def test_already_published_dev_drafts_are_individually_quarantined() -> None:
    drafts = sorted((ROOT / "launch" / "distribution" / "devto").glob("[0-9][0-9]-*.md"))
    assert len(drafts) == 25
    for draft in drafts:
        opening = "\n".join(draft.read_text(encoding="utf-8").splitlines()[:16])
        assert "> [!CAUTION]" in opening, draft.name
        assert "Archived launch copy — do not publish or reuse" in opening, draft.name
        assert "claims and `eolkits.com` links below may be false or stale" in opening, draft.name


def test_tracking_does_not_retain_full_referrer() -> None:
    track = (DOCS / "track.js").read_text(encoding="utf-8")
    assert "document.referrer" not in track
    assert "localStorage" not in track
    assert "sendBeacon" not in track
    assert "/api/capabilities" in track
    assert "report_version)==='2.0'" in track
    assert "credentials:'omit'" in track
    for page in DOCS.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert "ref: ref.slice" not in html
        assert "localStorage" not in html
        assert '<meta name="referrer" content="origin">' in html
        assert (
            '<meta http-equiv="Content-Security-Policy" content="'
            + build.CONTENT_SECURITY_POLICY
            + '">'
            in html
        )
        assert "stats.saiditright.com" not in html


def test_content_security_policy_blocks_unreviewed_third_party_scripts() -> None:
    policy = build.CONTENT_SECURITY_POLICY
    assert "script-src 'self' 'unsafe-inline'" in policy
    assert "connect-src 'self' https://eolkits.com" in policy
    assert "stats.saiditright.com" not in policy

    injected = build.inject_privacy_meta(
        "<html><head><title>test</title></head><body></body></html>"
    )
    assert injected.count('http-equiv="Content-Security-Policy"') == 1
    assert build.inject_privacy_meta(injected) == injected


def test_success_page_does_not_expose_a_stripe_session_identifier() -> None:
    success = (DOCS / "success" / "index.html").read_text(encoding="utf-8")
    api = (ROOT / "apps" / "grace-api" / "eolkits_grace" / "app.py").read_text(encoding="utf-8")

    assert "session_id" not in success
    assert 'success_path="/success/?sku=audit"' in api
    assert "CHECKOUT_SESSION_ID" not in api


def test_browser_tool_privacy_copy_discloses_bounded_aggregate_telemetry() -> None:
    scanner = (DOCS / "scan" / "index.html").read_text(encoding="utf-8")
    checker = (DOCS / "eol-checker" / "index.html").read_text(encoding="utf-8")
    llms = (DOCS / "llms.txt").read_text(encoding="utf-8")

    assert "File names and contents are not uploaded" in scanner
    assert "bounded aggregate counts may be sent" in scanner
    assert "finding_count" in scanner
    assert "file_count" in scanner
    assert "Pasted input stays in your browser" in checker
    assert "bounded first-party usage events may be sent" in checker
    assert "bounded aggregate file and finding counts may be sent" in llms

    public_text = (
        llms
        + "\n"
        + "\n".join(page.read_text(encoding="utf-8") for page in sorted(DOCS.rglob("*.html")))
    )
    assert "nothing uploaded" not in public_text.lower()
    assert "nothing is uploaded" not in public_text.lower()
    assert "repository-wide" not in public_text.lower()


def test_false_imds_deadline_and_unbuilt_drift_offer_stay_retired() -> None:
    imds = (DOCS / "migrate" / "imdsv1-enforcement" / "index.html").read_text(encoding="utf-8")
    drift = (DOCS / "drift" / "index.html").read_text(encoding="utf-8")

    assert 'name="robots" content="noindex,follow"' in imds
    assert "universal December 31, 2025 enforcement date that AWS does not document" in imds
    assert 'name="robots" content="noindex,follow"' in drift
    assert "No checkout · no subscription · no waitlist" in drift
    assert "$19" not in drift
    assert "auto-opened migration PR" not in drift


def test_closed_product_pages_collect_no_speculative_leads() -> None:
    for relative in ("pack/index.html", "license/index.html", "partners/index.html"):
        page = (DOCS / relative).read_text(encoding="utf-8")
        assert 'name="robots" content="noindex,follow"' in page
        assert "No checkout · no account · no waitlist" in page
        assert "/api/v1/lead" not in page
        assert "<form" not in page


def test_node_22_timeline_is_tracked_with_aws_source() -> None:
    page = (DOCS / "migrate" / "lambda-node.js-22-phase-1" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "Lambda Node.js 22 projected create/update restrictions" in page
    assert "2027-06-01" in page
    assert "2027-07-01" in page
    assert "docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html" in page


def test_future_python_runtime_dates_are_labeled_projected() -> None:
    for slug, runtime in (
        ("lambda-python-3.10-eol", "Python 3.10"),
        ("lambda-python-3.11-eol", "Python 3.11"),
    ):
        page = (DOCS / "migrate" / slug / "index.html").read_text(encoding="utf-8")
        assert f"Lambda {runtime} projected create/update restrictions" in page
        assert "AWS currently projects" in page
        assert "subject to change" in page


def test_generated_text_has_no_trailing_whitespace() -> None:
    offenders = []
    for path in sorted(item for item in DOCS.rglob("*") if item.is_file()):
        if path.suffix.lower() in {
            ".gif",
            ".jpeg",
            ".jpg",
            ".pdf",
            ".png",
            ".webp",
            ".zip",
        }:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.endswith((" ", "\t")):
                offenders.append(f"{path.relative_to(DOCS)}:{line_number}")
    assert not offenders, "generated trailing whitespace:\n" + "\n".join(offenders)


def test_commercial_inline_javascript_parses() -> None:
    for relative in ("audit/index.html", "scan/index.html", "status/index.html"):
        html = (DOCS / relative).read_text(encoding="utf-8")
        scripts = re.findall(r"<script>\s*(.*?)</script>", html, flags=re.DOTALL)
        assert scripts, f"no inline script found in {relative}"
        for script in scripts:
            checked = subprocess.run(
                ["node", "--check", "-"],
                input=script,
                text=True,
                capture_output=True,
                check=False,
            )
            assert checked.returncode == 0, f"{relative}: {checked.stderr}"


def test_audit_sample_is_a_hash_verifiable_fictional_engine_artifact() -> None:
    sample_dir = DOCS / "audit" / "sample"
    manifest = json.loads((sample_dir / "eolkits-sample-report.json").read_text())
    pdf = (sample_dir / manifest["pdf_file"]).read_bytes()
    source = (sample_dir / manifest["input_file"]).read_bytes()
    page = (sample_dir / "index.html").read_text(encoding="utf-8")

    assert manifest["fictional"] is True
    assert manifest["engine_sample_mode"] is True
    assert manifest["verification_registered"] is False
    assert manifest["pdf_pages"] == 4
    assert hashlib.sha256(pdf).hexdigest() == manifest["pdf_sha256"]
    assert hashlib.sha256(source).hexdigest() == manifest["input_sha256"]
    assert len(pdf) == manifest["pdf_bytes"]
    assert len(source) == manifest["input_bytes"]
    assert pdf.startswith(b"%PDF")
    with zipfile.ZipFile(sample_dir / manifest["input_file"]) as archive:
        assert sorted(archive.namelist()) == manifest["source_files"]
        assert all(not item.is_dir() for item in archive.infolist())

    assert f'{manifest["scanned_files"]} supported text files' in page
    assert f'{manifest["findings_count"]} distinct risk types' in page
    assert f'{manifest["evidence_count"]} file/line evidence records' in page
    assert f'{manifest["pdf_pages"]}-page engine-generated PDF' in page
    assert "Replace the two observed AL2" not in page
    assert "from $299" not in page


def test_public_pdf_and_zip_allowlist_is_exact_and_bounded() -> None:
    expected = {
        "audit/sample/eolkits-sample-report.pdf",
        "audit/sample/fictional-repository.zip",
    }
    artifacts = {
        path.relative_to(DOCS).as_posix(): path
        for path in DOCS.rglob("*")
        if path.suffix.lower() in {".pdf", ".zip"}
    }

    assert set(artifacts) == expected
    for relative, path in artifacts.items():
        assert not path.is_symlink(), relative
        assert path.is_file(), relative
        assert 0 < path.stat().st_size <= 2 * 1024 * 1024, relative


def test_public_docs_tree_contains_no_symlinks() -> None:
    symlinks = [path.relative_to(DOCS).as_posix() for path in DOCS.rglob("*") if path.is_symlink()]
    assert symlinks == []


def test_closed_checkout_ctas_describe_sample_and_availability() -> None:
    audit = (DOCS / "audit" / "index.html").read_text(encoding="utf-8")
    assert "archive-wide scanning of supported text files" in audit
    assert "severity-and-reach-ranked remediation order" in audit
    assert "Binary archive members are skipped" in audit
    assert "standalone binary inputs and archives with no supported text are rejected" in audit
    assert "binary, over-complex" not in audit
    for page in sorted((DOCS / "fix").glob("*/index.html")):
        content = page.read_text(encoding="utf-8")
        if "fix-cta" in content:
            assert "Inspect the $299 report sample and availability" in content
            assert "Get repository evidence" not in content


def test_browser_runtime_scan_requires_lambda_configuration_context() -> None:
    scanner_functions = build._SCAN_JS.split("const dz =", 1)[0]
    cases = {
        "generic": ["app.yml", "app:\n  runtime: python3.9\n"],
        "generic_cli": ["deploy.txt", "mytool deploy --runtime python3.9"],
        "generic_json": [
            "app.json",
            '{"FunctionName":"not-lambda","runtime":"python3.10"}',
        ],
        "sam": [
            "template.yaml",
            "Resources:\n"
            "  Fn:\n"
            "    Type: AWS::Serverless::Function\n"
            "    Properties:\n"
            "      Runtime: python3.9\n",
        ],
        "sam_comment": [
            "template.yaml",
            "Resources:\n"
            "  Fn:\n"
            "    Type: AWS::Serverless::Function # Lambda\n"
            "    Properties:\n"
            "      Runtime: python3.9\n",
        ],
        "minified_cfn": [
            "template.json",
            '{"Resources":{"Fn":{"Type":"AWS::Lambda::Function",'
            '"Properties":{"Runtime":"python3.9"}}}}',
        ],
        "sam_mixed": [
            "mixed.yaml",
            "Resources:\n"
            "  Real:\n"
            "    Type: AWS::Lambda::Function\n"
            "    Properties:\n"
            "      Runtime: nodejs20.x\n"
            "custom_app:\n"
            "  runtime: python3.9\n",
        ],
        "sam_cross_document": [
            "documents.yml",
            "Transform: AWS::Serverless-2016-10-31\n"
            "---\n"
            "Globals:\n"
            "  Function:\n"
            "    Runtime: python3.9\n",
        ],
        "resource_cross_document": [
            "documents.yml",
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
        ],
        "sam_globals_without_transform": [
            "globals.yml",
            "Globals:\n  Function:\n    Runtime: python3.9\n",
        ],
        "sam_globals": [
            "globals.yml",
            "Transform:\n"
            "  - AWS::Serverless-2016-10-31\n"
            "Globals:\n"
            "  Function:\n"
            "    Runtime: python3.9\n",
        ],
        "serverless": [
            "serverless.yml",
            "provider:\n  name: aws\n  runtime: python3.9\n",
        ],
        "serverless_mixed": [
            "serverless.yml",
            "provider:\n"
            "  name: aws\n"
            "  runtime: nodejs20.x\n"
            "custom:\n"
            "  runtime: python3.10\n",
        ],
        "serverless_not_aws": [
            "serverless.yml",
            "provider:\n" "  name: other\n" "functions:\n" "  fake:\n" "    runtime: python3.10\n",
        ],
        "serverless_cross_document": [
            "serverless.yml",
            "provider:\n" "  name: aws\n" "---\n" "provider:\n" "  runtime: python3.10\n",
        ],
        "terraform": [
            "main.tf",
            'resource "aws_lambda_function" "job" {\n' '  runtime = "python3.10"\n' "}\n",
        ],
        "terraform_nested": [
            "main.tf",
            'resource "aws_lambda_function" "job" {\n'
            "  environment {\n"
            '    variables = { runtime = "python3.11" }\n'
            "  }\n"
            "}\n",
        ],
        "terraform_string_brace": [
            "main.tf",
            'resource "aws_lambda_function" "job" {\n'
            '  description = "literal } in text"\n'
            '  runtime = "python3.10"\n'
            "}\n",
        ],
        "terraform_one_line": [
            "main.tf",
            'resource "aws_lambda_function" "job" { runtime = "python3.10" }\n',
        ],
        "terraform_heredoc": [
            "main.tf",
            'resource "aws_lambda_function" "job" {\n'
            "  description = <<EOT\n"
            "}\n"
            "EOT\n"
            '  runtime = "python3.10"\n'
            "}\n",
        ],
        "cdk_local": [
            "generic-stack.ts",
            "import * as lambda from 'aws-cdk-lib/aws-lambda';\n"
            "const local={runtime: 'python3.9'};\n",
        ],
        "cdk_qualified": [
            "stack.ts",
            "const fn = new lambda.Function(stack, 'Fn', "
            "{runtime: lambda.Runtime.PYTHON_3_11});\n",
        ],
        "cdk_imported": [
            "stack.py",
            "from aws_cdk.aws_lambda import Runtime\n"
            "config = dict(runtime=Runtime.PYTHON_3_11)\n",
        ],
        "aws_cli": [
            "deploy.sh",
            "aws lambda update-function-configuration --runtime python3.9\n",
        ],
    }
    script = (
        "const DATA={runtimes:{"
        "'python3.9':{severity:'high',date:'2027-02-01',kit:''},"
        "'python3.10':{severity:'high',date:'2027-02-01',kit:''},"
        "'python3.11':{severity:'medium',date:'2027-07-31',kit:''},"
        "'nodejs20.x':{severity:'high',date:'2027-02-01',kit:''}}};\n"
        + scanner_functions
        + "\nconst cases="
        + json.dumps(cases)
        + ";\nconst result=Object.fromEntries(Object.entries(cases).map("
        "([key,value])=>[key,scanIaC(value[0],value[1]).map((item)=>item.name).sort()]));"
        + "console.log(JSON.stringify(result));"
    )
    checked = subprocess.run(
        ["node", "-"], input=script, text=True, capture_output=True, check=False
    )

    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout) == {
        "aws_cli": ["python3.9"],
        "cdk_imported": ["python3.11"],
        "cdk_local": [],
        "cdk_qualified": ["python3.11"],
        "generic": [],
        "generic_cli": [],
        "generic_json": [],
        "minified_cfn": ["python3.9"],
        "resource_cross_document": ["nodejs20.x"],
        "sam": ["python3.9"],
        "sam_comment": ["python3.9"],
        "sam_cross_document": [],
        "sam_globals": ["python3.9"],
        "sam_globals_without_transform": [],
        "sam_mixed": ["nodejs20.x"],
        "serverless": ["python3.9"],
        "serverless_cross_document": [],
        "serverless_mixed": ["nodejs20.x"],
        "serverless_not_aws": [],
        "terraform": ["python3.10"],
        "terraform_heredoc": ["python3.10"],
        "terraform_nested": [],
        "terraform_one_line": ["python3.10"],
        "terraform_string_brace": ["python3.10"],
    }
