#!/usr/bin/env python3
"""
EOLkits Static Site Generator
Builds docs/ from templates and rule-pack data.
"""

import os
import sys
import json
import re
import yaml
from pathlib import Path
from datetime import UTC, datetime, timedelta

# Jinja2 is the only external dependency
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Installing jinja2...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "jinja2"])
    from jinja2 import Environment, FileSystemLoader, select_autoescape


BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR.parent.parent / "docs"
PRICING_FILE = BASE_DIR.parent.parent / "pricing.yml"
# Production = GRACE, serving eolkits.com at the domain ROOT. Both values are
# env-overridable so a GitHub Pages project build is still possible, e.g.:
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
    return (
        html.replace("{API_URL}", API_URL)
        .replace("{{", "{")
        .replace("}}", "}")
    )


ROOT_RELATIVE_ATTR_RE = re.compile(
    r'(?P<prefix>\b(?:href|src|action)=["\'])(?P<path>/(?!/|EOLkits(?:/|["\'])))'
)
ROOT_RELATIVE_FETCH_RE = re.compile(
    r"(?P<prefix>fetch\([\"'])(?P<path>/(?!/|EOLkits(?:/|[\"'])))"
)


def load_pricing():
    """Load pricing configuration."""
    with open(PRICING_FILE) as f:
        return yaml.safe_load(f)


def normalize_project_links(html):
    """Make root-relative links work on a project sub-path (e.g. the /EOLkits
    GitHub Pages path). No-op when EOLKITS_BASE_PATH is empty — GRACE serves
    eolkits.com at the domain root, so root-relative links must stay as-is."""
    if not PROJECT_BASE_PATH:
        return html

    def replace(match):
        return f"{match.group('prefix')}{PROJECT_BASE_PATH}{match.group('path')}"

    html = ROOT_RELATIVE_ATTR_RE.sub(replace, html)
    return ROOT_RELATIVE_FETCH_RE.sub(replace, html)


def get_days_until_deadline(deadline_str):
    """Calculate days until a deadline."""
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").replace(tzinfo=UTC)
        return (deadline - datetime.now(UTC)).days
    except Exception:
        return 999


def nearest_enforcement(dep, today=None):
    """(days_until, date_str) for the NEAREST FUTURE enforcement date a deprecation
    carries ('date' = block-create, 'block_update_date' = block-update).

    Fixes the surge-collapse bug (LB-3): pricing keyed off a single 'date'
    (block-create) dropped to the standard tier the moment it passed — even while
    the harder block-update enforcement was still weeks ahead (the exact Feb->Mar
    2027 demand peak where the procrastinator mass sits). We now consider every
    enforcement date and return the smallest non-negative days-until.

    Returning the DATE alongside the count also keeps copy honest: the block-create
    date is often already past while the real countdown runs to block-update, so a
    "N days until <dep.date>" headline showed a date that disagreed with N (and with
    the front-end JS countdown). Callers interpolate THIS date, not the raw entry.
    """
    if today is None:
        today = datetime.now(UTC).date()
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
    """The single, date-granular build timestamp. Using date precision (not the
    wall-clock instant) is what keeps the emitted site byte-for-byte identical across
    any two rebuilds on the same UTC day — the determinism guarantee EOLkits sells.
    The previous microsecond/second timestamps changed on every rebuild."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


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
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

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
    """Surge price for a deadline proximity, read from pricing.yml tiers so the
    DISPLAYED price always equals the price the API charges at checkout.

    The previous multiplier form (base*2, int(base*1.33)) produced 598/397 for a
    $299 base, which did not match the canonical Stripe tier prices ($599/$399).
    We now resolve the same tiers the server uses; base_price is only a fallback.
    """
    try:
        tiers = sorted(
            load_pricing().get("skus", {}).get("audit", {}).get("tiers", []),
            key=lambda t: t.get("max_days", 9999),
        )
    except Exception:
        tiers = []
    if days_until < 0:
        days_until = 9999  # passed deadline -> standard tier (mirrors compute_urgency)
    for tier in tiers:
        if days_until <= int(tier.get("max_days", 9999)):
            return int(tier.get("price_usd", base_price))
    return base_price


def build_audit_page(pricing):
    """Build the audit checkout page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit — see what AWS breaks, then fix it | EOLkits</title>
<meta name="description" content="A free scan shows every AWS deprecation in your stack. The $299 audit is the done-for-you fix report — severity scoring, roll-forward roadmap, every fact cited to its AWS source. 30-day money-back.">
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
<h1>See exactly what AWS is about to break — then fix it in one report</h1>
<p class="lede">Run the free scanner on your own files first — ~30 seconds, no signup. The <strong>$299 audit</strong> is the done-for-you fix report for everything it finds: scored, sequenced, and cited. Money back if it isn't useful.</p>

<div class="callout">
  <strong>Don't take our word for it.</strong> &nbsp;<a class="cta secondary" href="/scan/">▶ Run the free scan</a><br>
  See every deprecation in your stack, on your own machine, <em>before</em> you pay a cent. The audit picks up where the scan ends — scoring, a roll-forward plan, and a verifiable report.
</div>

<h2>What you get</h2>
<ul>
  <li>Every finding scored by <strong>severity × blast-radius</strong> — what breaks first vs. what's cosmetic</li>
  <li>A <strong>roll-forward roadmap</strong>: the exact order to migrate, with each breaking change called out</li>
  <li>A <strong>cost-of-not-fixing</strong> estimate you can forward to your manager</li>
  <li>Every fact <strong>cited to its AWS primary source</strong> — check our work</li>
  <li>A <strong>hash-anchored PDF</strong>, verifiable at <code>/verify/&lt;sha&gt;</code></li>
</ul>
<p><a class="cta secondary" href="/audit/sample/">▶ See a real (redacted) sample report →</a></p>

<div class="pricing">
  <h2>Pricing</h2>
  <div class="tiers">
    <div class="tier">
      <strong>Standard</strong>
      <div class="price">$299</div>
      <p>More than 30 days until deadline</p>
    </div>
    <div class="tier soon">
      <strong>Surge (30d)</strong>
      <div class="price">$399</div>
      <p>Within 30 days of deadline</p>
    </div>
    <div class="tier urgent">
      <strong>Urgent (7d)</strong>
      <div class="price">$599</div>
      <p>Within 7 days of deadline</p>
    </div>
  </div>
  <p class="reassure">Price rises as the deadline nears — acting sooner costs you less. No discounts; the guarantee is your protection instead.</p>
</div>

<div class="valuebox">
  <strong>What does <em>not</em> fixing it cost?</strong> One failed production deploy, an unpatched box running past the deadline, or a frozen Lambda burns hours of engineer time and real downtime — usually far more than the audit. $299 to know precisely what's coming and how to clear it.
</div>

<div class="guarantee">
  <h3>Your risk: zero</h3>
  <p><strong>100% money-back, 30 days, no questions.</strong> If the report isn't useful, email us — we refund, no argument.</p>
  <p><strong>Beat the deadline or it's free.</strong> Order inside a deadline window and if we can't hand you a clear roll-forward path before it hits, you pay nothing.</p>
</div>

<h2>Why you can trust the report (without trusting the brand)</h2>
<div class="grid">
  <div class="cell"><h4>Cited to source</h4>Every finding links AWS's own documentation. You verify the claim, not our reputation.</div>
  <div class="cell"><h4>Hash-anchored</h4>Each report carries a SHA-256 of your inputs, verifiable at <code>/verify</code>. We can't quietly change it.</div>
  <div class="cell"><h4>Deterministic &amp; open</h4>Same input → same report. The rule-pack is public — inspect exactly what we check for.</div>
  <div class="cell"><h4>Instant &amp; automated</h4>Delivered in ~5 minutes by machine. No waiting on a person, no back-and-forth.</div>
</div>

<div class="logos">
  <span>AWS</span><span>CloudFormation / SAM</span><span>CDK</span><span>Terraform</span><span>Serverless</span><span>Ansible</span><span>Packer</span><span>cloud-init</span><span>GitHub Actions</span>
</div>

<h2>How it works</h2>
<ol>
  <li>Upload your SAM / CDK / Terraform / Serverless / cloud-init files</li>
  <li>We scan for deprecated runtimes and breaking changes — deterministically</li>
  <li>Get your PDF by email in ~5 minutes — fully automated</li>
  <li>Verify authenticity at <code>/verify/&lt;sha&gt;</code></li>
</ol>

<p class="reassure">🔒 Secure checkout via Stripe · delivered in ~5 minutes · 30-day money-back guarantee</p>

<form id="auditForm">
  <h3>Start Audit</h3>
  <p><input type="email" id="auditEmail" name="email" placeholder="your@email.com" required style="padding:0.5rem;width:300px"></p>
  <p><input type="date" id="auditDeadline" name="deadline" style="padding:0.5rem;width:300px" aria-label="Deadline date"></p>
  <p><input type="file" id="auditFile" name="file" required accept=".yaml,.yml,.json,.tf,.tfvars,.js,.ts,.py,.txt"></p>
  <button id="auditSubmit" type="submit">Upload and Proceed to Checkout</button>
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
const auditForm = document.getElementById('auditForm');
const auditStatus = document.getElementById('auditStatus');
const auditSubmit = document.getElementById('auditSubmit');
const deadlineInput = document.getElementById('auditDeadline');
// Prefill the deadline from a deadline-tagged migrate-page link so surge pricing
// is consistent between the page the buyer came from and what we charge.
if (qp.get('deadline') && deadlineInput) deadlineInput.value = qp.get('deadline');
if (qp.get('cancelled')) auditStatus.textContent = 'Checkout cancelled — finish whenever you are ready.';
track('view');
auditForm.addEventListener('submit', async (event) => {{
  event.preventDefault();
  const file = document.getElementById('auditFile').files[0];
  const email = document.getElementById('auditEmail').value;
  const deadline = deadlineInput ? deadlineInput.value : '';
  if (!file || !email) return;

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
    if (!presign.ok) throw new Error(presignData.error || 'Upload storage is unavailable');

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
    if (!checkout.ok || !checkoutData.url) throw new Error(checkoutData.error || 'Checkout failed');
    window.location.href = checkoutData.url;
  }} catch (error) {{
    auditSubmit.disabled = false;
    auditStatus.textContent = error instanceof Error ? error.message : 'Audit checkout failed';
  }}
}});
</script>

<div class="faq">
<h2>Questions</h2>
<details><summary>Why pay when the CLI is free?</summary><p>The free CLI and scanner show you <em>what</em> breaks. The audit does the work <em>for</em> you — severity × blast-radius scoring, a roll-forward roadmap, a cost-of-not-fixing estimate, and a verifiable report you can hand to your team, in ~5 minutes.</p></details>
<details><summary>Is my code safe?</summary><p>Your files travel over TLS and are used only to generate your report — never shared. Prefer to keep everything local? Run the free CLI offline.</p></details>
<details><summary>How can I trust the results if I've never heard of you?</summary><p>You don't have to. Every finding cites AWS's own docs, the report is hash-anchored and deterministic, and the rule-pack is public — run the free scan and compare. And you're covered by a 30-day no-questions refund.</p></details>
<details><summary>How fast is it?</summary><p>About 5 minutes, fully automated. No waiting on a human.</p></details>
<details><summary>What if it's wrong, or I'm just not happy?</summary><p>Email us within 30 days for a full refund. No questions asked.</p></details>
</div>

<footer>
  <p>Delivered in ~5 minutes · every report carries a SHA-256 of your inputs for verification · 30-day money-back guarantee.</p>
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
<meta name="description" content="A real, redacted EOLkits audit report: findings scored by severity and blast-radius, each cited to its AWS source, with a roll-forward roadmap and cost-of-not-fixing estimate.">
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
<div class="banner"><strong>SAMPLE — redacted.</strong> An illustrative report for a fictional account, to show exactly what you receive. Your report covers your own stack.</div>
<h1>EOLkits audit report</h1>
<div class="meta">
  <div><strong>Account:</strong> acme-prod (redacted)</div>
  <div><strong>Inputs:</strong> 3 Terraform files, 1 SAM template, 2 Dockerfiles</div>
  <div><strong>Report SHA-256:</strong> <code>3f9a…c1e2</code> — verifiable at <code>/verify/&lt;sha&gt;</code></div>
  <div><strong>Findings:</strong> 2 critical · 3 high · 1 medium</div>
</div>

<h2>Findings — scored by severity × blast-radius</h2>
<table>
<tr><th>Finding</th><th class="sev">Severity</th><th>Blast radius</th><th>Cited source</th></tr>
<tr><td>EC2 launch template pinned to an <strong>Amazon Linux 2</strong> AMI (EOL 2026-06-30)</td><td class="sev crit">Critical</td><td>14 instances across 2 ASGs</td><td>AWS AL2 EOL notice</td></tr>
<tr><td><code>yum</code> / <code>amazon-linux-extras</code> in user-data — removed on AL2023</td><td class="sev crit">Critical</td><td>Boot-time failure on every new instance</td><td>AL2023 release notes</td></tr>
<tr><td>Lambda <code>python3.9</code> runtime — update blocked 2027-03-03</td><td class="sev high">High</td><td>6 functions</td><td>Lambda runtime table</td></tr>
<tr><td><code>import distutils</code> — removed in Python 3.12</td><td class="sev high">High</td><td>2 functions</td><td>Python 3.12 what's-new</td></tr>
<tr><td><code>iptables</code> rules in cloud-init — nftables on AL2023</td><td class="sev high">High</td><td>Network setup on 14 instances</td><td>AL2023 release notes</td></tr>
<tr><td><code>ntpd</code> — replaced by chronyd on AL2023</td><td class="sev med">Medium</td><td>Time sync on 14 instances</td><td>AL2023 release notes</td></tr>
</table>

<h2>Roll-forward roadmap</h2>
<ol>
  <li><strong>Now → deadline:</strong> rebuild the base AMI on AL2023; swap <code>yum</code>→<code>dnf</code> and drop <code>amazon-linux-extras</code> in user-data.</li>
  <li><strong>Same change:</strong> migrate <code>iptables</code>→nftables and <code>ntpd</code>→chronyd (bundle with the AMI rebuild).</li>
  <li><strong>Next:</strong> fix the two <code>distutils</code> imports and move the 6 Lambdas to <code>python3.12</code> before the 2027 block dates.</li>
</ol>

<h2>Cost of not fixing</h2>
<p>Leave the AL2 instances past 2026-06-30 and they stop receiving security patches while new launches fail at boot. Exposure for this account: <strong>~14 production instances unpatched</strong> plus blocked autoscaling — hours of incident time at the worst possible moment.</p>

<a class="cta" href="/audit/">Get this report for your own stack — from $299 →</a>
<p><a href="/scan/">Or run the free scan first →</a></p>

<footer>
  <p>In a real report, every finding links its AWS primary source. Reports are hash-anchored and deterministic.</p>
  <p><a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></p>
</footer>
</body>
</html>"""
    return html


def build_pack_page(pricing):
    """Build the Migration Pack checkout page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Migration Pack — EOLkits</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.6}
.brand{color:#2563eb;font-weight:600}
h1{margin-top:0}
.lede{font-size:1.15rem;color:#374151}
.price{font-size:3rem;font-weight:700;color:#059669}
.callout{background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #2563eb;border-radius:8px;padding:1.25rem;margin:1.5rem 0}
.guarantee{background:#ecfdf5;border:2px solid #059669;border-radius:8px;padding:1.5rem;margin:1.5rem 0}
.guarantee h3{margin-top:0;color:#059669}
button{background:#2563eb;color:white;border:none;padding:0.75rem 1.5rem;border-radius:6px;font-size:1rem;cursor:pointer}
button:hover{background:#1d4ed8}
.steps{background:#f9fafb;border-radius:8px;padding:1.5rem;margin:1.5rem 0}
.steps ol{margin:0;padding-left:1.5rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin:1.5rem 0}
.cell{border:1px solid #e5e7eb;border-radius:8px;padding:1rem;font-size:.92rem}
.cell h4{margin:.2rem 0}
.logos{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}
.logos span{border:1px solid #d1d5db;border-radius:999px;padding:.3rem .8rem;font-size:.85rem;color:#374151;background:#f9fafb}
.faq{margin:2rem 0}
.faq details{border-bottom:1px solid #e5e7eb;padding:.75rem 0}
.faq summary{font-weight:600;cursor:pointer}
.reassure{color:#6b7280;font-size:.9rem;margin:.5rem 0}
.downsell{background:#f9fafb;border:1px dashed #d1d5db;border-radius:8px;padding:1rem;margin:1.5rem 0}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.875rem}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1>Migration Pack — we do the migration for you</h1>
<p class="price">$1,499</p>
<p class="lede">The audit tells you what's broken. The Pack fixes it: a real pull request on your repo with codemods, IaC patches, a canary rollout plan, and a rollback script — opened within 5 minutes.</p>

<div class="callout">
  <strong>It opens a PR — nothing merges without you.</strong> You review every line and merge only if you're happy. The bot never pushes to your default branch. And if your CI fails on the PR, you're <strong>automatically refunded</strong> — worst case costs you nothing but a code review.
</div>

<div class="guarantee">
  <h3>How the auto-refund works</h3>
  <p><strong>If your CI fails on the migration PR within 7 days, Stripe refunds you automatically</strong> — no email, no argument, no human in the loop. We only get paid when your own tests pass on our changes.</p>
  <p class="reassure">"CI fail" = a GitHub <code>check_run</code> / <code>check_suite</code> conclusion of failure on the PR. Choosing to accept the PR anyway (the <code>override:ci-failure</code> label) waives the refund.</p>
</div>

<div class="steps">
  <h3>What you get</h3>
  <ol>
    <li><strong>GitHub App Install</strong> — Grant read/write access to your repo</li>
    <li><strong>Automated Analysis</strong> — We scan for deprecated patterns</li>
    <li><strong>PR Created</strong> — Real PR with codemods and IaC patches within 5 minutes</li>
    <li><strong>CI Check</strong> — Run your existing tests</li>
    <li><strong>Auto-Refund</strong> — If CI fails and no override label added</li>
  </ol>
</div>

<h3>Install GitHub App</h3>
<p>First, install the EOLkits Migration Bot on your repository:</p>
<p><a href="{API_URL}/pack/install" style="display:inline-block;background:#24292f;color:white;padding:0.75rem 1.5rem;border-radius:6px;text-decoration:none;font-weight:600">Install GitHub App</a></p>

<h3>Or Purchase Now</h3>
<form action="{API_URL}/api/pack/checkout" method="POST">
  <p><input type="email" name="email" placeholder="your@email.com" required style="padding:0.5rem;width:300px"></p>
  <p><input type="text" name="repo" placeholder="owner/repo" required style="padding:0.5rem;width:300px"></p>
  <button type="submit">Purchase Migration Pack — $1,499</button>
</form>
<p class="reassure">🔒 Secure checkout via Stripe · PR opened in ~5 minutes · auto-refund if CI fails</p>

<h2>Why pay $1,499 instead of running the free CLI?</h2>
<div class="grid">
  <div class="cell"><h4>Done for you</h4>You review a PR instead of writing codemods — minutes of review vs. days of migration work.</div>
  <div class="cell"><h4>You stay in control</h4>It's a PR on a branch. Merge only if you're happy; nothing touches your default branch.</div>
  <div class="cell"><h4>Risk reversed</h4>If your CI fails you're auto-refunded. We're paid only when your tests pass.</div>
  <div class="cell"><h4>Cited &amp; verifiable</h4>Every change traces to an AWS source; the rule-pack is public. Check our work.</div>
</div>

<div class="logos">
  <span>AWS</span><span>CloudFormation / SAM</span><span>CDK</span><span>Terraform</span><span>Serverless</span><span>Ansible</span><span>Packer</span><span>GitHub Actions</span>
</div>

<div class="faq">
<h2>Questions</h2>
<details><summary>Does the bot push to my repo?</summary><p>No. It opens a pull request on a new branch. You review and merge — or not. It never commits to your default branch.</p></details>
<details><summary>What access does the GitHub App need?</summary><p>Contents and pull-requests on the repo you name — enough to open a PR. You can uninstall it the moment the PR lands.</p></details>
<details><summary>What if the PR is wrong?</summary><p>Don't merge it. And if CI fails, you're auto-refunded within 7 days — you risk a code review, nothing more.</p></details>
<details><summary>Not ready for a PR?</summary><p>Start with the free scan or the $299 audit — see exactly what's broken first, then upgrade.</p></details>
</div>

<div class="downsell">
  Not ready to grant repo access? <a href="/scan/">Run the free scan</a> or <a href="/audit/">get the $299 audit</a> first — see the findings, then upgrade to the done-for-you Pack.
</div>

<footer>
  <p>Refund auto-fires if CI fails within 7 days. <a href="/legal/terms.html">Terms</a> apply.</p>
  <p><a href="/">Home</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></p>
</footer>
<script>
(function () {{
  var qp = new URLSearchParams(location.search);
  var form = document.querySelector('form[action$="/api/pack/checkout"]');
  if (form) {{
    ['source', 'utm_source', 'utm_medium', 'utm_campaign', 'kit'].forEach(function (k) {{
      var v = qp.get(k);
      if (v) {{ var i = document.createElement('input'); i.type = 'hidden'; i.name = k; i.value = v; form.appendChild(i); }}
    }});
    if (!qp.get('source')) {{ var s = document.createElement('input'); s.type = 'hidden'; s.name = 'source'; s.value = 'pack_page'; form.appendChild(s); }}
  }}
  try {{
    navigator.sendBeacon('{API_URL}/api/events', new Blob([JSON.stringify({{ event: 'view', sku: 'migration_pack', path: location.pathname, utm_source: qp.get('utm_source') || '', utm_campaign: qp.get('utm_campaign') || '', kit: qp.get('kit') || '' }})], {{ type: 'application/json' }}));
  }} catch (e) {{}}
}})();
</script>
</body>
</html>"""
    return _interpolate_api(html)


def build_license_page(pricing):
    """Build the Org License page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Org License — EOLkits</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.6}
.brand{color:#2563eb;font-weight:600}
h1{margin-top:0}
.price{font-size:3rem;font-weight:700;color:#7c3aed}
button{background:#2563eb;color:white;border:none;padding:0.75rem 1.5rem;border-radius:6px;font-size:1rem;cursor:pointer}
button:hover{background:#1d4ed8}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;margin:1.5rem 0}
.feature{background:#f9fafb;border-radius:8px;padding:1rem}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.875rem}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1>Organization License</h1>
<p class="price">$14,999<span style="font-size:1rem;font-weight:normal;color:#6b7280">/year</span></p>
<p>Unlimited runs, live rule-pack feed, and private rule extensions for your entire organization.</p>

<div class="features">
  <div class="feature">
    <h3>Live Rule Feed</h3>
    <p>Get new deprecation rules the moment they're published — no 7-day delay.</p>
  </div>
  <div class="feature">
    <h3>Private Rules</h3>
    <p>Define custom rules specific to your organization's infrastructure patterns.</p>
  </div>
  <div class="feature">
    <h3>Unlimited Runs</h3>
    <p>No caps on scans, audits, or PRs across all your repositories.</p>
  </div>
  <div class="feature">
    <h3>License Key</h3>
    <p>One key activates all features across your CI/CD pipelines.</p>
  </div>
</div>

<h3>Request License</h3>
<p>Organization licenses are provisioned manually after verification:</p>
<form action="{API_URL}/api/license/inquiry" method="POST">
  <p><input type="email" name="email" placeholder="your@company.com" required style="padding:0.5rem;width:300px"></p>
  <p><input type="text" name="company" placeholder="Company name" required style="padding:0.5rem;width:300px"></p>
  <p><input type="number" name="repos" placeholder="Estimated repositories" style="padding:0.5rem;width:300px"></p>
  <button type="submit">Request License</button>
</form>

<footer>
  <p>License valid for one year from purchase. Auto-renewal optional.</p>
  <p><a href="/">Home</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></p>
</footer>
</body>
</html>"""
    return _interpolate_api(html)


def load_deprecations():
    """Load deprecation data from rules."""
    deprecations_file = BASE_DIR.parent.parent / "rules" / "public" / "deprecations.yml"
    if deprecations_file.exists():
        with open(deprecations_file) as f:
            return yaml.safe_load(f)
    return {"deprecations": []}


def slugify(name):
    """Convert name to URL slug."""
    return (
        name.lower()
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "-")
    )


def build_pricing_view(full_pricing):
    """Extract the canonical Audit/Migration-Pack facts (price + Stripe link)
    from pricing.yml so every page stays correct as pricing.yml updates."""
    skus = full_pricing.get("skus", full_pricing)

    audit = skus.get("audit", {})
    audit_tiers = {t.get("name"): t for t in audit.get("tiers", [])}
    standard = audit_tiers.get("standard", {})
    surge_30 = audit_tiers.get("surge_30d", {})
    surge_7 = audit_tiers.get("surge_7d", {})
    audit_base = standard.get("price_usd", 299)

    pack = skus.get("migration_pack", {})
    pack_base = pack.get("price_usd", 1499)
    drift = skus.get("drift_watch", {})

    # Always route to the on-site pages, which open server-side Checkout
    # Sessions. Direct Stripe Payment Links are intentionally NOT used on
    # customer-facing surfaces: they strip our fulfillment metadata (upload_id,
    # repo, deadline) and attribution (source/utm/kit), and bypass the
    # repo-installed gate for the Migration Pack.
    return {
        "audit_pdf": {
            "base": audit_base,
            "link": "/audit/",
            "surge_30d_price": surge_30.get("price_usd", 399),
            "surge_30d_link": "/audit/",
            "surge_7d_price": surge_7.get("price_usd", 599),
            "surge_7d_link": "/audit/",
        },
        "migration_pack": {
            "base": pack_base,
            "link": "/pack/",
        },
        "drift_watch": {
            "base": drift.get("price_usd", 19),
            "link": "/drift/",
        },
    }


def _audit_checkout_link(dep):
    """Deadline- and kit-tagged link to the on-site audit page, which carries
    the deadline into the server Checkout Session (so surge pricing + attribution
    survive). Replaces per-tier direct Stripe Payment Links.

    The deadline carried is the NEAREST enforcement date — the same date the page's
    displayed surge price is computed from — so the server recomputes the identical
    tier and the charged price matches what the buyer saw."""
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


def _pack_checkout_link(dep):
    from urllib.parse import urlencode

    q = {"utm_source": "migrate", "utm_medium": "cta", "utm_campaign": dep.get("slug", "")}
    if dep.get("kit"):
        q["kit"] = dep["kit"]
    return "/pack/?" + urlencode(q)


def compute_urgency(dep, pricing_view):
    """Deterministic urgency + surge pricing derived ONLY from the cited
    deadline date in deprecations.yml and the tiers in pricing.yml."""
    days, deadline_date = nearest_enforcement(dep)
    audit = pricing_view["audit_pdf"]

    if days < 0:
        tier, label = "passed", "deadline passed"
        headline = (
            f"This deadline passed on {deadline_date}. "
            "Affected resources are now in the post-deadline window — clean up before the next enforcement phase."
        )
        audit_price = audit["base"]
    elif days <= 7:
        tier, label = "urgent", "less than 7 days"
        headline = f"Only {days} days until the {deadline_date} deadline. This is the final week."
        audit_price = audit["surge_7d_price"]
    elif days <= 30:
        tier, label = "soon", "within 30 days"
        headline = f"{days} days until the {deadline_date} deadline."
        audit_price = audit["surge_30d_price"]
    else:
        tier, label = "ahead", "more than 30 days out"
        headline = f"{days} days until the {deadline_date} deadline — enough runway to migrate safely."
        audit_price = audit["base"]

    return {
        "tier": tier,
        "label": label,
        "headline": headline,
        "days_until": days,
        # The date the day count actually runs to — interpolated wherever a date is
        # shown next to days_until, so copy and the JS countdown never disagree.
        "deadline_date": deadline_date,
        "audit_price": audit_price,
        # Server-routed, deadline+kit+utm tagged (price is recomputed server-side
        # from the deadline, so the charged price matches audit_price shown here).
        "audit_link": _audit_checkout_link(dep),
        "pack_link": _pack_checkout_link(dep),
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
    """Build SEO pages for each deprecation. Every fact is sourced from
    deprecations.yml (and carries its source_url), satisfying RULES.md by
    construction — zero LLM, deterministic."""
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
        dep["slug"] = slugify(dep["name"])

    build_date = _build_date()
    pages = {}
    for dep in all_deps:
        urgency = compute_urgency(dep, pricing_view)
        related = find_related(dep, all_deps)
        meta_description = _truncate_meta(
            f"{dep['name']} ends {urgency['deadline_date']} ({urgency['label']}). "
            f"{dep.get('service', '')}. {len(dep.get('breaking_changes', []))} breaking changes, "
            f"exact migration facts, and a free CLI ({dep.get('kit') or 'EOLkits'}) to scan, "
            "codemod, and ship before the deadline."
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
    return template.render(
        deprecations=rows, site_url=SITE_URL, now=now_iso
    )


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
        dep["slug"] = slugify(dep["name"])

    return template.render(
        deprecations=deprecations.get("deprecations", []),
        competitors=[{"slug": slugify(c["name"])} for c in COMPETITORS],
        fixes=[f["slug"] for f in load_fixes()],
        now=datetime.now(UTC).strftime("%Y-%m-%d"),
        site_url=SITE_URL,
    )


def build_llms_txt(deprecations, pricing_view):
    """Deterministic llms.txt (llmstxt.org) so AI search engines can cite
    EOLkits' deprecation facts. Every line is sourced from deprecations.yml
    and carries the primary source_url — no model output, cannot hallucinate."""
    all_deps = deprecations.get("deprecations", [])
    for dep in all_deps:
        dep["slug"] = slugify(dep["name"])
    ordered = sorted(all_deps, key=lambda d: d.get("date", "9999-99-99"))

    lines = [
        "# EOLkits",
        "",
        "> Deterministic, CI-citation-gated CLIs and migration services for AWS "
        "platform deprecation deadlines (Lambda runtimes, Amazon Linux 2, IMDSv1). "
        "Every fact below is sourced from a primary AWS or upstream document.",
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
        f"- Free CLI: MIT-licensed kits (al2023-gate, python-pivot, lambda-lifeline). "
        f"git clone https://github.com/ntoledo319/EOLkits",
        f"- [Audit PDF]({SITE_URL}/audit/): ${pricing_view['audit_pdf']['base']} "
        f"(surges to ${pricing_view['audit_pdf']['surge_30d_price']} within 30 days, "
        f"${pricing_view['audit_pdf']['surge_7d_price']} within 7 days) — "
        f"hash-anchored deterministic finding report.",
        f"- [Migration Pack]({SITE_URL}/pack/): "
        f"${pricing_view['migration_pack']['base']:,} — automated PR with codemods + "
        f"IaC patches + canary plan + rollback; auto-refund if CI fails within 7 days.",
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
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )


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
        d for d in deprecations.get("deprecations", [])
        if "lambda" in (str(d.get("service", "")) + " " + " ".join(d.get("tags", []))).lower()
    ]
    lam.sort(key=lambda d: str(d.get("block_update_date") or d.get("date") or "9999-12-31"))
    rows = ""
    for d in lam:
        name = _h.escape(str(d.get("name", "")))
        slug = slugify(str(d.get("name", "")))
        rt = _h.escape(_runtime_id_from_name(str(d.get("name", ""))) or name)
        create = _h.escape(str(d.get("date") or "—"))
        update = _h.escape(str(d.get("block_update_date") or "—"))
        sev = _h.escape(str(d.get("severity", "")))
        tags = " ".join(d.get("tags", [])).lower()
        target = "python3.12" if "python" in tags else ("nodejs22" if "nodejs" in tags else "—")
        src = _h.escape(str(d.get("url", "")))
        rows += (
            '<tr><td><a href="/migrate/' + slug + '/"><code>' + rt + "</code></a></td>"
            "<td>" + create + "</td><td>" + update + "</td>"
            '<td class="sev sev-' + sev + '">' + sev + "</td>"
            "<td><code>" + target + "</code></td>"
            '<td><a href="' + src + '" target="_blank" rel="noopener nofollow">AWS</a></td></tr>'
        )
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "What happens when an AWS Lambda runtime is deprecated?",
             "acceptedAnswer": {"@type": "Answer", "text": "Existing functions keep running, but stop receiving security patches. AWS then blocks creating new functions on the runtime, and about 30 days later blocks updating existing ones — after that the function is frozen until you move it to a supported runtime."}},
            {"@type": "Question", "name": "How do I find which Lambda runtimes I'm using?",
             "acceptedAnswer": {"@type": "Answer", "text": "Run the free scanner at eolkits.com/scan over your SAM/CDK/Terraform/Serverless config (nothing is uploaded), or run: aws lambda list-functions --query 'Functions[].Runtime'."}},
            {"@type": "Question", "name": "What should I upgrade Lambda Python and Node runtimes to?",
             "acceptedAnswer": {"@type": "Answer", "text": "AWS recommends python3.12 for Python and nodejs22.x for Node. Both run on Amazon Linux 2023; expect to fix removed stdlib modules (distutils, cgi), the unbundled AWS SDK v2 on Node 18+, and native-wheel/ABI changes."}},
        ],
    }
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>AWS Lambda runtime deprecation schedule (2026–2027) | EOLkits</title>\n"
        '<meta name="description" content="Every AWS Lambda runtime deprecation date — when AWS blocks creating and updating functions on python3.9-3.11 and nodejs18/20, the recommended upgrade target, and the AWS source. Plus a free scanner to find yours.">\n'
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
        "<p>When each AWS Lambda runtime stops getting patches, when AWS blocks <strong>creating</strong> new functions on it, when AWS blocks <strong>updating</strong> existing ones, and what to move to. Every date comes from the AWS Lambda runtime deprecation table — each row links the source.</p>\n"
        '<p><a class="cta" href="/scan/">Scan your stack free — find your deprecated runtimes →</a></p>\n'
        '<table class="sched"><thead><tr><th>Runtime</th><th>Blocks create</th><th>Blocks update</th><th>Severity</th><th>Upgrade to</th><th>Source</th></tr></thead><tbody>\n'
        + rows
        + "\n</tbody></table>\n"
        '<p class="muted">Functions keep running after deprecation, but become unpatched and — after the block-update date — unmodifiable. Dates reflect the AWS-published schedule and can shift; the linked AWS page is authoritative.</p>\n'
        "<h2>Fixing the upgrade</h2>\n"
        '<p>The upgrade usually surfaces specific errors — removed stdlib modules, the unbundled AWS SDK v2 on Node 18+, native-wheel/ABI breaks. See <a href="/fix/">common migration error fixes</a>, or get a <a href="/audit/">hash-anchored audit ($'
        + str(audit_base)
        + ', 30-day money-back)</a> that scores every finding and hands back a roll-forward plan.</p>\n'
        '<p><a href="/migrate/">See all tracked AWS deadlines →</a></p>\n'
        "</body>\n</html>\n"
    )


def build_al2_checklist_page(deprecations, pricing_view):
    """Head-term page — the Amazon Linux 2 -> AL2023 migration checklist, the highest-
    volume query in the current deadline window. Built from the cited deprecations.yml
    AL2 entry; cross-links the matching /fix pages. Static & deterministic."""
    import html as _h
    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299
    al2 = next((d for d in deprecations.get("deprecations", [])
                if "amazon linux 2" in str(d.get("name", "")).lower()), {})
    date = _h.escape(str(al2.get("date", "2026-06-30")))
    src = _h.escape(str(al2.get("url", "https://aws.amazon.com/blogs/aws/update-on-amazon-linux-2-end-of-life/")))
    changes_html = "".join("<li>" + _h.escape(c) + "</li>" for c in al2.get("breaking_changes", []))
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "When is Amazon Linux 2 end of life?",
             "acceptedAnswer": {"@type": "Answer", "text": "Amazon Linux 2 reaches end of life on " + date.replace("&amp;", "&") + ". After that there are no more security patches, no new AMIs, and no extras updates — anything still on AL2 runs unpatched."}},
            {"@type": "Question", "name": "What breaks moving from Amazon Linux 2 to AL2023?",
             "acceptedAnswer": {"@type": "Answer", "text": "yum is replaced by dnf, amazon-linux-extras is gone, ntpd is replaced by chronyd, iptables is replaced by nftables, and Python 2 is no longer available. Package names also change (version-namespaced or moved to SPAL)."}},
            {"@type": "Question", "name": "Can I keep running Amazon Linux 2 after EOL?",
             "acceptedAnswer": {"@type": "Answer", "text": "The instances keep running, but receive no security patches and no new AMIs, and new launches of the AL2 AMI stop. Running unpatched in production is the risk — migrate to Amazon Linux 2023."}},
            {"@type": "Question", "name": "How do I find Amazon Linux 2 usage in my account?",
             "acceptedAnswer": {"@type": "Answer", "text": "Run the free scanner at eolkits.com/scan over your Terraform/CloudFormation/Packer/Ansible (nothing is uploaded), or use the al2023-gate CLI to enumerate AL2 AMIs, launch templates, and node groups across regions."}},
        ],
    }
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Amazon Linux 2 end-of-life: migration checklist (AL2 → AL2023) | EOLkits</title>\n"
        '<meta name="description" content="Amazon Linux 2 is EOL ' + date + '. A step-by-step AL2 to AL2023 migration checklist: yum to dnf, amazon-linux-extras, ntpd to chronyd, iptables to nftables, Python 2 removal — with the fix for each error. Free scanner to find your AL2 usage.">\n'
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
        '<div class="note"><strong>Amazon Linux 2 reaches end of life ' + date + '.</strong> After that: no security patches, no new AMIs, no extras updates. Anything still pinned to AL2 in a launch template, EKS node group, ECS task, Beanstalk env, or container base image runs unpatched. <a href="' + src + '" target="_blank" rel="noopener nofollow">[AWS source]</a></div>\n'
        '<p><a class="cta" href="/scan/">Scan your stack free — find every AL2 reference →</a></p>\n'
        "<h2>What changes on AL2023</h2>\n<ul>" + changes_html + "</ul>\n"
        "<h2>The checklist</h2>\n<ol class=\"chk\">\n"
        "<li><strong>Inventory.</strong> Find every AL2 AMI, launch template, EKS node group, ECS task definition, Beanstalk platform, and container base image. (<a href=\"/scan/\">free scan</a> or the <code>al2023-gate</code> CLI.)</li>\n"
        "<li><strong>Rebuild the base AMI on AL2023</strong> (Packer/EC2 Image Builder), then bake your app layers on top.</li>\n"
        "<li><strong>Package manager.</strong> Move <code>yum</code> usage to <code>dnf</code> and drop <code>amazon-linux-extras</code> — install packages directly, version-namespaced, or via SPAL. (<a href=\"/fix/amazon-linux-extras-command-not-found/\">extras fix</a> · <a href=\"/fix/amazon-linux-2023-dnf-unable-to-find-a-match/\">missing-package fix</a>)</li>\n"
        "<li><strong>Time sync.</strong> Replace <code>ntpd</code> with <code>chronyd</code>. (<a href=\"/fix/amazon-linux-2023-ntpd-service-not-found/\">ntpd fix</a>)</li>\n"
        "<li><strong>Firewall.</strong> Move <code>iptables</code> rules to <code>nftables</code>.</li>\n"
        "<li><strong>Python.</strong> AL2023 ships no Python 2 — port <code>python2</code> scripts/shebangs to <code>python3</code>. (<a href=\"/fix/amazon-linux-2023-python2-command-not-found/\">python2 fix</a>)</li>\n"
        "<li><strong>Test</strong> boot, app start, networking, and time sync on a canary instance.</li>\n"
        "<li><strong>Roll out</strong> with a staged canary (5 → 25 → 50 → 100%) and a tested rollback to the previous AMI.</li>\n"
        "</ol>\n"
        "<h2>Do it faster</h2>\n"
        '<p>The free <a href="/scan/">scanner</a> and the MIT <code>al2023-gate</code> CLI find and patch most of this. Want it done for you? A <a href="/audit/">hash-anchored audit ($'
        + str(audit_base)
        + ', 30-day money-back)</a> scores every finding by blast-radius and hands back a roll-forward plan; the <a href="/pack/">Migration Pack</a> opens the PR. See the full <a href="/migrate/amazon-linux-2-eol/">Amazon Linux 2 migration guide</a>.</p>\n'
        "</body>\n</html>\n"
    )


def build_al2_vs_al2023_page(deprecations, pricing_view):
    """Head-term comparison page — Amazon Linux 2 vs Amazon Linux 2023. High-volume
    comparison query, distinct intent from the guide/checklist. Facts from the AL2023
    'compare with AL2' doc. Static & deterministic."""
    import html as _h
    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299
    al2 = next((d for d in deprecations.get("deprecations", [])
                if "amazon linux 2" in str(d.get("name", "")).lower()), {})
    date = _h.escape(str(al2.get("date", "2026-06-30")))
    cmp_src = "https://docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html"
    rows = [
        ("Package manager", "yum", "dnf (a <code>yum</code> symlink remains for compatibility)"),
        ("Extras library", "amazon-linux-extras", "Removed — packages are default, version-namespaced (python3.11, nginx1.24), or in SPAL"),
        ("Time sync", "ntpd", "chronyd"),
        ("Firewall backend", "iptables", "nftables"),
        ("Python", "2.7 and 3.x", "3.x only — no Python 2"),
        ("glibc", "2.26", "2.34"),
        ("Releases &amp; support", "Single rolling release", "Versioned releases, 5-year support, quarterly updates, deterministic upgrades"),
        ("Security defaults", "Looser", "Hardened — SELinux on, IMDSv2-friendly, locked-down by default"),
    ]
    table = "".join("<tr><td><strong>" + a + "</strong></td><td>" + b + "</td><td>" + c + "</td></tr>" for a, b, c in rows)
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "What is the difference between Amazon Linux 2 and Amazon Linux 2023?",
             "acceptedAnswer": {"@type": "Answer", "text": "AL2023 replaces yum with dnf, removes amazon-linux-extras, swaps ntpd for chronyd and iptables for nftables, drops Python 2, ships glibc 2.34, and uses versioned 5-year-supported releases with hardened defaults."}},
            {"@type": "Question", "name": "Do I have to migrate from Amazon Linux 2 to AL2023?",
             "acceptedAnswer": {"@type": "Answer", "text": "Yes — Amazon Linux 2 reaches end of life on " + date.replace("&amp;", "&") + ", after which there are no security patches or new AMIs. AL2023 is the supported successor."}},
            {"@type": "Question", "name": "Is yum still available on Amazon Linux 2023?",
             "acceptedAnswer": {"@type": "Answer", "text": "A yum command remains as a symlink to dnf for backward compatibility, but dnf is the real package manager and amazon-linux-extras is gone."}},
        ],
    }
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Amazon Linux 2 vs Amazon Linux 2023: what changes | EOLkits</title>\n"
        '<meta name="description" content="Amazon Linux 2 vs AL2023, side by side: dnf vs yum, amazon-linux-extras, chronyd, nftables, Python, glibc, support windows — and why AL2 (EOL ' + date + ') must move to AL2023. Free scanner to find your AL2 usage.">\n'
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
        "<p>What actually changes between Amazon Linux 2 and Amazon Linux 2023 — and why it matters now: <strong>AL2 reaches end of life " + date + "</strong> (no more patches or AMIs), so AL2023 isn't optional. Facts below are from AWS's own AL2-vs-AL2023 comparison.</p>\n"
        '<table class="cmp"><thead><tr><th>Area</th><th>Amazon Linux 2</th><th>Amazon Linux 2023</th></tr></thead><tbody>' + table + "</tbody></table>\n"
        '<p><a href="' + cmp_src + '" target="_blank" rel="noopener nofollow">[AWS source: comparing AL2 and AL2023]</a></p>\n'
        '<p><a class="cta" href="/scan/">Scan your stack free — find your AL2 usage →</a></p>\n'
        "<h2>Migrating off AL2</h2>\n"
        '<p>The breaking changes above each have a known fix. See the step-by-step <a href="/amazon-linux-2-eol-checklist/">AL2 → AL2023 checklist</a> and the <a href="/migrate/amazon-linux-2-eol/">migration guide</a>, or get a <a href="/audit/">hash-anchored audit ($'
        + str(audit_base)
        + ', 30-day money-back)</a> that finds every AL2 reference and scores it.</p>\n'
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
        "utm_campaign:ft.utm_campaign||qp.get('utm_campaign')||'',"
        "ref:document.referrer||''};"
        "navigator.sendBeacon('" + API_URL + "/api/events',new Blob([JSON.stringify(p)],{type:'application/json'}));"
        "}catch(e){}})();"
    )


def build_index_page(pricing):
    """Build the canonical landing page from source data, not stale docs output."""
    pricing_view = build_pricing_view(pricing)
    audit = pricing_view["audit_pdf"]
    pack = pricing_view["migration_pack"]
    skus = pricing.get("skus", pricing)
    drift_base = skus.get("drift_watch", {}).get("price_usd", 19)
    org_base = skus.get("org_license", {}).get("price_usd", 14999)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EOLkits - AWS deprecation migration tools</title>
<meta name="description" content="MIT-licensed CLIs and paid automation for AWS runtime and platform deprecation migrations.">
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
      <a href="/audit/">Audit</a>
      <a href="/pack/">Migration Pack</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>

<main>
  <section class="hero">
    <div class="container">
      <div class="eyebrow">AWS runtime &amp; OS EOLs that break production</div>
      <h1>Find what AWS is about to break in your stack — free.</h1>
      <p class="lede">Run the open-source scanner on your own files and see every deprecation, scored, in ~30 seconds — no signup. Then fix it yourself with the MIT CLIs, or let us do it: a $299 audit report or a done-for-you migration PR. Every finding cited to AWS's own docs.</p>
      <div class="cta-row">
        <a class="btn-primary" href="/scan/">Run the free scan</a>
        <a class="btn-secondary" href="https://github.com/ntoledo319/EOLkits">Clone the CLIs</a>
        <a class="btn-ghost" href="/migrate/">See the deadlines</a>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <p class="sub">Free &amp; open-source (MIT) · every finding cited to an AWS primary source · hash-anchored, verifiable reports · 30-day money-back on paid tiers</p>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <h2>Live Kits</h2>
      <p class="sub">Each kit is standalone, MIT-licensed, and safe by default: scan first, apply only when requested.</p>
      <div class="kit-grid">
        <article class="kit-card urgent">
          <div class="kit-deadline">Jun 30, 2026</div>
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
          <div class="kit-deadline">Post-deadline cleanup</div>
          <h3>lambda-lifeline</h3>
          <p class="kit-sub">Lambda Node.js 20 to 22</p>
          <p>Patch Lambda runtime fields, source syntax, aws-sdk v2 usage, and staged deploy/rollback plans.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/lambda-lifeline">Read docs</a>
        </article>
      </div>
    </div>
  </section>

  <section class="section dark" id="pricing">
    <div class="container">
      <h2>Pricing</h2>
      <p class="sub">Try before you buy: the CLIs and the <a href="/scan/">browser scanner</a> are free — see exactly what breaks first. Paid tiers do the work for you, with a 30-day money-back guarantee.</p>
      <div class="pricing-grid">
        <article class="pricing-card">
          <h3>CLI</h3>
          <div class="price">$0</div>
          <p>All kits, unlimited local runs, MIT license.</p>
          <a class="btn-outline" href="https://github.com/ntoledo319/EOLkits">Get source</a>
        </article>
        <article class="pricing-card featured">
          <h3>Audit PDF</h3>
          <div class="price">from ${audit["base"]}</div>
          <p>Hash-anchored, cited report: severity × blast-radius scoring, roll-forward roadmap, cost-of-not-fixing estimate. Delivered in ~5 min. 30-day money-back.</p>
          <a class="btn-primary" href="/audit/">Order audit</a>
          <p class="small"><a href="/audit/sample/">See a sample report →</a></p>
        </article>
        <article class="pricing-card">
          <h3>Migration Pack</h3>
          <div class="price">${pack["base"]:,}</div>
          <p>GitHub App PR with codemods, IaC patches, canary plan, rollback, and CI-failure refund policy.</p>
          <a class="btn-outline" href="/pack/">Get pack</a>
        </article>
        <article class="pricing-card">
          <h3>Drift Watch</h3>
          <div class="price">${drift_base}<span class="per">/mo</span></div>
          <p>Weekly re-scan of a read-only IAM role, delta PDF on change, and an auto-PR on each new deprecation.</p>
          <a class="btn-outline" href="/drift/">Start watching</a>
        </article>
      </div>
      <p class="sub">Running this org-wide? An annual <a href="/license/">Org License</a> (${org_base:,}/yr) covers unlimited runs, private rule extensions, and a live rule-pack feed.</p>
    </div>
  </section>
</main>

<footer class="footer">
  <div class="container">
    <div class="muted small">© 2026 EOLkits. MIT-licensed kits for AWS deprecation migrations.</div>
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
    navigator.sendBeacon('{SITE_URL}/api/events', new Blob([JSON.stringify({{ event: 'widget_view', source: 'widget', sku: 'audit', meta: {{ repo: repo }} }})], {{ type: 'application/json' }}));
  }} catch (e) {{}}
}})();
"""


def build_partners_page():
    return _interpolate_api("""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Partners — EOLkits</title>
<style>body{font-family:system-ui,sans-serif;max-width:780px;margin:0 auto;padding:2rem;line-height:1.6}.brand{color:#2563eb;font-weight:600}.box{border:1px solid #e5e7eb;border-radius:8px;padding:1.5rem;margin:1.25rem 0;background:#f9fafb}button{background:#2563eb;color:#fff;border:0;padding:.7rem 1.4rem;border-radius:6px;cursor:pointer}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>White-label Partners</h1>
<p>Run EOLkits audits under your brand. 70% revenue share. Stripe Connect handles the split automatically — no invoicing, no reconciliation.</p>
<div class="box"><h3>How it works</h3>
<ol><li>Sign up with your business email and domain.</li>
<li>Add a DNS TXT record we provide to verify domain ownership (anti-impersonation).</li>
<li>Stripe Connect Express onboarding (one-time, ~3 minutes, handled by Stripe).</li>
<li>Call <code>POST /partners/&lt;your-slug&gt;/audit</code> from your tooling. We deliver a co-branded PDF and split the payment 70/30.</li></ol></div>
<form action="{API_URL}/partners/signup" method="POST">
<p><input type="email" name="email" placeholder="contact@yourcompany.com" required style="padding:.5rem;width:300px"></p>
<p><input type="text" name="display_name" placeholder="Display name" required style="padding:.5rem;width:300px"></p>
<p><input type="text" name="domain" placeholder="yourcompany.com" required style="padding:.5rem;width:300px"></p>
<button type="submit">Start partner signup</button></form>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a> · <a href="/legal/terms.html">Terms</a></footer></body></html>""")


def build_drift_page(pricing):
    """Self-serve Drift Watch ($19/mo MRR) subscription checkout page."""
    skus = pricing.get("skus", pricing)
    price = skus.get("drift_watch", {}).get("price_usd", 19)
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Drift Watch — EOLkits</title>
<meta name="description" content="$PRICE/mo: weekly re-scan of a read-only IAM role, a delta PDF when a new AWS deprecation touches your stack, and an auto-opened migration PR.">
<link rel="canonical" href="https://eolkits.com/drift/">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.6}
.brand{color:#2563eb;font-weight:600}
h1{margin-top:0}
.price{font-size:3rem;font-weight:700;color:#0ea5e9}
.feature{background:#f9fafb;border-radius:8px;padding:1rem;margin:.75rem 0}
button{background:#2563eb;color:white;border:none;padding:0.75rem 1.5rem;border-radius:6px;font-size:1rem;cursor:pointer}
button:hover{background:#1d4ed8}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.875rem}
</style>
</head>
<body>
<a href="/" class="brand">← EOLkits</a>
<h1>Drift Watch</h1>
<p class="price">$PRICE<span style="font-size:1rem;font-weight:normal;color:#6b7280">/month</span></p>
<p>Never get caught by an AWS deadline again. Weekly re-scan of a <strong>read-only</strong> IAM role — you grant read-only access, nothing more — with a delta PDF the moment a new deprecation touches your stack, plus an auto-opened migration PR so the fix starts itself.</p>
<div class="feature"><strong>Weekly scan</strong> — cron-driven, zero effort after setup.</div>
<div class="feature"><strong>Delta PDF on change</strong> — only when something actually shifts, so it stays signal, not noise.</div>
<div class="feature"><strong>Auto-PR on new deprecation</strong> — the migration is opened for you, with the same CI-failure refund stance as the Migration Pack.</div>
<h3>Subscribe</h3>
<form id="driftForm">
  <p><input type="email" id="driftEmail" name="email" placeholder="your@email.com" required style="padding:0.5rem;width:300px"></p>
  <p><input type="text" id="driftRepo" name="repo" placeholder="owner/repo (optional)" style="padding:0.5rem;width:300px"></p>
  <button id="driftSubmit" type="submit">Subscribe — $PRICE/mo</button>
  <p id="driftStatus" style="color:#6b7280;font-size:.875rem"></p>
</form>
<p style="color:#6b7280;font-size:.9rem">🔒 Secure checkout via Stripe · no contract, cancel anytime · read-only access only. Not sure yet? <a href="/scan/">Run the free scan first →</a></p>
<script>
const API = '{API_URL}';
const qp = new URLSearchParams(location.search);
const f = document.getElementById('driftForm');
const s = document.getElementById('driftStatus');
const b = document.getElementById('driftSubmit');
if (qp.get('cancelled')) s.textContent = 'Checkout cancelled.';
try {{ navigator.sendBeacon(API + '/api/events', new Blob([JSON.stringify({{ event: 'view', sku: 'drift_watch', path: location.pathname, utm_source: qp.get('utm_source') || '', utm_campaign: qp.get('utm_campaign') || '' }})], {{ type: 'application/json' }})); }} catch (e) {{}}
f.addEventListener('submit', async (e) => {{
  e.preventDefault();
  const email = document.getElementById('driftEmail').value;
  if (!email) return;
  b.disabled = true; s.textContent = 'Opening secure checkout...';
  try {{
    const body = new URLSearchParams({{ email: email, repo: document.getElementById('driftRepo').value, source: 'drift_page', utm_source: qp.get('utm_source') || '', utm_campaign: qp.get('utm_campaign') || '' }});
    const r = await fetch(API + '/api/drift/checkout', {{ method: 'POST', headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }}, body: body }});
    const d = await r.json();
    if (!r.ok || !d.url) throw new Error(d.error || 'Checkout failed');
    window.location.href = d.url;
  }} catch (err) {{ b.disabled = false; s.textContent = err instanceof Error ? err.message : 'Checkout failed'; }}
}});
</script>
<footer>
  <p>Cancel anytime. <a href="/">Home</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></p>
</footer>
</body>
</html>""".replace("$PRICE", str(price))
    return _interpolate_api(html)


def build_success_page():
    """Post-checkout success + per-SKU onboarding, with the audit->pack upsell."""
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
  h('<div class="card"><p>Payment received. Your hash-anchored audit PDF is generating now and lands in your inbox within ~5 minutes.</p><p>Verify authenticity any time at <a href="/verify/">/verify/</a>.</p></div>'
    + '<div class="card upsell"><h3>Want it fixed, not just found?</h3><p>Upgrade to a <strong>Migration Pack</strong> within 48 hours and we credit your $299 audit toward the $1,499 — a real PR with codemods, IaC patches, canary plan, and a CI-failure refund guarantee.</p><p><a class="btn" href="/pack/?utm_source=audit_upsell&utm_medium=success&utm_campaign=audit48h">Apply my $299 credit →</a></p></div>'
    + '<div class="card"><h3>Never get surprised again</h3><p>Add <strong>Drift Watch</strong> ($19/mo) — weekly re-scan of a read-only role, a delta PDF when a new AWS deadline hits your stack, and an auto-PR. Cancel anytime.</p><p><a class="btn" href="/drift/?utm_source=audit_success&utm_medium=success&utm_campaign=drift_xsell">Add Drift Watch →</a></p></div>');
}} else if (sku === 'pack') {{
  title.textContent = 'Migration Pack confirmed';
  h('<div class="card"><p>Payment received. We are opening your migration PR now (within ~5 minutes). Watch the repo you authorized.</p><p>If CI fails on the PR within 7 days and you have not added the <code>override:ci-failure</code> label, you are refunded automatically.</p><p>Track fulfillment on the <a href="/status/">status page</a>.</p></div>');
}} else if (sku === 'drift') {{
  title.textContent = 'Drift Watch is on';
  h('<div class="card"><p>Subscription active. We will scan weekly and email a delta PDF the moment a new AWS deprecation touches your stack.</p></div>');
}} else {{
  h('<div class="card"><p>Payment received. Check your email for next steps.</p></div>');
}}
try {{ navigator.sendBeacon('{API_URL}/api/events', new Blob([JSON.stringify({{ event: 'purchase_success', sku: sku, path: location.pathname, meta: {{ session_id: sid }} }})], {{ type: 'application/json' }})); }} catch (e) {{}}
</script>
</body>
</html>"""
    return _interpolate_api(html)


def build_status_page():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Status — EOLkits</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:2rem;line-height:1.6}.brand{color:#2563eb;font-weight:600}.svc{display:flex;justify-content:space-between;align-items:center;border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin:.5rem 0}.dot{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;background:#9ca3af}.dot.green{background:#10b981}.dot.red{background:#ef4444}.muted{color:#6b7280;font-size:.85rem}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>System Status</h1>
<p class="muted">Synthetic checks every 5 minutes. Data pulled from <a href="/status/data.json">/status/data.json</a>.</p>
<div id="services"><div class="svc"><span><span class="dot" id="dot-stripe"></span>Stripe checkout</span><span id="t-stripe">—</span></div>
<div class="svc"><span><span class="dot" id="dot-worker"></span>Worker API</span><span id="t-worker">—</span></div>
<div class="svc"><span><span class="dot" id="dot-runner"></span>Job runner</span><span id="t-runner">—</span></div>
<div class="svc"><span><span class="dot" id="dot-email"></span>Email delivery</span><span id="t-email">—</span></div>
<div class="svc"><span><span class="dot" id="dot-github"></span>GitHub App</span><span id="t-github">—</span></div></div>
<h2>Throughput (last 7 days)</h2>
<ul id="metrics"><li>Loading…</li></ul>
<script>
fetch('/status/data.json').then(r=>r.json()).then(d=>{
  for(const s of ['stripe','worker','runner','email','github']){
    const v=(d.checks||{})[s];
    if(v){document.getElementById('dot-'+s).className='dot '+(v.ok?'green':'red');document.getElementById('t-'+s).textContent=v.last_checked||'';}
  }
  const m=document.getElementById('metrics');m.innerHTML='';
  for(const [k,v] of Object.entries(d.metrics||{})){const li=document.createElement('li');li.textContent=k+': '+v;m.appendChild(li);}
}).catch(()=>{document.getElementById('metrics').innerHTML='<li>status feed unavailable</li>';});
</script>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>"""


def build_status_data_seed():
    # Date-stable so the committed seed doesn't churn on every rebuild; the live
    # status feed is refreshed at runtime by status-synth.yml.
    now = _build_date() + "T00:00:00Z"
    return json.dumps(
        {
            "generated_at": now,
            "checks": {
                "stripe": {"ok": True, "last_checked": now},
                "worker": {"ok": True, "last_checked": now},
                "runner": {"ok": True, "last_checked": now},
                "email": {"ok": True, "last_checked": now},
                "github": {"ok": True, "last_checked": now},
            },
            "metrics": {
                "audits_delivered_7d": 0,
                "prs_opened_7d": 0,
                "drift_watch_subscribers": 0,
                "rules_in_public_pack": 0,
            },
        },
        indent=2,
    )


def build_blog_index():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blog — EOLkits</title>
<style>body{font-family:system-ui,sans-serif;max-width:780px;margin:0 auto;padding:2rem;line-height:1.6}.brand{color:#2563eb;font-weight:600}article{border-bottom:1px solid #e5e7eb;padding:1rem 0}time{color:#6b7280;font-size:.85rem}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>Operations log</h1>
<p>Auto-published every week from CI. <a href="/blog/feed.xml">RSS</a></p>
<article><time>—</time><h2>Welcome</h2><p>This log is generated weekly by <code>.github/workflows/blog-loop.yml</code>. The first real entry lands after the next CI run.</p></article>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>"""


def build_vs_index(competitors):
    items = "".join(
        f'<li><a href="/vs/{slugify(c["name"])}/">EOLkits vs {c["name"]}</a> <span style="color:#6b7280">— {c["category"]}</span></li>'
        for c in competitors
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comparisons — EOLkits</title>
<style>body{{font-family:system-ui,sans-serif;max-width:780px;margin:0 auto;padding:2rem;line-height:1.6}}.brand{{color:#2563eb;font-weight:600}}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>EOLkits vs alternatives</h1>
<p>Factual comparisons updated nightly from public sources. No logos used. Plain-text product names under nominative fair use.</p>
<ul>{items}</ul>
<p style="color:#6b7280;font-size:.85rem">Pages reflect public data as of the timestamp shown on each page. If a fact is wrong or outdated, open an issue.</p>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>"""


def build_vs_page(competitor):
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EOLkits vs {competitor["name"]} — comparison</title>
<meta name="description" content="Factual comparison of EOLkits and {competitor["name"]} for AWS deprecation migrations. As of {today}.">
<link rel="canonical" href="{SITE_URL}/vs/{slugify(competitor["name"])}/">
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:2rem;line-height:1.6}}.brand{{color:#2563eb;font-weight:600}}table{{width:100%;border-collapse:collapse;margin:1rem 0}}th,td{{border:1px solid #e5e7eb;padding:.6rem;text-align:left}}th{{background:#f9fafb}}.muted{{color:#6b7280;font-size:.85rem}}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>EOLkits vs {competitor["name"]}</h1>
<p class="muted">Category: {competitor["category"]}. Source: <a href="{competitor["url"]}" rel="nofollow">{competitor["url"]}</a>. As of {today}.</p>
<table><tr><th>Capability</th><th>EOLkits</th><th>{competitor["name"]}</th></tr>
<tr><td>License</td><td>MIT (open core)</td><td>{competitor.get("license", "—")}</td></tr>
<tr><td>Codemod / source rewriting</td><td>Yes</td><td>{competitor.get("codemod", "—")}</td></tr>
<tr><td>IaC patching (SAM/CDK/TF)</td><td>Yes</td><td>{competitor.get("iac", "—")}</td></tr>
<tr><td>Canary deploy + rollback</td><td>Yes</td><td>{competitor.get("canary", "—")}</td></tr>
<tr><td>Determinism (CI-gated)</td><td>Yes</td><td>{competitor.get("deterministic", "—")}</td></tr>
<tr><td>Hash-anchored audit reports</td><td>Yes</td><td>{competitor.get("hash_anchored", "—")}</td></tr>
<tr><td>Pricing</td><td>Free CLI; Audit $299; Pack $1,499</td><td>{competitor.get("pricing", "—")}</td></tr></table>
<p class="muted">Trademark notice: "{competitor["name"]}" is referenced in plain text under nominative fair use. No logos are used. If you operate this product and a fact above is wrong, please open an issue at <a href="https://github.com/ntoledo319/EOLkits/issues">github.com/ntoledo319/EOLkits/issues</a> and we will correct within 24h of confirmation.</p>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a> · <a href="/vs/">All comparisons</a></footer></body></html>"""


COMPETITORS = [
    {
        "name": "CloudQuery",
        "category": "Cloud asset inventory",
        "url": "https://www.cloudquery.io/",
        "license": "Apache-2.0",
        "codemod": "No",
        "iac": "No (read-only)",
        "canary": "No",
        "deterministic": "n/a",
        "hash_anchored": "No",
        "pricing": "Free + paid SaaS",
    },
    {
        "name": "HeroDevs",
        "category": "Post-EOL support subscription",
        "url": "https://www.herodevs.com/",
        "license": "Proprietary",
        "codemod": "No",
        "iac": "No",
        "canary": "No",
        "deterministic": "n/a",
        "hash_anchored": "No",
        "pricing": "Enterprise quote",
    },
    {
        "name": "aws-samples runtime-update-helper",
        "category": "AWS sample script",
        "url": "https://github.com/aws-samples/aws-lambda-runtime-update-helper",
        "license": "MIT-0",
        "codemod": "No",
        "iac": "No (runtime field flip only)",
        "canary": "No",
        "deterministic": "Unspecified",
        "hash_anchored": "No",
        "pricing": "Free",
    },
]


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
        uid = f"{slugify(dep['name'])}@eolkits"
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
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            r'<a href="\2" rel="noopener">\1</a>',
            s,
        )
        return s

    out, para, in_list = [], [], False

    def flush_para():
        if para:
            text = " ".join(para).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            para.clear()

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            flush_para()
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue
        if re.match(r"^[-*]\s+", line):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(re.sub(r'^[-*]\s+', '', line))}</li>")
            continue
        para.append(line.strip())
    flush_para()
    if in_list:
        out.append("</ul>")

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
        "</head>\n"
        '<body class="container article">\n'
        f"{body}\n"
        "</body>\n</html>\n"
    )


# First-touch attribution shim (M4a): persists the first MEANINGFUL referral
# (utm params, or an AI answer-engine referrer like chatgpt.com / perplexity.ai)
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
    var q=new URLSearchParams(location.search), ref=document.referrer||'', aeo='';
    if(/chatgpt\\.com|chat\\.openai\\.com/i.test(ref))aeo='chatgpt';
    else if(/perplexity\\.ai/i.test(ref))aeo='perplexity';
    else if(/gemini\\.google\\.com/i.test(ref))aeo='gemini';
    else if(/claude\\.ai/i.test(ref))aeo='claude';
    var ext = ref && ref.indexOf(location.host)===-1;
    var hasUtm = q.get('utm_source')||q.get('source')||q.get('utm_campaign')||q.get('kit');
    if(!hasUtm && !aeo && !ext)return;  // wait for the first MEANINGFUL touch
    localStorage.setItem(KEY, JSON.stringify({
      source: q.get('source')||(aeo?('aeo_'+aeo):'')||'',
      utm_source: q.get('utm_source')||aeo||'',
      utm_medium: q.get('utm_medium')||(aeo?'ai_referral':''),
      utm_campaign: q.get('utm_campaign')||'',
      kit: q.get('kit')||'',
      ref: ref.slice(0,200), landing: location.pathname, ts: new Date().toISOString()
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
# Ported faithfully from the paid kits so the free scan reports the SAME findings
# the kits would (honest + citable, not an approximation). Tables sourced from:
#   kits/lambda-lifeline/src/deps/index.mjs  (NATIVE_PACKAGES, cross-checked 2026-04-28)
#   kits/python-pivot/src/python_pivot/audit.py  (PY312_WHEEL_TABLE)
# Runtime deadlines are derived from the cited deprecations.yml at build time, so
# the scanner stays in lockstep with the source of truth (no duplicated dates).
_NATIVE_PACKAGES = {
    "sharp": {"min": "0.33.0", "note": "libvips native binding. v0.33+ ships Node 22 prebuilds."},
    "bcrypt": {"min": "5.1.1", "note": "Native bcrypt. Consider bcryptjs for a pure-JS drop-in."},
    "better-sqlite3": {"min": "11.0.0", "note": "SQLite native binding."},
    "canvas": {"min": "2.11.2", "note": "node-canvas. Needs rebuilt prebuilds for Node 22."},
    "node-gyp": {"min": "10.0.0", "note": "Build system. Upgrade before rebuilding natives."},
    "node-sass": {"min": None, "note": "DEAD. Use sass (Dart Sass) instead — no native deps."},
    "bufferutil": {"min": "4.0.8", "note": "WebSocket utility native addon."},
    "utf-8-validate": {"min": "6.0.4", "note": "WebSocket utility native addon."},
    "libpq": {"min": "2.0.0", "note": "PostgreSQL client. Prefer pg-native alternatives."},
    "grpc": {"min": None, "note": "DEAD. Migrate to @grpc/grpc-js (pure JS)."},
    "@grpc/grpc-js": {"min": "1.10.0", "note": "Pure JS, no native; just keep up to date."},
    "sqlite3": {"min": "5.1.7", "note": "SQLite3 bindings. Prebuilds available."},
    "argon2": {"min": "0.40.0", "note": "argon2 bindings."},
    "re2": {"min": "1.21.0", "note": "RE2 regex engine."},
    "fibers": {"min": None, "note": "DEAD since Node 16. Must remove."},
    "@tensorflow/tfjs-node": {"min": "4.20.0", "note": "TensorFlow native."},
    "sodium-native": {"min": "4.3.0", "note": "libsodium bindings."},
    "zmq": {"min": None, "note": "DEAD. Use zeromq instead."},
    "zeromq": {"min": "6.1.2", "note": "ZeroMQ bindings."},
    "farmhash": {"min": "4.0.0", "note": "Native hashing."},
    "@napi-rs/snappy": {"min": "7.2.0", "note": "Snappy compression."},
    "heapdump": {"min": None, "note": "DEAD. Use node --heapsnapshot-signal instead."},
}
_PY312_WHEELS = {
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
    "python-snappy": {"min": None, "note": "No cp312 wheels. Switch to cramjam or plyvel."},
    "fastparquet": {"min": "2023.10.1", "note": "2023.10.1+ for cp312."},
}


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
    if (d) out.push({ kind: 'runtime', file, name: rt, severity: d.historical ? 'critical' : (d.severity || 'high'), date: d.date, kit: d.kit, historical: d.historical, note: d.historical ? 'Already past deprecation — unpatched and increasingly unblockable.' : 'Deprecated Lambda runtime; AWS blocks function create/update after this date.' });
  });
  return out;
}
function scanPkg(file, c) {
  let pkg; try { pkg = JSON.parse(c); } catch (e) { return []; }
  const deps = Object.assign({}, pkg.dependencies || {}, pkg.devDependencies || {}), out = [];
  for (const name in deps) {
    const info = DATA.native[name]; if (!info) continue;
    const declared = cleanV(deps[name]);
    if (info.min === null) { out.push({ kind: 'native', file, name, severity: 'critical', declared: declared || '(unpinned)', required: '(no Node 22 build — remove)', note: info.note }); continue; }
    if (declared && !vlt(declared, info.min)) continue;
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
function auditLink(deadline, kit) { const p = new URLSearchParams({ source: 'scan', utm_source: 'scan', utm_medium: 'tool', utm_campaign: 'free-scan' }); if (deadline) p.set('deadline', deadline); if (kit) p.set('kit', kit); return '/audit/?' + p.toString(); }
const SEV_RANK = { critical: 0, high: 1, low: 2 };
function render(all) {
  const box = $('#results');
  if (!all.length) { box.innerHTML = '<div class="scan-ok">No deprecated runtimes or incompatible dependencies in the files you dropped. This free scan covers the high-blast-radius cases; a full audit checks every function, AMI and launch template.</div>'; return; }
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
    '<a class="scan-cta" href="' + auditLink(deadline, kit) + '">Fix all of this — full audit of every function, AMI &amp; dependency, hash-anchored PDF, 30-day money-back &rarr;</a>';
}
const dz = $('#dz'), fi = $('#fi'); let acc = [];
function handle(files) { acc = []; const arr = [...files]; let pending = arr.length; if (!pending) return; arr.forEach((file) => { const r = new FileReader(); r.onload = () => { try { acc = acc.concat(scanFile(file.name, r.result)); } catch (e) {} if (--pending === 0) render(acc); }; r.onerror = () => { if (--pending === 0) render(acc); }; r.readAsText(file); }); }
dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', (e) => { e.preventDefault(); dz.classList.remove('over'); handle(e.dataTransfer.files); });
dz.addEventListener('click', () => fi.click());
fi.addEventListener('change', () => handle(fi.files));
var lf = document.getElementById('leadForm');
if (lf) lf.addEventListener('submit', function (e) {
  e.preventDefault();
  var msg = document.getElementById('leadMsg');
  if (document.getElementById('leadHoney').value) { if (msg) msg.textContent = 'Thanks!'; lf.reset(); return; }
  var email = document.getElementById('leadEmail').value;
  if (msg) msg.textContent = 'Saving...';
  fetch('/api/v1/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: email, product: 'eolkits', source: 'scan' }) })
    .then(function (r) { return r.ok ? (r.json().catch(function () { return {}; })) : Promise.reject(); })
    .then(function () { if (msg) msg.textContent = '✓ You are on the list.'; lf.reset(); })
    .catch(function () { if (msg) msg.textContent = 'Could not save — email hello@toledotechnologies.com'; });
});
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
                "slug": slugify(dep.get("name", "")),
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
        '<meta name="description" content="Drop your SAM/CDK/Terraform/Serverless, package.json or requirements.txt to instantly find deprecated AWS Lambda runtimes and the Node 22 / Python 3.12 dependency breakages that block a migration. Runs entirely in your browser — nothing is uploaded.">\n'
        f'<link rel="canonical" href="{SITE_URL}/scan/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        + _og_image_meta()
        + "<style>"
        "#dz{border:2px dashed #94a3b8;border-radius:10px;padding:2.5rem 1rem;text-align:center;cursor:pointer;background:#f8fafc}"
        "#dz.over{border-color:#2563eb;background:#eff6ff}"
        ".scan-tbl{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.88rem}"
        ".scan-tbl th,.scan-tbl td{border-bottom:1px solid #eee;padding:.5rem;text-align:left;vertical-align:top}"
        ".sev-critical td:first-child{color:#b91c1c;font-weight:700}"
        ".sev-high td:first-child{color:#b45309;font-weight:700}"
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
        "Node&nbsp;22 / Python&nbsp;3.12 dependency breakages that block a migration. "
        '<span class="privacy">Everything runs in your browser — nothing is uploaded.</span> '
        "Open your browser&rsquo;s Network tab and watch: this page makes zero requests while it scans.</p>\n"
        '<div id="dz"><strong>Drop files here</strong><br><small>or click to choose — template.yaml, serverless.yml, *.tf, CDK *.ts, package.json, requirements.txt, pyproject.toml</small>'
        '<input id="fi" type="file" multiple accept=".yaml,.yml,.json,.tf,.ts,.js,.mjs,.txt,.toml" style="display:none"></div>\n'
        '<div id="results"></div>\n'
        "<h2>What it checks</h2>\n<ul>"
        "<li><strong>Lambda runtimes</strong> in SAM, CloudFormation, CDK, Terraform and Serverless Framework — flagged against AWS&rsquo;s published deprecation dates.</li>"
        "<li><strong>Node native dependencies</strong> (sharp, bcrypt, better-sqlite3&hellip;) that need a version bump or removal for Node&nbsp;22.</li>"
        "<li><strong>Python wheels</strong> (numpy, pandas, cryptography&hellip;) that need a bump for a Python&nbsp;3.12 runtime.</li>"
        "</ul>\n"
        '<p>Hit a specific error message? See <a href="/fix/">common AWS migration error fixes &rarr;</a></p>\n'
        "<p><small>This free scan covers the high-blast-radius cases. The paid audit checks every function, AMI and launch "
        "template in your account, produces a hash-anchored PDF and a roll-forward roadmap, and is priced by how close your deadline is.</small></p>\n"
        '<section class="leadcap" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:1.25rem;margin:2rem 0">\n'
        "<h2 style=\"margin-top:0\">Not migrating today? Don't get caught by the next deadline.</h2>\n"
        "<p>AWS retires runtimes on a schedule. Drop your email and we'll warn you before each deadline that affects your stack &mdash; no spam, one heads-up per deadline.</p>\n"
        '<form id="leadForm" autocomplete="on" style="display:flex;flex-wrap:wrap;gap:.5rem;align-items:center">\n'
        '<input type="email" id="leadEmail" name="email" placeholder="you@company.com" required style="padding:.6rem;border:1px solid #cbd5e1;border-radius:6px;min-width:260px">\n'
        '<input type="text" name="_honey" id="leadHoney" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px" value="">\n'
        '<button type="submit" style="background:#2563eb;color:#fff;border:0;padding:.65rem 1.2rem;border-radius:6px;font-weight:600;cursor:pointer">Email me deadline alerts</button>\n'
        '<span id="leadMsg" style="font-size:.9rem;color:#16a34a"></span>\n'
        "</form>\n"
        '<p style="font-size:.8rem;color:#6b7280;margin:.5rem 0 0">Free. Unsubscribe anytime. We email you only about AWS deadlines that hit your stack.</p>\n'
        "</section>\n"
    )
    tail = "</body>\n</html>\n"
    return head + body + "<script>\nconst DATA = " + data + ";\n" + _SCAN_JS + "\n</script>\n" + tail


# --- M2: the /fix/<error> verbatim-error corpus --------------------------- #
def load_fixes():
    """Load the hand-verified verbatim-error corpus that drives /fix pages.
    Tolerant: returns [] if the file is absent."""
    p = BASE_DIR / "content" / "fixes.yml"
    if not p.exists():
        return []
    with open(p) as f:
        data = yaml.safe_load(f) or {}
    return data.get("fixes", [])


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
    Every fix is sourced; FAQPage + HowTo JSON-LD make them answer-engine-citable;
    each cross-links /scan, the related /migrate deadline, and the audit CTA. The
    CTA points at the on-site /audit/ Checkout path (not a raw Stripe link)."""
    import html as _h
    if not fixes:
        return {}
    pricing_view = build_pricing_view(full_pricing)
    try:
        ap = pricing_view["audit_pdf"]
        audit_base = ap["base"] if isinstance(ap, dict) else getattr(ap, "base", None)
    except Exception:
        audit_base = None
    dep_by_slug = {slugify(d["name"]): d for d in deprecations.get("deprecations", [])}

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
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": 'What does "' + error + '" mean?',
                 "acceptedAnswer": {"@type": "Answer", "text": (summary + " " + cause).strip()}},
                {"@type": "Question", "name": 'How do I fix "' + error + '"?',
                 "acceptedAnswer": {"@type": "Answer", "text": (" ".join(steps) + (" Source: " + source if source else "")).strip()}},
            ],
        }
        howto = {
            "@context": "https://schema.org", "@type": "HowTo", "name": "Fix: " + error,
            "step": [{"@type": "HowToStep", "position": i + 1, "text": s} for i, s in enumerate(steps)],
        }
        if source:
            howto["citation"] = source

        desc = _h.escape((summary + " " + (steps[0] if steps else ""))[:155])
        steps_html = "".join("<li>" + _h.escape(s) + "</li>" for s in steps)
        rel_html = ""
        if rel and rel_dep:
            rel_html = ('<p class="fix-rel">Related deadline: <a href="/migrate/' + rel + '/">'
                        + _h.escape(rel_dep.get("name", "")) + "</a> — <strong>"
                        + _h.escape(str(rel_date)) + "</strong>.</p>\n")
        audit_link = _fix_audit_link(slug, kit, rel_date)
        cta_price = ("$" + str(audit_base)) if audit_base else "the audit"

        head = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            "<title>" + _h.escape(error) + " — cause &amp; fix (" + _h.escape(context) + ") | EOLkits</title>\n"
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
            + _h.escape(context) + "</span></nav>\n"
            '<p class="muted">' + _h.escape(context) + "</p>\n"
            "<h1>" + _h.escape(error) + "</h1>\n"
            '<pre class="fix-err"><code>' + _h.escape(error) + "</code></pre>\n"
            "<h2>What it means</h2>\n<p>" + _h.escape(summary) + "</p>\n"
            "<h2>Why it happens</h2>\n<p>" + _h.escape(cause) + "</p>\n"
            '<h2>How to fix it</h2>\n<ol class="fix-steps">' + steps_html + "</ol>\n"
            + rel_html
            + "<h2>Find every instance in your project</h2>\n"
            + '<p>The free <a href="/scan/">EOLkits scanner</a> runs in your browser (nothing uploaded) and flags this and related breakages across your IaC and dependency files.</p>\n'
            + (('<p>Primary source: <a href="' + _h.escape(source) + '" target="_blank" rel="noopener nofollow">' + _h.escape(source) + "</a></p>\n") if source else "")
            + '<p><a class="fix-cta" href="' + audit_link + '">Get the full migration audit — ' + cta_price + ", hash-anchored PDF &rarr;</a></p>\n"
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
        '<meta name="description" content="Plain-English causes and verified fixes for the exact errors you hit migrating off deprecated AWS Lambda runtimes, Amazon Linux 2, Python 3.9 and Node native dependencies.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/fix/">\n<link rel="stylesheet" href="/style.css">\n<script defer src="/track.js"></script>\n</head>\n'
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <span>Fixes</span></nav>\n'
        "<h1>AWS migration error fixes</h1>\n"
        "<p>Exact-match causes and verified fixes for the errors developers hit migrating off deprecated AWS runtimes and Amazon Linux 2. "
        'Every fix cites a primary source. Not sure which apply to you? <a href="/scan/">Scan your project free</a> — it runs entirely in your browser.</p>\n'
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
    """M5: a deterministic deadline badge per deprecation. Repos embed them and each
    embed is a crawlable backlink to the /migrate deadline page (the embed loop).
    Rebuilt daily by the GRACE cron, so the date/colour stay current."""
    from datetime import date as _date

    today = datetime.now(UTC).date()
    pages = {}
    for dep in deprecations.get("deprecations", []):
        slug = slugify(dep["name"])
        d = str(dep.get("date", ""))
        days = None
        try:
            y, m, dd = (int(x) for x in d.split("-"))
            days = (_date(y, m, dd) - today).days
        except Exception:
            pass
        msg = ("deadline " + d) if (days is None or days >= 0) else ("EOL passed " + d)
        pages["badge/" + slug + ".svg"] = _badge_svg("EOLkits", msg, _badge_color(days))
    return pages


def build_deprecations_rss(deprecations):
    """M3: the Cloud Deprecation Radar as an RSS 2.0 feed (deterministic, from the
    cited YAML). Fixes the live /blog/feed.xml 404 and gives answer-engines and
    feed readers a citable, auto-updating list of every tracked AWS deadline."""
    import html as _h

    # Pin to midnight UTC of the build day so two same-day rebuilds are byte-identical.
    now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    pub = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    ordered = sorted(deprecations.get("deprecations", []), key=lambda d: d.get("date", "9999-99-99"))
    items = []
    for dep in ordered:
        slug = slugify(dep["name"])
        link = f"{SITE_URL}/migrate/{slug}/"
        bc = "; ".join(dep.get("breaking_changes", []))
        desc = (
            f"Deadline {dep.get('date', '')} ({dep.get('severity', 'n/a')}). "
            f"{dep.get('description', '')} Breaking changes: {bc}. "
            f"Source: {dep.get('url', '')}"
        )
        items.append(
            "<item>"
            f"<title>{_h.escape(dep['name'])} — deadline {_h.escape(str(dep.get('date', '')))}</title>"
            f"<link>{_h.escape(link)}</link>"
            f"<guid isPermaLink=\"true\">{_h.escape(link)}</guid>"
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
        "<description>Every tracked AWS deprecation deadline — Lambda runtimes, Amazon Linux 2, IMDSv1 — "
        "with cited breaking changes and migration guides. Deterministic, sourced from primary AWS docs.</description>\n"
        "<language>en-us</language>\n"
        f"<lastBuildDate>{pub}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n</channel></rss>\n"
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
        "vs/index.html": build_vs_index(COMPETITORS),
        "lambda-runtime-deprecation-schedule/index.html": build_lambda_schedule_page(deprecations, build_pricing_view(pricing)),
        "amazon-linux-2-eol-checklist/index.html": build_al2_checklist_page(deprecations, build_pricing_view(pricing)),
        "amazon-linux-2-vs-amazon-linux-2023/index.html": build_al2_vs_al2023_page(deprecations, build_pricing_view(pricing)),
        "deprecations.ics": build_deprecations_ics(deprecations),
    }
    pages["widget.js"] = build_widget_js()

    for c in COMPETITORS:
        pages[f"vs/{slugify(c['name'])}/index.html"] = build_vs_page(c)

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
        with open(full_path, "w") as f:
            f.write(inject_first_touch(path, normalize_project_links(content)))
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
                (
                    line[2:].strip()
                    for line in md_text.splitlines()
                    if line.startswith("# ")
                ),
                f"{name.title()} — EOLkits",
            )
            html_doc = md_to_html(md_text, title, f"/legal/{name}.html")
            output = legal_output / f"{name}.html"
            output.write_text(normalize_project_links(html_doc))
            print(f"Rendered: legal/{name}.html")

    print("=" * 40)
    print("Build complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
