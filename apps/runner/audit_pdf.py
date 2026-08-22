"""Evidence-based AWS deprecation audit report generation.

The report is deliberately a static source scan. It does not claim to inventory a
live AWS account, predict downtime cost, or sign the rendered PDF. Instead it
records exact file/line evidence, configured references, the uploaded-byte hash, and a
deterministic evidence fingerprint that can be recomputed from the same input and
rule pack.
"""

from __future__ import annotations

import base64
import hashlib
import io
import ipaddress
import json
import os
import re
import socket
import unicodedata
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Optional
from urllib.parse import urlparse

import requests
import yaml
from jinja2 import Environment, select_autoescape

MAX_INPUT_BYTES = int(os.environ.get("EOLKITS_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_EXPANDED_BYTES = int(os.environ.get("EOLKITS_MAX_EXPANDED_BYTES", str(25 * 1024 * 1024)))
MAX_SOURCE_FILES = int(os.environ.get("EOLKITS_MAX_SOURCE_FILES", "2000"))
MAX_ZIP_RATIO = int(os.environ.get("EOLKITS_MAX_ZIP_RATIO", "100"))
MAX_ZIP_NAME_BYTES = int(os.environ.get("EOLKITS_MAX_ZIP_NAME_BYTES", str(1024 * 1024)))
MAX_SCAN_LINES = int(os.environ.get("EOLKITS_MAX_SCAN_LINES", "500000"))
MAX_CONFIG_RECORDS = int(os.environ.get("EOLKITS_MAX_CONFIG_RECORDS", "100000"))
MAX_LAMBDA_RESOURCES = int(os.environ.get("EOLKITS_MAX_LAMBDA_RESOURCES", "10000"))
MAX_FLOW_LINE_CHARS = int(os.environ.get("EOLKITS_MAX_FLOW_LINE_CHARS", "8192"))
MAX_FLOW_RESOURCE_MATCHES = int(os.environ.get("EOLKITS_MAX_FLOW_RESOURCE_MATCHES", "100"))
MAX_HCL_STRUCTURE_EVENTS = int(os.environ.get("EOLKITS_MAX_HCL_STRUCTURE_EVENTS", "100000"))
MAX_SCAN_LINE_CHARS = int(os.environ.get("EOLKITS_MAX_SCAN_LINE_CHARS", str(256 * 1024)))
MAX_EVIDENCE_RECORDS = int(os.environ.get("EOLKITS_MAX_EVIDENCE_RECORDS", "10000"))
MAX_EVIDENCE_PER_RULE = int(os.environ.get("EOLKITS_MAX_EVIDENCE_PER_RULE", "2000"))
MAX_MANIFEST_BYTES = int(os.environ.get("EOLKITS_MAX_MANIFEST_BYTES", str(1024 * 1024)))
MAX_DEPENDENCY_SPEC_CHARS = int(os.environ.get("EOLKITS_MAX_DEPENDENCY_SPEC_CHARS", "256"))
MAX_LOCATIONS_PER_FINDING = 25
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "https://eolkits.com")
ALLOWED_UPLOAD_ORIGIN = os.environ.get("EOLKITS_ALLOWED_UPLOAD_ORIGIN", PUBLIC_SITE_URL).rstrip("/")
REPORT_VERSION = "2.0"
RULESET_VERSION = "audit-v2-2026-08-22.2"

SUPPORTED_SUFFIXES = {
    ".bash",
    ".cjs",
    ".conf",
    ".hcl",
    ".ini",
    ".js",
    ".json",
    ".lock",
    ".mjs",
    ".properties",
    ".py",
    ".sh",
    ".tf",
    ".tfvars",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SUPPORTED_BASENAMES = {
    "dockerfile",
    "gemfile",
    "makefile",
    "package.json",
    "pipfile",
    "requirements.txt",
    "serverless.yml",
    "serverless.yaml",
}

AWS_LAMBDA_SOURCE = "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html"
AWS_LAMBDA_NODE_SOURCE = "https://docs.aws.amazon.com/lambda/latest/dg/lambda-nodejs.html"
AWS_AL2023_SOURCE = "https://docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html"
AWS_IMDS_SOURCE = (
    "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html"
)


def _dependency_rules_file() -> Path:
    configured = os.environ.get("EOLKITS_DEPENDENCY_RULES_FILE")
    candidates = [
        Path(configured) if configured else None,
        Path(__file__).resolve().parents[2] / "rules" / "public" / "dependency-compatibility.json",
        Path("/app/rules/public/dependency-compatibility.json"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise RuntimeError("dependency compatibility rule pack is missing")


def _load_dependency_rules() -> tuple[dict[str, Any], dict[str, Any]]:
    data = json.loads(_dependency_rules_file().read_text(encoding="utf-8"))
    node = data.get("node_native")
    python = data.get("python_312_wheels")
    if not isinstance(node, dict) or not isinstance(python, dict):
        raise RuntimeError("dependency compatibility rule pack is invalid")
    return node, python


NODE_NATIVE_PACKAGES, PY312_WHEELS = _load_dependency_rules()


AUDIT_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "lambda-nodejs16",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Node.js 16 runtime reference",
        "patterns": (r"\bnodejs16\.x\b", r"\bNODEJS_16_X\b"),
        "requires_lambda_context": True,
        "runtime_id": "nodejs16.x",
        "description": "Node.js 16 is a retired Lambda runtime. Deploy operations may be blocked.",
        "remediation": "Move the function to a currently supported Lambda Node.js runtime, rebuild native dependencies, and run its tests before deployment.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-nodejs18",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Node.js 18 runtime reference",
        "patterns": (r"\bnodejs18\.x\b", r"\bNODEJS_18_X\b"),
        "requires_lambda_context": True,
        "runtime_id": "nodejs18.x",
        "description": "Node.js 18 is deprecated in Lambda and no longer receives runtime updates.",
        "remediation": "Move to a currently supported Lambda Node.js runtime and validate SDK and native-addon compatibility.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-nodejs20",
        "category": "Lambda runtime",
        "severity": "high",
        "title": "Lambda Node.js 20 runtime reference",
        "patterns": (r"\bnodejs20\.x\b", r"\bNODEJS_20_X\b"),
        "requires_lambda_context": True,
        "runtime_id": "nodejs20.x",
        "description": "Node.js 20 is in Lambda's deprecation lifecycle; AWS publishes the applicable create/update block dates in its runtime table.",
        "remediation": "Plan a move to a currently supported Lambda Node.js runtime, then test native modules, OpenSSL behavior, and deployment packaging.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-nodejs22",
        "category": "Lambda runtime",
        "severity": "medium",
        "title": "Lambda Node.js 22 runtime reference",
        "patterns": (r"\bnodejs22\.x\b", r"\bNODEJS_22_X\b"),
        "requires_lambda_context": True,
        "runtime_id": "nodejs22.x",
        "description": "AWS publishes a projected 2027 deprecation and create/update block timeline for Node.js 22.",
        "remediation": "Plan and test a move to Node.js 24 while Node.js 22 still has runway; recheck AWS's current dates before scheduling the change.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python38",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Python 3.8 runtime reference",
        "patterns": (
            r"\bruntime\b[\"']?\s*[:=]\s*[\"']?\s*\bpython3\.8\b",
            r"\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)[\"']?python3\.8\b",
            r"\bRuntime\.PYTHON_3_8\b",
        ),
        "requires_lambda_context": True,
        "runtime_id": "python3.8",
        "description": "Python 3.8 is a retired Lambda runtime.",
        "remediation": "Move to a supported Python runtime and test removed standard-library modules and native wheels before deployment.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python39",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Python 3.9 runtime reference",
        "patterns": (
            r"\bruntime\b[\"']?\s*[:=]\s*[\"']?\s*\bpython3\.9\b",
            r"\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)[\"']?python3\.9\b",
            r"\bRuntime\.PYTHON_3_9\b",
        ),
        "requires_lambda_context": True,
        "runtime_id": "python3.9",
        "description": "Python 3.9 is deprecated in Lambda and no longer receives runtime updates.",
        "remediation": "Move to a supported Python runtime and resolve Python 3.12+ compatibility findings before deployment.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python310",
        "category": "Lambda runtime",
        "severity": "high",
        "title": "Lambda Python 3.10 runtime reference",
        "patterns": (
            r"\bruntime\b[\"']?\s*[:=]\s*[\"']?\s*\bpython3\.10\b",
            r"\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)[\"']?python3\.10\b",
            r"\bRuntime\.PYTHON_3_10\b",
        ),
        "requires_lambda_context": True,
        "runtime_id": "python3.10",
        "description": "Python 3.10 has a published Lambda deprecation timeline.",
        "remediation": "Schedule the runtime move while there is test runway; check removed modules, typing changes, and native wheels.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python311",
        "category": "Lambda runtime",
        "severity": "medium",
        "title": "Lambda Python 3.11 runtime reference",
        "patterns": (
            r"\bruntime\b[\"']?\s*[:=]\s*[\"']?\s*\bpython3\.11\b",
            r"\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)[\"']?python3\.11\b",
            r"\bRuntime\.PYTHON_3_11\b",
        ),
        "requires_lambda_context": True,
        "runtime_id": "python3.11",
        "description": "Python 3.11 has a published Lambda deprecation timeline.",
        "remediation": "Track the AWS deadline and test the next supported runtime before the block window.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "amazon-linux-2",
        "category": "Operating system",
        "severity": "critical",
        "title": "Amazon Linux 2 dependency",
        "patterns": (
            r"\bamazonlinux\s*:\s*2(?:\b|$)",
            r"\bamazon-linux-2\b",
            r"\bamzn2(?:-ami)?\b",
            r"\blatestAmazonLinux2\b",
            r"\bEKS_AL2\b",
        ),
        "description": "Amazon Linux 2 has reached end of life. Continued operation and any temporary support updates do not replace a migration plan.",
        "remediation": "Move the image or host build to Amazon Linux 2023, then validate package names, service names, firewall rules, and application dependencies.",
        "source_url": "https://aws.amazon.com/amazon-linux-2/faqs/",
    },
    {
        "id": "amazon-linux-extras",
        "category": "AL2023 compatibility",
        "severity": "high",
        "title": "amazon-linux-extras command removed in AL2023",
        "patterns": (r"\bamazon-linux-extras\b",),
        "description": "Amazon Linux 2023 does not provide the Amazon Linux Extras mechanism.",
        "remediation": "Replace the Extras topic with the corresponding dnf package, versioned package, or supported repository.",
        "source_url": AWS_AL2023_SOURCE,
    },
    {
        "id": "al2023-ntpd",
        "category": "AL2023 compatibility",
        "severity": "high",
        "title": "ntpd service reference incompatible with AL2023",
        "patterns": (r"\bntpd(?:\.service)?\b",),
        "description": "Amazon Linux 2023 uses chrony rather than the ntpd service used by older builds.",
        "remediation": "Migrate the configuration to chronyd and verify time synchronization with chronyc.",
        "source_url": AWS_AL2023_SOURCE,
    },
    {
        "id": "al2023-iptables-service",
        "category": "AL2023 compatibility",
        "severity": "high",
        "title": "iptables.service reference incompatible with AL2023",
        "patterns": (r"\biptables(?:-services|\.service)\b",),
        "description": "Amazon Linux 2023 uses nftables and does not provide the old iptables service by default.",
        "remediation": "Translate and persist rules with nftables, or explicitly validate an iptables-nft compatibility path.",
        "source_url": AWS_AL2023_SOURCE,
    },
    {
        "id": "aws-sdk-v2",
        "category": "Node.js compatibility",
        "severity": "high",
        "title": "AWS SDK for JavaScript v2 dependency",
        "patterns": (
            r"(?:require\s*\(\s*|from\s+|import\s+)[\"']aws-sdk[\"']",
            r"[\"']aws-sdk[\"']\s*:\s*[\"']",
        ),
        "description": "Lambda Node.js 18 and later do not bundle aws-sdk v2. A runtime-only upgrade can therefore fail at cold start.",
        "remediation": "Migrate to modular @aws-sdk/* v3 clients, or explicitly bundle v2 as a temporary compatibility step.",
        "source_url": AWS_LAMBDA_NODE_SOURCE,
    },
    {
        "id": "node-sass",
        "category": "Node.js compatibility",
        "severity": "high",
        "title": "Deprecated node-sass dependency",
        "patterns": (r"[\"']node-sass[\"']", r"\brequire\s*\(\s*[\"']node-sass[\"']\s*\)"),
        "description": "Node Sass/LibSass is end-of-life and lacks support for current Node runtimes.",
        "remediation": "Replace node-sass with Dart Sass (`sass`) and re-run the stylesheet build on the target Node runtime.",
        "source_url": "https://sass-lang.com/blog/libsass-is-deprecated/",
    },
    {
        "id": "node-createcipher",
        "category": "Node.js compatibility",
        "severity": "critical",
        "title": "Removed Node.js crypto API",
        "patterns": (r"\bcrypto\.(?:createCipher|createDecipher)\s*\(",),
        "description": "createCipher/createDecipher are removed in current Node.js releases and use an unsafe legacy key derivation.",
        "remediation": "Use createCipheriv/createDecipheriv with an explicit modern KDF, salt, key, and random IV; plan a legacy-data migration if needed.",
        "source_url": "https://nodejs.org/api/deprecations.html#dep0106-cryptocreatecipher-and-cryptocreatedecipher",
    },
    {
        "id": "python-distutils",
        "category": "Python compatibility",
        "severity": "critical",
        "title": "distutils removed in Python 3.12",
        "patterns": (r"^\s*(?:from|import)\s+distutils\b", r"\bdistutils\."),
        "description": "Python 3.12 removed distutils from the standard library.",
        "remediation": "Replace distutils usage with setuptools and packaging, and upgrade dependencies that still import it.",
        "source_url": "https://docs.python.org/3/whatsnew/3.12.html#distutils",
    },
    {
        "id": "python-imp",
        "category": "Python compatibility",
        "severity": "critical",
        "title": "imp module removed in Python 3.12",
        "patterns": (
            r"^\s*(?:from|import)\s+imp\b",
            r"\bimp\.(?:find_module|load_module|reload)\b",
        ),
        "description": "Python 3.12 removed the deprecated imp module.",
        "remediation": "Move module loading to importlib and upgrade dependencies that still import imp.",
        "source_url": "https://docs.python.org/3/whatsnew/3.12.html#imp",
    },
    {
        "id": "python-collections-abc",
        "category": "Python compatibility",
        "severity": "high",
        "title": "Removed collections ABC alias",
        "patterns": (
            r"\bcollections\.(?:Mapping|MutableMapping|Sequence|MutableSequence|Iterable|Iterator|Callable)\b",
        ),
        "description": "Legacy collections ABC aliases were removed; code fails on modern Python runtimes.",
        "remediation": "Import the affected abstract base class from collections.abc and upgrade stale dependencies.",
        "source_url": "https://docs.python.org/3/whatsnew/3.10.html#removed",
    },
    {
        "id": "python-asyncio-coroutine",
        "category": "Python compatibility",
        "severity": "high",
        "title": "asyncio.coroutine removed in Python 3.11",
        "patterns": (r"@?asyncio\.coroutine\b",),
        "description": "The legacy generator-based asyncio.coroutine API was removed in Python 3.11.",
        "remediation": "Rewrite generator-based coroutines with async def/await and upgrade affected dependencies.",
        "source_url": "https://docs.python.org/3/whatsnew/3.11.html#removed",
    },
    {
        "id": "python-datetime-utcnow",
        "category": "Python compatibility",
        "severity": "medium",
        "title": "Naive UTC datetime API",
        "patterns": (r"\bdatetime\.utcnow\s*\(",),
        "description": "datetime.utcnow() is deprecated in modern Python because it returns a naive datetime.",
        "remediation": "Use datetime.now(datetime.UTC) (or timezone.utc) and confirm downstream serialization expects an aware datetime.",
        "source_url": "https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow",
    },
    {
        "id": "imdsv1-request",
        "category": "EC2 metadata security",
        "severity": "high",
        "title": "Possible IMDSv1 metadata request",
        "patterns": (r"https?://169\.254\.169\.254/latest/meta-data",),
        "description": "A direct metadata URL is evidence of a possible IMDSv1 call. Static analysis cannot determine whether a token header is added elsewhere.",
        "remediation": "Require IMDSv2 on the instance or launch template and fetch a session token before metadata requests.",
        "source_url": AWS_IMDS_SOURCE,
    },
)

SEVERITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}


PDF_TEMPLATE = """
<!DOCTYPE html><html><head><meta charset="utf-8"><title>{% if illustrative_sample %}Illustrative fictional sample — {% endif %}EOLkits AWS Deprecation Evidence Report</title>
<style>
@page{margin:1.6cm;@bottom-center{content:"EOLkits · " counter(page) " / " counter(pages);color:#6b7280;font-size:8pt}}body{font-family:"DejaVu Sans",sans-serif;color:#111827;line-height:1.45;font-size:10.5pt}h1{color:#1f2937;border-bottom:3px solid #2563eb;padding-bottom:.45rem}h2{color:#1f2937;margin-top:1.7rem;border-bottom:1px solid #d1d5db;padding-bottom:.25rem;break-after:avoid}h3{margin-bottom:.35rem}a{color:#1d4ed8}code{background:#f3f4f6;padding:.1rem .25rem;border-radius:3px;font-family:"DejaVu Sans Mono",monospace;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;margin:.8rem 0}th,td{padding:.55rem;text-align:left;border-bottom:1px solid #e5e7eb;vertical-align:top}th{background:#f9fafb}.meta,.scope,.verification,.limitation{padding:.85rem 1rem;border-radius:7px;margin:.8rem 0}.meta,.scope{background:#f9fafb}.verification{background:#eff6ff;break-inside:avoid}.limitation{background:#fffbeb;border:1px solid #fde68a;break-inside:avoid}.finding{break-inside:avoid;border-left:4px solid #d1d5db;padding:0 0 .7rem .9rem;margin:1rem 0}.severity{display:inline-block;padding:.12rem .4rem;border-radius:4px;font-size:8.5pt;font-weight:700;text-transform:uppercase}.critical{background:#fee2e2;color:#991b1b}.high{background:#ffedd5;color:#9a3412}.medium{background:#fef3c7;color:#92400e}.low{background:#dcfce7;color:#166534}.evidence{font-family:"DejaVu Sans Mono",monospace;font-size:8.5pt;overflow-wrap:anywhere}.muted{color:#6b7280;font-size:9pt}
</style></head><body>
<section class="cover"><h1>{% if illustrative_sample %}Illustrative fictional sample — {% endif %}AWS Deprecation Evidence Report</h1>
{% if illustrative_sample %}<div class="limitation"><strong>ILLUSTRATIVE SAMPLE.</strong> This report was generated from a published fictional repository fixture. It is not a customer report or evidence of a live AWS account scan.</div>{% endif %}
<div class="meta"><p><strong>Generated:</strong> {{ generated_at }}</p><p><strong>Report engine:</strong> {{ report_version }}</p><p><strong>Rule pack:</strong> {{ rule_pack_version }}</p><p><strong>Uploaded artifact:</strong> <code>{{ input_name }}</code></p><p><strong>Input SHA-256:</strong> <code>{{ input_hash }}</code></p><p><strong>Evidence fingerprint:</strong> <code>{{ evidence_hash }}</code></p></div>
<h2>Executive summary</h2><p>The static scan found <strong>{{ total_findings }} distinct risk type{% if total_findings != 1 %}s{% endif %}</strong> across <strong>{{ affected_files }}</strong> of {{ scanned_files }} scanned source files, supported by {{ evidence_lines }} file/line evidence record{% if evidence_lines != 1 %}s{% endif %}.</p>
{% if deadline %}<p><strong>Buyer-supplied target date:</strong> {{ deadline }}. This date is context only; it does not alter scan results.</p>{% endif %}
{% if categories %}<table><thead><tr><th>Category</th><th>Risk types</th><th>Evidence records</th></tr></thead><tbody>{% for category in categories %}<tr><td>{{ category.name }}</td><td>{{ category.count }}</td><td>{{ category.evidence_count }}</td></tr>{% endfor %}</tbody></table>{% else %}<p>No configured rule matched the supplied files. This is not proof that the repository or AWS account is free of deprecation risk.</p>{% endif %}
<div class="scope"><strong>Observed scope:</strong> {{ scanned_files }} supported text file{% if scanned_files != 1 %}s{% endif %}; {{ scanned_bytes }} decoded bytes.{% if skipped_files %} {{ skipped_files }} unsupported/binary file{% if skipped_files != 1 %}s were{% else %} was{% endif %} skipped.{% endif %}</div>
<div class="limitation"><strong>Important limitation:</strong> This is a static scan of the uploaded artifact. It does not query a live AWS account, execute code, prove exploitability, inspect files that were not uploaded, or guarantee a complete resource inventory. Validate every recommended change in a non-production environment.</div></section>
<h2>Prioritized findings</h2>{% if not findings %}<p>No configured evidence pattern matched.</p>{% endif %}
{% for finding in findings %}<section class="finding"><h3><span class="severity {{ finding.severity }}">{{ finding.severity }}</span> {{ finding.title }}</h3><p>{{ finding.description }}</p><p><strong>Observed reach:</strong> {{ finding.affected_files }} file{% if finding.affected_files != 1 %}s{% endif %}, {{ finding.occurrences }} evidence line{% if finding.occurrences != 1 %}s{% endif %}.</p><p><strong>Remediation:</strong> {{ finding.remediation }}</p><p><strong>Rule or package reference:</strong> <a href="{{ finding.source_url }}">{{ finding.source_url }}</a></p><table><thead><tr><th>Location</th><th>Observed text</th></tr></thead><tbody>{% for location in finding.locations %}<tr><td><code>{{ location.file }}:{{ location.line }}</code></td><td class="evidence">{{ location.evidence }}</td></tr>{% endfor %}</tbody></table>{% if finding.omitted_locations %}<p class="muted">{{ finding.omitted_locations }} additional evidence locations omitted from the PDF.</p>{% endif %}</section>{% endfor %}
<h2>Roll-forward order</h2>{% if findings %}<ol>{% for finding in findings %}<li><strong>{{ finding.title }}</strong> — {{ finding.remediation }}</li>{% endfor %}</ol>{% else %}<p>Confirm the upload was complete, then compare deployed AWS inventory with the current AWS runtime and operating-system support tables.</p>{% endif %}
{% if upcoming_deprecations %}<h2>Tracked AWS dates</h2><p class="muted">Dates below come from the cited public rule pack and should be rechecked before production planning.</p><ul>{% for dep in upcoming_deprecations %}<li><strong>{{ dep.name }}</strong> — {{ dep.date }} — <a href="{{ dep.url }}">source</a></li>{% endfor %}</ul>{% endif %}
{% if illustrative_sample %}<div class="verification"><h2>Sample evidence fingerprint</h2><p>This fictional sample fingerprint is intentionally not registered in the customer verification store. The <a href="{{ sample_manifest_url }}">published sample manifest</a> records the input and PDF hashes so the artifact can still be checked byte-for-byte.</p><p class="muted">The evidence fingerprint covers the input hash, report-engine/rule-pack versions, and canonical findings. It is not a digital signature of the PDF file.</p></div>{% else %}<div class="verification"><h2>Evidence verification</h2><p>Look up the evidence fingerprint at <a href="{{ verify_url }}">{{ verify_url }}</a>.</p><p class="muted">The fingerprint covers the input hash, report-engine/rule-pack versions, and canonical findings. It is not a digital signature of the PDF file.</p></div>{% endif %}
</body></html>
"""


def generate_audit_pdf(
    upload_url: Optional[str],
    email: str,
    deadline: Optional[str] = None,
    output_path: Optional[str] = None,
    upload_path: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """Generate a PDF on disk for callers that need a path."""
    package = generate_audit_package(
        upload_url=upload_url,
        email=email,
        deadline=deadline,
        output_path=output_path,
        upload_path=upload_path,
        filename=filename,
    )
    if package["pdf_path"]:
        return str(package["pdf_path"])
    target = Path.cwd() / f"audit_{package['evidence_hash'][:12]}.pdf"
    target.write_bytes(base64.b64decode(package["pdf_base64"]))
    return str(target)


def generate_audit_package(
    upload_url: Optional[str],
    email: str,
    deadline: Optional[str] = None,
    output_path: Optional[str] = None,
    upload_path: Optional[str] = None,
    filename: Optional[str] = None,
    report_time: Optional[datetime] = None,
    illustrative_sample: bool = False,
) -> dict[str, Any]:
    """Generate a PDF and the metadata required for delivery/verification."""
    from weasyprint import HTML

    input_content = _read_input(upload_path, upload_url)
    input_hash = hashlib.sha256(input_content).hexdigest()
    input_name = _safe_input_name(filename, upload_path, upload_url)
    sources, skipped_files = _source_files(input_content, input_name)
    findings = _scan_sources(sources)
    rule_pack_version = _rule_pack_version()
    evidence_hash = _evidence_fingerprint(input_hash, rule_pack_version, findings)
    if report_time is not None and report_time.tzinfo is None:
        raise ValueError("report_time must include a timezone")
    generated = report_time.astimezone(UTC) if report_time is not None else datetime.now(UTC)
    categories = _summarize_categories(findings)
    affected_files = len({loc["file"] for finding in findings for loc in finding["locations_all"]})
    evidence_lines = sum(finding["occurrences"] for finding in findings)
    public_findings = [
        {key: value for key, value in finding.items() if key != "locations_all"}
        for finding in findings
    ]

    template = Environment(
        autoescape=select_autoescape(default=True, default_for_string=True)
    ).from_string(PDF_TEMPLATE)
    html_content = template.render(
        generated_at=generated.strftime("%Y-%m-%d %H:%M UTC"),
        report_version=REPORT_VERSION,
        rule_pack_version=rule_pack_version,
        input_name=input_name,
        input_hash=input_hash,
        evidence_hash=evidence_hash,
        total_findings=len(public_findings),
        findings=public_findings,
        categories=categories,
        affected_files=affected_files,
        scanned_files=len(sources),
        scanned_bytes=sum(len(content.encode("utf-8")) for _, content in sources),
        skipped_files=skipped_files,
        evidence_lines=evidence_lines,
        deadline=_valid_deadline(deadline),
        upcoming_deprecations=_upcoming_deprecations(generated),
        verify_url=f"{PUBLIC_SITE_URL}/verify/?hash={evidence_hash}",
        sample_manifest_url=(
            f"{PUBLIC_SITE_URL.rstrip('/')}/audit/sample/eolkits-sample-report.json"
        ),
        illustrative_sample=illustrative_sample,
    )
    rendered_document = HTML(string=html_content, base_url=PUBLIC_SITE_URL).render()
    pdf_pages = len(rendered_document.pages)
    pdf_bytes = rendered_document.write_pdf()
    if output_path:
        Path(output_path).write_bytes(pdf_bytes)
    return {
        "pdf_path": output_path,
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        "email": email,
        "input_hash": input_hash,
        "evidence_hash": evidence_hash,
        "rule_pack_version": rule_pack_version,
        "report_version": REPORT_VERSION,
        "pdf_pages": pdf_pages,
        "generated_at": generated.isoformat().replace("+00:00", "Z"),
        "findings_count": len(public_findings),
        "evidence_count": evidence_lines,
        "scanned_files": len(sources),
        "skipped_files": skipped_files,
        "illustrative_sample": illustrative_sample,
    }


def preflight_audit_input(upload_path: str, filename: str | None = None) -> dict[str, Any]:
    """Validate the exact local bytes before a Checkout Session may be created."""
    content = _read_local_input(upload_path)
    input_name = _safe_input_name(filename, upload_path, None)
    sources, skipped = _source_files(content, input_name)
    findings = _scan_sources(sources)
    return {
        "input_hash": hashlib.sha256(content).hexdigest(),
        "scanned_files": len(sources),
        "skipped_files": skipped,
        "decoded_bytes": sum(len(body.encode("utf-8")) for _, body in sources),
        "findings_count": len(findings),
        "evidence_count": sum(int(finding["occurrences"]) for finding in findings),
    }


def _read_input(upload_path: Optional[str], upload_url: Optional[str]) -> bytes:
    if upload_path:
        return _read_local_input(upload_path)
    if upload_url:
        return _download_input(upload_url)
    raise ValueError("upload_path or upload_url is required")


def _read_local_input(path: str) -> bytes:
    if not os.path.isfile(path):
        raise ValueError("upload not found")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise ValueError("upload too large")
    with open(path, "rb") as handle:
        return handle.read()


def _assert_public_host(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"cannot resolve upload host: {hostname}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(f"refusing to fetch upload from non-public address: {ip}")


def _download_input(upload_url: Optional[str]) -> bytes:
    if not upload_url:
        raise ValueError("upload_url is required")
    parsed = urlparse(upload_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("upload_url must be a valid http(s) URL")
    allowed = urlparse(ALLOWED_UPLOAD_ORIGIN)
    if (
        parsed.scheme != allowed.scheme
        or parsed.hostname != allowed.hostname
        or parsed.port != allowed.port
        or parsed.username
        or parsed.password
    ):
        raise ValueError("upload_url origin is not allowed")
    _assert_public_host(parsed.hostname)
    # Redirects are rejected: validating only the first hostname and then
    # following a redirect would reopen SSRF access to private/link-local hosts.
    response = requests.get(upload_url, timeout=30, stream=True, allow_redirects=False)
    if 300 <= response.status_code < 400:
        raise ValueError("upload URL redirects are not allowed")
    response.raise_for_status()
    chunks = bytearray()
    for chunk in response.iter_content(8192):
        chunks.extend(chunk)
        if len(chunks) > MAX_INPUT_BYTES:
            raise ValueError("upload too large")
    return bytes(chunks)


def _safe_input_name(
    filename: Optional[str], upload_path: Optional[str], upload_url: Optional[str]
) -> str:
    candidate = filename
    if not candidate and upload_path:
        candidate = Path(upload_path).name
    if not candidate and upload_url:
        candidate = Path(urlparse(upload_url).path).name
    return Path(candidate or "uploaded-input.txt").name[:240]


def _source_files(input_content: bytes, input_name: str) -> tuple[list[tuple[str, str]], int]:
    if zipfile.is_zipfile(io.BytesIO(input_content)):
        return _zip_source_files(input_content)
    if input_name.lower().endswith(".zip"):
        raise ValueError("file has a .zip name but is not a valid ZIP archive")
    if not _supported_source_name(input_name):
        raise ValueError("file type is not supported for source analysis")
    if b"\x00" in input_content[:8192]:
        raise ValueError("binary files are not supported for source analysis")
    return [(input_name, input_content.decode("utf-8", errors="replace"))], 0


def _zip_source_files(input_content: bytes) -> tuple[list[tuple[str, str]], int]:
    sources: list[tuple[str, str]] = []
    skipped = 0
    total_uncompressed = 0
    with zipfile.ZipFile(io.BytesIO(input_content)) as archive:
        all_members = archive.infolist()
        if len(all_members) > MAX_SOURCE_FILES:
            raise ValueError(f"archive contains more than {MAX_SOURCE_FILES} files or directories")
        if (
            sum(len(member.filename.encode("utf-8", errors="replace")) for member in all_members)
            > MAX_ZIP_NAME_BYTES
        ):
            raise ValueError("archive member names exceed the analysis limit")
        members = [member for member in all_members if not member.is_dir()]
        normalized_names: set[str] = set()
        for member in members:
            normalized = unicodedata.normalize(
                "NFC", str(PurePosixPath(member.filename.replace("\\", "/")))
            ).casefold()
            if normalized in normalized_names:
                raise ValueError("archive contains duplicate normalized file paths")
            normalized_names.add(normalized)
        for member in members:
            name = member.filename.replace("\\", "/")
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("archive contains an unsafe path")
            if member.flag_bits & 0x1:
                raise ValueError("encrypted archives are not supported")
            total_uncompressed += member.file_size
            if total_uncompressed > MAX_EXPANDED_BYTES:
                raise ValueError("archive expands beyond the upload limit")
            if (
                member.file_size > 1024 * 1024
                and member.file_size > max(member.compress_size, 1) * MAX_ZIP_RATIO
            ):
                raise ValueError("archive contains a suspicious compression ratio")
            if not _supported_source_name(name):
                skipped += 1
                continue
            raw = archive.read(member)
            if b"\x00" in raw[:8192]:
                skipped += 1
                continue
            sources.append((name[:500], raw.decode("utf-8", errors="replace")))
    if not sources:
        raise ValueError("archive contains no supported text source files")
    return sorted(sources, key=lambda item: item[0]), skipped


def _supported_source_name(name: str) -> bool:
    lower_name = PurePosixPath(name).name.lower()
    return lower_name in SUPPORTED_BASENAMES or any(
        lower_name.endswith(suffix) for suffix in SUPPORTED_SUFFIXES
    )


def _scan_sources(sources: list[tuple[str, str]]) -> list[dict[str, Any]]:
    normalized_names = [
        unicodedata.normalize("NFC", str(PurePosixPath(filename))).casefold()
        for filename, _ in sources
    ]
    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError("source input contains duplicate normalized file paths")
    total_lines = 0
    for _, content in sources:
        start = 0
        while True:
            end = content.find("\n", start)
            line_end = len(content) if end < 0 else end
            if line_end - start > MAX_SCAN_LINE_CHARS:
                raise ValueError(
                    f"source line exceeds the {MAX_SCAN_LINE_CHARS}-character analysis limit"
                )
            total_lines += 1
            if total_lines > MAX_SCAN_LINES:
                raise ValueError(f"source input exceeds the {MAX_SCAN_LINES}-line analysis limit")
            if end < 0:
                break
            start = end + 1
    findings: list[dict[str, Any]] = []
    evidence_records = 0
    lambda_runtime_records = {
        filename: (
            _lambda_runtime_records(filename, content)
            if re.search(
                r"(?:nodejs(?:16|18|20|22)\.x|python3\.(?:8|9|10|11))\b|"
                r"Runtime\.(?:NODEJS_(?:16|18|20|22)_X|PYTHON_3_(?:8|9|10|11))\b",
                content,
                re.IGNORECASE,
            )
            else set()
        )
        for filename, content in sources
    }
    for rule in AUDIT_RULES:
        compiled = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in rule["patterns"]
        ]
        locations: list[dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        for filename, content in sources:
            for line_number, line in enumerate(content.splitlines(), start=1):
                match = next(
                    (candidate for pattern in compiled if (candidate := pattern.search(line))),
                    None,
                )
                if not match:
                    continue
                if (
                    rule.get("requires_lambda_context")
                    and (
                        line_number,
                        str(rule["runtime_id"]),
                    )
                    not in lambda_runtime_records[filename]
                ):
                    continue
                key = (filename, line_number)
                if key in seen:
                    continue
                evidence_records += 1
                if len(locations) >= MAX_EVIDENCE_PER_RULE:
                    raise ValueError(
                        f"a finding exceeds the {MAX_EVIDENCE_PER_RULE}-record analysis limit"
                    )
                if evidence_records > MAX_EVIDENCE_RECORDS:
                    raise ValueError(
                        f"source findings exceed the {MAX_EVIDENCE_RECORDS}-record analysis limit"
                    )
                seen.add(key)
                locations.append(
                    {
                        "file": filename,
                        "line": line_number,
                        "evidence": _compact_evidence(line, match.start()),
                    }
                )
        if not locations:
            continue
        severity = str(rule["severity"])
        findings.append(
            {
                "id": rule["id"],
                "category": rule["category"],
                "severity": severity,
                "severity_weight": SEVERITY_WEIGHT[severity],
                "title": rule["title"],
                "description": rule["description"],
                "remediation": rule["remediation"],
                "source_url": rule["source_url"],
                "affected_files": len({location["file"] for location in locations}),
                "occurrences": len(locations),
                "locations": locations[:MAX_LOCATIONS_PER_FINDING],
                "locations_all": locations,
                "omitted_locations": max(0, len(locations) - MAX_LOCATIONS_PER_FINDING),
            }
        )
    findings.extend(_scan_dependency_manifests(sources, MAX_EVIDENCE_RECORDS - evidence_records))
    findings.sort(
        key=lambda item: (
            -item["severity_weight"],
            -item["affected_files"],
            -item["occurrences"],
            item["id"],
        )
    )
    return findings


def _config_key_records(
    content: str,
) -> Iterator[tuple[int, int, str, str, tuple[str, ...]]]:
    """Lex YAML/JSON mapping paths without building attacker-controlled object graphs."""
    stack: list[tuple[int, str]] = []
    record_count = 0
    document = 0
    key_pattern = re.compile(
        r"^(?P<space>[ \t]*)(?P<quote>[\"']?)(?P<key>[A-Za-z0-9_.-]+)"
        r"(?P=quote)\s*:\s*(?P<value>.*)$"
    )
    for line_number, line in enumerate(content.splitlines(), 1):
        if re.fullmatch(r"[ \t]*(?:---|\.\.\.)[ \t]*(?:#.*)?", line):
            stack.clear()
            document += 1
            continue
        match = key_pattern.match(line)
        if not match:
            continue
        indent = len(match.group("space").expandtabs(8))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        key = match.group("key").lower()
        raw_value = re.sub(r"\s+#.*$", "", match.group("value")).strip().rstrip(",").strip()
        value = raw_value
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        # Only shallow paths are meaningful to the supported IaC formats. Keeping
        # a bounded suffix avoids quadratic tuple growth on maliciously deep YAML.
        path = tuple(item[1] for item in stack[-8:]) + (key,)
        record_count += 1
        if record_count > MAX_CONFIG_RECORDS:
            raise ValueError(
                f"source structure exceeds the {MAX_CONFIG_RECORDS}-record analysis limit"
            )
        yield document, line_number, key, value, path
        if raw_value in {"", "{"}:
            stack.append((indent, key))


def _sam_transform_documents(content: str) -> set[int]:
    documents: set[int] = set()
    document = 0
    pending_indent: int | None = None
    for line in content.splitlines():
        if re.fullmatch(r"[ \t]*(?:---|\.\.\.)[ \t]*(?:#.*)?", line):
            document += 1
            pending_indent = None
            continue
        transform = re.match(
            r"^(?P<space>[ \t]*)[\"']?Transform[\"']?\s*:\s*(?P<value>.*)$",
            line,
            re.IGNORECASE,
        )
        if transform:
            value = re.sub(r"\s+#.*$", "", transform.group("value")).strip()
            if re.search(r"AWS::Serverless-", value, re.IGNORECASE):
                documents.add(document)
            pending_indent = len(transform.group("space").expandtabs(8)) if not value else None
            continue
        if pending_indent is None or not line.strip():
            continue
        indent = len(line[: len(line) - len(line.lstrip(" \t"))].expandtabs(8))
        if indent <= pending_indent:
            pending_indent = None
        elif re.match(r"^[ \t]*-[ \t]*[\"']?AWS::Serverless-", line, re.IGNORECASE):
            documents.add(document)
            pending_indent = None
    return documents


def _runtime_id(value: str) -> str | None:
    match = re.match(
        r"^[\"']?(nodejs\d+\.x|python\d+\.\d+|ruby\d+\.\d+|java\d+|"
        r"dotnet\d+|dotnetcore\d+\.\d+|go\d+\.x|provided\.al\d+|provided)\b",
        value.strip(),
        re.IGNORECASE,
    )
    return match.group(1).lower() if match else None


def _cdk_runtime_id(value: str) -> str | None:
    match = re.search(
        r"Runtime\.(NODEJS|PYTHON|RUBY|JAVA|DOTNET|GO)_(\d+)(?:_(\d+))?(?:_X)?\b",
        value,
        re.IGNORECASE,
    )
    if not match:
        return None
    language, major, minor = match.groups()
    language = language.lower()
    if language == "nodejs":
        return f"nodejs{major}.x"
    if language in {"python", "ruby"}:
        return f"{language}{major}.{minor or '0'}"
    return f"{language}{major}"


def _single_line_json_lambda_runtime_records(content: str) -> set[tuple[int, str]]:
    """Recognize bounded minified CloudFormation/SAM JSON without recursive traversal."""
    stripped = content.strip()
    if "\n" in stripped or not stripped.startswith("{"):
        return set()
    if len(stripped) > 1024 * 1024:
        raise ValueError("single-line JSON exceeds the structured analysis limit")
    try:
        document = json.loads(stripped)
    except (json.JSONDecodeError, RecursionError):
        return set()
    if not isinstance(document, dict):
        return set()

    runtime_ids: set[str] = set()
    resources = document.get("Resources")
    if isinstance(resources, dict):
        for resource in resources.values():
            if not isinstance(resource, dict) or str(resource.get("Type", "")).lower() not in {
                "aws::lambda::function",
                "aws::serverless::function",
            }:
                continue
            properties = resource.get("Properties")
            runtime = properties.get("Runtime") if isinstance(properties, dict) else None
            runtime_id = _runtime_id(str(runtime or ""))
            if runtime_id:
                runtime_ids.add(runtime_id)

    transform = document.get("Transform")
    transforms = transform if isinstance(transform, list) else [transform]
    is_sam = any(
        isinstance(item, str) and item.lower().startswith("aws::serverless-") for item in transforms
    )
    globals_section = document.get("Globals")
    function_globals = (
        globals_section.get("Function") if isinstance(globals_section, dict) else None
    )
    if is_sam and isinstance(function_globals, dict):
        runtime_id = _runtime_id(str(function_globals.get("Runtime") or ""))
        if runtime_id:
            runtime_ids.add(runtime_id)
    line_number = content.count("\n", 0, content.find(stripped)) + 1
    return {(line_number, runtime_id) for runtime_id in runtime_ids}


def _matching_brace(text: str, start: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    index = start
    while index < len(text):
        character = text[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\" and quote == '"':
                escaped = True
            elif character == quote:
                if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if character in {"'", '"'}:
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _yaml_flow_lambda_runtime_records(content: str) -> set[tuple[int, str]]:
    """Recognize direct Runtime properties in one-line YAML flow-map resources."""
    records: set[tuple[int, str]] = set()
    type_pattern = re.compile(
        r"\bType\s*:\s*[\"']?AWS::(?:Lambda|Serverless)::Function\b", re.IGNORECASE
    )
    properties_pattern = re.compile(r"\bProperties\s*:\s*\{", re.IGNORECASE)
    runtime_pattern = re.compile(r"\bRuntime\s*:\s*[\"']?([A-Za-z0-9.]+)", re.IGNORECASE)
    flow_matches = 0
    for line_number, line in enumerate(content.splitlines(), 1):
        if not type_pattern.search(line):
            continue
        if len(line) > MAX_FLOW_LINE_CHARS:
            raise ValueError("source flow-mapping line exceeds the analysis limit")
        for type_match in type_pattern.finditer(line):
            flow_matches += 1
            if flow_matches > MAX_FLOW_RESOURCE_MATCHES:
                raise ValueError("source flow mapping exceeds the analysis limit")
            resource_start = line.rfind("{", 0, type_match.start())
            resource_end = _matching_brace(line, resource_start) if resource_start >= 0 else None
            if resource_end is None:
                continue
            resource = line[resource_start : resource_end + 1]
            properties_match = properties_pattern.search(resource)
            if not properties_match:
                continue
            properties_start = resource.find("{", properties_match.start())
            properties_end = _matching_brace(resource, properties_start)
            if properties_end is None:
                continue
            properties = resource[properties_start : properties_end + 1]
            runtime_match = runtime_pattern.search(properties)
            runtime_id = _runtime_id(runtime_match.group(1)) if runtime_match else None
            if runtime_id:
                records.add((line_number, runtime_id))
    return records


def _yaml_lambda_runtime_records(content: str) -> set[tuple[int, str]]:
    records: set[tuple[int, str]] = set()
    lambda_resources: set[tuple[int, tuple[str, ...]]] = set()
    aws_provider_documents: set[int] = set()
    for document, _, key, value, path in _config_key_records(content):
        if (
            key == "type"
            and value.lower() in {"aws::lambda::function", "aws::serverless::function"}
            and "resources" in path
        ):
            lambda_resources.add((document, path[:-1]))
            if len(lambda_resources) > MAX_LAMBDA_RESOURCES:
                raise ValueError(
                    f"source contains more than {MAX_LAMBDA_RESOURCES} Lambda resources"
                )
        if path == ("provider", "name") and value.lower() == "aws":
            aws_provider_documents.add(document)
    sam_documents = _sam_transform_documents(content)
    for document, line_number, key, value, path in _config_key_records(content):
        if key != "runtime":
            continue
        runtime_id = _runtime_id(value)
        if not runtime_id:
            continue
        if (
            path[-2:] == ("properties", "runtime")
            and (
                document,
                path[:-2],
            )
            in lambda_resources
        ):
            records.add((line_number, runtime_id))
            continue
        if document in sam_documents and path == ("globals", "function", "runtime"):
            records.add((line_number, runtime_id))
            continue
        if document in aws_provider_documents and (
            path == ("provider", "runtime")
            or (len(path) == 3 and path[0] == "functions" and path[-1] == "runtime")
        ):
            records.add((line_number, runtime_id))
    records.update(_single_line_json_lambda_runtime_records(content))
    records.update(_yaml_flow_lambda_runtime_records(content))
    return records


def _hcl_code_lines(content: str) -> Iterator[tuple[int, str, str]]:
    """Yield original and same-length HCL code lines with strings/comments blanked."""
    in_block_comment = False
    heredoc: tuple[str, bool] | None = None
    for line_number, original in enumerate(content.splitlines(), 1):
        if heredoc:
            marker, allow_indent = heredoc
            candidate = original.strip() if allow_indent else original
            if candidate == marker:
                heredoc = None
            yield line_number, original, " " * len(original)
            continue
        visible = list(original)
        quote: str | None = None
        escaped = False
        index = 0
        while index < len(original):
            character = original[index]
            following = original[index : index + 2]
            if in_block_comment:
                visible[index] = " "
                if following == "*/":
                    if index + 1 < len(visible):
                        visible[index + 1] = " "
                    in_block_comment = False
                    index += 2
                    continue
                index += 1
                continue
            if quote:
                visible[index] = " "
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                index += 1
                continue
            if following == "/*":
                visible[index] = visible[index + 1] = " "
                in_block_comment = True
                index += 2
                continue
            if following == "//" or character == "#":
                for remainder in range(index, len(visible)):
                    visible[remainder] = " "
                break
            if character in {"'", '"'}:
                visible[index] = " "
                quote = character
            index += 1
        code = "".join(visible)
        heredoc_match = re.search(r"<<(?P<indent>-?)(?P<marker>[A-Za-z_][A-Za-z0-9_]*)", code)
        if heredoc_match:
            heredoc = (
                heredoc_match.group("marker"),
                heredoc_match.group("indent") == "-",
            )
        yield line_number, original, code


def _terraform_lambda_runtime_records(content: str) -> set[tuple[int, str]]:
    records: set[tuple[int, str]] = set()
    inside_lambda = False
    depth = 0
    declaration = re.compile(
        r"\bresource\s+[\"']aws_lambda_function[\"']\s+[\"'][^\"']+[\"']\s*\{",
        re.IGNORECASE,
    )
    runtime_key = re.compile(r"\bruntime\b\s*=", re.IGNORECASE)
    runtime_value = re.compile(r"\bruntime\b\s*=\s*[\"']?([^\"'\s}]+)", re.IGNORECASE)
    structural_events = 0
    for line_number, original, code in _hcl_code_lines(content):
        original_match = None if inside_lambda else declaration.search(original)
        visible_match = None if inside_lambda else re.search(r"\bresource\s+", code, re.IGNORECASE)
        resource_match = (
            original_match
            if original_match and visible_match and original_match.start() == visible_match.start()
            else None
        )
        if resource_match:
            inside_lambda = True
            depth = 0
        if not inside_lambda:
            continue
        scan_start = resource_match.start() if resource_match else 0
        position = scan_start
        while position < len(code):
            character = code[position]
            if character == "{":
                structural_events += 1
                depth += 1
            elif character == "}":
                structural_events += 1
                depth -= 1
            elif depth == 1 and code[position : position + 7].lower() == "runtime":
                runtime_match = runtime_key.match(code, position)
                if not runtime_match:
                    position += 1
                    continue
                structural_events += 1
                value_match = runtime_value.match(original, position)
                runtime_id = _runtime_id(value_match.group(1)) if value_match else None
                if runtime_id:
                    records.add((line_number, runtime_id))
                position = runtime_match.end()
                if structural_events > MAX_HCL_STRUCTURE_EVENTS:
                    raise ValueError("Terraform structure exceeds the analysis limit")
                continue
            if structural_events > MAX_HCL_STRUCTURE_EVENTS:
                raise ValueError("Terraform structure exceeds the analysis limit")
            if depth <= 0 and character == "}":
                inside_lambda = False
                break
            position += 1
    return records


def _lambda_runtime_records(filename: str, content: str) -> set[tuple[int, str]]:
    """Return only (line, runtime) pairs bound to an AWS Lambda construct."""
    records: set[tuple[int, str]] = set()
    has_imported_cdk_runtime = bool(
        re.search(
            r"(?:aws-cdk-lib|@aws-cdk)/aws-lambda|"
            r"from\s+aws_cdk\.aws_lambda\s+import[^\n]*\bRuntime\b|"
            r"software\.amazon\.awscdk\.services\.lambda\.Runtime|"
            r"Amazon\.CDK\.AWS\.Lambda",
            content,
            re.IGNORECASE,
        )
    )
    for line_number, line in enumerate(content.splitlines(), 1):
        cli_match = re.search(
            r"\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)[\"']?([^\"'\s]+)",
            line,
            re.IGNORECASE,
        )
        cli_runtime = _runtime_id(cli_match.group(1)) if cli_match else None
        if cli_runtime:
            records.add((line_number, cli_runtime))
        qualified_cdk = re.search(
            r"\bruntime\b\s*[:=(]\s*(?:aws_)?_?lambda\.(Runtime\.[A-Z0-9_]+)",
            line,
            re.IGNORECASE,
        )
        imported_cdk = (
            re.search(r"\bruntime\b\s*[:=(]\s*(Runtime\.[A-Z0-9_]+)", line, re.IGNORECASE)
            if has_imported_cdk_runtime
            else None
        )
        cdk_match = qualified_cdk or imported_cdk
        cdk_runtime = _cdk_runtime_id(cdk_match.group(1)) if cdk_match else None
        if cdk_runtime:
            records.add((line_number, cdk_runtime))

    suffix = PurePosixPath(filename).suffix.lower()
    basename = PurePosixPath(filename).name.lower()
    if suffix in {".json", ".yaml", ".yml"} or basename in {
        "serverless.yml",
        "serverless.yaml",
    }:
        records.update(_yaml_lambda_runtime_records(content))
    if suffix in {".tf", ".tfvars", ".hcl"}:
        records.update(_terraform_lambda_runtime_records(content))
    return records


def _version_tuple(value: str) -> tuple[int, ...]:
    value = re.sub(r"^[^0-9]*", "", value or "")
    parts: list[int] = []
    for part in re.split(r"[.\-+]", value):
        match = re.match(r"\d+", part)
        parts.append(int(match.group(0)) if match else 0)
    return tuple(parts or [0])


def _version_lt(value: str, minimum: str) -> bool:
    left = list(_version_tuple(value))
    right = list(_version_tuple(minimum))
    length = max(len(left), len(right))
    return tuple(left + [0] * (length - len(left))) < tuple(right + [0] * (length - len(right)))


def _python_minimum(specifier: str | None) -> str | None:
    if not specifier:
        return None
    for operator in ("==", ">="):
        for part in specifier.split(","):
            part = part.strip()
            if part.startswith(operator):
                return part[len(operator) :].strip()
    return None


def _bounded_dependency_spec(spec: Any, manifest_name: str) -> str | None:
    if spec is None:
        return None
    if not isinstance(spec, (str, int, float)):
        raise ValueError(f"{manifest_name} contains a non-scalar dependency version")
    value = str(spec).strip()
    if len(value) > MAX_DEPENDENCY_SPEC_CHARS:
        raise ValueError(
            f"{manifest_name} dependency versions must be at most "
            f"{MAX_DEPENDENCY_SPEC_CHARS} characters"
        )
    return value or None


def _evidence_near(content: str, position: int) -> tuple[int, str]:
    line_number = content.count("\n", 0, position) + 1
    line_start = content.rfind("\n", 0, position) + 1
    line_end = content.find("\n", position)
    if line_end < 0:
        line_end = len(content)
    excerpt_start = max(line_start, position - 80)
    excerpt_end = min(line_end, position + 360)
    return line_number, _compact_evidence(content[excerpt_start:excerpt_end])


def _manifest_dependencies(
    filename: str, content: str
) -> list[tuple[str, str, str | None, int, str]]:
    """Return (ecosystem, package, spec, line, evidence) manifest entries."""
    basename = PurePosixPath(filename).name.lower()
    is_requirements = basename.endswith("requirements.txt") or bool(
        re.fullmatch(r"requirements.*\.txt", basename)
    )
    is_python_manifest = basename in {"pyproject.toml", "pipfile"}
    if (basename == "package.json" or is_requirements or is_python_manifest) and len(
        content.encode("utf-8")
    ) > MAX_MANIFEST_BYTES:
        raise ValueError(
            f"{basename} exceeds the {MAX_MANIFEST_BYTES}-byte dependency analysis limit"
        )
    entries: list[tuple[str, str, str | None, int, str]] = []
    if basename == "package.json":
        try:
            package = json.loads(content)
        except (json.JSONDecodeError, RecursionError):
            return entries
        if not isinstance(package, dict):
            raise ValueError("package.json root must be an object")
        dependencies: dict[str, Any] = {}
        for key in ("dependencies", "devDependencies"):
            values = package.get(key) or {}
            if isinstance(values, dict):
                dependencies.update(
                    (str(name), spec)
                    for name, spec in values.items()
                    if str(name) in NODE_NATIVE_PACKAGES
                )
        for name, spec in dependencies.items():
            bounded_spec = _bounded_dependency_spec(spec, basename)
            position = content.find(json.dumps(name))
            line_no, evidence = _evidence_near(content, max(position, 0))
            entries.append(("node", name, bounded_spec, line_no, evidence))
        return entries

    requirement_re = re.compile(r"^([A-Za-z0-9_.-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~].+)?$")
    if is_requirements:
        for line_no, raw in enumerate(content.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(("#", "-")):
                continue
            name_match = re.match(r"^([A-Za-z0-9_.-]+)", line)
            if not name_match:
                continue
            name = re.sub(r"[-_.]+", "-", name_match.group(1).lower())
            if name not in PY312_WHEELS:
                continue
            if len(line) > MAX_DEPENDENCY_SPEC_CHARS + 256:
                raise ValueError(f"{basename} dependency lines exceed the analysis limit")
            match = requirement_re.match(line.split(" #", 1)[0].strip())
            if match:
                spec = _bounded_dependency_spec((match.group(2) or "").strip() or None, basename)
                entries.append(("python", name, spec, line_no, _compact_evidence(raw)))
        return entries

    if is_python_manifest:
        for block in re.finditer(r"dependencies\s*=\s*\[([\s\S]*?)\]", content):
            for match in re.finditer(
                r"[\"']\s*([A-Za-z0-9_.-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~][^\"']*)?\s*[\"']",
                block.group(1),
            ):
                name = re.sub(r"[-_.]+", "-", match.group(1).lower())
                if name not in PY312_WHEELS:
                    continue
                spec = _bounded_dependency_spec((match.group(2) or "").strip() or None, basename)
                absolute = block.start(1) + match.start()
                line_no, evidence = _evidence_near(content, absolute)
                entries.append(("python", name, spec, line_no, evidence))
    return entries


def _scan_dependency_manifests(
    sources: list[tuple[str, str]], evidence_budget: int = MAX_EVIDENCE_RECORDS
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    evidence_records = 0
    for filename, content in sources:
        for ecosystem, name, spec, line_no, evidence in _manifest_dependencies(filename, content):
            if ecosystem == "node":
                rule = NODE_NATIVE_PACKAGES.get(name)
                if not rule:
                    continue
                declared = re.sub(r"^[\^~>=<\s]+", "", spec or "") or None
                minimum = rule.get("min")
                baseline_met = bool(
                    minimum is not None and declared and not _version_lt(declared, str(minimum))
                )
                severity = "critical" if minimum is None else "low" if baseline_met else "high"
                required = (
                    "removal/replacement"
                    if minimum is None
                    else (
                        "verified Node.js 24 support plus a target-runtime rebuild/test"
                        if baseline_met
                        else f">= {minimum} baseline, then Node.js 24 verification"
                    )
                )
                category = "Node.js dependency compatibility"
                title = f"{name} requires Node.js 24 compatibility evidence"
                source_url = f"https://www.npmjs.com/package/{name}"
            else:
                rule = PY312_WHEELS.get(name)
                if not rule:
                    continue
                minimum = rule.get("min")
                declared = _python_minimum(spec)
                if minimum is not None and declared and not _version_lt(declared, str(minimum)):
                    continue
                severity = "critical" if minimum is None else "low" if declared is None else "high"
                required = "a maintained replacement" if minimum is None else f">= {minimum}"
                category = "Python dependency compatibility"
                title = f"{name} may block a Python 3.12 migration"
                source_url = f"https://pypi.org/project/{name}/"
            key = (ecosystem, name)
            finding = grouped.setdefault(
                key,
                {
                    "id": f"dependency-{ecosystem}-{re.sub(r'[^a-z0-9]+', '-', name).strip('-')}",
                    "category": category,
                    "severity": severity,
                    "severity_weight": SEVERITY_WEIGHT[severity],
                    "title": title,
                    "description": (
                        f"The manifest declares {name} as {spec or '(unpinned)'}. "
                        f"The local rule pack uses {required} as a conservative triage baseline; "
                        "actual support varies by package release, platform, and architecture. "
                        f"{rule.get('note', '')}"
                    ),
                    "remediation": (
                        f"Update {name} to {required}, rebuild on the target runtime and architecture, "
                        "then run the repository's tests before deployment."
                    ),
                    "source_url": source_url,
                    "locations_all": [],
                },
            )
            evidence_records += 1
            if evidence_records > evidence_budget:
                raise ValueError("dependency findings exceed the evidence analysis limit")
            finding["locations_all"].append(
                {
                    "file": filename,
                    "line": line_no,
                    "evidence": _compact_evidence(evidence),
                }
            )
    findings: list[dict[str, Any]] = []
    for finding in grouped.values():
        locations = finding["locations_all"]
        finding.update(
            {
                "affected_files": len({item["file"] for item in locations}),
                "occurrences": len(locations),
                "locations": locations[:MAX_LOCATIONS_PER_FINDING],
                "omitted_locations": max(0, len(locations) - MAX_LOCATIONS_PER_FINDING),
            }
        )
        findings.append(finding)
    return findings


def _compact_evidence(line: str, match_position: int = 0) -> str:
    start = max(0, match_position - 100)
    excerpt = line[start : match_position + 340]
    compact = " ".join(excerpt.strip().split())
    return compact if len(compact) <= 220 else compact[:217] + "..."


def _summarize_categories(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {}
    for finding in findings:
        bucket = buckets.setdefault(finding["category"], {"count": 0, "evidence_count": 0})
        bucket["count"] += 1
        bucket["evidence_count"] += int(finding["occurrences"])
    return [{"name": name, **counts} for name, counts in sorted(buckets.items())]


def _rules_file() -> Path | None:
    configured = os.environ.get("EOLKITS_DEPRECATIONS_FILE")
    candidates = [
        Path(configured) if configured else None,
        Path(__file__).resolve().parents[2] / "rules" / "public" / "deprecations.yml",
        Path("/app/rules/public/deprecations.yml"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def _rule_pack_version() -> str:
    digest = hashlib.sha256(RULESET_VERSION.encode("utf-8"))
    path = _rules_file()
    if path:
        digest.update(path.read_bytes())
    digest.update(_dependency_rules_file().read_bytes())
    digest.update(json.dumps(AUDIT_RULES, sort_keys=True).encode("utf-8"))
    return f"{RULESET_VERSION}+{digest.hexdigest()[:12]}"


def _upcoming_deprecations(as_of: datetime | None = None) -> list[dict[str, str]]:
    path = _rules_file()
    if not path:
        return []
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return []
    items: list[dict[str, str]] = []
    effective_time = as_of.astimezone(UTC) if as_of is not None else datetime.now(UTC)
    today = effective_time.date().isoformat()
    for dep in data.get("deprecations", []):
        if not dep.get("url"):
            continue
        name = str(dep.get("name") or "")
        subject = re.sub(
            r"\s+(?:projected\s+)?create/update restrictions$", "", name, flags=re.IGNORECASE
        )
        is_lambda = (
            "lambda"
            in (str(dep.get("service") or "") + " " + " ".join(dep.get("tags") or [])).lower()
        )
        projected = bool(dep.get("dates_projected"))
        candidates: list[tuple[str, str]] = []
        deprecation_date = str(dep.get("deprecation_date") or "")
        if deprecation_date:
            label = "projected deprecation" if projected else "deprecation"
            candidates.append((deprecation_date, f"{subject} — {label}"))
        create_date = str(dep.get("date") or "")
        if create_date:
            label = "projected block on new functions" if projected else "block new functions"
            candidates.append((create_date, f"{subject} — {label}" if is_lambda else name))
        update_date = str(dep.get("block_update_date") or "")
        if update_date:
            label = "projected block on function updates" if projected else "block function updates"
            candidates.append((update_date, f"{subject} — {label}"))
        future = [candidate for candidate in candidates if candidate[0] >= today]
        if future:
            date, label = min(future)
            items.append({"name": label, "date": date, "url": str(dep.get("url"))})
    return sorted(items, key=lambda item: (item["date"], item["name"]))[:8]


def _evidence_fingerprint(
    input_hash: str, rule_pack_version: str, findings: list[dict[str, Any]]
) -> str:
    canonical_findings = [
        {
            "id": finding["id"],
            "severity": finding["severity"],
            "locations": finding["locations_all"],
        }
        for finding in findings
    ]
    payload = {
        "input_sha256": input_hash,
        "report_version": REPORT_VERSION,
        "rule_pack_version": rule_pack_version,
        "findings": canonical_findings,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _valid_deadline(deadline: Optional[str]) -> str | None:
    if not deadline:
        return None
    try:
        return datetime.strptime(deadline, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None
