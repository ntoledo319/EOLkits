#!/usr/bin/env python3
"""
EOLkits Static Site Generator
Builds docs/ from templates and rule-pack data.
"""

import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

# Dependencies are installed explicitly from requirements-dev.txt; the builder
# never mutates its Python environment.
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as exc:
    raise SystemExit(
        "Jinja2 is required; install apps/web/requirements-dev.txt in a project-local venv"
    ) from exc


BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR.parent.parent / "docs"
PRICING_FILE = BASE_DIR.parent.parent / "pricing.yml"
BUILD_DATE_FILE = BASE_DIR / "BUILD_DATE"
# GRACE serves eolkits.com at the domain root, while the committed fallback
# artifact is built for GitHub Pages at /EOLkits. Both values are env-overridable:
#   EOLKITS_BASE_PATH=/EOLkits EOLKITS_SITE_URL=https://ntoledo319.github.io/EOLkits
PROJECT_BASE_PATH = os.environ.get("EOLKITS_BASE_PATH", "")
SITE_URL = os.environ.get("EOLKITS_SITE_URL", "https://eolkits.com")
API_URL = os.environ.get("EOLKITS_API_URL", "https://eolkits.com")
# IndexNow key (Bing/Yandex + AI engines that consume it — instant indexing of new
# pages). Stable + committed so the hosted key file at /<key>.txt always matches what
# we submit to api.indexnow.org; rotating it would break verification.
INDEXNOW_KEY = "0c7a25ebf8815c561ded8ab9a156dfb5"


def _interpolate_api(html):
    """Render a commerce-page template string.

    These page builders write ``{API_URL}`` for the API origin and double their
    in-script JS object braces (``{{`` / ``}}``). The page is NOT an f-string and
    its CSS uses single braces, so a plain ``.format()`` would crash on the CSS.
    We interpolate explicitly: substitute the API origin, then collapse the
    doubled JS braces back to singles, leaving single-brace CSS untouched. The
    result has zero ``{API_URL}`` / ``{{`` / ``}}`` left — which the CI gate and
    the deploy gate both enforce.
    """
    return html.replace("{API_URL}", API_URL).replace("{{", "{").replace("}}", "}")


ROOT_RELATIVE_ATTR_RE = re.compile(
    r'(?P<prefix>\b(?:href|src|action)=["\'])(?P<path>/(?!/|EOLkits(?:/|["\'])))'
)
ROOT_RELATIVE_FETCH_RE = re.compile(r"(?P<prefix>fetch\([\"'])(?P<path>/(?!/|EOLkits(?:/|[\"'])))")
API_RELATIVE_ATTR_RE = re.compile(
    r'(?P<prefix>\b(?:href|src|action)=["\'])(?P<path>/(?:api|upload|webhook)(?:/|["\']))'
)
API_RELATIVE_CALL_RE = re.compile(
    r"(?P<prefix>\b(?:fetch|navigator\.sendBeacon)\([\"'])(?P<path>/(?:api|upload|webhook)(?:/|[\"']))"
)


def load_pricing():
    """Load pricing configuration."""
    with open(PRICING_FILE) as f:
        return yaml.safe_load(f)


def normalize_project_links(html):
    """Make root-relative links work on a project sub-path (e.g. the /EOLkits
    GitHub Pages path) while keeping API routes on their separate live origin.
    No-op when EOLKITS_BASE_PATH is empty — the GRACE deployment script builds
    eolkits.com at the domain root immediately before rsync."""
    if not PROJECT_BASE_PATH:
        return html

    def replace_api(match):
        return f"{match.group('prefix')}{API_URL.rstrip('/')}{match.group('path')}"

    def replace(match):
        return f"{match.group('prefix')}{PROJECT_BASE_PATH}{match.group('path')}"

    html = API_RELATIVE_ATTR_RE.sub(replace_api, html)
    html = API_RELATIVE_CALL_RE.sub(replace_api, html)
    html = ROOT_RELATIVE_ATTR_RE.sub(replace, html)
    return ROOT_RELATIVE_FETCH_RE.sub(replace, html)


def normalize_generated_text(content: str) -> str:
    """Remove template-only indentation left behind by Jinja control lines."""
    return "\n".join(line.rstrip(" \t") for line in content.split("\n"))


def nearest_enforcement(dep, today=None):
    """(days_until, date_str) for the NEAREST FUTURE enforcement date a deprecation
    carries ('date' = block-create, 'block_update_date' = block-update).

    Returning the date alongside the count keeps copy honest: the block-create
    date is often already past while the real countdown runs to block-update, so a
    "N days until <dep.date>" headline showed a date that disagreed with N (and with
    the front-end JS countdown). Callers interpolate THIS date, not the raw entry.
    """
    if today is None:
        today = datetime.strptime(_build_date(), "%Y-%m-%d").date()
    candidates = []
    for key in ("date", "block_update_date"):
        val = dep.get(key)
        if not val:
            continue
        try:
            d = datetime.strptime(val, "%Y-%m-%d").date()
            candidates.append(((d - today).days, val))
        except Exception:
            continue
    if not candidates:
        return 999, str(dep.get("date", ""))
    future = [c for c in candidates if c[0] >= 0]
    return min(future) if future else max(candidates)


def days_until_nearest_enforcement(dep, today=None):
    """Back-compat shim returning only the day count (see nearest_enforcement)."""
    return nearest_enforcement(dep, today)[0]


def _build_date():
    """Return the explicit source date used by every generated artifact.

    A committed date makes rebuilds reproducible on every day, not merely within
    one UTC day. Update BUILD_DATE when public source content changes; release
    automation may override it with EOLKITS_BUILD_DATE.
    """
    value = os.environ.get("EOLKITS_BUILD_DATE")
    if value is None:
        value = BUILD_DATE_FILE.read_text(encoding="utf-8").strip()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("EOLKITS build date must use YYYY-MM-DD") from exc
    return value


def _truncate_meta(text, limit=158):
    """Collapse whitespace and trim a meta description to <= limit chars on a word
    boundary, so it isn't cut mid-word in SERPs. The value is plain text (the
    template escapes it), so this never truncates inside an HTML entity."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def _og_image_meta():
    """OG + Twitter image tags (absolute URLs, no user data) so links unfurl with a
    card instead of a blank box. The PNG itself is emitted by write_og_image()."""
    img = f"{SITE_URL}/og-default.png"
    return (
        f'<meta property="og:image" content="{img}">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:image" content="{img}">\n'
    )


def write_og_image(path):
    """Emit a deterministic 1200x630 social card (solid brand slate) with only the
    stdlib, so every page's og:image/twitter:image resolves and unfurls aren't blank.
    Pure function of its inputs — preserves the build's determinism guarantee.
    (Placeholder art; a designed card can replace it without touching any meta tag.)"""
    import struct
    import zlib

    width, height = 1200, 630
    pixel = bytes((0x0F, 0x17, 0x2A))  # brand slate #0f172a

    def _chunk(tag, data):
        body = tag + data
        return (
            struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    raw = (b"\x00" + pixel * width) * height  # per row: filter byte 0 + RGB pixels
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def get_surge_price(base_price, days_until):
    """Audit has one price; deadlines are report context, not a price lever."""
    return base_price


def build_audit_page(pricing):
    """Build the audit checkout page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AWS deprecation evidence report | EOLkits</title>
<meta name="description" content="A static repository evidence report for AWS runtime and Amazon Linux migration risks: exact file/line evidence, remediation, and official source links.">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:820px;margin:0 auto;padding:2rem;line-height:1.6;color:#111827}
.brand{color:#2563eb;font-weight:600}
h1{margin-top:.3rem}
.lede{font-size:1.15rem;color:#374151}
.cta{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:.7rem 1.2rem;border-radius:6px;font-weight:600}
.cta:hover{background:#1d4ed8}
.cta.secondary{background:#fff;color:#2563eb;border:2px solid #2563eb}
.callout{background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #2563eb;border-radius:8px;padding:1.25rem;margin:1.5rem 0}
.pricing{border:2px solid #e5e7eb;border-radius:8px;padding:1.5rem;margin:1.5rem 0}
.price{font-size:2rem;font-weight:700;color:#059669}
.tiers{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin:1rem 0}
.tier{border:1px solid #d1d5db;border-radius:6px;padding:1rem;text-align:center}
.tier.urgent{border-color:#dc2626;background:#fef2f2}
.tier.soon{border-color:#f59e0b;background:#fffbeb}
.valuebox{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:1.25rem;margin:1.5rem 0}
.guarantee{background:#ecfdf5;border:2px solid #059669;border-radius:8px;padding:1.5rem;margin:1.5rem 0}
.guarantee h3{margin-top:0;color:#059669}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin:1.5rem 0}
.cell{border:1px solid #e5e7eb;border-radius:8px;padding:1rem;font-size:.92rem}
.cell h4{margin:.2rem 0}
.logos{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}
.logos span{border:1px solid #d1d5db;border-radius:999px;padding:.3rem .8rem;font-size:.85rem;color:#374151;background:#f9fafb}
.reassure{color:#6b7280;font-size:.9rem;margin:.5rem 0}
.faq{margin:2rem 0}
.faq details{border-bottom:1px solid #e5e7eb;padding:.75rem 0}
.faq summary{font-weight:600;cursor:pointer}
button{background:#2563eb;color:white;border:none;padding:0.75rem 1.5rem;border-radius:6px;font-size:1rem;cursor:pointer}
button:hover{background:#1d4ed8}
form#auditForm{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:1.5rem;margin:1rem 0}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.875rem}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1>Turn a repository into reviewable AWS migration evidence</h1>
<p class="lede">Upload one repository ZIP or supported source file. The <strong>$299 evidence report</strong> returns the exact files and lines that matched, a prioritized remediation order, and a source link for every rule. It is a static source scan—not a live AWS inventory.</p>

<div class="callout">
  <strong>Don't take our word for it.</strong> &nbsp;<a class="cta secondary" href="/scan/">▶ Run the free scan</a><br>
  Check representative files locally before paying. The paid report adds repository-wide ZIP scanning, exact line evidence, a sequenced remediation plan, and an evidence fingerprint.
</div>

<h2>What you get</h2>
<ul>
  <li>Exact <strong>file:line evidence</strong> and observed match counts—no invented resource counts</li>
  <li>A <strong>roll-forward order</strong> based on finding severity and observed reach</li>
  <li>Official AWS, Python, Node.js, or project source link for every configured rule</li>
  <li>Explicit scope and limitations: what was scanned, skipped, and not inferred</li>
  <li>Input SHA-256 plus a deterministic <strong>evidence fingerprint</strong> verifiable at <code>/verify/</code></li>
</ul>
<p><a class="cta secondary" href="/audit/sample/">▶ See an illustrative fictional sample →</a></p>

<div class="pricing">
  <h2>Pricing</h2>
  <div class="tiers"><div class="tier"><strong>One repository</strong><div class="price">$299</div><p>ZIP archive or one supported source file · one fixed price</p></div></div>
  <p class="reassure">A target date may be included as planning context. It never changes the price or scan results.</p>
</div>

<div class="valuebox">
  <strong>What this buys:</strong> a reviewable change-approval artifact your team can check against the uploaded repository and the linked official sources. No speculative downtime-dollar estimate is included.
</div>

<div class="guarantee">
  <h3>30-day refund policy</h3>
  <p><strong>Request a full refund within 30 days.</strong> Email from the purchase address with the Stripe receipt or Checkout Session identifier; no explanation is required.</p>
  <p>If fulfillment permanently fails after retries, the system queues a full refund. Any refund that cannot be confirmed is surfaced for operator review.</p>
</div>

<h2>Why you can trust the report (without trusting the brand)</h2>
<div class="grid">
  <div class="cell"><h4>Evidence, not estimates</h4>Each match includes the observed file, line, and text.</div>
  <div class="cell"><h4>Checkable sources</h4>Each configured rule links the official documentation used for the claim.</div>
  <div class="cell"><h4>Repeatable findings</h4>The evidence fingerprint covers the input hash, rule-pack version, and canonical findings.</div>
  <div class="cell"><h4>Bounded scope</h4>The report says plainly that it does not query AWS or prove a complete inventory.</div>
</div>

<div class="logos">
  <span>AWS</span><span>CloudFormation / SAM</span><span>CDK</span><span>Terraform</span><span>Serverless</span><span>Ansible</span><span>Packer</span><span>cloud-init</span><span>GitHub Actions</span>
</div>

<h2>How it works</h2>
<ol>
  <li>Upload a repository ZIP or a supported SAM / CDK / Terraform / Serverless / cloud-init source file (10 MiB compressed maximum)</li>
  <li>We safely inspect supported text files without extracting the archive to disk</li>
  <li>Get a PDF by email after automated processing; delays and retries are possible</li>
  <li>Verify the evidence metadata at <code>/verify/</code></li>
</ol>

<p class="reassure">🔒 Secure checkout via Stripe · automated delivery with durable retries · 30-day money-back guarantee</p>

<div id="auditGate" class="callout"><strong>Checkout safety check:</strong> waiting for the v2 fulfillment backend. Checkout stays closed unless the live API confirms report engine 2.0.</div>
<form id="auditForm" hidden>
  <h3>Start Audit</h3>
  <p><input type="email" id="auditEmail" name="email" placeholder="your@email.com" required style="padding:0.5rem;width:300px"></p>
  <p><input type="date" id="auditDeadline" name="deadline" style="padding:0.5rem;width:300px" aria-label="Deadline date"></p>
  <p><input type="file" id="auditFile" name="file" required accept=".zip,.yaml,.yml,.json,.tf,.tfvars,.js,.ts,.tsx,.py,.toml,.lock,.sh,.txt"></p>
  <p class="reassure">Upload limits: 10 MiB input; ZIPs may contain at most 2,000 files and 25 MiB expanded text. Encrypted, path-traversing, binary, and suspiciously compressed archives are rejected before checkout. Do not upload secrets or unrelated personal data.</p>
  <button id="auditSubmit" type="submit">Upload and Proceed to Checkout</button>
  <p class="reassure">By continuing, you authorize this upload to be scanned and agree to the <a href="/legal/terms.html">Terms</a> and <a href="/legal/privacy.html">Privacy Policy</a>. Stripe Checkout shows the final $299 price before payment.</p>
  <p id="auditStatus" style="color:#6b7280;font-size:.875rem"></p>
</form>

<script>
const API = '{API_URL}';
const qp = new URLSearchParams(location.search);
function attribution() {{
  var ft = {{}};
  try {{ ft = JSON.parse(localStorage.getItem('eolkits_ft') || '{{}}'); }} catch (e) {{}}
  return {{
    source: ft.source || qp.get('source') || 'audit_page',
    utm_source: ft.utm_source || qp.get('utm_source') || '',
    utm_medium: ft.utm_medium || qp.get('utm_medium') || '',
    utm_campaign: ft.utm_campaign || qp.get('utm_campaign') || '',
    kit: ft.kit || qp.get('kit') || ''
  }};
}}
function track(eventName, extra) {{
  try {{
    const payload = Object.assign({{ event: eventName, sku: 'audit', path: location.pathname }}, attribution(), extra || {{}});
    navigator.sendBeacon(API + '/api/events', new Blob([JSON.stringify(payload)], {{ type: 'application/json' }}));
  }} catch (e) {{}}
}}
function apiMessage(data, fallback) {{
  if (data && typeof data.detail === 'string') return data.detail;
  if (data && data.detail && typeof data.detail.error === 'string') return data.detail.error;
  if (data && typeof data.error === 'string') return data.error;
  return fallback;
}}
const auditForm = document.getElementById('auditForm');
const auditStatus = document.getElementById('auditStatus');
const auditSubmit = document.getElementById('auditSubmit');
const deadlineInput = document.getElementById('auditDeadline');
const auditGate = document.getElementById('auditGate');
// Prefill report context from a deadline-tagged migration page. The deadline does
// not alter price.
if (qp.get('deadline') && deadlineInput) deadlineInput.value = qp.get('deadline');
if (qp.get('cancelled')) auditStatus.textContent = 'Checkout cancelled — finish whenever you are ready.';
track('view');
fetch(API + '/api/capabilities').then(r => r.ok ? r.json() : Promise.reject()).then(c => {{
  const a = c && c.audit;
  if (a && a.checkout_enabled === true && String(a.report_version) === '2.0') {{
    auditForm.hidden = false;
    auditGate.hidden = true;
  }} else {{
    auditGate.textContent = 'Audit checkout is temporarily paused while fulfillment is verified.';
  }}
}}).catch(() => {{ auditGate.textContent = 'Audit checkout is temporarily paused while fulfillment is verified.'; }});
auditForm.addEventListener('submit', async (event) => {{
  event.preventDefault();
  const file = document.getElementById('auditFile').files[0];
  const email = document.getElementById('auditEmail').value;
  const deadline = deadlineInput ? deadlineInput.value : '';
  if (!file || !email) return;
  if (file.size > 10 * 1024 * 1024) {{
    auditStatus.textContent = 'Upload must be 10 MiB or smaller.';
    return;
  }}

  auditSubmit.disabled = true;
  auditStatus.textContent = 'Requesting upload URL...';

  try {{
    const presign = await fetch(API + '/upload/presign', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        filename: file.name,
        contentType: file.type || 'application/octet-stream',
        size: file.size
      }})
    }});
    const presignData = await presign.json();
    if (!presign.ok) throw new Error(apiMessage(presignData, 'Upload storage is unavailable'));

    auditStatus.textContent = 'Uploading audit input...';
    const upload = await fetch(presignData.uploadUrl, {{
      method: 'PUT',
      headers: {{ 'Content-Type': file.type || 'application/octet-stream' }},
      body: file
    }});
    if (!upload.ok) throw new Error('Upload failed');

    auditStatus.textContent = 'Opening secure checkout...';
    track('checkout_click', {{ deadline: deadline }});
    const a = attribution();
    const checkoutBody = new URLSearchParams({{ email: email, upload_id: presignData.uploadId }});
    if (deadline) checkoutBody.set('deadline', deadline);
    for (const k of ['source', 'utm_source', 'utm_medium', 'utm_campaign', 'kit']) {{
      if (a[k]) checkoutBody.set(k, a[k]);
    }}
    const checkout = await fetch(API + '/api/audit/checkout', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
      body: checkoutBody
    }});
    const checkoutData = await checkout.json();
    if (!checkout.ok || !checkoutData.url) throw new Error(apiMessage(checkoutData, 'Checkout failed'));
    window.location.href = checkoutData.url;
  }} catch (error) {{
    auditSubmit.disabled = false;
    auditStatus.textContent = error instanceof Error ? error.message : 'Audit checkout failed';
  }}
}});
</script>

<div class="faq">
<h2>Questions</h2>
<details><summary>Why pay when the CLI is free?</summary><p>The CLI is the right choice for hands-on engineers. The paid product packages repository-wide evidence, line locations, prioritization, limitations, and sources into a shareable PDF.</p></details>
<details><summary>Is my code safe?</summary><p>Uploads travel over TLS, are used only for report generation, and are deleted after successful delivery. Unchecked uploads normally expire within 24 hours; checkout-bound uploads are retained for no more than 48 hours so retries can finish. Generated reports expire within 30 days. Prefer no upload? Use the free local tools.</p></details>
<details><summary>How can I trust the results?</summary><p>Check the exact file/line evidence and official source for each rule. The report carries an input hash and evidence fingerprint. It does not claim to be a digitally signed PDF.</p></details>
<details><summary>How fast is it?</summary><p>Processing is automated, but delivery time depends on queue, runner, and email-provider availability. Failed jobs retry and unresolved failures surface for refund review.</p></details>
<details><summary>What if it's wrong, or I'm just not happy?</summary><p>Email us within 30 days for a full refund. No questions asked.</p></details>
</div>

<footer>
  <p>Automated delivery · file/line evidence · official sources · input hash + evidence fingerprint · 30-day money-back guarantee.</p>
  <p><a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a> · <a href="/scan/">Free scan</a> · <a href="/audit/sample/">Sample report</a></p>
</footer>
</body>
</html>"""
    return _interpolate_api(html)


def build_audit_sample_page(pricing):
    """A redacted, illustrative sample of the Audit report rendered as HTML — the
    'see exactly what you get' proof artifact. Static and deterministic; not passed
    through _interpolate_api (no API origin needed)."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sample audit report — EOLkits</title>
<meta name="description" content="Illustrative EOLkits evidence report format: exact file/line matches, observed reach, remediation order, limitations, and official source links.">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:820px;margin:0 auto;padding:2rem;line-height:1.6;color:#111827}
.brand{color:#2563eb;font-weight:600}
.banner{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:.75rem 1rem;margin:1rem 0;font-size:.9rem}
.meta{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin:1rem 0;font-size:.9rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.92rem}
th,td{border:1px solid #e5e7eb;padding:.5rem .6rem;text-align:left;vertical-align:top}
th{background:#f3f4f6}
.sev{font-weight:700;white-space:nowrap}
.crit{color:#dc2626}
.high{color:#ea580c}
.med{color:#ca8a04}
.cta{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:.7rem 1.2rem;border-radius:6px;font-weight:600;margin:1rem 0}
code{background:#f3f4f6;padding:.1rem .3rem;border-radius:4px}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:.875rem}
</style>
</head>
<body>
<a href="/audit/" class="brand">← Back to Audit</a>
<div class="banner"><strong>ILLUSTRATIVE SAMPLE.</strong> This fictional repository shows the v2 report format. It is not a customer report or evidence of a live AWS account scan.</div>
<h1>AWS deprecation evidence report</h1>
<div class="meta">
  <div><strong>Uploaded artifact:</strong> <code>fictional-repository.zip</code></div>
  <div><strong>Observed scope:</strong> 6 supported text files; 1 unsupported binary skipped</div>
  <div><strong>Input SHA-256:</strong> <code>3f9a…c1e2</code></div>
  <div><strong>Evidence fingerprint:</strong> <code>8b74…91aa</code> — metadata lookup at <code>/verify/</code></div>
  <div><strong>Findings:</strong> 4 distinct risk types · 6 file/line evidence records</div>
</div>

<div class="banner"><strong>Scope limitation:</strong> static uploaded-source scan only. No AWS account was queried; resource inventory and runtime behavior are not inferred.</div>

<h2>Prioritized findings</h2>
<table>
<tr><th>Severity</th><th>Finding</th><th>Observed location</th><th>Official source</th></tr>
<tr><td class="sev crit">Critical</td><td>Amazon Linux 2 dependency</td><td><code>infra/main.tf:12</code><br><code>images/Dockerfile:1</code></td><td><a href="https://aws.amazon.com/amazon-linux-2/faqs/">Amazon Linux 2 FAQ</a></td></tr>
<tr><td class="sev crit">Critical</td><td><code>distutils</code> removed in Python 3.12</td><td><code>src/compat.py:2</code></td><td><a href="https://docs.python.org/3/whatsnew/3.12.html#distutils">Python 3.12 changes</a></td></tr>
<tr><td class="sev high">High</td><td><code>amazon-linux-extras</code> removed in AL2023</td><td><code>scripts/bootstrap.sh:4</code></td><td><a href="https://docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html">AWS AL2/AL2023 comparison</a></td></tr>
<tr><td class="sev high">High</td><td>Lambda Python 3.9 runtime reference</td><td><code>template.yaml:18</code><br><code>serverless.yml:9</code></td><td><a href="https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html">Lambda runtime table</a></td></tr>
</table>

<h2>Roll-forward roadmap</h2>
<ol>
  <li>Replace the two observed AL2 image references and remove the incompatible Extras command; validate a rebuilt image in staging.</li>
  <li>Replace the observed <code>distutils</code> import and run the Python test suite on the target runtime.</li>
  <li>Update the two observed Lambda runtime fields, rebuild dependencies, and deploy through the repository's normal canary/rollback controls.</li>
</ol>

<h2>What the report does not claim</h2>
<p>It does not estimate downtime dollars, count deployed instances/functions, inspect omitted files, or guarantee that a match is reachable at runtime. Those facts require environment-specific validation.</p>

<a class="cta" href="/audit/">Get this report for your own stack — from $299 →</a>
<p><a href="/scan/">Or run the free scan first →</a></p>

<footer>
  <p>Production reports include exact observed evidence, rule sources, input SHA-256, and a deterministic evidence fingerprint. The PDF itself is not digitally signed.</p>
  <p><a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></p>
</footer>
</body>
</html>"""
    return html


def _build_unavailable_product_page(name: str, explanation: str) -> str:
    """Render a noindex tombstone for a retired or unproved product route."""
    import html

    safe_name = html.escape(name)
    safe_explanation = html.escape(explanation)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow">
<title>{safe_name} is unavailable — EOLkits</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:2rem;line-height:1.6}}
.brand{{color:#2563eb;font-weight:600}}
.badge{{display:inline-block;background:#fef3c7;color:#92400e;border-radius:999px;padding:.25rem .75rem;font-size:.82rem;font-weight:700}}
.box{{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:1.25rem;margin:1.5rem 0}}
footer{{margin-top:3rem;border-top:1px solid #e5e7eb;padding-top:1rem;color:#6b7280;font-size:.875rem}}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1>{safe_name} is unavailable</h1>
<p class="badge">No checkout · no account · no waitlist</p>
<p>{safe_explanation}</p>
<div class="box"><strong>Available now:</strong> use the <a href="/scan/">free local browser scanner</a>, or check whether the server-gated <a href="/audit/">$299 repository evidence report</a> is open.</div>
<footer><a href="/">Home</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></footer>
</body>
</html>"""


def build_pack_page(pricing):
    """Keep the legacy Migration Pack route safe without advertising a beta."""
    del pricing
    return _build_unavailable_product_page(
        "Migration Pack",
        "The former automated pull-request offer was never proved through a public "
        "GitHub App and paid end-to-end fulfillment. It is not offered for sale.",
    )


def build_license_page(pricing):
    """Keep the legacy organization-license route safe."""
    del pricing
    return _build_unavailable_product_page(
        "Organization License",
        "The former private-rule feed and organization controls were not built or "
        "operationally verified. No organization product or license is offered.",
    )


def load_deprecations():
    """Load cited deprecation data from the public rules file."""
    deprecations_file = BASE_DIR.parent.parent / "rules" / "public" / "deprecations.yml"
    if deprecations_file.exists():
        with open(deprecations_file) as f:
            data = yaml.safe_load(f) or {}
        entries = data.get("deprecations", [])
        if not isinstance(entries, list):
            raise ValueError("rules/public/deprecations.yml: deprecations must be a list")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or not str(entry.get("url") or "").startswith(
                "https://"
            ):
                raise ValueError(
                    f"rules/public/deprecations.yml: deprecations[{index}] needs an HTTPS primary-source url"
                )
        return data
    return {"deprecations": []}


def slugify(name):
    """Convert name to URL slug."""
    return name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")


def deprecation_slug(dep):
    """Use an explicit stable route when a corrected display name replaces old copy."""
    return str(dep.get("slug") or slugify(str(dep.get("name", ""))))


def build_pricing_view(full_pricing):
    """Extract canonical Audit price/link facts for public pages."""
    skus = full_pricing.get("skus", full_pricing)

    audit = skus.get("audit", {})
    audit_tiers = {t.get("name"): t for t in audit.get("tiers", [])}
    standard = audit_tiers.get("standard", {})
    audit_base = standard.get("price_usd", 299)

    # Always route to the on-site page, which opens a server-side Checkout
    # Session. Direct Stripe Payment Links are intentionally not used because
    # they bypass the input-bound fulfillment gate.
    return {
        "audit_pdf": {
            "base": audit_base,
            "link": "/audit/",
        },
    }


def _audit_checkout_link(dep):
    """Deadline- and kit-tagged link to the on-site audit page, which carries
    report context and attribution into the server Checkout Session. Replaces raw
    Stripe Payment Links and keeps price enforcement server-side."""
    from urllib.parse import urlencode

    _, deadline_date = nearest_enforcement(dep)
    q = {
        "deadline": deadline_date,
        "utm_source": "migrate",
        "utm_medium": "cta",
        "utm_campaign": dep.get("slug", ""),
    }
    if dep.get("kit"):
        q["kit"] = dep["kit"]
    return "/audit/?" + urlencode(q)


def compute_urgency(dep, pricing_view):
    """Deterministic urgency and flat Audit pricing from canonical data."""
    days, deadline_date = nearest_enforcement(dep)
    audit = pricing_view["audit_pdf"]

    if days < 0:
        tier, label = "passed", "deadline passed"
        headline = (
            f"This deadline passed on {deadline_date}. "
            "Affected resources are now in the post-deadline window — clean up before the next enforcement phase."
        )
    elif days <= 7:
        tier, label = "urgent", "less than 7 days"
        headline = f"Only {days} days until the {deadline_date} deadline. This is the final week."
    elif days <= 30:
        tier, label = "soon", "within 30 days"
        headline = f"{days} days until the {deadline_date} deadline."
    else:
        tier, label = "ahead", "more than 30 days out"
        headline = (
            f"{days} days until the {deadline_date} deadline — enough runway to migrate safely."
        )

    return {
        "tier": tier,
        "label": label,
        "headline": headline,
        "days_until": days,
        # The date the day count actually runs to — interpolated wherever a date is
        # shown next to days_until, so copy and the JS countdown never disagree.
        "deadline_date": deadline_date,
        "audit_price": audit["base"],
        # Server-routed, deadline+kit+UTM tagged. The server enforces one flat
        # Audit price; the deadline is report context only.
        "audit_link": _audit_checkout_link(dep),
    }


def find_related(dep, all_deps, limit=4):
    """Internal-linking signal: deprecations sharing a kit or any tag.
    Deterministic ordering (by deadline date) so output is stable."""
    dep_tags = set(dep.get("tags", []))
    related = []
    for other in all_deps:
        if other["slug"] == dep["slug"]:
            continue
        same_kit = other.get("kit") and other.get("kit") == dep.get("kit")
        shared_tags = dep_tags & set(other.get("tags", []))
        if same_kit or shared_tags:
            related.append(other)
    related.sort(key=lambda d: d.get("date", "9999-99-99"))
    return related[:limit]


def build_migration_pages(deprecations, full_pricing):
    """Build deterministic pages from reviewed rule data and provider links."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )

    try:
        template = env.get_template("migrate.html.j2")
    except Exception:
        # Fallback if template doesn't exist
        return {}

    pricing_view = build_pricing_view(full_pricing)

    all_deps = deprecations.get("deprecations", [])
    for dep in all_deps:
        dep["slug"] = deprecation_slug(dep)

    build_date = _build_date()
    pages = {}
    for dep in all_deps:
        urgency = compute_urgency(dep, pricing_view)
        related = find_related(dep, all_deps)
        meta_description = _truncate_meta(
            f"{dep['name']}: tracked milestone {urgency['deadline_date']} "
            f"({urgency['label']}). {dep.get('service', '')}. "
            f"{len(dep.get('breaking_changes', []))} migration checks to verify, "
            f"plus a free bounded CLI ({dep.get('kit') or 'EOLkits'})."
        )
        html = template.render(
            deprecation=dep,
            pricing=pricing_view,
            urgency=urgency,
            related=related,
            site_url=SITE_URL,
            now=build_date,
            meta_description=meta_description,
        )
        pages[f"migrate/{dep['slug']}/index.html"] = html

    # Hub / index page that links every deprecation page (internal linking +
    # crawlable entry point referenced by every leaf page's breadcrumb).
    pages["migrate/index.html"] = build_migrate_index(all_deps, pricing_view, build_date)

    return pages


def build_migrate_index(all_deps, pricing_view, now_iso):
    """Deterministic hub page listing every tracked AWS deprecation,
    ordered by deadline, with cited deadlines and severities."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    ordered = sorted(all_deps, key=lambda d: d.get("date", "9999-99-99"))
    rows = []
    for dep in ordered:
        urgency = compute_urgency(dep, pricing_view)
        rows.append(
            {
                **dep,
                "days_until": urgency["days_until"],
                "tier": urgency["tier"],
            }
        )
    try:
        template = env.get_template("migrate_index.html.j2")
    except Exception:
        return ""
    return template.render(deprecations=rows, site_url=SITE_URL, now=now_iso)


def build_sitemap(deprecations):
    """Build sitemap.xml."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )

    try:
        template = env.get_template("sitemap.xml.j2")
    except Exception:
        return None

    # Add slugs to deprecations
    for dep in deprecations.get("deprecations", []):
        dep["slug"] = deprecation_slug(dep)

    return template.render(
        deprecations=deprecations.get("deprecations", []),
        fixes=[f["slug"] for f in load_fixes()],
        now=_build_date(),
        site_url=SITE_URL,
    )


def build_llms_txt(deprecations, pricing_view):
    """Build deterministic discovery text from reviewed rule data."""
    all_deps = deprecations.get("deprecations", [])
    for dep in all_deps:
        dep["slug"] = deprecation_slug(dep)
    ordered = sorted(all_deps, key=lambda d: d.get("date", "9999-99-99"))

    lines = [
        "# EOLkits",
        "",
        "> Deterministic, source-linked CLIs and migration guidance for AWS "
        "platform deprecation milestones (Lambda runtimes and Amazon Linux 2). "
        "Provider dates link their primary source; severity is EOLkits triage.",
        "",
        "## AWS deprecation deadlines",
        "",
    ]
    for dep in ordered:
        page = f"{SITE_URL}/migrate/{dep['slug']}/"
        lines.append(
            f"- [{dep['name']}]({page}): deadline {dep['date']}, "
            f"severity {dep.get('severity', 'n/a')}, service {dep.get('service', 'n/a')}. "
            f"Source: {dep.get('url', '')}"
        )

    fixes = load_fixes()
    if fixes:
        lines += ["", "## Common migration errors (verified fixes)", ""]
        for fx in fixes:
            lines.append(
                f"- [{fx['error']}]({SITE_URL}/fix/{fx['slug']}/): "
                f"{fx.get('summary', '')} Source: {fx.get('source_url', '')}"
            )
        lines.append(
            f"- [Free in-browser scanner]({SITE_URL}/scan/): drop IaC / dependency files "
            f"to find deprecated runtimes and incompatible dependencies locally — nothing uploaded."
        )

    lines += [
        "",
        "## Pricing",
        "",
        "- Free CLI: MIT-licensed kits (al2023-gate, python-pivot, lambda-lifeline). "
        "git clone https://github.com/ntoledo319/EOLkits",
        f"- [Audit PDF]({SITE_URL}/audit/): ${pricing_view['audit_pdf']['base']} "
        f"— one repository ZIP or supported source file; exact file/line evidence, "
        f"remediation order, source links, and a deterministic evidence fingerprint.",
        "- No subscription, AWS-account inventory, or automated pull-request product is for sale.",
        "",
        "## Calendar",
        "",
        f"- [Deadline calendar (.ics)]({SITE_URL}/deprecations.ics): subscribe to "
        f"every tracked AWS deprecation deadline.",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_robots_txt():
    """robots.txt pointing crawlers at the sitemap and llms.txt."""
    return "User-agent: *\n" "Allow: /\n" "\n" f"Sitemap: {SITE_URL}/sitemap.xml\n"


def build_verify_page():
    """Build the verification page."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )

    try:
        template = env.get_template("verify.html.j2")
        return template.render()
    except Exception:
        return None


def build_lambda_schedule_page(deprecations, pricing_view):
    """Head-term reference page — the AWS Lambda runtime deprecation schedule, built
    from the cited deprecations.yml. Targets high-volume 'lambda runtime deprecation
    schedule / dates / end of life' queries; each row links its /migrate guide + the
    AWS source. Static & deterministic (not passed through _interpolate_api)."""
    import html as _h

    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299
    lam = [
        d
        for d in deprecations.get("deprecations", [])
        if "lambda" in (str(d.get("service", "")) + " " + " ".join(d.get("tags", []))).lower()
    ]
    lam.sort(key=lambda d: str(d.get("block_update_date") or d.get("date") or "9999-12-31"))
    rows = ""
    for d in lam:
        name = _h.escape(str(d.get("name", "")))
        slug = deprecation_slug(d)
        rt = _h.escape(_runtime_id_from_name(str(d.get("name", ""))) or name)
        create = _h.escape(str(d.get("date") or "—"))
        update = _h.escape(str(d.get("block_update_date") or "—"))
        sev = _h.escape(str(d.get("severity", "")))
        tags = " ".join(d.get("tags", [])).lower()
        target = "python3.12" if "python" in tags else ("nodejs24.x" if "nodejs" in tags else "—")
        src = _h.escape(str(d.get("url", "")))
        rows += (
            '<tr><td><a href="/migrate/' + slug + '/"><code>' + rt + "</code></a></td>"
            "<td>" + create + "</td><td>" + update + "</td>"
            '<td class="sev sev-' + sev + '">' + sev + "</td>"
            "<td><code>" + target + "</code></td>"
            '<td><a href="' + src + '" target="_blank" rel="noopener nofollow">AWS</a></td></tr>'
        )
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "What happens when an AWS Lambda runtime is deprecated?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Existing functions keep running after deprecation, but AWS no longer applies runtime updates or security patches. AWS publishes separate dates for blocking creation and updates; those intervals vary, so use the current per-runtime table rather than assuming a fixed delay.",
                },
            },
            {
                "@type": "Question",
                "name": "How do I find which Lambda runtimes I'm using?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Run the free scanner at eolkits.com/scan over your SAM/CDK/Terraform/Serverless config (nothing is uploaded), or run: aws lambda list-functions --query 'Functions[].Runtime'.",
                },
            },
            {
                "@type": "Question",
                "name": "What should I upgrade Lambda Python and Node runtimes to?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "EOLkits' bounded rewrite paths currently target python3.12 and nodejs24.x; that is a tool choice, not an AWS recommendation. Recheck AWS's current support table, then test removed standard-library modules, SDK packaging, and native-wheel or ABI changes on the chosen target.",
                },
            },
        ],
    }
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>AWS Lambda runtime deprecation schedule (2026–2027) | EOLkits</title>\n"
        '<meta name="description" content="Tracked AWS Lambda runtime deprecation dates for python3.9-3.11 and nodejs18/20/22, including published create/update block dates, EOLkits bounded targets, and AWS source links.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/lambda-runtime-deprecation-schedule/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
        "<style>.sched{width:100%;border-collapse:collapse;margin:1.25rem 0;font-size:.92rem}"
        ".sched th,.sched td{border:1px solid #e5e7eb;padding:.5rem .6rem;text-align:left}"
        ".sched th{background:#f3f4f6}.sched .sev{font-weight:700}"
        ".sev-critical{color:#dc2626}.sev-high{color:#ea580c}.sev-medium{color:#ca8a04}"
        ".cta{display:inline-block;margin:1rem 0;padding:.7rem 1.2rem;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;font-weight:600}</style>\n"
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/migrate/">Deadlines</a> / <span>Lambda runtime schedule</span></nav>\n'
        "<h1>AWS Lambda runtime deprecation schedule (2026–2027)</h1>\n"
        "<p>For the runtimes EOLkits tracks: when patches stop, when AWS says it will block <strong>creating</strong> new functions, when it will block <strong>updating</strong> existing ones, and the target currently supported by these bounded tools. Each row links the AWS source; future dates can change.</p>\n"
        '<p><a class="cta" href="/scan/">Scan your stack free — find your deprecated runtimes →</a></p>\n'
        '<p>Prefer a 10-second check? Paste your config into the <a href="/eol-checker/">free AWS EOL checker</a> — nothing uploaded.</p>\n'
        '<table class="sched"><thead><tr><th>Runtime</th><th>Blocks create</th><th>Blocks update</th><th>Severity</th><th>EOLkits target</th><th>Source</th></tr></thead><tbody>\n'
        + rows
        + "\n</tbody></table>\n"
        '<p class="muted">Functions keep running after deprecation, but become unpatched and — after the block-update date — unmodifiable. Dates reflect the AWS-published schedule and can shift; the linked AWS page is authoritative.</p>\n'
        "<h2>Fixing the upgrade</h2>\n"
        '<p>The upgrade can surface specific errors — removed stdlib modules, the unbundled AWS SDK v2 on Node 18+, native-wheel/ABI breaks. See <a href="/fix/">common migration error fixes</a>, or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ", 30-day money-back)</a> for exact file/line matches, source links, and a remediation order.</p>\n"
        '<p><a href="/migrate/">See all tracked AWS deadlines →</a></p>\n'
        "</body>\n</html>\n"
    )


def build_eol_checker_page(deprecations, pricing_view):
    """Free interactive tool: paste your runtimes / IaC (or click chips) and instantly see
    which are past AWS end-of-life and when AWS blocks them. Runs entirely client-side —
    nothing is uploaded. The dataset is baked from the cited deprecations.yml, so the built
    HTML is static & deterministic (the day-countdown is computed in the browser). A linkable,
    shareable top-of-funnel asset that routes to the free /scan and the paid /audit."""
    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299

    rows = {}
    for d in deprecations.get("deprecations", []):
        name = str(d.get("name", ""))
        tags = " ".join(d.get("tags", [])).lower()
        block_create = str(d.get("date") or "")
        block_update = str(d.get("block_update_date") or d.get("date") or "")
        sev = str(d.get("severity", "medium"))
        slug = deprecation_slug(d)
        if "nodejs" in tags:
            rid = _runtime_id_from_name(name) or name
            matches = [rid.lower(), rid.replace(".x", "").lower()]
            target, kind = "nodejs24.x", "runtime"
        elif "python" in tags:
            rid = _runtime_id_from_name(name) or name
            matches = [rid.lower()]
            target, kind = "python3.12", "runtime"
        elif "al2" in tags or "amazon linux 2" in name.lower():
            rid = "Amazon Linux 2"
            matches = ["amazonlinux2", "amazon-linux-2", "amazon linux 2", "al2", "amazonlinux:2"]
            target, kind = "Amazon Linux 2023", "os"
        else:
            # Only Lambda runtimes + the AL2 OS belong in an "EOL checker"; skip config
            # enforcements (e.g. IMDSv1) so the block/EOL messaging stays accurate.
            continue
        rows[rid] = {
            "id": rid,
            "label": rid,
            "matches": sorted({m for m in matches if m}),
            "blockCreate": block_create,
            "blockUpdate": block_update,
            "sev": sev,
            "target": target,
            "slug": slug,
            "kind": kind,
        }
    data = sorted(rows.values(), key=lambda r: (r["blockUpdate"] or "9999-99-99", r["id"]))
    data_json = json.dumps(data, sort_keys=True)

    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "How do I know if my AWS Lambda runtime is deprecated?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Paste SAM/CloudFormation/Terraform/Serverless source or a runtime list, or click a runtime. The browser checker matches configured text patterns against the cited AWS Lambda deprecation table; it does not query an AWS account.",
                },
            },
            {
                "@type": "Question",
                "name": "Is Amazon Linux 2 end of life?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Amazon Linux 2 reached its published end-of-life date on 2026-06-30. Verify the installed release and current AWS support terms; Amazon Linux 2023 is the durable migration path.",
                },
            },
            {
                "@type": "Question",
                "name": "Does this tool upload my configuration?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Configuration contents stay in the browser. The site sends a count-only usage event; it does not send file names or contents.",
                },
            },
        ],
    }

    js = (
        "<script>\n"
        "var RT = " + data_json + ";\n"
        "function daysBetween(a,b){return Math.round((a-b)/86400000);}\n"
        "function statusFor(r){\n"
        "  var now=new Date();var bc=r.blockCreate?new Date(r.blockCreate+'T00:00:00Z'):null;var bu=r.blockUpdate?new Date(r.blockUpdate+'T00:00:00Z'):null;\n"
        "  if(r.kind==='os'){\n"
        "    if(bc&&now>bc)return{cls:'crit',txt:'Published end-of-life date passed '+r.blockCreate+' — verify the installed release and current support terms; migrate to '+r.target+'.'};\n"
        "    if(bc){var d=daysBetween(bc,now);return{cls:d<60?'crit':(d<180?'high':'med'),txt:d+' days until end of life ('+r.blockCreate+'). Migrate to '+r.target+'.'};}\n"
        "    return{cls:'high',txt:'End of life — migrate to '+r.target+'.'};\n"
        "  }\n"
        "  if(bu&&now>bu)return{cls:'crit',txt:'Updates already BLOCKED (since '+r.blockUpdate+') — functions are frozen on this runtime.'};\n"
        "  if(bc&&now>bc)return{cls:'crit',txt:'New-function creation BLOCKED (since '+r.blockCreate+'); updates block '+r.blockUpdate+'.'};\n"
        "  if(bc){var dc=daysBetween(bc,now);return{cls:dc<60?'crit':(dc<180?'high':'med'),txt:dc+' days until AWS blocks creating new functions ('+r.blockCreate+'); updates block '+r.blockUpdate+'.'};}\n"
        "  return{cls:'high',txt:'Deprecated / end-of-life — migrate off it.'};\n"
        "}\n"
        "var picked={};\n"
        "function render(){\n"
        "  var out=document.getElementById('results');var keys=Object.keys(picked);\n"
        "  if(!keys.length){out.innerHTML='';return;}\n"
        "  var rowsById={};RT.forEach(function(r){rowsById[r.id]=r;});\n"
        "  var html='<table class=\"res\"><thead><tr><th>Runtime</th><th>Status</th><th>Upgrade to</th><th></th></tr></thead><tbody>';\n"
        "  keys.sort();keys.forEach(function(k){var r=rowsById[k];if(!r)return;var s=statusFor(r);\n"
        "    html+='<tr class=\"'+s.cls+'\"><td><code>'+r.label+'</code></td><td>'+s.txt+'</td><td>'+(r.target?'<code>'+r.target+'</code>':'\\u2014')+'</td><td><a href=\"/migrate/'+r.slug+'/\">fix &rarr;</a></td></tr>';});\n"
        "  html+='</tbody></table>';\n"
        "  html+='<div class=\"ctaway\"><strong>This is a quick check of what you pasted.</strong> A real migration also needs every region, your IaC, and native-dependency landmines. '+\n"
        '    \'<a class="cta" href="/scan/">Run the full free scan &rarr;</a> or <a href="/audit/">get a $'
        + str(audit_base)
        + " repository evidence report</a> (30-day money-back).</div>';\n"
        "  out.innerHTML=html;\n"
        "}\n"
        "function check(){\n"
        "  var t=(document.getElementById('inp').value||'').toLowerCase();\n"
        "  RT.forEach(function(r){if(r.matches.some(function(m){return t.indexOf(m)>=0;}))picked[r.id]=1;});\n"
        "  render();\n"
        "}\n"
        "function toggle(id){if(picked[id])delete picked[id];else picked[id]=1;render();var el=document.querySelector('[data-id=\"'+id+'\"]');if(el)el.classList.toggle('on');}\n"
        "document.addEventListener('DOMContentLoaded',function(){\n"
        "  var chips=document.getElementById('chips');\n"
        "  RT.forEach(function(r){var b=document.createElement('button');b.className='chip';b.setAttribute('data-id',r.id);b.textContent=r.label;b.onclick=function(){toggle(r.id);};chips.appendChild(b);});\n"
        "  document.getElementById('go').onclick=check;\n"
        "});\n"
        "</script>\n"
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>AWS runtime EOL checker — is your Lambda runtime or Amazon Linux deprecated? | EOLkits</title>\n"
        '<meta name="description" content="Free, instant check: paste your AWS Lambda runtimes or IaC (or click your runtime) and see which are past end-of-life and when AWS blocks creating/updating functions. Nothing uploaded. Dates from the AWS runtime deprecation table.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/eol-checker/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
        "<style>#chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.75rem 0}"
        ".chip{border:1px solid #cbd5e1;background:#fff;border-radius:999px;padding:.35rem .7rem;font-size:.85rem;cursor:pointer;font-family:inherit}"
        ".chip.on{background:#2563eb;color:#fff;border-color:#2563eb}"
        "#inp{width:100%;min-height:110px;font-family:ui-monospace,Menlo,monospace;font-size:.85rem;padding:.6rem;border:1px solid #cbd5e1;border-radius:6px}"
        ".res{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem}"
        ".res th,.res td{border:1px solid #e5e7eb;padding:.5rem .6rem;text-align:left;vertical-align:top}"
        ".res th{background:#f3f4f6}.res tr.crit td{background:#fef2f2}.res tr.high td{background:#fff7ed}.res tr.med td{background:#fefce8}"
        ".cta{display:inline-block;margin:.3rem .3rem .3rem 0;padding:.7rem 1.2rem;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;font-weight:600}"
        ".ctaway{margin:1rem 0;padding:1rem;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px}"
        "#go{padding:.6rem 1.1rem;background:#111827;color:#fff;border:0;border-radius:6px;font-weight:600;cursor:pointer;font-family:inherit}</style>\n"
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/migrate/">Deadlines</a> / <span>EOL checker</span></nav>\n'
        "<h1>Is your AWS runtime past end-of-life?</h1>\n"
        '<p>Paste your SAM / CloudFormation / Terraform / Serverless config (or a list of runtimes), or click the runtimes you use. This checks them against EOLkits\' cited snapshot of the <a href="/lambda-runtime-deprecation-schedule/">AWS runtime deprecation schedule</a> and shows the tracked create/update block dates. <strong>Runs in your browser — nothing is uploaded.</strong></p>\n'
        '<div id="chips"></div>\n'
        '<textarea id="inp" placeholder="Paste template.yaml / serverless.yml / *.tf here — e.g. Runtime: nodejs20.x, python3.9, FROM amazonlinux:2 ..."></textarea>\n'
        '<p><button id="go">Check my runtimes</button></p>\n'
        '<div id="results"></div>\n'
        '<p class="muted">Dates come from the AWS Lambda runtime deprecation table and can shift; the per-runtime <a href="/migrate/">migration guides</a> link the AWS source. AWS documents phased create/update restrictions; verify the current runtime status before planning.</p>\n'
        "<h2>Once you know what's exposed</h2>\n"
        '<p>Each deprecated runtime fails in specific ways — removed stdlib modules, the unbundled AWS SDK v2 on Node 18+, native-wheel/ABI breaks, Amazon Linux 2 &rarr; 2023 package renames. See the <a href="/fix/">common error fixes</a>, run the <a href="/scan/">free scanner</a>, or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ", 30-day money-back)</a> for exact matches and a remediation order.</p>\n"
        + js
        + "</body>\n</html>\n"
    )


def build_al2_checklist_page(deprecations, pricing_view):
    """Head-term page — the Amazon Linux 2 -> AL2023 migration checklist, the highest-
    volume query in the current deadline window. Built from the cited deprecations.yml
    AL2 entry; cross-links the matching /fix pages. Static & deterministic."""
    import html as _h

    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299
    al2 = next(
        (
            d
            for d in deprecations.get("deprecations", [])
            if "amazon linux 2" in str(d.get("name", "")).lower()
        ),
        {},
    )
    date = _h.escape(str(al2.get("date", "2026-06-30")))
    src = _h.escape(
        str(
            al2.get("url", "https://aws.amazon.com/blogs/aws/update-on-amazon-linux-2-end-of-life/")
        )
    )
    changes_html = "".join("<li>" + _h.escape(c) + "</li>" for c in al2.get("breaking_changes", []))
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "When is Amazon Linux 2 end of life?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Amazon Linux 2 reached end of life on "
                    + date.replace("&amp;", "&")
                    + ". AWS has published post-EOL AL2 releases, so verify your installed release and current support terms; the durable path is migration to AL2023.",
                },
            },
            {
                "@type": "Question",
                "name": "What breaks moving from Amazon Linux 2 to AL2023?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "yum is replaced by dnf, amazon-linux-extras is gone, ntpd is replaced by chronyd, iptables is replaced by nftables, and Python 2 is no longer available. Package names also change (version-namespaced or moved to SPAL).",
                },
            },
            {
                "@type": "Question",
                "name": "Can I keep running Amazon Linux 2 after EOL?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Existing instances can keep running, but standard support has ended. Do not infer an individual host's patch state from the date alone; verify its installed release and migrate to Amazon Linux 2023.",
                },
            },
            {
                "@type": "Question",
                "name": "How do I find Amazon Linux 2 usage in my account?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Use the al2023-gate CLI from the repository to inspect its documented local or AWS inventory modes. The browser scanner covers only configured source patterns and does not enumerate an account.",
                },
            },
        ],
    }
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Amazon Linux 2 end-of-life: migration checklist (AL2 → AL2023) | EOLkits</title>\n"
        '<meta name="description" content="Amazon Linux 2 is EOL '
        + date
        + '. A step-by-step AL2 to AL2023 migration checklist: yum to dnf, amazon-linux-extras, ntpd to chronyd, iptables to nftables, Python 2 removal — with the fix for each error. Free scanner to find your AL2 usage.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/amazon-linux-2-eol-checklist/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
        "<style>.chk li{margin:.4rem 0}.cta{display:inline-block;margin:1rem 0;padding:.7rem 1.2rem;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;font-weight:600}"
        ".note{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:1rem;margin:1rem 0}</style>\n"
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/migrate/">Deadlines</a> / <span>Amazon Linux 2 checklist</span></nav>\n'
        "<h1>Amazon Linux 2 end-of-life: migration checklist (AL2 → AL2023)</h1>\n"
        '<div class="note"><strong>Amazon Linux 2 reached end of life '
        + date
        + '.</strong> Standard support ended and migration is due. AWS has published post-EOL AL2 releases, so verify the installed release and current support terms instead of assuming a host patch state from the calendar alone. <a href="'
        + src
        + '" target="_blank" rel="noopener nofollow">[AWS source]</a></div>\n'
        '<p><a class="cta" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/al2023-gate">Inspect the al2023-gate CLI coverage →</a></p>\n'
        "<h2>What changes on AL2023</h2>\n<ul>" + changes_html + "</ul>\n"
        '<h2>The checklist</h2>\n<ol class="chk">\n'
        "<li><strong>Inventory.</strong> Find AL2 AMIs, launch templates, EKS node groups, ECS task definitions, Beanstalk platforms, and container base images. Use the documented <code>al2023-gate</code> modes and verify the result against AWS inventory.</li>\n"
        "<li><strong>Rebuild the base AMI on AL2023</strong> (Packer/EC2 Image Builder), then bake your app layers on top.</li>\n"
        '<li><strong>Package manager.</strong> Move <code>yum</code> usage to <code>dnf</code> and drop <code>amazon-linux-extras</code> — install packages directly, version-namespaced, or via SPAL. (<a href="/fix/amazon-linux-extras-command-not-found/">extras fix</a> · <a href="/fix/amazon-linux-2023-dnf-unable-to-find-a-match/">missing-package fix</a>)</li>\n'
        '<li><strong>Time sync.</strong> Replace <code>ntpd</code> with <code>chronyd</code>. (<a href="/fix/amazon-linux-2023-ntpd-service-not-found/">ntpd fix</a>)</li>\n'
        "<li><strong>Firewall.</strong> Move <code>iptables</code> rules to <code>nftables</code>.</li>\n"
        '<li><strong>Python.</strong> AL2023 ships no Python 2 — port <code>python2</code> scripts/shebangs to <code>python3</code>. (<a href="/fix/amazon-linux-2023-python2-command-not-found/">python2 fix</a>)</li>\n'
        "<li><strong>Test</strong> boot, app start, networking, and time sync on a canary instance.</li>\n"
        "<li><strong>Roll out</strong> with a staged canary (5 → 25 → 50 → 100%) and a tested rollback to the previous AMI.</li>\n"
        "</ol>\n"
        "<h2>Do it faster</h2>\n"
        '<p>The free <a href="/scan/">scanner</a> and the MIT <code>al2023-gate</code> CLI detect and patch configured source patterns. Need a review artifact? The <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ', 30-day money-back)</a> returns exact observed file/line matches and a remediation order. See the full <a href="/migrate/amazon-linux-2-eol/">Amazon Linux 2 migration guide</a>.</p>\n'
        "</body>\n</html>\n"
    )


def build_al2_vs_al2023_page(deprecations, pricing_view):
    """Head-term comparison page — Amazon Linux 2 vs Amazon Linux 2023. High-volume
    comparison query, distinct intent from the guide/checklist. Facts from the AL2023
    'compare with AL2' doc. Static & deterministic."""
    import html as _h

    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299
    al2 = next(
        (
            d
            for d in deprecations.get("deprecations", [])
            if "amazon linux 2" in str(d.get("name", "")).lower()
        ),
        {},
    )
    date = _h.escape(str(al2.get("date", "2026-06-30")))
    cmp_src = "https://docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html"
    rows = [
        ("Package manager", "yum", "dnf (a <code>yum</code> symlink remains for compatibility)"),
        (
            "Extras library",
            "amazon-linux-extras",
            "Removed — packages are default, version-namespaced (python3.11, nginx1.24), or in SPAL",
        ),
        ("Time sync", "ntpd", "chronyd"),
        ("Firewall backend", "iptables", "nftables"),
        ("Python", "2.7 and 3.x", "3.x only — no Python 2"),
        ("glibc", "2.26", "2.34"),
        (
            "Releases &amp; support",
            "Single rolling release",
            "Versioned releases, 5-year support, quarterly updates, deterministic upgrades",
        ),
        (
            "Security defaults",
            "Looser",
            "Hardened — SELinux on, IMDSv2-friendly, locked-down by default",
        ),
    ]
    table = "".join(
        "<tr><td><strong>" + a + "</strong></td><td>" + b + "</td><td>" + c + "</td></tr>"
        for a, b, c in rows
    )
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "What is the difference between Amazon Linux 2 and Amazon Linux 2023?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "AL2023 replaces yum with dnf, removes amazon-linux-extras, swaps ntpd for chronyd and iptables for nftables, drops Python 2, ships glibc 2.34, and uses versioned 5-year-supported releases with hardened defaults.",
                },
            },
            {
                "@type": "Question",
                "name": "Do I have to migrate from Amazon Linux 2 to AL2023?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Amazon Linux 2 reached its published end-of-life date on "
                    + date.replace("&amp;", "&")
                    + ". Verify the installed release and current AWS support terms; AL2023 is the durable successor.",
                },
            },
            {
                "@type": "Question",
                "name": "Is yum still available on Amazon Linux 2023?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "A yum command remains as a symlink to dnf for backward compatibility, but dnf is the real package manager and amazon-linux-extras is gone.",
                },
            },
        ],
    }
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Amazon Linux 2 vs Amazon Linux 2023: what changes | EOLkits</title>\n"
        '<meta name="description" content="Amazon Linux 2 vs AL2023, side by side: dnf vs yum, amazon-linux-extras, chronyd, nftables, Python, glibc, support windows — and why AL2 (EOL '
        + date
        + ') must move to AL2023. Free scanner to find your AL2 usage.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/amazon-linux-2-vs-amazon-linux-2023/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
        "<style>.cmp{width:100%;border-collapse:collapse;margin:1.25rem 0;font-size:.92rem}"
        ".cmp th,.cmp td{border:1px solid #e5e7eb;padding:.5rem .6rem;text-align:left;vertical-align:top}"
        ".cmp th{background:#f3f4f6}.cta{display:inline-block;margin:1rem 0;padding:.7rem 1.2rem;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;font-weight:600}</style>\n"
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/migrate/">Deadlines</a> / <span>AL2 vs AL2023</span></nav>\n'
        "<h1>Amazon Linux 2 vs Amazon Linux 2023</h1>\n"
        "<p>What actually changes between Amazon Linux 2 and Amazon Linux 2023 — and why it matters now: <strong>AL2 reached end of life "
        + date
        + "</strong>. AWS has published post-EOL AL2 releases, but standard support ended and AL2023 is the durable migration path. Facts below are from AWS's own AL2-vs-AL2023 comparison.</p>\n"
        '<table class="cmp"><thead><tr><th>Area</th><th>Amazon Linux 2</th><th>Amazon Linux 2023</th></tr></thead><tbody>'
        + table
        + "</tbody></table>\n"
        '<p><a href="'
        + cmp_src
        + '" target="_blank" rel="noopener nofollow">[AWS source: comparing AL2 and AL2023]</a></p>\n'
        '<p><a class="cta" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/al2023-gate">Inspect the al2023-gate CLI coverage →</a></p>\n'
        "<h2>Migrating off AL2</h2>\n"
        '<p>The differences above require workload-specific validation. Use the <a href="/amazon-linux-2-eol-checklist/">AL2 → AL2023 checklist</a> and the <a href="/migrate/amazon-linux-2-eol/">migration guide</a>, or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ", 30-day money-back)</a> for exact observed AL2 source references and a remediation order.</p>\n"
        "</body>\n</html>\n"
    )


def build_track_js():
    """First-party pageview beacon for content pages (home/scan/migrate/fix). The
    commerce pages fire their own richer inline events; this gives the TOP of the
    funnel visibility via POST /api/events -> /status funnel counts. No third party,
    no cookies — a single sendBeacon on load with path + first-touch attribution."""
    return (
        "(function(){try{"
        "var qp=new URLSearchParams(location.search);"
        "var ft={};try{ft=JSON.parse(localStorage.getItem('eolkits_ft')||'{}');}catch(e){}"
        "var p={event:'view',path:location.pathname,"
        "source:ft.source||qp.get('source')||'organic',"
        "utm_source:ft.utm_source||qp.get('utm_source')||'',"
        "utm_medium:ft.utm_medium||qp.get('utm_medium')||'',"
        "utm_campaign:ft.utm_campaign||qp.get('utm_campaign')||''};"
        "navigator.sendBeacon('"
        + API_URL
        + "/api/events',new Blob([JSON.stringify(p)],{type:'application/json'}));"
        "}catch(e){}})();"
    )


def build_index_page(pricing):
    """Build the canonical landing page from source data, not stale docs output."""
    pricing_view = build_pricing_view(pricing)
    audit = pricing_view["audit_pdf"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EOLkits - AWS deprecation migration tools</title>
<meta name="description" content="MIT-licensed AWS deprecation scanners and an optional paid repository evidence report with exact file and line matches.">
<link rel="canonical" href="{SITE_URL}/">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head>
<body>
<header class="nav">
  <div class="container nav-inner">
    <a href="/" class="brand"><span class="brand-mark">></span> EOLkits</a>
    <nav>
      <a href="/migrate/">Deadlines</a>
      <a href="/scan/">Free scan</a>
      <a href="/audit/">Audit</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>

<main>
  <section class="hero">
    <div class="container">
      <div class="eyebrow">AWS runtime &amp; OS EOLs that break production</div>
      <h1>Find high-impact AWS deprecation risks in your source — free.</h1>
      <p class="lede">The browser scanner checks configured Lambda runtime and Node/Python dependency patterns without uploading file contents. Repository CLIs add their documented operating-system checks. The $299 evidence report adds repository-wide file/line evidence, remediation order, sources, and explicit scope limitations.</p>
      <div class="cta-row">
        <a class="btn-primary" href="/scan/">Run the free scan</a>
        <a class="btn-secondary" href="https://github.com/ntoledo319/EOLkits">Clone the CLIs</a>
        <a class="btn-ghost" href="/migrate/">See the deadlines</a>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <p class="sub">Free &amp; open-source (MIT) · official source links · local browser scan available · one server-gated paid product · 30-day audit refund policy</p>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <h2>Live Kits</h2>
      <p class="sub">Each kit is standalone, MIT-licensed, and safe by default: scan first, apply only when requested.</p>
      <div class="kit-grid">
        <article class="kit-card urgent">
          <div class="kit-deadline">AL2 standard support ended Jun 30, 2026 — plan migration</div>
          <h3>al2023-gate</h3>
          <p class="kit-sub">Amazon Linux 2 to AL2023</p>
          <p>Find AL2 AMIs, remap packages, patch cloud-init, Packer, and Ansible, then generate rollout runbooks.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/al2023-gate">Read docs</a>
        </article>
        <article class="kit-card">
          <div class="kit-deadline">Rolling Lambda EOL waves</div>
          <h3>python-pivot</h3>
          <p class="kit-sub">Lambda Python 3.9/3.10/3.11 to 3.12</p>
          <p>Audit deprecated modules, native wheels, runtime fields, and Python 3.12 compatibility hazards.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/python-pivot">Read docs</a>
        </article>
        <article class="kit-card">
          <div class="kit-deadline">Lambda Node.js migration readiness</div>
          <h3>lambda-lifeline</h3>
          <p class="kit-sub">Lambda Node.js 16–22 to 24</p>
          <p>Patch Lambda runtime fields, source syntax, aws-sdk v2 usage, and staged deploy/rollback plans.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/lambda-lifeline">Read docs</a>
        </article>
      </div>
    </div>
  </section>

  <section class="section dark" id="pricing">
    <div class="container">
      <h2>Pricing</h2>
      <p class="sub">Try before you buy: the CLIs and browser scanner are free. The repository evidence report is the only paid product.</p>
      <div class="pricing-grid">
        <article class="pricing-card">
          <h3>CLI</h3>
          <div class="price">$0</div>
          <p>All kits, unlimited local runs, MIT license.</p>
          <a class="btn-outline" href="https://github.com/ntoledo319/EOLkits">Get source</a>
        </article>
        <article class="pricing-card featured">
          <h3>Audit PDF</h3>
          <div class="price">${audit["base"]}</div>
          <p>One repository ZIP or source file: exact file/line evidence, observed reach, remediation order, official sources, and an evidence fingerprint. 30-day money-back.</p>
          <a class="btn-primary" href="/audit/">Check availability</a>
          <p class="small"><a href="/audit/sample/">See a sample report →</a></p>
        </article>
      </div>
      <p class="sub">There is no subscription, managed migration, AWS-account inventory, or automated pull-request product for sale.</p>
    </div>
  </section>
</main>

<footer class="footer">
  <div class="container">
    <div class="muted small">© 2026 EOLkits. MIT-licensed kits for AWS deprecation migrations.</div>
    <div class="muted small"><a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a> · <a href="/legal/SECURITY.html">Security</a> · <a href="mailto:hello@toledotechnologies.com">Support</a></div>
  </div>
</footer>
</body>
</html>"""


def build_widget_js():
    return f"""/**
 * EOLkits embeddable widget.
 * Usage: <script src="{SITE_URL}/widget.js" data-repo="owner/repo"></script>
 */
(function() {{
  'use strict';
  const script = document.currentScript;
  const repo = script && script.dataset ? script.dataset.repo : '';
  if (!repo) {{
    console.error('EOLkits widget: data-repo attribute required');
    return;
  }}
  const styles = `
    .eolkits-widget{{font-family:system-ui,-apple-system,sans-serif;border:1px solid #e5e7eb;border-radius:12px;padding:1rem;max-width:420px;background:#fff;color:#111827}}
    .eolkits-widget h3{{margin:0 0 .5rem;font-size:1rem}}
    .eolkits-widget p{{margin:.4rem 0;color:#4b5563;font-size:.9rem}}
    .eolkits-widget a{{display:inline-block;margin-top:.75rem;background:#2563eb;color:#fff;padding:.55rem .8rem;border-radius:6px;text-decoration:none;font-size:.875rem}}
    .eolkits-widget .powered{{margin-top:.75rem;color:#9ca3af;font-size:.75rem}}
  `;
  const style = document.createElement('style');
  style.textContent = styles;
  document.head.appendChild(style);
  const container = document.createElement('div');
  container.className = 'eolkits-widget';
  container.innerHTML = `
    <h3>${{repo}}</h3>
    <p>Check this repository for AWS runtime and platform deprecation risks.</p>
    <a href="{SITE_URL}/audit/?repo=${{encodeURIComponent(repo)}}&utm_source=widget&utm_medium=embed&source=widget" target="_blank" rel="noopener">Run EOLkits audit</a>
    <div class="powered">Powered by EOLkits</div>
  `;
  script.parentNode.insertBefore(container, script.nextSibling);
  try {{
    navigator.sendBeacon('{API_URL}/api/events', new Blob([JSON.stringify({{ event: 'widget_view', source: 'widget', sku: 'audit', meta: {{ repo: repo }} }})], {{ type: 'application/json' }}));
  }} catch (e) {{}}
}})();
"""


def build_partners_page():
    """Keep the legacy partner route safe without collecting speculative leads."""
    return _build_unavailable_product_page(
        "Partner Program",
        "The former white-label, co-branding, and revenue-share offer was not "
        "operationally verified. No partner account or fulfillment program is offered.",
    )


def build_drift_page(pricing):
    """Keep the legacy route safe without advertising an unbuilt product."""
    del pricing
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow">
<title>Drift Watch is unavailable — EOLkits</title>
<meta name="description" content="Drift Watch is not available for purchase. Use the free local scanner or check the repository evidence report status.">
<link rel="canonical" href="https://eolkits.com/drift/">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.6}
.brand{color:#2563eb;font-weight:600}
h1{margin-top:0}
.badge{display:inline-block;background:#fef3c7;color:#92400e;border-radius:999px;padding:.2rem .75rem;font-size:.8rem;font-weight:600;margin-bottom:.5rem}
.feature{background:#f9fafb;border-radius:8px;padding:1rem;margin:.75rem 0}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.875rem}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1>Drift Watch is unavailable</h1>
<p class="badge">No checkout · no subscription · no waitlist</p>
<p>The former page described a hosted monitoring product before its account inventory, scheduling, change detection, and delivery path existed. It is not offered for sale.</p>
<div class="feature"><strong>Available now:</strong> use the <a href="/scan/">free local browser scanner</a>, or check whether the server-gated <a href="/audit/">repository evidence report</a> is open.</div>
<footer>
  <p><a href="/">Home</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></p>
</footer>
</body>
</html>"""
    return _interpolate_api(html)


def build_success_page():
    """Post-checkout status for the only active paid SKU (Audit v2)."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thank you — EOLkits</title>
<meta name="robots" content="noindex">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:720px;margin:0 auto;padding:2rem;line-height:1.6}
.brand{color:#2563eb;font-weight:600}
h1{margin-top:0}
.card{border:1px solid #e5e7eb;border-radius:10px;padding:1.5rem;margin:1.25rem 0}
.upsell{background:#ecfdf5;border:2px solid #059669}
.btn{display:inline-block;background:#2563eb;color:#fff;padding:.6rem 1.2rem;border-radius:6px;text-decoration:none;font-weight:600}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.875rem}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1 id="title">Thank you</h1>
<div id="body"></div>
<footer><a href="/">Home</a> · <a href="/status/">Status</a> · <a href="/legal/terms.html">Terms</a></footer>
<script>
const qp = new URLSearchParams(location.search);
const sku = qp.get('sku') || '';
const sid = qp.get('session_id') || '';
const title = document.getElementById('title');
const body = document.getElementById('body');
function h(html) {{ body.innerHTML = html; }}
if (sku === 'audit') {{
  title.textContent = 'Your audit is on the way';
  h('<div class="card"><p>Payment received. Your repository evidence PDF is queued for automated generation and email delivery. Delays are possible.</p><p>Its evidence lookup records the input hash, rule-pack version, evidence fingerprint, and observed counts. The PDF itself is not digitally signed.</p><p>If fulfillment cannot complete after retries, the system attempts an automatic refund and surfaces any unresolved refund for operator review.</p></div>');
}} else if (sku === 'pack') {{
  title.textContent = 'Migration Pack is closed';
  h('<div class="card"><p>Migration Pack is not available for purchase. If a legacy payment link charged you, email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> with the Stripe receipt so the payment can be reviewed and refunded.</p></div>');
}} else if (sku === 'drift') {{
  title.textContent = 'Drift Watch is unavailable';
  h('<div class="card"><p>Drift Watch is not open for purchase. If a legacy payment link charged you, email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> with the Stripe receipt so the payment can be reviewed and refunded.</p></div>');
}} else {{
  h('<div class="card"><p>Payment received. Check your email for next steps.</p></div>');
}}
</script>
</body>
</html>"""
    return _interpolate_api(html)


def build_status_page():
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Status — EOLkits</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:2rem;line-height:1.6}.brand{color:#2563eb;font-weight:600}.svc{display:flex;justify-content:space-between;align-items:center;border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin:.5rem 0}.dot{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;background:#9ca3af}.dot.green{background:#10b981}.dot.red{background:#ef4444}.muted{color:#6b7280;font-size:.85rem}.notice{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:1rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}.card{border:1px solid #e5e7eb;border-radius:8px;padding:1rem}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>System Status</h1>
<p class="muted">Live backend readiness and anonymous seven-day funnel/commerce aggregates. This is not an end-to-end synthetic purchase test.</p>
<p id="feedState" class="notice">Loading the live API status…</p>
<div id="services"><div class="svc"><span><span class="dot" id="dot-storage"></span>Upload/report storage</span><span id="t-storage">unknown</span></div>
<div class="svc"><span><span class="dot" id="dot-stripe"></span>Stripe configuration</span><span id="t-stripe">unknown</span></div>
<div class="svc"><span><span class="dot" id="dot-runner"></span>Job runner</span><span id="t-runner">—</span></div>
<div class="svc"><span><span class="dot" id="dot-email"></span>Email configuration</span><span id="t-email">unknown</span></div></div>
<h2>Product availability</h2><ul id="capabilities"><li>Loading…</li></ul>
<div class="grid"><div class="card"><h2>Funnel (7 days)</h2><ul id="funnel"><li>Loading…</li></ul></div><div class="card"><h2>Commerce (7 days)</h2><ul id="commerce"><li>Loading…</li></ul></div></div>
<script>
function list(id,data){const el=document.getElementById(id);el.innerHTML='';const entries=Object.entries(data||{});if(!entries.length){el.innerHTML='<li>No events observed</li>';return;}for(const [k,v] of entries){const li=document.createElement('li');li.textContent=k+': '+v;el.appendChild(li);}}
fetch('{API_URL}/api/status',{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject(new Error('HTTP '+r.status))).then(d=>{
  document.getElementById('feedState').textContent='Live API reported '+(d.overall||'unknown')+' at '+(d.timestamp||'unknown time')+'.';
  for(const s of ['storage','stripe','runner','email']){
    const v=(d.components||{})[s];
    if(v){document.getElementById('dot-'+s).className='dot '+(v.ok?'green':'red');document.getElementById('t-'+s).textContent=v.ok?'ready':'not ready';}
  }
  list('capabilities',d.capabilities);list('funnel',d.funnel_7d);list('commerce',d.commerce_7d);
}).catch(e=>{document.getElementById('feedState').textContent='Live status unavailable; all component states remain unknown. '+e.message;list('capabilities',{});list('funnel',{});list('commerce',{});});
</script>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>"""
    return _interpolate_api(html)


def build_status_data_seed():
    # Fail-closed static fallback. The page reads /api/status from the real API;
    # a build can never manufacture green checks or zero-valued business data.
    now = _build_date() + "T00:00:00Z"
    return json.dumps(
        {
            "generated_at": now,
            "source": "static-fallback-only",
            "checks": {
                "storage": {"ok": None, "status": "unknown"},
                "stripe": {"ok": None, "status": "unknown"},
                "runner": {"ok": None, "status": "unknown"},
                "email": {"ok": None, "status": "unknown"},
            },
            "metrics": None,
        },
        indent=2,
    )


def build_blog_index():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blog — AWS migration guides | EOLkits</title>
<meta name="description" content="In-depth, sourced guides for migrating off deprecated AWS runtimes — Lambda Node.js, Python, and Amazon Linux 2.">
<link rel="canonical" href="{SITE}/blog/">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head><body class="container article"><a href="/" class="brand">← EOLkits</a><h1>AWS migration guides</h1>
<p>The former long-form post mixed verified facts with unsupported completeness and performance claims, so it has been retired pending a primary-source rewrite.</p>
<p>Use the cited <a href="/migrate/">deadline pages</a>, the <a href="/fix/">specific error references</a>, or the <a href="/scan/">free local scanner</a>.</p>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>""".replace(
        "{SITE}", SITE_URL
    )


def build_vs_index():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comparisons — EOLkits</title>
<style>body{font-family:system-ui,sans-serif;max-width:780px;margin:0 auto;padding:2rem;line-height:1.6}.brand{color:#2563eb;font-weight:600}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>Evaluate EOLkits</h1>
<p>The previous side-by-side pages contained product and pricing claims that were not continuously verified, so they have been retired.</p>
<p>Evaluate EOLkits against the tool you already use by running the <a href="/scan/">free local browser scanner</a>, reviewing the <a href="https://github.com/ntoledo319/EOLkits">MIT source and tests</a>, and checking the other vendor's current official documentation directly.</p>
<p>EOLkits currently offers local source/IaC checks and, when the fulfillment service is healthy, a $299 static repository evidence report. It is not an AWS account inventory or managed migration service.</p>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>"""


def build_retired_path_page(title, destination, explanation):
    """Keep historical inbound links useful without preserving unsupported copy."""
    import html as _html

    safe_title = _html.escape(title)
    safe_destination = _html.escape(destination, quote=True)
    safe_explanation = _html.escape(explanation)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow"><link rel="canonical" href="{SITE_URL}{safe_destination}">
<title>{safe_title} — moved | EOLkits</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:2rem;line-height:1.6}}.brand{{color:#2563eb;font-weight:600}}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>{safe_title} moved</h1>
<p>{safe_explanation}</p><p><a href="{safe_destination}">Continue to the current page →</a></p></body></html>"""


def build_deprecations_ics(deprecations):
    """RFC 5545 calendar feed."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//EOLkits//AWS Deprecations//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:AWS Deprecation Deadlines (EOLkits)",
        "X-WR-TIMEZONE:UTC",
    ]
    for dep in deprecations.get("deprecations", []):
        try:
            d = datetime.strptime(dep["date"], "%Y-%m-%d")
        except Exception:
            continue
        dtstart = d.strftime("%Y%m%d")
        dtend = (d + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"{deprecation_slug(dep)}@eolkits"
        summary = dep["name"].replace(",", "\\,")
        desc_raw = dep.get("description", "") + f" Source: {dep.get('url','')}"
        desc = desc_raw.replace("\\", "\\\\").replace(",", "\\,").replace("\n", "\\n")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{_build_date().replace('-', '')}T000000Z",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            f"URL:{dep.get('url','')}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\n".join(lines) + "\n"


def md_to_html(md_text, title, canonical_path):
    """Deterministic, stdlib-only Markdown -> HTML for legal docs (no LLM, no
    third-party deps). Supports #/##/### headings, **bold**, [text](url) links,
    - bullet lists, and blank-line-delimited paragraphs. Output is a pure
    function of the input, preserving the RULES.md determinism guarantee."""
    import html as _html

    def inline(s):
        s = _html.escape(s)
        # inline `code` first so its contents aren't bold/link-processed
        s = re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

        def link(match):
            label, target = match.group(1), match.group(2)
            lower = target.lower()
            if lower.startswith(("javascript:", "data:", "//")):
                return label
            if ":" in target and not lower.startswith(("http://", "https://", "mailto:")):
                return label
            rel = ' rel="noopener"' if lower.startswith(("http://", "https://")) else ""
            return f'<a href="{target}"{rel}>{label}</a>'

        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
        return s

    lines = md_text.splitlines()
    out, para = [], []
    state = {"ul": False, "ol": False}

    def flush_para():
        if para:
            text = " ".join(para).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            para.clear()

    def close_lists():
        if state["ul"]:
            out.append("</ul>")
            state["ul"] = False
        if state["ol"]:
            out.append("</ol>")
            state["ol"] = False

    def _cells(row):
        row = row.strip()
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]
        return [c.strip() for c in row.split("|")]

    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        # fenced code block
        if s.startswith("```"):
            flush_para()
            close_lists()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append("<pre><code>" + _html.escape("\n".join(buf)) + "</code></pre>")
            continue
        if not s:
            flush_para()
            close_lists()
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})$", s):
            flush_para()
            close_lists()
            out.append("<hr>")
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", s)
        if heading:
            flush_para()
            close_lists()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue
        if s.startswith(">"):
            flush_para()
            close_lists()
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]).strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue
        # pipe table: a row with | followed by a |---|--- separator row
        if (
            "|" in s
            and i + 1 < n
            and "|" in lines[i + 1]
            and re.match(r"^[\s|:-]+$", lines[i + 1].strip())
            and "-" in lines[i + 1]
        ):
            flush_para()
            close_lists()
            header = _cells(lines[i])
            i += 2
            thead = "".join("<th>" + inline(c) + "</th>" for c in header)
            body = ""
            while i < n and "|" in lines[i] and lines[i].strip():
                body += (
                    "<tr>"
                    + "".join("<td>" + inline(c) + "</td>" for c in _cells(lines[i]))
                    + "</tr>"
                )
                i += 1
            out.append(
                "<table><thead><tr>" + thead + "</tr></thead><tbody>" + body + "</tbody></table>"
            )
            continue
        if re.match(r"^[-*]\s+", s):
            flush_para()
            if state["ol"]:
                out.append("</ol>")
                state["ol"] = False
            if not state["ul"]:
                out.append("<ul>")
                state["ul"] = True
            item = [re.sub(r"^[-*]\s+", "", s)]
            i += 1
            while i < n:
                continuation = lines[i].strip()
                if not continuation or re.match(r"^(?:[-*]|\d+\.)\s+", continuation):
                    break
                if continuation.startswith(("#", ">", "```")):
                    break
                item.append(continuation)
                i += 1
            out.append(f"<li>{inline(' '.join(item))}</li>")
            continue
        if re.match(r"^\d+\.\s+", s):
            flush_para()
            if state["ul"]:
                out.append("</ul>")
                state["ul"] = False
            if not state["ol"]:
                out.append("<ol>")
                state["ol"] = True
            item = [re.sub(r"^\d+\.\s+", "", s)]
            i += 1
            while i < n:
                continuation = lines[i].strip()
                if not continuation or re.match(r"^(?:[-*]|\d+\.)\s+", continuation):
                    break
                if continuation.startswith(("#", ">", "```")):
                    break
                item.append(continuation)
                i += 1
            out.append(f"<li>{inline(' '.join(item))}</li>")
            continue
        para.append(s)
        i += 1
    flush_para()
    close_lists()

    description = ""
    for node in out:
        if node.startswith("<p>"):
            description = re.sub(r"<[^>]+>", "", node)[:155]
            break
    body = "\n".join(out)
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_html.escape(title)}</title>\n"
        f'<meta name="description" content="{_html.escape(description)}">\n'
        f'<link rel="canonical" href="{SITE_URL}{canonical_path}">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        "</head>\n"
        '<body class="container article">\n'
        f"{body}\n"
        "</body>\n</html>\n"
    )


# First-touch attribution shim (M4a): persists the first meaningful referral
# (UTM parameters or an external referrer hostname, never its path/query)
# into localStorage on the page where a cold visitor LANDS, so it survives the
# internal navigation to /audit/ where conversion happens. Without it,
# attribution() reads only the current URL, so a buyer who lands on a /migrate/
# page via an AEO citation and clicks through to /audit/ is mis-credited
# 'audit_page' and the cold-reach channel that produced the sale is invisible.
FIRST_TOUCH_JS = """<script>
(function(){
  try{
    var KEY='eolkits_ft';
    if(localStorage.getItem(KEY))return;
    var q=new URLSearchParams(location.search), ref=document.referrer||'', aeo='', refHost='';
    try{refHost=(new URL(ref)).hostname.toLowerCase().slice(0,100);}catch(e){}
    if(refHost===location.hostname.toLowerCase())refHost='';
    if(/chatgpt\\.com|chat\\.openai\\.com/i.test(ref))aeo='chatgpt';
    else if(/perplexity\\.ai/i.test(ref))aeo='perplexity';
    else if(/gemini\\.google\\.com/i.test(ref))aeo='gemini';
    else if(/claude\\.ai/i.test(ref))aeo='claude';
    var hasUtm = q.get('utm_source')||q.get('source')||q.get('utm_campaign')||q.get('kit');
    if(!hasUtm && !refHost)return;
    localStorage.setItem(KEY, JSON.stringify({
      source: q.get('source')||(aeo?('aeo_'+aeo):'referral'),
      utm_source: q.get('utm_source')||aeo||refHost,
      utm_medium: q.get('utm_medium')||(aeo?'ai_referral':'referral'),
      utm_campaign: q.get('utm_campaign')||'',
      kit: q.get('kit')||''
    }));
  }catch(e){}
})();
</script>
"""


def inject_first_touch(path: str, content: str) -> str:
    """Insert the first-touch shim before </head> on every generated HTML page."""
    if path.endswith(".html") and "</head>" in content:
        return content.replace("</head>", FIRST_TOUCH_JS + "</head>", 1)
    return content


# --- M1: the free /scan engine -------------------------------------------- #
# The checked snapshot below is compared with the shared machine-readable rules at
# build time. Both the browser scanner and paid report consume the shared file, so
# a future one-sided rule change fails loudly instead of weakening the paid result.
# Tables were originally sourced from:
#   kits/lambda-lifeline/src/deps/index.mjs  (NATIVE_PACKAGES, cross-checked 2026-08-21)
#   kits/python-pivot/src/python_pivot/audit.py  (PY312_WHEEL_TABLE, cross-checked 2026-08-21)
# Runtime deadlines are derived from the cited deprecations.yml at build time, so
# the scanner stays in lockstep with the source of truth (no duplicated dates).
_NATIVE_PACKAGES_SNAPSHOT = {
    "sharp": {"min": "0.33.0", "note": "Conservative baseline; verify Node.js 24 support."},
    "bcrypt": {"min": "5.1.1", "note": "Native bcrypt. Consider bcryptjs for a pure-JS drop-in."},
    "better-sqlite3": {"min": "11.0.0", "note": "SQLite native binding."},
    "canvas": {"min": "2.11.2", "note": "Conservative baseline; verify target prebuilds."},
    "node-gyp": {"min": "10.0.0", "note": "Build system. Upgrade before rebuilding natives."},
    "node-sass": {"min": None, "note": "Unmaintained. Use sass (Dart Sass)."},
    "bufferutil": {"min": "4.0.8", "note": "WebSocket utility native addon."},
    "utf-8-validate": {"min": "6.0.4", "note": "WebSocket utility native addon."},
    "libpq": {
        "min": "1.11.0",
        "note": "PostgreSQL client; verify the current release and target prebuild.",
    },
    "grpc": {"min": None, "note": "Unmaintained. Migrate to @grpc/grpc-js."},
    "@grpc/grpc-js": {"min": "1.10.0", "note": "Pure JS, no native; just keep up to date."},
    "sqlite3": {"min": "5.1.7", "note": "SQLite3 bindings. Prebuilds available."},
    "argon2": {"min": "0.40.1", "note": "argon2 bindings. 0.40.0 exact was never published."},
    "re2": {"min": "1.21.0", "note": "RE2 regex engine."},
    "fibers": {"min": None, "note": "Unmaintained since the Node.js 16 era; remove it."},
    "@tensorflow/tfjs-node": {"min": "4.20.0", "note": "TensorFlow native."},
    "sodium-native": {"min": "4.3.0", "note": "libsodium bindings."},
    "zmq": {"min": None, "note": "Unmaintained. Use zeromq instead."},
    "zeromq": {"min": "6.1.2", "note": "ZeroMQ bindings."},
    "farmhash": {"min": "4.0.0", "note": "Native hashing."},
    "@napi-rs/snappy": {
        "min": None,
        "note": "Stale package; use a maintained compressor.",
    },
    "heapdump": {"min": None, "note": "Unmaintained. Use node --heapsnapshot-signal instead."},
}
_PY312_WHEELS_SNAPSHOT = {
    "numpy": {"min": "1.26.0", "note": "1.26+ ships cp312 wheels."},
    "scipy": {"min": "1.11.4", "note": "1.11.4+ for cp312."},
    "pandas": {"min": "2.1.1", "note": "2.1.1+ for cp312."},
    "scikit-learn": {"min": "1.3.2", "note": "1.3.2+ for cp312."},
    "matplotlib": {"min": "3.8.0", "note": "3.8.0+ for cp312."},
    "pillow": {"min": "10.1.0", "note": "10.1.0+ for cp312."},
    "lxml": {"min": "4.9.4", "note": "4.9.4+ for cp312."},
    "cryptography": {"min": "41.0.5", "note": "41.0.5+ for cp312 (libssl3)."},
    "pycryptodome": {"min": "3.19.0", "note": "3.19.0+ for cp312."},
    "bcrypt": {"min": "4.1.1", "note": "4.1.1+ for cp312."},
    "pyopenssl": {"min": "23.3.0", "note": "23.3.0+ for cp312."},
    "psycopg2-binary": {"min": "2.9.9", "note": "2.9.9+ for cp312."},
    "psycopg": {"min": "3.1.13", "note": "3.1.13+ for cp312."},
    "mysqlclient": {"min": "2.2.0", "note": "2.2.0+ for cp312."},
    "pymssql": {"min": "2.2.11", "note": "2.2.11+ for cp312."},
    "pyyaml": {"min": "6.0.1", "note": "6.0.1+ for cp312."},
    "orjson": {"min": "3.9.10", "note": "3.9.10+ for cp312."},
    "ujson": {"min": "5.8.0", "note": "5.8.0+ for cp312."},
    "msgpack": {"min": "1.0.7", "note": "1.0.7+ for cp312."},
    "aiohttp": {"min": "3.9.0", "note": "3.9.0+ for cp312."},
    "grpcio": {"min": "1.59.0", "note": "1.59.0+ for cp312."},
    "protobuf": {"min": "4.25.0", "note": "4.25.0+ for cp312."},
    "frozenlist": {"min": "1.4.0", "note": "1.4.0+ for cp312."},
    "multidict": {"min": "6.0.4", "note": "6.0.4+ for cp312."},
    "yarl": {"min": "1.9.3", "note": "1.9.3+ for cp312."},
    "tiktoken": {"min": "0.5.2", "note": "0.5.2+ for cp312."},
    "tokenizers": {"min": "0.15.0", "note": "0.15.0+ for cp312."},
    "awscrt": {"min": "0.19.17", "note": "0.19.17+ for cp312."},
    "boto3": {"min": "1.29.0", "note": "1.29+ tested on cp312."},
    "botocore": {"min": "1.32.0", "note": "1.32+ tested on cp312."},
    "python-snappy": {
        "min": "0.7.0",
        "note": "0.7.0+ (2024-02-27) ships a pure-Python wheel built on cramjam — installs fine on cp312, no swap needed.",
    },
    "fastparquet": {"min": "2023.10.1", "note": "2023.10.1+ for cp312."},
}

_DEPENDENCY_RULES_FILE = (
    BASE_DIR.parent.parent / "rules" / "public" / "dependency-compatibility.json"
)
_DEPENDENCY_RULES = json.loads(_DEPENDENCY_RULES_FILE.read_text(encoding="utf-8"))
_NATIVE_PACKAGES = _DEPENDENCY_RULES["node_native"]
_PY312_WHEELS = _DEPENDENCY_RULES["python_312_wheels"]
if {name: rule.get("min") for name, rule in _NATIVE_PACKAGES_SNAPSHOT.items()} != {
    name: rule.get("min") for name, rule in _NATIVE_PACKAGES.items()
}:
    raise RuntimeError("browser Node compatibility snapshot drifted from shared rules")
if {name: rule.get("min") for name, rule in _PY312_WHEELS_SNAPSHOT.items()} != {
    name: rule.get("min") for name, rule in _PY312_WHEELS.items()
}:
    raise RuntimeError("browser Python compatibility snapshot drifted from shared rules")


def _runtime_id_from_name(name: str):
    """Derive an AWS runtime identifier (python3.9 / nodejs20.x / ruby3.2) from a
    deprecation entry name, so the scanner's deadlines come straight from the YAML."""
    n = (name or "").lower()
    m = re.search(r"python\s*(\d+)\.(\d+)", n)
    if m:
        return f"python{m.group(1)}.{m.group(2)}"
    m = re.search(r"node(?:\.|\s)?js\s*(\d+)", n)
    if m:
        return f"nodejs{m.group(1)}.x"
    m = re.search(r"ruby\s*(\d+)\.(\d+)", n)
    if m:
        return f"ruby{m.group(1)}.{m.group(2)}"
    return None


_SCAN_JS = r"""
const $ = (s) => document.querySelector(s);
const RT_RE = /(?:runtime\s*[:=]\s*["']?)(nodejs\d+\.x|python\d+\.\d+|ruby\d+\.\d+|java\d+|dotnet\d+|dotnetcore\d+\.\d+|go\d+\.x|provided\.al\d+|provided)\b/gi;
const CDK_RE = /Runtime\.(NODEJS|PYTHON|RUBY|JAVA|DOTNET|GO)_(\d+)(?:_(\d+))?(?:_X)?/gi;
function cdkId(l, a, b) { l = l.toLowerCase(); if (l === 'nodejs') return 'nodejs' + a + '.x'; if (l === 'python') return 'python' + a + '.' + (b || '0'); if (l === 'ruby') return 'ruby' + a + '.' + (b || '0'); return l + a; }
function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function classify(name) {
  const n = name.toLowerCase();
  if (n.endsWith('package.json')) return 'pkg';
  if (n.endsWith('requirements.txt') || /requirements.*\.txt$/.test(n)) return 'req';
  if (n.endsWith('pyproject.toml') || n.endsWith('.toml') || n.endsWith('pipfile')) return 'pyproject';
  return 'iac';
}
function vtuple(v) { return (v || '').replace(/^[^\d]*/, '').split(/[.\-+]/).map((x) => parseInt(x, 10) || 0); }
function vlt(a, b) { const A = vtuple(a), B = vtuple(b); for (let i = 0; i < Math.max(A.length, B.length); i++) { const x = A[i] || 0, y = B[i] || 0; if (x < y) return true; if (x > y) return false; } return false; }
function cleanV(v) { return v ? v.replace(/^[\^~>=<\s]+/, '') : null; }
function extractMin(spec) { if (!spec) return null; for (const op of ['==', '>=']) { for (let part of spec.split(',')) { part = part.trim(); if (part.indexOf(op) === 0) return part.slice(op.length).trim(); } } return null; }
function scanIaC(file, c) {
  const f = new Set(), out = []; let m;
  RT_RE.lastIndex = 0; while ((m = RT_RE.exec(c))) f.add(m[1].toLowerCase());
  CDK_RE.lastIndex = 0; while ((m = CDK_RE.exec(c))) { const id = cdkId(m[1], m[2], m[3]); if (id) f.add(id); }
  f.forEach((rt) => {
    const d = DATA.runtimes[rt];
    if (d) out.push({ kind: 'runtime', file, name: rt, severity: d.historical ? 'critical' : (d.severity || 'high'), date: d.date, kit: d.kit, historical: d.historical, note: d.historical ? 'Past a published milestone; recheck the linked provider status and enforcement dates.' : 'Runtime with an AWS-published deprecation and create/update restriction timeline.' });
  });
  return out;
}
function scanPkg(file, c) {
  let pkg; try { pkg = JSON.parse(c); } catch (e) { return []; }
  const deps = Object.assign({}, pkg.dependencies || {}, pkg.devDependencies || {}), out = [];
  for (const name in deps) {
    const info = DATA.native[name]; if (!info) continue;
    const declared = cleanV(deps[name]);
    if (info.min === null) { out.push({ kind: 'native', file, name, severity: 'critical', declared: declared || '(unpinned)', required: '(unmaintained — replace)', note: info.note }); continue; }
    if (declared && !vlt(declared, info.min)) { out.push({ kind: 'native', file, name, severity: 'low', declared, required: 'verify Node.js 24 support', note: 'Meets the configured older baseline; confirm the package release and rebuild/test on Node.js 24.' }); continue; }
    out.push({ kind: 'native', file, name, severity: 'high', declared: declared || '(unpinned)', required: '>= ' + info.min, note: info.note });
  }
  return out;
}
function pyFindings(pkgs, file) {
  const out = [];
  for (const pair of pkgs) {
    const name = pair[0], spec = pair[1], req = DATA.wheels[name]; if (!req) continue;
    const declared = extractMin(spec);
    if (req.min === null) { out.push({ kind: 'wheel', file, name, severity: 'critical', declared: spec || '(unpinned)', required: '(no cp312 wheels)', note: req.note }); continue; }
    if (declared === null) { out.push({ kind: 'wheel', file, name, severity: 'low', declared: '(unpinned)', required: '>= ' + req.min, note: 'unpinned; pin >= ' + req.min + ' for reproducibility.' }); continue; }
    if (vlt(declared, req.min)) out.push({ kind: 'wheel', file, name, severity: 'high', declared: spec, required: '>= ' + req.min, note: req.note });
  }
  return out;
}
function parseReq(c) { const out = []; for (let raw of c.split(/\r?\n/)) { const line = raw.trim(); if (!line || line[0] === '#' || line[0] === '-') continue; const m = line.match(/^([A-Za-z0-9_.\-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~].+)?/); if (!m) continue; out.push([m[1].toLowerCase(), (m[2] || '').trim() || null]); } return out; }
function parsePyproject(c) { const out = []; const blocks = c.match(/dependencies\s*=\s*\[([\s\S]*?)\]/g) || []; for (const b of blocks) { const re = /"\s*([A-Za-z0-9_.\-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~][^"]*)?\s*"/g; let m; while ((m = re.exec(b))) out.push([m[1].toLowerCase(), (m[2] || '').trim() || null]); } return out; }
function scanFile(name, content) {
  const k = classify(name);
  if (k === 'pkg') return scanPkg(name, content);
  if (k === 'req') return pyFindings(parseReq(content), name);
  if (k === 'pyproject') return pyFindings(parsePyproject(content), name);
  return scanIaC(name, content);
}
function auditLink(deadline, kit) { const p = new URLSearchParams({ source: 'scan', utm_source: 'scan', utm_medium: 'tool', utm_campaign: 'free-scan' }); if (deadline) p.set('deadline', deadline); if (kit) p.set('kit', kit); return SITE_BASE + '/audit/?' + p.toString(); }
const SEV_RANK = { critical: 0, high: 1, medium: 2, low: 3 };
function render(all) {
  const box = $('#results');
  if (!all.length) { box.innerHTML = '<div class="scan-ok">No configured browser-scan pattern matched the files you dropped. That is not proof that the repository or AWS account is free of deprecation risk.</div>'; return; }
  all.sort((a, b) => (SEV_RANK[a.severity] - SEV_RANK[b.severity]));
  let deadline = null, kit = '', today = new Date().toISOString().slice(0, 10);
  for (const f of all) { if (f.kind === 'runtime' && f.date && f.date >= today) { if (!deadline || f.date < deadline) { deadline = f.date; kit = f.kit || kit; } } }
  const rows = all.map((f) => {
    const what = f.kind === 'runtime' ? ('Runtime ' + f.name) : f.name;
    const when = f.kind === 'runtime' ? (f.historical ? ('deprecated ' + f.date) : ('blocks ' + (f.date || '?'))) : (f.declared + ' → ' + f.required);
    return '<tr class="sev-' + f.severity + '"><td>' + f.severity.toUpperCase() + '</td><td>' + esc(what) + '</td><td>' + esc(f.file) + '</td><td>' + esc(when) + '</td><td>' + esc(f.note || '') + '</td></tr>';
  }).join('');
  const n = all.length;
  box.innerHTML = '<p class="scan-count">' + n + ' finding' + (n === 1 ? '' : 's') + ' — all detected locally in your browser.</p>' +
    '<table class="scan-tbl"><thead><tr><th>Severity</th><th>What</th><th>File</th><th>Deadline / fix</th><th>Detail</th></tr></thead><tbody>' + rows + '</tbody></table>' +
    '<a class="scan-cta" href="' + auditLink(deadline, kit) + '">Get repository-wide file/line evidence, sources &amp; remediation order — check Audit v2 availability &rarr;</a>';
}
const dz = $('#dz'), fi = $('#fi'); let acc = [];
function scanDone(fileCount) { try { navigator.sendBeacon(API_BASE + '/api/events', new Blob([JSON.stringify({ event: 'scan_completed', sku: 'audit', path: location.pathname, meta: { finding_count: acc.length, file_count: fileCount } })], { type: 'application/json' })); } catch (e) {} }
function handle(files) { acc = []; const arr = [...files]; let pending = arr.length; if (!pending) return; arr.forEach((file) => { const r = new FileReader(); r.onload = () => { try { acc = acc.concat(scanFile(file.name, r.result)); } catch (e) {} if (--pending === 0) { render(acc); scanDone(arr.length); } }; r.onerror = () => { if (--pending === 0) { render(acc); scanDone(arr.length); } }; r.readAsText(file); }); }
dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', (e) => { e.preventDefault(); dz.classList.remove('over'); handle(e.dataTransfer.files); });
dz.addEventListener('click', () => fi.click());
fi.addEventListener('change', () => handle(fi.files));
"""


def build_scan_page(deprecations):
    """M1: the free, zero-upload, client-side EOL scanner. Findings mirror the paid
    kits; runtime deadlines come from the cited deprecations.yml; CTA points at the
    on-site /audit/ Checkout path (NOT a raw Stripe link) so fulfillment metadata
    survives, and carries source/utm so the sale is attributed to the scanner."""
    runtimes = {}
    for group in ("deprecations", "historical"):
        for dep in deprecations.get(group, []):
            rt = _runtime_id_from_name(dep.get("name", ""))
            if not rt:
                continue
            runtimes[rt] = {
                "date": dep.get("date"),
                "slug": deprecation_slug(dep),
                "severity": dep.get("severity", "high"),
                "kit": dep.get("kit") or "",
                "historical": group == "historical",
            }
    data = json.dumps(
        {"runtimes": runtimes, "native": _NATIVE_PACKAGES, "wheels": _PY312_WHEELS},
        separators=(",", ":"),
    )
    head = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Free AWS Lambda Runtime &amp; Dependency EOL Scanner — EOLkits</title>\n"
        '<meta name="description" content="Drop SAM/CDK/Terraform/Serverless, package.json, or requirements files to find tracked AWS Lambda runtime and native-dependency migration risks. Runs entirely in your browser — nothing is uploaded.">\n'
        f'<link rel="canonical" href="{SITE_URL}/scan/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n' + _og_image_meta() + "<style>"
        "#dz{border:2px dashed #94a3b8;border-radius:10px;padding:2.5rem 1rem;text-align:center;cursor:pointer;background:#f8fafc}"
        "#dz.over{border-color:#2563eb;background:#eff6ff}"
        ".scan-tbl{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.88rem}"
        ".scan-tbl th,.scan-tbl td{border-bottom:1px solid #eee;padding:.5rem;text-align:left;vertical-align:top}"
        ".sev-critical td:first-child{color:#b91c1c;font-weight:700}"
        ".sev-high td:first-child{color:#b45309;font-weight:700}"
        ".sev-medium td:first-child{color:#a16207;font-weight:700}"
        ".sev-low td:first-child{color:#2563eb}"
        ".scan-cta{display:inline-block;margin-top:1rem;padding:.75rem 1.25rem;background:#111;color:#fff;border-radius:8px;text-decoration:none;font-weight:600}"
        ".scan-ok{padding:1rem;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px}"
        ".scan-count{font-weight:600;margin-top:1rem}.privacy{color:#16a34a;font-weight:600}"
        "</style>\n</head>\n"
    )
    body = (
        '<body class="container">\n'
        '<a href="/" class="brand">&larr; EOLkits</a>\n'
        "<h1>Free AWS runtime &amp; dependency EOL scanner</h1>\n"
        "<p>Drop your infrastructure and dependency files below to find deprecated AWS Lambda runtimes and the "
        "native Node.js&nbsp;24 / Python&nbsp;3.12 dependency risks that can block a migration. "
        '<span class="privacy">File names and contents stay in your browser.</span> '
        "After a scan, the page sends only file and finding counts for funnel measurement.</p>\n"
        '<div id="dz"><strong>Drop files here</strong><br><small>or click to choose — template.yaml, serverless.yml, *.tf, CDK *.ts, package.json, requirements.txt, pyproject.toml</small>'
        '<input id="fi" type="file" multiple accept=".yaml,.yml,.json,.tf,.ts,.js,.mjs,.txt,.toml" style="display:none"></div>\n'
        '<div id="results"></div>\n'
        "<h2>What it checks</h2>\n<ul>"
        "<li><strong>Lambda runtimes</strong> in SAM, CloudFormation, CDK, Terraform and Serverless Framework — flagged against AWS&rsquo;s published deprecation dates.</li>"
        "<li><strong>Node native dependencies</strong> (sharp, bcrypt, better-sqlite3&hellip;) that need a version bump, rebuild, or replacement before a Node&nbsp;24 migration.</li>"
        "<li><strong>Python wheels</strong> (numpy, pandas, cryptography&hellip;) that need a bump for a Python&nbsp;3.12 runtime.</li>"
        "</ul>\n"
        '<p>Hit a specific error message? See <a href="/fix/">common AWS migration error fixes &rarr;</a></p>\n'
        "<p><small>This free scan covers configured high-impact source patterns. The paid report accepts one repository ZIP or source file and adds exact line evidence, sources, a remediation order, and explicit limitations. It does not query your AWS account.</small></p>\n"
    )
    tail = "</body>\n</html>\n"
    return (
        head
        + body
        + "<script>\nconst SITE_BASE = "
        + json.dumps(SITE_URL.rstrip("/"))
        + ";\nconst API_BASE = "
        + json.dumps(API_URL.rstrip("/"))
        + ";\nconst DATA = "
        + data
        + ";\n"
        + _SCAN_JS
        + "\n</script>\n"
        + tail
    )


# --- M2: the /fix/<error> verbatim-error corpus --------------------------- #
def load_fixes():
    """Load and validate the cited verbatim-error corpus for /fix pages."""
    p = BASE_DIR / "content" / "fixes.yml"
    if not p.exists():
        return []
    with open(p) as f:
        data = yaml.safe_load(f) or {}
    fixes = data.get("fixes", [])
    if not isinstance(fixes, list):
        raise ValueError("apps/web/content/fixes.yml: fixes must be a list")
    for index, entry in enumerate(fixes):
        if not isinstance(entry, dict) or not str(entry.get("source_url") or "").startswith(
            "https://"
        ):
            raise ValueError(
                f"apps/web/content/fixes.yml: fixes[{index}] needs an HTTPS primary-source source_url"
            )
    return fixes


def _fix_audit_link(slug, kit, deadline):
    from urllib.parse import urlencode

    q = {"source": "fix", "utm_source": "fix", "utm_medium": "content", "utm_campaign": slug}
    if deadline:
        q["deadline"] = deadline
    if kit:
        q["kit"] = kit
    return "/audit/?" + urlencode(q)


def build_error_pages(fixes, deprecations, full_pricing):
    """M2: deterministic /fix/<slug> pages keyed on REAL, paste-able error strings.
    Each entry carries a source for its core claim and cross-links the bounded
    scanner, related milestone, and capability-gated Audit path."""
    import html as _h

    if not fixes:
        return {}
    pricing_view = build_pricing_view(full_pricing)
    try:
        ap = pricing_view["audit_pdf"]
        audit_base = ap["base"] if isinstance(ap, dict) else getattr(ap, "base", None)
    except Exception:
        audit_base = None
    dep_by_slug = {deprecation_slug(d): d for d in deprecations.get("deprecations", [])}

    pages = {}
    cards = []
    for fx in fixes:
        slug = fx["slug"]
        error = fx["error"]
        context = fx.get("context", "")
        summary = fx.get("summary", "")
        cause = fx.get("cause", "")
        steps = fx.get("fix_steps", [])
        source = fx.get("source_url", "")
        rel = fx.get("related_migrate")
        kit = fx.get("kit", "")
        rel_dep = dep_by_slug.get(rel) if rel else None
        rel_date = rel_dep.get("date") if rel_dep else None

        faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": 'What does "' + error + '" mean?',
                    "acceptedAnswer": {"@type": "Answer", "text": (summary + " " + cause).strip()},
                },
                {
                    "@type": "Question",
                    "name": 'How do I fix "' + error + '"?',
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": (
                            " ".join(steps) + (" Source: " + source if source else "")
                        ).strip(),
                    },
                },
            ],
        }
        howto = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "Fix: " + error,
            "step": [
                {"@type": "HowToStep", "position": i + 1, "text": s} for i, s in enumerate(steps)
            ],
        }
        if source:
            howto["citation"] = source

        desc = _h.escape((summary + " " + (steps[0] if steps else ""))[:155])
        steps_html = "".join("<li>" + _h.escape(s) + "</li>" for s in steps)
        rel_html = ""
        if rel and rel_dep:
            rel_html = (
                '<p class="fix-rel">Related deadline: <a href="/migrate/'
                + rel
                + '/">'
                + _h.escape(rel_dep.get("name", ""))
                + "</a> — <strong>"
                + _h.escape(str(rel_date))
                + "</strong>.</p>\n"
            )
        audit_link = _fix_audit_link(slug, kit, rel_date)
        cta_price = ("$" + str(audit_base)) if audit_base else "the audit"

        head = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            "<title>"
            + _h.escape(error)
            + " — cause &amp; fix ("
            + _h.escape(context)
            + ") | EOLkits</title>\n"
            '<meta name="description" content="' + desc + '">\n'
            '<link rel="canonical" href="' + SITE_URL + "/fix/" + slug + '/">\n'
            '<link rel="stylesheet" href="/style.css">\n'
            '<script defer src="/track.js"></script>\n'
            + _og_image_meta()
            + "<style>.fix-err{background:#0f172a;color:#e2e8f0;padding:.9rem 1rem;border-radius:8px;overflow-x:auto;font-size:.85rem}"
            ".fix-steps li{margin:.35rem 0}.fix-cta{display:inline-block;margin-top:1rem;padding:.7rem 1.2rem;background:#111;color:#fff;border-radius:8px;text-decoration:none;font-weight:600}"
            ".fix-rel{background:#fff7ed;border:1px solid #fed7aa;padding:.6rem .8rem;border-radius:8px}</style>\n"
            '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
            '<script type="application/ld+json">' + json.dumps(howto) + "</script>\n"
            "</head>\n"
        )
        body = (
            '<body class="container article">\n'
            '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/fix/">Fixes</a> / <span>'
            + _h.escape(context)
            + "</span></nav>\n"
            '<p class="muted">' + _h.escape(context) + "</p>\n"
            "<h1>" + _h.escape(error) + "</h1>\n"
            '<pre class="fix-err"><code>' + _h.escape(error) + "</code></pre>\n"
            "<h2>What it means</h2>\n<p>" + _h.escape(summary) + "</p>\n"
            "<h2>Why it happens</h2>\n<p>" + _h.escape(cause) + "</p>\n"
            '<h2>How to fix it</h2>\n<ol class="fix-steps">'
            + steps_html
            + "</ol>\n"
            + rel_html
            + "<h2>Check configured patterns in your project</h2>\n"
            + '<p>The free <a href="/scan/">EOLkits scanner</a> runs in your browser (nothing uploaded) and flags selected related patterns in supported IaC and dependency files. It is not a complete source or AWS-account scan.</p>\n'
            + '<p>Prefer a 10-second check? Paste your config into the <a href="/eol-checker/">free AWS EOL checker</a> — nothing uploaded.</p>\n'
            + (
                (
                    '<p>Primary source: <a href="'
                    + _h.escape(source)
                    + '" target="_blank" rel="noopener nofollow">'
                    + _h.escape(source)
                    + "</a></p>\n"
                )
                if source
                else ""
            )
            + '<p><a class="fix-cta" href="'
            + audit_link
            + '">Get repository evidence — '
            + cta_price
            + ", exact file/line matches &rarr;</a></p>\n"
            "</body>\n</html>\n"
        )
        pages["fix/" + slug + "/index.html"] = head + body
        cards.append((context, error, slug))

    cards.sort()
    items = "".join(
        '<li><a href="/fix/' + slug + '/"><code>' + _h.escape(err) + "</code></a> "
        '<span class="muted">— ' + _h.escape(ctx) + "</span></li>"
        for ctx, err, slug in cards
    )
    hub = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>AWS migration error fixes — Lambda, Amazon Linux, Python &amp; Node | EOLkits</title>\n"
        '<meta name="description" content="Source-linked causes and remediation checks for specific AWS Lambda, Amazon Linux, Python, and Node migration errors.">\n'
        '<link rel="canonical" href="'
        + SITE_URL
        + '/fix/">\n<link rel="stylesheet" href="/style.css">\n<script defer src="/track.js"></script>\n</head>\n'
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <span>Fixes</span></nav>\n'
        "<h1>AWS migration error fixes</h1>\n"
        "<p>Source-linked causes and remediation checks for specific errors seen during AWS runtime and Amazon Linux migrations. "
        'Each entry links a primary or official-project source for its core claim; validate the steps in your workload. Not sure which apply? <a href="/scan/">Run the bounded browser scan</a>.</p>\n'
        '<ul class="fix-list">' + items + "</ul>\n"
        '<p><a href="/migrate/">See all tracked AWS deadlines &rarr;</a></p>\n'
        "</body>\n</html>\n"
    )
    pages["fix/index.html"] = hub
    return pages


# --- M5: deterministic deadline badges (embed/backlink loop) --------------- #
def _badge_color(days):
    if days is None or days < 0:
        return "#6b7280"
    if days < 90:
        return "#e11d48"
    if days < 180:
        return "#f59e0b"
    return "#3b82f6"


def _badge_svg(label, message, color):
    """Self-contained shields-style flat SVG badge — no external service, no JS."""
    import html as _h

    label = _h.escape(label)
    message = _h.escape(message)
    lw = int(len(label) * 6.5) + 12
    mw = int(len(message) * 6.5) + 12
    total = lw + mw
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" role="img" aria-label="{label}: {message}">'
        '<linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="a"><rect width="{total}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#a)"><rect width="{lw}" height="20" fill="#444"/>'
        f'<rect x="{lw}" width="{mw}" height="20" fill="{color}"/>'
        f'<rect width="{total}" height="20" fill="url(#b)"/></g>'
        '<g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,Geneva,sans-serif" font-size="11">'
        f'<text x="{lw / 2:.0f}" y="14">{label}</text>'
        f'<text x="{lw + mw / 2:.0f}" y="14">{message}</text>'
        "</g></svg>"
    )


def build_badges(deprecations):
    """Build one deterministic published-milestone badge per tracked entry."""
    from datetime import date as _date

    today = datetime.strptime(_build_date(), "%Y-%m-%d").date()
    pages = {}
    for dep in deprecations.get("deprecations", []):
        slug = deprecation_slug(dep)
        d = str(dep.get("date", ""))
        days = None
        try:
            y, m, dd = (int(x) for x in d.split("-"))
            days = (_date(y, m, dd) - today).days
        except Exception:
            pass
        msg = ("milestone " + d) if (days is None or days >= 0) else ("milestone passed " + d)
        pages["badge/" + slug + ".svg"] = _badge_svg("EOLkits", msg, _badge_color(days))
    return pages


def build_deprecations_rss(deprecations):
    """Build a deterministic RSS list of tracked provider milestones."""
    import html as _h

    # Pin to the explicit source date so rebuilds are byte-identical on every day.
    now = datetime.strptime(_build_date(), "%Y-%m-%d").replace(tzinfo=UTC)
    pub = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    ordered = sorted(
        deprecations.get("deprecations", []), key=lambda d: d.get("date", "9999-99-99")
    )
    items = []
    for dep in ordered:
        slug = deprecation_slug(dep)
        link = f"{SITE_URL}/migrate/{slug}/"
        bc = "; ".join(dep.get("breaking_changes", []))
        desc = (
            f"Deadline {dep.get('date', '')} ({dep.get('severity', 'n/a')}). "
            f"{dep.get('description', '')} Migration checks to validate: {bc}. "
            f"Provider status source: {dep.get('url', '')}"
        )
        items.append(
            "<item>"
            f"<title>{_h.escape(dep['name'])} — milestone {_h.escape(str(dep.get('date', '')))}</title>"
            f"<link>{_h.escape(link)}</link>"
            f'<guid isPermaLink="true">{_h.escape(link)}</guid>'
            f"<pubDate>{pub}</pubDate>"
            f"<description>{_h.escape(desc)}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n'
        "<title>EOLkits — AWS Deprecation Radar</title>\n"
        f"<link>{SITE_URL}/migrate/</link>\n"
        f'<atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>\n'
        "<description>Tracked AWS deprecation milestones for Lambda runtimes and Amazon Linux 2, "
        "with provider source links and bounded migration checks to validate.</description>\n"
        "<language>en-us</language>\n"
        f"<lastBuildDate>{pub}</lastBuildDate>\n" + "\n".join(items) + "\n</channel></rss>\n"
    )


def main():
    """Main build entry point."""
    print("EOLkits Static Site Builder")
    print("=" * 40)

    # Load configuration
    pricing = load_pricing()
    print(f"Loaded {len(pricing['skus'])} SKUs from pricing.yml")

    # Ensure docs directory exists
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Load deprecations
    deprecations = load_deprecations()
    print(f"Loaded {len(deprecations.get('deprecations', []))} deprecations")

    # Build pages
    pages = {
        "index.html": build_index_page(pricing),
        "track.js": build_track_js(),
        f"{INDEXNOW_KEY}.txt": INDEXNOW_KEY,
        "audit/index.html": build_audit_page(pricing),
        "audit/sample/index.html": build_audit_sample_page(pricing),
        "scan/index.html": build_scan_page(deprecations),
        "pack/index.html": build_pack_page(pricing),
        "license/index.html": build_license_page(pricing),
        "drift/index.html": build_drift_page(pricing),
        "success/index.html": build_success_page(),
        "partners/index.html": build_partners_page(),
        "status/index.html": build_status_page(),
        "status/data.json": build_status_data_seed(),
        "blog/index.html": build_blog_index(),
        "vs/index.html": build_vs_index(),
        "blog/migrating-lambda-nodejs-20-to-22/index.html": build_retired_path_page(
            "Lambda Node.js 20 migration guide",
            "/migrate/lambda-node.js-20-phase-1/",
            "The old article was retired because its claims were not all continuously verified. The current deadline page uses the cited rule data.",
        ),
        "migrate/imdsv1-enforcement/index.html": build_retired_path_page(
            "IMDSv1 deadline correction",
            "/migrate/",
            "The former page asserted a universal December 31, 2025 enforcement date that AWS does not document. IMDS behavior depends on account policy, AMI settings, launch options, and instance type; use current AWS guidance before changing a workload.",
        ),
        "vs/cloudquery/index.html": build_retired_path_page(
            "CloudQuery comparison",
            "/vs/",
            "The unverified comparison was retired. Use the current evaluation guidance instead.",
        ),
        "vs/herodevs/index.html": build_retired_path_page(
            "HeroDevs comparison",
            "/vs/",
            "The unverified comparison was retired. Use the current evaluation guidance instead.",
        ),
        "vs/aws-samples-runtime-update-helper/index.html": build_retired_path_page(
            "AWS runtime helper comparison",
            "/vs/",
            "The unverified comparison was retired. Use the current evaluation guidance instead.",
        ),
        "fix/amazon-linux-2-eol/index.html": build_retired_path_page(
            "Amazon Linux 2 EOL reference",
            "/amazon-linux-2-eol-checklist/",
            "This historical route now points to the maintained, source-linked checklist.",
        ),
        "eol-checker/index.html": build_eol_checker_page(deprecations, build_pricing_view(pricing)),
        "lambda-runtime-deprecation-schedule/index.html": build_lambda_schedule_page(
            deprecations, build_pricing_view(pricing)
        ),
        "amazon-linux-2-eol-checklist/index.html": build_al2_checklist_page(
            deprecations, build_pricing_view(pricing)
        ),
        "amazon-linux-2-vs-amazon-linux-2023/index.html": build_al2_vs_al2023_page(
            deprecations, build_pricing_view(pricing)
        ),
        "deprecations.ics": build_deprecations_ics(deprecations),
    }
    pages["widget.js"] = build_widget_js()

    # Build migration pages
    migration_pages = build_migration_pages(deprecations, pricing)
    pages.update(migration_pages)

    # Build /fix/<error> verbatim-error pages (M2) — sourced, deterministic, AEO-shaped
    error_pages = build_error_pages(load_fixes(), deprecations, pricing)
    pages.update(error_pages)
    print(f"Built {len(error_pages)} /fix + hub pages")

    # Deadline badges (M5 embed/backlink loop) — one SVG per deprecation
    badge_pages = build_badges(deprecations)
    pages.update(badge_pages)
    print(f"Built {len(badge_pages)} deadline badges")

    # Deprecation Radar RSS (M3) — also written to /blog/feed.xml to fix the live 404
    rss = build_deprecations_rss(deprecations)
    pages["feed.xml"] = rss
    pages["blog/feed.xml"] = rss

    # Build sitemap
    sitemap = build_sitemap(deprecations)
    if sitemap:
        pages["sitemap.xml"] = sitemap

    # Build verification page
    verify_page = build_verify_page()
    if verify_page:
        pages["verify/index.html"] = verify_page

    # AI-search + crawler discovery, deterministic from the cited YAML
    pricing_view = build_pricing_view(pricing)
    pages["llms.txt"] = build_llms_txt(deprecations, pricing_view)
    pages["robots.txt"] = build_robots_txt()

    for path, content in pages.items():
        full_path = DOCS_DIR / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = inject_first_touch(path, normalize_project_links(content))
        full_path.write_text(normalize_generated_text(rendered), encoding="utf-8")
        print(f"Built: docs/{path}")

    # Binary social card (written outside the text loop) so every page's
    # og:image / twitter:image resolves instead of unfurling blank.
    write_og_image(DOCS_DIR / "og-default.png")
    print("Built: docs/og-default.png")

    # Render legal docs from Markdown into real, indexable HTML (deterministic,
    # stdlib-only). Replaces the old shutil.copy that served raw markdown as
    # .html with no <title>/meta/canonical. sorted() keeps output stable.
    legal_dir = DOCS_DIR.parent / "legal"
    legal_output = DOCS_DIR / "legal"
    if legal_dir.exists():
        legal_output.mkdir(exist_ok=True)
        legal_sources = sorted(legal_dir.glob("*.md"))
        security_file = DOCS_DIR.parent / "SECURITY.md"
        if security_file.exists():
            legal_sources.append(security_file)
        for legal_file in legal_sources:
            name = legal_file.stem
            md_text = legal_file.read_text()
            title = next(
                (line[2:].strip() for line in md_text.splitlines() if line.startswith("# ")),
                f"{name.title()} — EOLkits",
            )
            html_doc = md_to_html(md_text, title, f"/legal/{name}.html")
            output = legal_output / f"{name}.html"
            output.write_text(
                normalize_generated_text(normalize_project_links(html_doc)), encoding="utf-8"
            )
            print(f"Rendered: legal/{name}.html")

    print("=" * 40)
    print("Build complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
