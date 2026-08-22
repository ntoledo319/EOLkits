"""Evidence-based AWS deprecation audit report generation.

The report is deliberately a static source scan. It does not claim to inventory a
live AWS account, predict downtime cost, or sign the rendered PDF. Instead it
records exact file/line evidence, primary sources, the uploaded-byte hash, and a
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
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Optional
from urllib.parse import urlparse

import requests
import yaml
from jinja2 import Environment, select_autoescape

MAX_INPUT_BYTES = int(os.environ.get("EOLKITS_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_EXPANDED_BYTES = int(os.environ.get("EOLKITS_MAX_EXPANDED_BYTES", str(25 * 1024 * 1024)))
MAX_SOURCE_FILES = int(os.environ.get("EOLKITS_MAX_SOURCE_FILES", "2000"))
MAX_ZIP_RATIO = int(os.environ.get("EOLKITS_MAX_ZIP_RATIO", "100"))
MAX_LOCATIONS_PER_FINDING = 25
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "https://eolkits.com")
ALLOWED_UPLOAD_ORIGIN = os.environ.get("EOLKITS_ALLOWED_UPLOAD_ORIGIN", PUBLIC_SITE_URL).rstrip("/")
REPORT_VERSION = "2.0"
RULESET_VERSION = "audit-v2-2026-08-22"

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
        "patterns": (r"\bnodejs16\.x\b",),
        "description": "Node.js 16 is a retired Lambda runtime. Deploy operations may be blocked.",
        "remediation": "Move the function to a currently supported Lambda Node.js runtime, rebuild native dependencies, and run its tests before deployment.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-nodejs18",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Node.js 18 runtime reference",
        "patterns": (r"\bnodejs18\.x\b",),
        "description": "Node.js 18 is deprecated in Lambda and no longer receives runtime updates.",
        "remediation": "Move to a currently supported Lambda Node.js runtime and validate SDK and native-addon compatibility.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-nodejs20",
        "category": "Lambda runtime",
        "severity": "high",
        "title": "Lambda Node.js 20 runtime reference",
        "patterns": (r"\bnodejs20\.x\b",),
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
        "description": "AWS publishes a projected 2027 deprecation and create/update block timeline for Node.js 22.",
        "remediation": "Plan and test a move to Node.js 24 while Node.js 22 still has runway; recheck AWS's current dates before scheduling the change.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python38",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Python 3.8 runtime reference",
        "patterns": (r"\bpython3\.8\b", r"\bPYTHON_3_8\b"),
        "description": "Python 3.8 is a retired Lambda runtime.",
        "remediation": "Move to a supported Python runtime and test removed standard-library modules and native wheels before deployment.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python39",
        "category": "Lambda runtime",
        "severity": "critical",
        "title": "Lambda Python 3.9 runtime reference",
        "patterns": (r"\bpython3\.9\b", r"\bPYTHON_3_9\b"),
        "description": "Python 3.9 is deprecated in Lambda and no longer receives runtime updates.",
        "remediation": "Move to a supported Python runtime and resolve Python 3.12+ compatibility findings before deployment.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python310",
        "category": "Lambda runtime",
        "severity": "high",
        "title": "Lambda Python 3.10 runtime reference",
        "patterns": (r"\bpython3\.10\b", r"\bPYTHON_3_10\b"),
        "description": "Python 3.10 has a published Lambda deprecation timeline.",
        "remediation": "Schedule the runtime move while there is test runway; check removed modules, typing changes, and native wheels.",
        "source_url": AWS_LAMBDA_SOURCE,
    },
    {
        "id": "lambda-python311",
        "category": "Lambda runtime",
        "severity": "medium",
        "title": "Lambda Python 3.11 runtime reference",
        "patterns": (r"\bpython3\.11\b", r"\bPYTHON_3_11\b"),
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
<!DOCTYPE html><html><head><meta charset="utf-8"><title>EOLkits AWS Deprecation Evidence Report</title>
<style>
@page{margin:1.6cm}body{font-family:"DejaVu Sans",sans-serif;color:#111827;line-height:1.45;font-size:10.5pt}h1{color:#1f2937;border-bottom:3px solid #2563eb;padding-bottom:.45rem}h2{color:#1f2937;margin-top:1.7rem;border-bottom:1px solid #d1d5db;padding-bottom:.25rem}h3{margin-bottom:.35rem}a{color:#1d4ed8}code{background:#f3f4f6;padding:.1rem .25rem;border-radius:3px;font-family:"DejaVu Sans Mono",monospace;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;margin:.8rem 0}th,td{padding:.55rem;text-align:left;border-bottom:1px solid #e5e7eb;vertical-align:top}th{background:#f9fafb}.cover{page-break-after:always}.meta,.scope,.verification,.limitation{padding:.85rem 1rem;border-radius:7px;margin:.8rem 0}.meta,.scope{background:#f9fafb}.verification{background:#eff6ff}.limitation{background:#fffbeb;border:1px solid #fde68a}.finding{break-inside:avoid;border-left:4px solid #d1d5db;padding:0 0 .7rem .9rem;margin:1rem 0}.severity{display:inline-block;padding:.12rem .4rem;border-radius:4px;font-size:8.5pt;font-weight:700;text-transform:uppercase}.critical{background:#fee2e2;color:#991b1b}.high{background:#ffedd5;color:#9a3412}.medium{background:#fef3c7;color:#92400e}.low{background:#dcfce7;color:#166534}.evidence{font-family:"DejaVu Sans Mono",monospace;font-size:8.5pt;overflow-wrap:anywhere}.muted{color:#6b7280;font-size:9pt}
</style></head><body>
<section class="cover"><h1>AWS Deprecation Evidence Report</h1>
<div class="meta"><p><strong>Generated:</strong> {{ generated_at }}</p><p><strong>Report engine:</strong> {{ report_version }}</p><p><strong>Rule pack:</strong> {{ rule_pack_version }}</p><p><strong>Uploaded artifact:</strong> <code>{{ input_name }}</code></p><p><strong>Input SHA-256:</strong> <code>{{ input_hash }}</code></p><p><strong>Evidence fingerprint:</strong> <code>{{ evidence_hash }}</code></p></div>
<h2>Executive summary</h2><p>The static scan found <strong>{{ total_findings }} distinct risk type{% if total_findings != 1 %}s{% endif %}</strong> across <strong>{{ affected_files }}</strong> of {{ scanned_files }} scanned source files, supported by {{ evidence_lines }} file/line evidence record{% if evidence_lines != 1 %}s{% endif %}.</p>
{% if deadline %}<p><strong>Buyer-supplied target date:</strong> {{ deadline }}. This date is context only; it does not alter scan results.</p>{% endif %}
{% if categories %}<table><thead><tr><th>Category</th><th>Risk types</th><th>Evidence records</th></tr></thead><tbody>{% for category in categories %}<tr><td>{{ category.name }}</td><td>{{ category.count }}</td><td>{{ category.evidence_count }}</td></tr>{% endfor %}</tbody></table>{% else %}<p>No configured rule matched the supplied files. This is not proof that the repository or AWS account is free of deprecation risk.</p>{% endif %}
<div class="scope"><strong>Observed scope:</strong> {{ scanned_files }} supported text files; {{ scanned_bytes }} decoded bytes.{% if skipped_files %} {{ skipped_files }} unsupported/binary files were skipped.{% endif %}</div>
<div class="limitation"><strong>Important limitation:</strong> This is a static scan of the uploaded artifact. It does not query a live AWS account, execute code, prove exploitability, inspect files that were not uploaded, or guarantee a complete resource inventory. Validate every recommended change in a non-production environment.</div></section>
<h2>Prioritized findings</h2>{% if not findings %}<p>No configured evidence pattern matched.</p>{% endif %}
{% for finding in findings %}<section class="finding"><h3><span class="severity {{ finding.severity }}">{{ finding.severity }}</span> {{ finding.title }}</h3><p>{{ finding.description }}</p><p><strong>Observed reach:</strong> {{ finding.affected_files }} file{% if finding.affected_files != 1 %}s{% endif %}, {{ finding.occurrences }} evidence line{% if finding.occurrences != 1 %}s{% endif %}.</p><p><strong>Remediation:</strong> {{ finding.remediation }}</p><p><strong>Primary/official source:</strong> <a href="{{ finding.source_url }}">{{ finding.source_url }}</a></p><table><thead><tr><th>Location</th><th>Observed text</th></tr></thead><tbody>{% for location in finding.locations %}<tr><td><code>{{ location.file }}:{{ location.line }}</code></td><td class="evidence">{{ location.evidence }}</td></tr>{% endfor %}</tbody></table>{% if finding.omitted_locations %}<p class="muted">{{ finding.omitted_locations }} additional evidence locations omitted from the PDF.</p>{% endif %}</section>{% endfor %}
<h2>Roll-forward order</h2>{% if findings %}<ol>{% for finding in findings %}<li><strong>{{ finding.title }}</strong> — {{ finding.remediation }}</li>{% endfor %}</ol>{% else %}<p>Confirm the upload was complete, then compare deployed AWS inventory with the current AWS runtime and operating-system support tables.</p>{% endif %}
{% if upcoming_deprecations %}<h2>Tracked AWS dates</h2><p class="muted">Dates below come from the cited public rule pack and should be rechecked before production planning.</p><ul>{% for dep in upcoming_deprecations %}<li><strong>{{ dep.name }}</strong> — {{ dep.date }} — <a href="{{ dep.url }}">source</a></li>{% endfor %}</ul>{% endif %}
<div class="verification"><h2>Evidence verification</h2><p>Look up the evidence fingerprint at <a href="{{ verify_url }}">{{ verify_url }}</a>.</p><p class="muted">The fingerprint covers the input hash, report-engine/rule-pack versions, and canonical findings. It is not a digital signature of the PDF file.</p></div>
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
    generated = datetime.now(UTC)
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
        upcoming_deprecations=_upcoming_deprecations(),
        verify_url=f"{PUBLIC_SITE_URL}/verify/?hash={evidence_hash}",
    )
    pdf_bytes = HTML(string=html_content, base_url=PUBLIC_SITE_URL).write_pdf()
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
        "generated_at": generated.isoformat().replace("+00:00", "Z"),
        "findings_count": len(public_findings),
        "evidence_count": evidence_lines,
        "scanned_files": len(sources),
    }


def preflight_audit_input(upload_path: str, filename: str | None = None) -> dict[str, Any]:
    """Validate the exact local bytes before a Checkout Session may be created."""
    content = _read_local_input(upload_path)
    input_name = _safe_input_name(filename, upload_path, None)
    sources, skipped = _source_files(content, input_name)
    return {
        "input_hash": hashlib.sha256(content).hexdigest(),
        "scanned_files": len(sources),
        "skipped_files": skipped,
        "decoded_bytes": sum(len(body.encode("utf-8")) for _, body in sources),
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
        members = [member for member in archive.infolist() if not member.is_dir()]
        if len(members) > MAX_SOURCE_FILES:
            raise ValueError(f"archive contains more than {MAX_SOURCE_FILES} files")
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
    findings: list[dict[str, Any]] = []
    for rule in AUDIT_RULES:
        compiled = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in rule["patterns"]
        ]
        locations: list[dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        for filename, content in sources:
            for line_number, line in enumerate(content.splitlines(), start=1):
                if not any(pattern.search(line) for pattern in compiled):
                    continue
                key = (filename, line_number)
                if key in seen:
                    continue
                seen.add(key)
                locations.append(
                    {"file": filename, "line": line_number, "evidence": _compact_evidence(line)}
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
    findings.extend(_scan_dependency_manifests(sources))
    findings.sort(
        key=lambda item: (
            -item["severity_weight"],
            -item["affected_files"],
            -item["occurrences"],
            item["id"],
        )
    )
    return findings


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


def _manifest_dependencies(
    filename: str, content: str
) -> list[tuple[str, str, str | None, int, str]]:
    """Return (ecosystem, package, spec, line, evidence) manifest entries."""
    basename = PurePosixPath(filename).name.lower()
    entries: list[tuple[str, str | None, int, str, str]] = []
    if basename == "package.json":
        try:
            package = json.loads(content)
        except json.JSONDecodeError:
            return entries
        dependencies: dict[str, Any] = {}
        for key in ("dependencies", "devDependencies"):
            values = package.get(key) or {}
            if isinstance(values, dict):
                dependencies.update(values)
        lines = content.splitlines()
        for name, spec in dependencies.items():
            line_no = next(
                (index for index, line in enumerate(lines, 1) if json.dumps(str(name)) in line),
                1,
            )
            evidence = lines[line_no - 1] if lines else f"{name}: {spec}"
            entries.append(
                ("node", str(name), str(spec) if spec is not None else None, line_no, evidence)
            )
        return entries

    requirement_re = re.compile(r"^([A-Za-z0-9_.-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~].+)?$")
    if basename.endswith("requirements.txt") or re.fullmatch(r"requirements.*\.txt", basename):
        for line_no, raw in enumerate(content.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(("#", "-")):
                continue
            match = requirement_re.match(line.split(" #", 1)[0].strip())
            if match:
                name = re.sub(r"[-_.]+", "-", match.group(1).lower())
                entries.append(
                    ("python", name, (match.group(2) or "").strip() or None, line_no, raw)
                )
        return entries

    if basename == "pyproject.toml" or basename == "pipfile" or basename.endswith(".toml"):
        for block in re.finditer(r"dependencies\s*=\s*\[([\s\S]*?)\]", content):
            for match in re.finditer(
                r"[\"']\s*([A-Za-z0-9_.-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~][^\"']*)?\s*[\"']",
                block.group(1),
            ):
                name = re.sub(r"[-_.]+", "-", match.group(1).lower())
                absolute = block.start(1) + match.start()
                line_no = content.count("\n", 0, absolute) + 1
                evidence = content.splitlines()[line_no - 1]
                entries.append(
                    ("python", name, (match.group(2) or "").strip() or None, line_no, evidence)
                )
    return entries


def _scan_dependency_manifests(sources: list[tuple[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
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
                        f"The configured migration floor is {required}. {rule.get('note', '')}"
                    ),
                    "remediation": (
                        f"Update {name} to {required}, rebuild on the target runtime and architecture, "
                        "then run the repository's tests before deployment."
                    ),
                    "source_url": source_url,
                    "locations_all": [],
                },
            )
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


def _compact_evidence(line: str) -> str:
    compact = " ".join(line.strip().split())
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


def _upcoming_deprecations() -> list[dict[str, str]]:
    path = _rules_file()
    if not path:
        return []
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return []
    items = []
    today = datetime.now(UTC).date().isoformat()
    for dep in data.get("deprecations", []):
        date = str(dep.get("date") or "")
        if date and date >= today and dep.get("url"):
            items.append({"name": str(dep.get("name")), "date": date, "url": str(dep.get("url"))})
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
