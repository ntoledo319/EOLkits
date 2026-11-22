#!/usr/bin/env python3
"""
EOLkits Static Site Generator
Builds docs/ from templates and rule-pack data.
"""

import json
import os
import re
import sys
from datetime import UTC, date, datetime, timedelta
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
AUDIT_INTEREST_URL = "https://github.com/ntoledo319/EOLkits/issues/new?template=audit-interest.yml"
# The studio's fixed-scope migration page. Each link carries a from= tag that
# names the EOLkits page the visit came from.
STUDIO_MIGRATION_URL = "https://toledotechnologies.com/end-of-life-migration/"
# IndexNow ownership key for notifying participating search engines about changed
# URLs. Stable + committed so the hosted key file at /<key>.txt always matches the
# bounded submission workflow; receipt never implies crawling or indexing.
INDEXNOW_KEY = "0c7a25ebf8815c561ded8ab9a156dfb5"
# GitHub Pages cannot set response headers, and the GRACE static host has
# historically post-processed HTML outside this repository. Keep a restrictive
# document policy in every generated page so an unreviewed cross-origin script
# cannot execute or transmit page/query data even if a host injects a tag.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "base-uri 'none'; "
    "object-src 'none'; "
    "frame-src 'none'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self' https://eolkits.com; "
    "form-action 'self'"
)

# BUILD_DATE is the stable default publication date for the existing generated
# corpus. Record only materially changed pages here so a release does not falsely
# rewrite every sitemap lastmod (or every article's first-publication date).
PAGE_LASTMOD_OVERRIDES = {
    "legal/dpa.html": "2026-09-04",
}


def _interpolate_api(html):
    """Render a commerce-page template string.

    These page builders write ``{API_URL}`` for the API origin and double their
    in-script JS object braces (``{{`` / ``}}``). The page is NOT an f-string and
    its CSS uses single braces, so a plain ``.format()`` would crash on the CSS.
    We interpolate explicitly: substitute the API and canonical site origins,
    then collapse the doubled JS braces back to singles, leaving single-brace
    CSS untouched. The result has zero commerce placeholders or doubled braces
    left — which the CI gate and deploy gate both enforce.
    """
    return (
        html.replace("{API_URL}", API_URL)
        .replace("{SITE_URL}", SITE_URL)
        .replace("{AUDIT_INTEREST_URL}", AUDIT_INTEREST_URL)
        .replace("{{", "{")
        .replace("}}", "}")
    )


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
    """Emit a deterministic 1200x630 social card with stdlib-only PNG encoding.

    Renders dark #0b0e14 background, #ff5c2a top accent bar, framed #161c28 card,
    and crisp block-pixel '> EOLKITS' emblem so every page's og:image unfurls
    as an intentional developer card while remaining byte-deterministic.
    """
    import struct
    import zlib

    width, height = 1200, 630
    bg = b"\x0b\x0e\x14"
    card = b"\x16\x1c\x28"
    border = b"\x22\x2a\x38"
    accent = b"\xff\x5c\x2a"
    ink = b"\xe6\xe8\xeb"
    muted = b"\x8b\x93\xa3"

    glyphs = {
        ">": ["11000", "01100", "00110", "00011", "00110", "01100", "11000"],
        " ": ["000", "000", "000", "000", "000", "000", "000"],
        "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
        "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
        "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
        "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
        "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
        "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    }
    scale = 12
    x0, y0 = 120, 210
    text = "> EOLKITS"
    bitmap_cols = []
    for idx, ch in enumerate(text):
        pat = glyphs[ch]
        color = accent if ch == ">" else ink
        for col in range(len(pat[0])):
            bitmap_cols.append(([pat[r][col] == "1" for r in range(7)], color))
        if idx + 1 < len(text):
            bitmap_cols.append(([False] * 7, ink))

    def _chunk(tag, data):
        body = tag + data
        return (
            struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    rows = []
    for y in range(height):
        if y < 14:
            rows.append(b"\x00" + accent * width)
            continue
        if y < 72 or y >= height - 72:
            rows.append(b"\x00" + bg * width)
            continue
        if y in (72, 73, height - 73, height - 74):
            rows.append(b"\x00" + bg * 72 + border * (width - 144) + bg * 72)
            continue
        row = bytearray(b"\x00" + bg * 72 + border * 2 + card * (width - 148) + border * 2 + bg * 72)
        if y0 <= y < y0 + 7 * scale:
            gr = (y - y0) // scale
            cx = x0
            for col_bits, col_rgb in bitmap_cols:
                if col_bits[gr]:
                    start = 1 + cx * 3
                    row[start : start + scale * 3] = col_rgb * scale
                cx += scale
        elif 340 <= y < 350:
            start = 1 + 120 * 3
            row[start : start + 260 * 3] = accent * 260
        elif 384 <= y < 396:
            start = 1 + 120 * 3
            row[start : start + 640 * 3] = muted * 640
        elif 416 <= y < 428:
            start = 1 + 120 * 3
            row[start : start + 500 * 3] = muted * 500
        rows.append(bytes(row))

    raw = b"".join(rows)
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
    """Build the audit & offline toolkit commercial hub page."""
    pricing_view = build_pricing_view(pricing)
    tk = pricing_view["toolkit"]
    html = (
        """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AWS deprecation evidence report &amp; offline toolkit | EOLkits</title>
<meta name="description" content="Choose between the $79 air-gapped Offline Migration &amp; Audit Toolkit (instant download, zero source upload) or the $299 hosted static repository evidence report.">
<link rel="canonical" href="{SITE_URL}/audit/">
<link rel="stylesheet" href="/style.css">
<meta property="og:type" content="website">
<meta property="og:title" content="AWS deprecation evidence report &amp; offline toolkit | EOLkits">
<meta property="og:description" content="Reviewable file/line AWS migration evidence — run locally with the $79 Offline Toolkit or request a $299 hosted repository PDF.">
<meta property="og:url" content="{SITE_URL}/audit/">
<script defer src="/track.js"></script>
"""
        + _og_image_meta()
        + """<style>
.audit-wrap{max-width:960px;margin:0 auto;padding:2rem 1.5rem 4rem}
.cta{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;padding:.75rem 1.25rem;border-radius:8px;font-weight:600}
.cta:hover{background:var(--accent-dim);color:#fff}
.cta.secondary{background:var(--bg-card);color:var(--ink);border:1px solid var(--border)}
.cta.secondary:hover{border-color:var(--accent);color:var(--ink)}
.callout{background:var(--bg-card);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:10px;padding:1.25rem;margin:1.5rem 0}
.pricing{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin:1.5rem 0}
.price{font-size:2.1rem;font-weight:800;color:var(--ink)}
.tiers{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.25rem;margin:1rem 0}
.tier{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:1.35rem;text-align:left}
.tier.featured{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.valuebox{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1.25rem;margin:1.5rem 0}
.refund-box{background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.4);border-radius:10px;padding:1.35rem;margin:1.5rem 0}
.refund-box h3{margin-top:0;color:#4ade80}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem;margin:1.5rem 0}
.cell{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1rem;font-size:.92rem}
.cell h4{margin:.2rem 0 .4rem;color:var(--ink)}
.logos{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}
.logos span{border:1px solid var(--border);border-radius:999px;padding:.3rem .8rem;font-size:.85rem;color:var(--ink-muted);background:var(--bg-card)}
.reassure{color:var(--ink-muted);font-size:.9rem;margin:.5rem 0}
button{background:var(--accent);color:white;border:none;padding:0.75rem 1.5rem;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer}
button:hover{background:var(--accent-dim)}
form#auditForm{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1.5rem;margin:1rem 0}
form#auditForm input{box-sizing:border-box;max-width:100%;width:100%;padding:.65rem;background:var(--bg);color:var(--ink);border:1px solid var(--border);border-radius:6px}
.assurances{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1rem 1.25rem;margin:1rem 0}
.assurances ul{margin:.5rem 0 0;padding-left:1.2rem}
.assurances a,.callout a,.pricing a{color:var(--accent);text-decoration:underline}
.pricing a.cta,.callout a.cta{color:#fff;text-decoration:none}
.callout a.cta.secondary,.pricing a.cta.secondary{color:var(--ink)}
</style>
</head>
<body>
<header class="nav">
  <div class="container nav-inner">
    <a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>
    <nav>
      <a href="/migrate/">Deadlines</a>
      <a href="/scan/">Free scan</a>
      <a href="/toolkit/">Toolkit ($79)</a>
      <a href="/audit/">Audit</a>
      <a href="/about/">About</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>
<main class="audit-wrap">
<h1>Turn a repository into reviewable AWS migration evidence</h1>
<p class="lede">Pick the delivery model your security team approves: download the <strong>$79 air-gapped Offline Migration &amp; Audit Toolkit</strong> to scan and codemod locally with zero source upload, or use the <strong>$299 hosted repository evidence report</strong> for one uploaded ZIP or supported source file. Both produce static source evidence—not a live AWS account inventory.</p>

<div class="callout">
  <strong>Start with a local check.</strong> &nbsp;<a class="cta secondary" href="/scan/">▶ Run the free scan</a> &nbsp;<a class="cta" href=\""""
        + tk["payment_link"]
        + """\">Buy $79 Offline Toolkit (Instant Download) →</a><br>
  Check representative files in your browser first. Paid options add archive-wide scanning of supported text files, exact line evidence, a severity-and-reach-ranked remediation order, and an evidence fingerprint. Self-serve Stripe checkouts are for <strong>US buyers only</strong>.
</div>

<h2>Two ways to get CAB-ready migration evidence</h2>
<div class="pricing">
  <div class="tiers">
    <div class="tier featured">
      <strong>Offline Migration &amp; Audit Toolkit (Instant Download)</strong>
      <div class="price">$79</div>
      <p>Zero source upload · unlimited internal repositories · instant ZIP link by email.</p>
      <ul>
        <li>Stdlib-only Python 3.10+ scanner emitting local HTML/PDF-printable report, Jira CSV, and SHA-256 <code>attestation.json</code></li>
        <li>AST codemods for Python 3.12/3.13 removed stdlib modules, <code>aws-sdk</code> v2 → v3 mapper, and AL2023 cutover linter</li>
        <li>AL2023 native Lambda layer Dockerfiles (<code>x86_64</code> &amp; <code>arm64</code>) + Terraform/SAM canary rollback templates</li>
      </ul>
      <p><a class="cta" href=\""""
        + tk["payment_link"]
        + """\">Buy Offline Toolkit — $79</a> &nbsp;<a class="cta secondary" href="/toolkit/">Full specs</a></p>
      <p class="reassure"><a href="/toolkit/sample/">Inspect the synthetic air-gapped HTML report →</a> · US buyers only · 30-day full refund policy.</p>
    </div>
    <div class="tier">
      <strong>Hosted Repository Evidence Report (One Repository)</strong>
      <div class="price">$299</div>
      <p>ZIP archive or one supported source file · one fixed price · server-rendered 4+ page PDF.</p>
      <ul>
        <li>Exact <strong>file:line evidence</strong> and observed match counts—no invented resource counts</li>
        <li>A <strong>roll-forward order</strong> based on finding severity and observed reach</li>
        <li>Configured rule or package reference per finding + input SHA-256 verifiable at <code>/verify/</code></li>
      </ul>
      <p><a class="cta secondary" href="/audit/sample/">▶ Inspect the fictional sample</a> &nbsp;<a href="/audit/sample/eolkits-sample-report.pdf">Sample PDF →</a></p>
      <p class="reassure">A target date may be included as planning context. It never changes the price or scan results. US buyers only.</p>
    </div>
  </div>
</div>

<h2>Hosted $299 report upload &amp; readiness gate</h2>
<div class="assurances">
  <strong>Before you upload for the $299 hosted PDF:</strong>
  <ul>
    <li>No AWS credentials or AWS account access are requested.</li>
    <li>Source uploads for delivered reports are deleted immediately upon delivery; unchecked uploads expire within 24 hours; checkout-bound uploads expire within 48 hours and generated reports within 30 days.</li>
    <li>Cannot upload proprietary source code? <a href="/toolkit/">Use the $79 Offline Migration &amp; Audit Toolkit instead</a> so code stays on your workstation or CI runner.</li>
    <li><a href="/audit/sample/">Inspect the fictional input, engine-generated PDF, and hash manifest</a> before deciding.</li>
  </ul>
</div>

<div id="auditGate" class="callout"><strong>Checkout status:</strong> The upload form appears here only when the live API confirms checkout is open on report engine 2.0. The form needs JavaScript.</div>
<div id="auditInterest" class="callout">
  <strong>Rather not do this upgrade yourself?</strong>
  The studio that builds EOLkits takes the
  whole migration as a fixed-scope project: runtime, dependencies, tests, a staged
  deploy and a rollback plan. Scoped in writing. From US$7,500.
  <p><a class="cta" href="https://toledotechnologies.com/end-of-life-migration/?from=eolkits-audit">Describe the upgrade &rarr;</a></p>
  <p>For immediate self-serve delivery with zero code upload, grab the <a href="/toolkit/">$79 Offline Migration &amp; Audit Toolkit</a> above.</p>
  <p class="reassure">If checkout is not open when you visit and this exact one-repository
  report would be worth $299 to you,
  <a href="{AUDIT_INTEREST_URL}" target="_blank" rel="noopener">record qualified public interest on GitHub</a>.
  It is not an order, reservation, waitlist, or promise of a reply. GitHub publishes your username and submission. Do not include
  repository names, filenames, code, secrets, security details, company information, or personal data.</p>
</div>
<form id="auditForm" hidden>
  <h3>Start Hosted $299 Audit (US buyers only)</h3>
  <p><input type="email" id="auditEmail" name="email" placeholder="your@email.com" required></p>
  <p><input type="date" id="auditDeadline" name="deadline" aria-label="Deadline date"></p>
  <p><input type="file" id="auditFile" name="file" required accept=".zip,.yaml,.yml,.json,.tf,.tfvars,.js,.ts,.tsx,.py,.toml,.lock,.sh,.txt"></p>
  <p class="reassure">Upload limits: 10 MiB input; ZIPs may contain at most 2,000 entries and 25 MiB expanded text. Analysis is also bounded to 500,000 decoded lines, 100,000 mapping records per file, 10,000 Lambda resources per file, 10,000 retained evidence records, and 1 MiB per dependency manifest. Binary archive members are skipped; standalone binary inputs and archives with no supported text are rejected. Encrypted, ambiguous-path, path-traversing, over-complex, and suspiciously compressed archives are rejected before checkout. Do not upload secrets or unrelated personal data.</p>
  <button id="auditSubmit" type="submit">Upload and Proceed to Checkout</button>
  <p class="reassure">By continuing, you confirm you are a US buyer, authorize this upload to be scanned, and agree to the <a href="/legal/terms.html">Terms</a> and <a href="/legal/privacy.html">Privacy Policy</a>. Stripe Checkout shows the final $299 price before payment.</p>
  <p id="auditStatus" style="color:var(--ink-muted);font-size:.875rem"></p>
</form>

<div class="valuebox">
  <strong>What both paid options buy:</strong> a reviewable change-approval artifact your team can verify against repository files and primary-source AWS/Python/Node references. No speculative downtime-dollar estimate is included.
</div>

<div class="refund-box">
  <h3>30-day full refund policy</h3>
  <p><strong>Request a full refund within 30 days on either paid product.</strong> Email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> from the purchase address with your Stripe receipt; no explanation is required.</p>
  <p>If automated Audit v2 fulfillment permanently fails after retries, the system queues a full refund and surfaces any unconfirmed refund for operator review.</p>
</div>

<h2>How findings are verified</h2>
<div class="grid">
  <div class="cell"><h4>Evidence, not estimates</h4>Each match includes the observed file, line, and matched snippet.</div>
  <div class="cell"><h4>Checkable references</h4>Each finding links its configured rule or package reference; conservative dependency floors still require release and target verification.</div>
  <div class="cell"><h4>Repeatable hashes</h4>Both the $79 local CLI and $299 hosted PDF emit deterministic SHA-256 input and evidence hashes.</div>
  <div class="cell"><h4>Bounded scope</h4>Neither product queries live AWS credentials on its own or claims an unbounded cloud inventory.</div>
</div>

<div class="logos">
  <span>AWS Lambda</span><span>Amazon Linux 2023</span><span>CloudFormation / SAM</span><span>CDK</span><span>Terraform</span><span>Serverless</span><span>Python 3.12 / 3.13</span><span>Node.js 24</span><span>.NET 10</span>
</div>

<h2>How the hosted $299 report works</h2>
<ol>
  <li>Upload a repository ZIP or a supported SAM / CDK / Terraform / Serverless / cloud-init source file (10 MiB compressed maximum)</li>
  <li>We inspect supported text files in memory without extracting the archive onto the host filesystem</li>
  <li>Receive the generated PDF by email after automated processing; delays and retries are possible</li>
  <li>Verify the evidence metadata at <code>/verify/</code> during its 30-day retention window</li>
</ol>

<p class="reassure">Stripe checkout (US buyers only) · automated delivery with durable retries · 30-day full refund policy</p>

<script>
const API = '{API_URL}';
const qp = new URLSearchParams(location.search);
function attributionToken(value) {{
  value = String(value || '').toLowerCase();
  return /^[a-z0-9._-]{{1,64}}$/.test(value) ? value : '';
}}
function attribution() {{
  return {{
    source: attributionToken(qp.get('source')) || 'audit_page',
    utm_source: attributionToken(qp.get('utm_source')),
    utm_medium: attributionToken(qp.get('utm_medium')),
    utm_campaign: attributionToken(qp.get('utm_campaign')),
    kit: attributionToken(qp.get('kit'))
  }};
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
const auditInterest = document.getElementById('auditInterest');
if (qp.get('deadline') && deadlineInput) deadlineInput.value = qp.get('deadline');
if (qp.get('cancelled')) auditStatus.textContent = 'Checkout cancelled — finish whenever you are ready.';
auditGate.textContent = 'Checking checkout status…';
function auditGateUnconfirmed() {{
  auditGate.textContent = 'Checkout status could not be confirmed just now. ';
  const retry = document.createElement('a');
  retry.href = location.href.split('#')[0];
  retry.textContent = 'Reload this page';
  auditGate.append(retry, ' to try again.');
}}
fetch(API + '/api/capabilities', {{ cache: 'no-store', credentials: 'omit' }}).then(r => r.ok ? r.json() : Promise.reject()).then(c => {{
  const a = c && c.audit;
  if (a && a.checkout_enabled === true && String(a.report_version) === '2.0') {{
    auditForm.hidden = false;
    auditGate.hidden = true;
    auditInterest.hidden = true;
  }} else if (a && a.checkout_enabled === false) {{
    auditGate.textContent = 'Audit checkout is paused right now — the $79 Offline Toolkit above remains open for instant download.';
  }} else {{
    auditGateUnconfirmed();
  }}
}}).catch(auditGateUnconfirmed);
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
    if (typeof window.eolkitsTrack === 'function') {{
      window.eolkitsTrack('checkout_click', {{ sku: 'audit', deadline: deadline }});
    }}
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
<details><summary>Which option should I pick: $0 CLI, $79 Offline Toolkit, or $299 Hosted PDF?</summary><p>Use the free MIT CLIs to inspect single runtimes by hand. Pick the $79 Offline Toolkit when InfoSec forbids uploading source code or when you want unified cross-stack HTML/PDF + Jira CSV reports, Python 3.12/3.13 &amp; AWS SDK v3 codemods, AL2023 Dockerfiles, and canary rollback IaC across unlimited company repos. Pick the $299 Hosted PDF when you want a zero-install server-rendered PDF + <code>/verify/</code> hash for one uploaded repository.</p></details>
<details><summary>Is my code safe?</summary><p>With the $79 Offline Toolkit and free browser scanner, source code never leaves your machine. For the $299 hosted report, uploads travel over TLS, are used only for report generation, and are deleted immediately after delivery (unchecked uploads expire within 24 hours; checkout-bound uploads expire within 48 hours; generated reports expire within 30 days).</p></details>
<details><summary>How are findings verified?</summary><p>Check the exact file/line evidence and the configured rule or package reference for each finding. Dependency floors are conservative triage baselines, not proof of target compatibility. Reports carry an input hash and deterministic evidence fingerprint; they do not claim to be cryptographically signed PDFs.</p></details>
<details><summary>How does delivery work?</summary><p>The $79 Offline Toolkit emails an unlisted HTTPS ZIP download link after Stripe confirms payment. The $299 hosted PDF runs through automated background processing with durable retries.</p></details>
<details><summary>What if I need a refund?</summary><p>Email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> within 30 days from your purchase email with your Stripe receipt for a full refund. No explanation is required.</p></details>
</div>
</main>

<footer class="footer">
  <div class="container">
    <div class="muted small">Toledo Technologies LLC · 2389 Main St. STE 100, Glastonbury, CT 06033, United States · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> · Self-serve Stripe checkouts: US buyers only.</div>
    <div class="muted small"><a href="/">Home</a> · <a href="/toolkit/">Offline Toolkit ($79)</a> · <a href="/scan/">Free scan</a> · <a href="/audit/sample/">Sample report</a> · <a href="/about/">About</a> · <a href="/changelog/">Changelog</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/terms.html#refunds">Refund policy</a> · <a href="/legal/privacy.html">Privacy</a></div>
  </div>
</footer>
</body>
</html>"""
    )
    return _interpolate_api(html)


def build_audit_sample_page(pricing):
    """Landing page for the engine-generated fictional PDF and hash manifest."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sample audit report — EOLkits</title>
<meta name="description" content="Illustrative EOLkits evidence report format: exact file/line matches, observed reach, remediation order, limitations, and configured references.">
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:820px;margin:0 auto;padding:2rem;line-height:1.6;color:#111827}
.brand{color:#2563eb;font-weight:600}
.banner{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:.75rem 1rem;margin:1rem 0;font-size:.9rem}
.download{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:1rem;margin:1rem 0}
.meta{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin:1rem 0;font-size:.9rem}
.cta{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:.7rem 1.2rem;border-radius:6px;font-weight:600;margin:1rem 0}
code{background:#f3f4f6;padding:.1rem .3rem;border-radius:4px}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;color:#6b7280;font-size:.875rem}
</style>
</head>
<body>
<a href="/audit/" class="brand">← Back to Audit</a>
<div class="banner"><strong>ILLUSTRATIVE SAMPLE.</strong> This fictional repository shows the v2 report format. It is not a customer report or evidence of a live AWS account scan.</div>
<div class="download"><strong>Inspect the actual engine output.</strong><br><a class="cta" href="/audit/sample/eolkits-sample-report.pdf">Download the sample PDF</a><br><a href="/audit/sample/fictional-repository.zip">Fictional input ZIP</a> · <a href="/audit/sample/eolkits-sample-report.json">SHA-256 and evidence manifest</a></div>
<h1>AWS deprecation evidence report</h1>
<div class="meta">
  <div><strong>Uploaded artifact:</strong> <code>fictional-repository.zip</code></div>
  <div><strong>Format:</strong> 4-page engine-generated PDF</div>
  <div><strong>Observed scope:</strong> 4 supported text files; 1 unsupported README skipped</div>
  <div><strong>Hashes:</strong> the downloadable manifest records the complete input SHA-256, PDF SHA-256, and evidence fingerprint.</div>
  <div><strong>Findings:</strong> 4 distinct risk types · 5 file/line evidence records</div>
</div>

<div class="banner"><strong>Scope limitation:</strong> static uploaded-source scan only. No AWS account was queried; resource inventory and runtime behavior are not inferred.</div>

<h2>What is inside the PDF</h2>
<ul>
  <li>Engine-ranked findings with exact observed file/line evidence</li>
  <li>Observed reach, remediation notes, and a configured reference per finding</li>
  <li>Explicit scan scope, skipped-file count, limitations, and roll-forward order</li>
  <li>The same input hash and evidence fingerprint recorded in the manifest above</li>
</ul>

<h2>What the report does not claim</h2>
<p>It does not estimate downtime dollars, count deployed instances/functions, inspect omitted files, or certify that a match is reachable at runtime. Those facts require environment-specific validation.</p>

<a class="cta" href="/audit/?source=audit_sample&amp;utm_source=audit_sample&amp;utm_medium=proof">Review the fixed $299 scope and availability →</a>
<p><a href="/scan/">Or run the free scan first →</a></p>

<footer>
  <p>Production reports include exact observed evidence, configured rule or package references, input SHA-256, and a deterministic evidence fingerprint. The PDF itself is not digitally signed.</p>
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
            if "lambda" in (
                str(entry.get("service") or "") + " " + " ".join(entry.get("tags") or [])
            ).lower() and not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}", str(entry.get("deprecation_date") or "")
            ):
                raise ValueError(
                    f"rules/public/deprecations.yml: deprecations[{index}] needs a Lambda deprecation_date"
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
    """Extract canonical Toolkit and Audit price/link facts for public pages."""
    skus = full_pricing.get("skus", full_pricing)

    toolkit = skus.get("toolkit", {})
    toolkit_price = toolkit.get("price_usd", 79)
    toolkit_plink = toolkit.get("payment_link", "https://buy.stripe.com/9B66oH5s2cFy2l51oE87K0C")

    audit = skus.get("audit", {})
    audit_tiers = {t.get("name"): t for t in audit.get("tiers", [])}
    standard = audit_tiers.get("standard", {})
    audit_base = standard.get("price_usd", 299)

    return {
        "toolkit": {
            "price": toolkit_price,
            "link": "/toolkit/",
            "payment_link": toolkit_plink,
        },
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
            studio_block=studio_block("eolkits-migrate"),
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
        deprecations=rows,
        site_url=SITE_URL,
        now=now_iso,
        studio_block=studio_block("eolkits-migrate"),
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
        dep["slug"] = deprecation_slug(dep)

    return template.render(
        deprecations=deprecations.get("deprecations", []),
        fixes=[f["slug"] for f in load_fixes()],
        lastmod=lambda path: PAGE_LASTMOD_OVERRIDES.get(path, _build_date()),
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
            f"to find deprecated runtimes and incompatible dependencies locally. File names and contents are not uploaded; bounded aggregate file and finding counts may be sent."
        )

    lines += [
        "",
        "## Pricing (US buyers only for self-serve paid Stripe checkouts)",
        "",
        "- Free CLI: MIT-licensed kits (al2023-gate, python-pivot, lambda-lifeline). "
        "git clone https://github.com/ntoledo319/EOLkits",
        f"- [Offline Migration & Audit Toolkit]({SITE_URL}/toolkit/): "
        f"${pricing_view['toolkit']['price']} — instant ZIP download (zero source upload) "
        f"with air-gapped Python 3.10+ scanner (HTML/PDF-printable report + Jira CSV + "
        f"SHA-256 attestation), Python 3.12/3.13 & AWS SDK v3 codemods, AL2023 native "
        f"Lambda layer Dockerfiles, canary rollback IaC, and CAB sign-off templates.",
        f"- [Audit PDF]({SITE_URL}/audit/): ${pricing_view['audit_pdf']['base']} "
        f"— one repository ZIP or supported source file; exact file/line evidence, "
        f"remediation order, configured references, and a deterministic evidence fingerprint.",
        "- No subscription, AWS-account inventory, or automated pull-request product is for sale.",
        "",
        "## Company & Trust",
        "",
        f"- [About EOLkits]({SITE_URL}/about/): Toledo Technologies LLC, Glastonbury, CT.",
        f"- [Changelog]({SITE_URL}/changelog/): rule-pack and schedule updates.",
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
    tk = pricing_view.get("toolkit", {}) if isinstance(pricing_view, dict) else {}
    tk_price = tk.get("price", 79) if isinstance(tk, dict) else 79
    tk_plink = (
        tk.get("payment_link", "https://buy.stripe.com/9B66oH5s2cFy2l51oE87K0C")
        if isinstance(tk, dict)
        else "https://buy.stripe.com/9B66oH5s2cFy2l51oE87K0C"
    )
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
        deprecated = _h.escape(str(d.get("deprecation_date") or "—"))
        create = _h.escape(str(d.get("date") or "—"))
        update = _h.escape(str(d.get("block_update_date") or "—"))
        sev = _h.escape(str(d.get("severity", "")))
        tags = " ".join(d.get("tags", [])).lower()
        if "python" in tags:
            target = "python3.12"
        elif "nodejs" in tags:
            target = "nodejs24.x"
        elif "dotnet" in tags:
            target = "dotnet10"
        elif "provided.al2" in rt.lower():
            target = "provided.al2023"
        else:
            target = "—"
        src = _h.escape(str(d.get("url", "")))
        rows += (
            '<tr><td><a href="/migrate/' + slug + '/"><code>' + rt + "</code></a></td>"
            "<td>" + deprecated + "</td><td>" + create + "</td><td>" + update + "</td>"
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
                    "text": "Run the free scanner at eolkits.com/scan over your SAM/CDK/Terraform/Serverless config; file names and contents are not uploaded, while bounded aggregate file and finding counts may be sent. Or run: aws lambda list-functions --query 'Functions[].Runtime'.",
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
        '<meta name="description" content="Tracked AWS Lambda runtime deprecation dates for python3.8-3.11 and nodejs16/18/20/22, including published create/update block dates, EOLkits bounded targets, and AWS source links.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/lambda-runtime-deprecation-schedule/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
        "<style>.sched{width:100%;border-collapse:collapse;margin:1.25rem 0;font-size:.92rem}"
        ".sched th,.sched td{border:1px solid var(--border);padding:.55rem .65rem;text-align:left}"
        ".sched th{background:var(--bg-card);color:var(--ink-muted)}.sched .sev{font-weight:700}"
        ".sev-critical{color:#ff6b6b}.sev-high{color:var(--accent)}.sev-medium{color:#eab308}"
        ".audit-card{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1.1rem 1.35rem;margin:1.5rem 0}"
        ".audit-card h2{margin:.1rem 0 .35rem}.audit-card .cta{margin:.5rem .5rem .5rem 0}"
        ".cta{display:inline-block;margin:1rem 0;padding:.7rem 1.2rem;background:var(--accent);color:#fff;text-decoration:none;border-radius:8px;font-weight:600}"
        ".cta.sec{background:var(--bg);border:1px solid var(--border);color:var(--ink)}</style>\n"
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/migrate/">Deadlines</a> / <span>Lambda runtime schedule</span></nav>\n'
        "<h1>AWS Lambda runtime deprecation schedule (2026–2027)</h1>\n"
        "<p>For the runtimes EOLkits tracks: when patches stop, when AWS says it will block <strong>creating</strong> new functions, when it will block <strong>updating</strong> existing ones, and the target currently supported by these bounded tools. Each row links the AWS source; future dates can change.</p>\n"
        '<p><a class="cta" href="/scan/">Scan your stack free — find your deprecated runtimes →</a> <a class="cta sec" href="/toolkit/">Offline Toolkit ($'
        + str(tk_price)
        + ", no code upload) →</a></p>\n"
        '<p>Prefer a 10-second check? Paste your config into the <a href="/eol-checker/">free AWS EOL checker</a>. Pasted input is not uploaded; bounded first-party usage events may be sent.</p>\n'
        '<table class="sched"><thead><tr><th>Runtime</th><th>Deprecation</th><th>Blocks create</th><th>Blocks update</th><th>Severity</th><th>EOLkits target</th><th>Source</th></tr></thead><tbody>\n'
        + rows
        + "\n</tbody></table>\n"
        '<p class="muted">Functions keep running after deprecation, but become unpatched and — after the block-update date — unmodifiable. Dates reflect the AWS-published schedule and can shift; the linked AWS page is authoritative.</p>\n'
        '<div class="audit-card"><h2>Need archive-wide source evidence?</h2>'
        "<p>Cannot upload company source code? The $"
        + str(tk_price)
        + " Offline Migration &amp; Audit Toolkit downloads instantly via Stripe and runs 100% locally (HTML/PDF-printable report, Jira CSV, SHA-256 attestation, Python/Node codemods, AL2023 Dockerfiles, and canary rollback IaC). Or use the fixed $"
        + str(audit_base)
        + " report to scan one uploaded archive without AWS credentials and return observed file/line evidence, configured references, scope limits, and a remediation order. Self-serve paid checkouts: US buyers only.</p>"
        '<p><a class="cta" href="'
        + tk_plink
        + '">Buy $'
        + str(tk_price)
        + ' Offline Toolkit (Instant Download) →</a> <a class="cta sec" href="/audit/?source=lambda_schedule&amp;utm_source=organic&amp;utm_medium=schedule&amp;utm_campaign=repo_audit">Inspect the sample and report availability →</a></p>'
        '<p class="muted">Schedule source: <a href="https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html" target="_blank" rel="noopener nofollow">AWS Lambda runtimes</a>. Future dates can change.</p></div>\n'
        "<h2>Fixing the upgrade</h2>\n"
        '<p>The upgrade can surface specific errors — removed stdlib modules, the unbundled AWS SDK v2 on Node 18+, native-wheel/ABI breaks. See <a href="/fix/">common migration error fixes</a>, grab the <a href="/toolkit/">$'
        + str(tk_price)
        + ' Offline Toolkit</a>, or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ", 30-day refund policy)</a> for exact file/line matches, configured references, and a remediation order.</p>\n"
        '<p><a href="/migrate/">See all tracked AWS deadlines →</a></p>\n'
        "</body>\n</html>\n"
    )


def build_eol_checker_page(deprecations, pricing_view):
    """Free interactive tool: paste your runtimes / IaC (or click chips) and instantly see
    which are past AWS end-of-life and when AWS blocks them. Input processing is entirely
    client-side; bounded first-party usage events may be sent. The dataset is baked from the cited deprecations.yml, so the built
    HTML is static & deterministic (the day-countdown is computed in the browser). A linkable,
    shareable top-of-funnel asset that routes to the free /scan and the paid /audit."""
    ap = pricing_view.get("audit_pdf", {}) if isinstance(pricing_view, dict) else {}
    audit_base = ap.get("base", 299) if isinstance(ap, dict) else 299
    tk = pricing_view.get("toolkit", {}) if isinstance(pricing_view, dict) else {}
    tk_price = tk.get("price", 79) if isinstance(tk, dict) else 79

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
        elif "dotnet" in tags:
            rid = _runtime_id_from_name(name) or "dotnet8"
            matches = [rid.lower(), "net8.0", ".net 8"]
            target, kind = "dotnet10", "runtime"
        elif "provided.al2" in name.lower():
            rid = "provided.al2"
            matches = ["provided.al2"]
            target, kind = "provided.al2023", "runtime"
        elif "al2" in tags or "amazon linux 2" in name.lower():
            rid = "Amazon Linux 2"
            matches = ["amazonlinux2", "amazon-linux-2", "amazon linux 2", "al2", "amazonlinux:2"]
            target, kind = "Amazon Linux 2023", "os"
        else:
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
        '    \'<a class="cta" href="/toolkit/">Get $'
        + str(tk_price)
        + ' Offline Toolkit (no upload) &rarr;</a> <a class="cta sec" href="/scan/">Run full free scan &rarr;</a> or <a href="/audit/">check $'
        + str(audit_base)
        + " hosted report</a> (US buyers only).</div>';\n"
        "  out.innerHTML=html;\n"
        "}\n"
        "function trackChecker(){try{if(window.umami&&typeof window.umami.track==='function')window.umami.track('scan');if(typeof window.eolkitsTrack==='function')window.eolkitsTrack('scan_completed',{sku:'toolkit',meta:{finding_count:Object.keys(picked).length,file_count:1}});}catch(e){}}\n"
        "function check(){\n"
        "  var t=(document.getElementById('inp').value||'').toLowerCase();\n"
        "  RT.forEach(function(r){if(r.matches.some(function(m){return t.indexOf(m)>=0;}))picked[r.id]=1;});\n"
        "  render();trackChecker();\n"
        "}\n"
        "function toggle(id){if(picked[id])delete picked[id];else picked[id]=1;render();trackChecker();var el=document.querySelector('[data-id=\"'+id+'\"]');if(el)el.classList.toggle('on');}\n"
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
        '<meta name="description" content="Free, instant check: paste AWS Lambda runtimes or IaC and see tracked deprecation milestones. Pasted input is not uploaded; bounded first-party usage events may be sent.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/eol-checker/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        '<script type="application/ld+json">' + json.dumps(faq) + "</script>\n"
        "<style>#chips{display:flex;flex-wrap:wrap;gap:.45rem;margin:.75rem 0}"
        ".chip{border:1px solid var(--border);background:var(--bg-card);color:var(--ink);border-radius:999px;padding:.35rem .75rem;font-size:.85rem;cursor:pointer;font-family:inherit}"
        ".chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}"
        "#inp{width:100%;min-height:110px;font-family:ui-monospace,Menlo,monospace;font-size:.85rem;padding:.65rem;background:var(--bg-card);color:var(--ink);border:1px solid var(--border);border-radius:8px}"
        ".res{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem}"
        ".res th,.res td{border:1px solid var(--border);padding:.55rem .65rem;text-align:left;vertical-align:top}"
        ".res th{background:var(--bg-card);color:var(--ink-muted)}.res tr.crit td{background:rgba(255,59,59,0.10)}.res tr.high td{background:rgba(255,92,42,0.10)}.res tr.med td{background:rgba(234,179,8,0.10)}"
        ".cta{display:inline-block;margin:.3rem .3rem .3rem 0;padding:.7rem 1.2rem;background:var(--accent);color:#fff;text-decoration:none;border-radius:8px;font-weight:600}"
        ".cta.sec{background:var(--bg);border:1px solid var(--border);color:var(--ink)}"
        ".ctaway{margin:1rem 0;padding:1rem;background:var(--bg-card);border:1px solid var(--border);border-radius:10px}"
        "#go{padding:.65rem 1.2rem;background:var(--accent);color:#fff;border:0;border-radius:8px;font-weight:600;cursor:pointer;font-family:inherit}</style>\n"
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <a href="/migrate/">Deadlines</a> / <span>EOL checker</span></nav>\n'
        "<h1>Is your AWS runtime past end-of-life?</h1>\n"
        '<p>Paste your SAM / CloudFormation / Terraform / Serverless config (or a list of runtimes), or click the runtimes you use. This checks them against EOLkits\' cited snapshot of the <a href="/lambda-runtime-deprecation-schedule/">AWS runtime deprecation schedule</a> and shows the tracked create/update block dates. <strong>Pasted input stays in your browser; bounded first-party usage events may be sent.</strong></p>\n'
        '<div id="chips"></div>\n'
        '<textarea id="inp" placeholder="Paste template.yaml / serverless.yml / *.tf here — e.g. Runtime: nodejs20.x, python3.10, dotnet8, FROM amazonlinux:2 ..."></textarea>\n'
        '<p><button id="go">Check my runtimes</button></p>\n'
        '<div id="results"></div>\n'
        '<p class="muted">Dates come from the AWS Lambda runtime deprecation table and can shift; the per-runtime <a href="/migrate/">migration guides</a> link the AWS source. AWS documents phased create/update restrictions; verify the current runtime status before planning.</p>\n'
        "<h2>Once you know what's exposed</h2>\n"
        '<p>Each deprecated runtime fails in specific ways — removed stdlib modules, the unbundled AWS SDK v2 on Node 18+, native-wheel/ABI breaks, Amazon Linux 2 &rarr; 2023 package renames. See the <a href="/fix/">common error fixes</a>, run the <a href="/scan/">free scanner</a>, grab the <a href="/toolkit/">$'
        + str(tk_price)
        + ' Offline Toolkit</a>, or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ", 30-day refund policy)</a> for exact matches and a remediation order.</p>\n"
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
        '<p>The free <a href="/scan/">scanner</a> and the MIT <code>al2023-gate</code> CLI detect and patch configured source patterns. Need an air-gapped CAB artifact? Download the <a href="/toolkit/">$79 Offline Migration &amp; Audit Toolkit</a> or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ', 30-day refund policy)</a> for exact observed file/line matches and a remediation order. See the full <a href="/migrate/amazon-linux-2-eol/">Amazon Linux 2 migration guide</a>.</p>\n'
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
        '<p>The differences above require workload-specific validation. Use the <a href="/amazon-linux-2-eol-checklist/">AL2 → AL2023 checklist</a> and the <a href="/migrate/amazon-linux-2-eol/">migration guide</a>, download the <a href="/toolkit/">$79 Offline Migration &amp; Audit Toolkit</a>, or check the <a href="/audit/">repository evidence report ($'
        + str(audit_base)
        + ", 30-day refund policy)</a> for exact observed AL2 source references and a remediation order.</p>\n"
        "</body>\n</html>\n"
    )


def studio_block(from_tag: str) -> str:
    """Studio door block (out/1.1.6 copy) linking the studio migration page with a from= tag.

    The US$7,500 figure matches the /end-of-life-migration/ page it links to
    ("Quoted $7,500-$25,000"). The tag is the only attribution: no pixel, no
    cross-origin request from EOLkits pages.
    """
    tag = re.sub(r"[^a-z0-9_-]", "", from_tag.lower())[:64]
    href = STUDIO_MIGRATION_URL + "?from=" + tag
    return (
        '<div class="studio-door">\n'
        "<p><strong>Rather not do this upgrade yourself?</strong> "
        "The studio that builds EOLkits takes the whole migration as a fixed-scope "
        "project: runtime, dependencies, tests, a staged deploy and a rollback plan. "
        "Scoped in writing. From US$7,500.</p>\n"
        '<p><a class="cta" href="' + href + '">Describe the upgrade &rarr;</a></p>\n'
        "</div>\n"
    )


def build_track_js():
    """Expose bounded first-party telemetry only after the v2 API proves itself.

    Also bridges qualified developer actions ('scan' and 'checkout_start') to
    first-party Umami when injected on eolkits.com, and delegates clicks on
    approved Stripe Payment Links so conversions never go unmeasured.
    No visitor identifier, referrer, cookie, or local-storage value is collected.
    """
    return (
        "(function(){'use strict';"
        "var ready=false,qp=new URLSearchParams(location.search),api="
        + json.dumps(API_URL.rstrip("/"))
        + ";"
        "function tok(v){v=String(v||'').toLowerCase();return/^[a-z0-9._-]{1,64}$/.test(v)?v:'';}"
        "function count(v){v=Number(v);return Number.isFinite(v)?Math.max(0,Math.min(Math.trunc(v),10000)):0;}"
        "function um(ev,d){try{if(window.umami&&typeof window.umami.track==='function')window.umami.track(ev,d);}catch(e){}}"
        "window.eolkitsTrack=function(name,extra){"
        "if(name==='scan_completed'||name==='scan')um('scan',{sku:extra&&tok(extra.sku)||'toolkit'});"
        "if(name==='checkout_click'||name==='checkout_start')um('checkout_start',{sku:extra&&tok(extra.sku)||'toolkit'});"
        "if(!ready)return;try{"
        "var p={event:name,path:location.pathname,"
        "source:tok(qp.get('source'))||'organic',"
        "utm_source:tok(qp.get('utm_source')),"
        "utm_medium:tok(qp.get('utm_medium')),"
        "utm_campaign:tok(qp.get('utm_campaign')),"
        "kit:tok(qp.get('kit'))};"
        "if(extra&&tok(extra.sku))p.sku=tok(extra.sku);"
        "if(extra&&/^\\d{4}-\\d{2}-\\d{2}$/.test(String(extra.deadline||'')))p.deadline=String(extra.deadline);"
        "if(name==='scan_completed'&&extra&&extra.meta)p.meta={finding_count:count(extra.meta.finding_count),file_count:count(extra.meta.file_count)};"
        "fetch(api+'/api/events',{method:'POST',mode:'cors',cache:'no-store',credentials:'omit',keepalive:true,"
        "headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}).catch(function(){});"
        "}catch(e){}};"
        "document.addEventListener('click',function(ev){try{"
        "var a=ev.target&&ev.target.closest?ev.target.closest('a[href^=\"https://buy.stripe.com/\"]'):null;"
        "if(a)window.eolkitsTrack('checkout_click',{sku:'toolkit'});"
        "}catch(e){}},true);"
        "fetch(api+'/api/capabilities',{cache:'no-store',credentials:'omit'})"
        ".then(function(r){if(!r.ok)throw new Error('unavailable');return r.json();})"
        ".then(function(c){var a=c&&c.audit;ready=Boolean(a&&String(a.report_version)==='2.0');"
        "if(ready)window.eolkitsTrack('view');}).catch(function(){});"
        "})();"
    )


def build_toolkit_page(pricing):
    """Build the dedicated $79 Offline Migration & Audit Toolkit product page."""
    pv = build_pricing_view(pricing)
    tk = pv["toolkit"]
    audit = pv["audit_pdf"]
    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "EOLkits — AWS Runtime & AL2023 Offline Migration Toolkit",
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "Linux, macOS, Windows (Python 3.10+)",
            "offers": {
                "@type": "Offer",
                "price": str(tk["price"]),
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "url": f"{SITE_URL}/toolkit/",
                "eligibleRegion": {"@type": "Country", "name": "US"},
            },
        },
        indent=2,
    )
    html = (
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AWS Runtime &amp; AL2023 Offline Migration Toolkit (${tk["price"]}) | EOLkits</title>
<meta name="description" content="Air-gapped AWS Lambda &amp; Amazon Linux 2023 migration toolkit (${tk["price"]}): stdlib-only local scanner (HTML/PDF report + Jira CSV + SHA-256 attestation), Python 3.12/3.13 &amp; AWS SDK v3 codemods, AL2023 Lambda layer Dockerfiles, and canary rollback IaC.">
<link rel="canonical" href="{SITE_URL}/toolkit/">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
"""
        + _og_image_meta()
        + f"""<script type="application/ld+json">{schema}</script>
</head>
<body>
<header class="nav">
  <div class="container nav-inner">
    <a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>
    <nav>
      <a href="/migrate/">Deadlines</a>
      <a href="/scan/">Free scan</a>
      <a href="/toolkit/">Toolkit (${tk["price"]})</a>
      <a href="/audit/">Audit</a>
      <a href="/about/">About</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>

<div class="urgency-strip">
  <div class="container">
    <span class="urgency-pill">Active AWS Alerts</span>
    <strong>Python 3.10</strong> deprecated Oct 31, 2026 · <strong>.NET 8</strong> deprecated Nov 10, 2026 · <strong>AL2</strong> standard support ended Jun 30, 2026 · Create/update blocks: <strong>Jul 29 / Aug 31, 2027</strong>.
  </div>
</div>

<main>
  <section class="hero">
    <div class="container hero-split">
      <div>
        <div class="eyebrow">Instant ZIP Download · Zero Source Upload · Unlimited Company Repos</div>
        <h1>Audit &amp; migrate AWS runtimes behind your own firewall.</h1>
        <p class="lede">Most engineering teams cannot upload proprietary source ZIPs to a third-party web form. The <strong>${tk["price"]} Offline Migration &amp; Audit Toolkit</strong> runs 100% locally on Python 3.10+ stdlib—turning repositories, IaC, and <code>aws lambda list-functions</code> JSON into CAB-ready HTML/PDF reports, Jira CSV tickets, safe AST codemods, AL2023 container layers, and canary rollback IaC.</p>
        <div class="cta-row">
          <a class="btn-primary" href="{tk["payment_link"]}">Buy Offline Toolkit — ${tk["price"]} →</a>
          <a class="btn-secondary" href="/toolkit/sample/">Inspect sample HTML report</a>
          <a class="btn-ghost" href="/scan/">Try free browser scan</a>
        </div>
        <p class="market-note">One-time Stripe payment (${tk["price"]} USD) · Unlisted HTTPS ZIP link emailed immediately after checkout · <strong>US buyers only</strong> · 30-day full refund policy via <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a>.</p>
      </div>
      <div class="terminal-card" aria-label="Sample offline CLI execution">
        <div class="terminal-bar">
          <span class="terminal-dot r"></span><span class="terminal-dot y"></span><span class="terminal-dot g"></span>
          <span>eolkits_offline_audit.py — air-gapped local run</span>
        </div>
        <div class="terminal-body">
          <div class="t-cmd">$ python3 src/eolkits_offline_audit.py \\</div>
          <div class="t-cmd">&nbsp;&nbsp;--repo ./payments-monorepo \\</div>
          <div class="t-cmd">&nbsp;&nbsp;--aws-lambda-json lambdas.json --out ./evidence</div>
          <div class="t-dim">Scanning 142 IaC, Python, Node, .NET &amp; Dockerfile targets...</div>
          <div><span class="t-crit">[CRITICAL]</span> infra/main.tf:14 — amzn2 AMI (AL2 EOL 2026-06-30)</div>
          <div><span class="t-high">[HIGH]</span> infra/main.tf:9 — python3.10 (deprecated 2026-10-31)</div>
          <div><span class="t-high">[HIGH]</span> ledger/Ledger.csproj:3 — net8.0 (dotnet8 deprecated 2026-11-10)</div>
          <div><span class="t-high">[HIGH]</span> billing/app.py:1 — distutils removed in Python 3.12</div>
          <div><span class="t-high">[HIGH]</span> webhooks/index.js:1 — aws-sdk v2 unbundled in Node 18+</div>
          <div class="t-ok">✓ Wrote evidence/migration-evidence-report.html (Print-PDF ready)</div>
          <div class="t-ok">✓ Wrote evidence/findings.csv (Jira / Linear import)</div>
          <div class="t-ok">✓ Wrote evidence/attestation.json (SHA-256: 247f1685...d294)</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <h2>Everything inside <code>AWS-Runtime-EOL-Migration-Toolkit-v1.0.0.zip</code></h2>
      <p class="sub">Zero external pip/npm runtime dependencies required to run the scanners and codemods—drop into air-gapped laptops, bastion hosts, or private GitHub/GitLab runners.</p>
      <div class="deliverable-grid">
        <article class="deliverable-card">
          <h3>1. Air-Gapped Repo &amp; IaC Auditor</h3>
          <p><code>src/eolkits_offline_audit.py</code> scans CloudFormation, SAM, CDK, Terraform, Serverless, Dockerfiles, <code>package.json</code>, <code>requirements.txt</code>, <code>.csproj</code>, and optional <code>aws lambda list-functions</code> JSON. Emits dark/print-CSS HTML reports, Jira CSVs, and deterministic SHA-256 attestations.</p>
        </article>
        <article class="deliverable-card">
          <h3>2. Python 3.12 / 3.13 AST Doctor</h3>
          <p><code>src/codemods/py312_313_stdlib_doctor.py</code> inspects Python ASTs for PEP 632 (<code>distutils</code>), PEP 594 (all 19 removed 3.13 modules), <code>collections.abc</code>, <code>@asyncio.coroutine</code>, and <code>datetime.utcnow()</code>—with safe <code>--apply</code> rewrites where semantics are 1:1.</p>
        </article>
        <article class="deliverable-card">
          <h3>3. Node 24 &amp; AWS SDK v3 Mapper</h3>
          <p><code>src/codemods/node_aws_sdk_v3_mapper.py</code> maps every <code>new AWS.&lt;Service&gt;()</code> call across JS/TS files to exact <code>@aws-sdk/client-*</code> v3 packages + install commands, and flags removed <code>crypto.createCipher</code> and OpenSSL 3 hazards.</p>
        </article>
        <article class="deliverable-card">
          <h3>4. AL2 → AL2023 Cutover Linter</h3>
          <p><code>src/codemods/al2_to_al2023_cutover_lint.py</code> catches <code>amazon-linux-extras</code>, <code>ntpd</code>, <code>iptables.service</code>, <code>python2</code> shebangs, EPEL assumptions, and unauthenticated IMDSv1 <code>169.254.169.254</code> calls in user-data, Packer, and shell scripts.</p>
        </article>
        <article class="deliverable-card">
          <h3>5. AL2023 Native Layer Dockerfiles</h3>
          <p>Reproducible multi-arch (<code>x86_64</code> and Graviton <code>arm64</code>) Dockerfiles on <code>public.ecr.aws/lambda/python:3.12</code>, <code>3.13</code>, and <code>nodejs:24</code> that compile C/Rust wheels and N-API addons against <code>glibc 2.34</code> with zero ELF mismatches.</p>
        </article>
        <article class="deliverable-card">
          <h3>6. Canary Rollback IaC &amp; CAB Pack</h3>
          <p>Production Terraform + AWS SAM weighted Lambda alias templates (10% canary traffic shift + automatic CloudWatch error-alarm rollback), GitHub Actions matrix CI gate, and Markdown CAB / SOC 2 sign-off templates.</p>
        </article>
      </div>
      <p><a class="btn-primary" href="{tk["payment_link"]}">Instant Download — ${tk["price"]} USD →</a> &nbsp;<a class="btn-outline" href="/toolkit/sample/">Preview synthetic 14-finding HTML report →</a></p>
    </div>
  </section>

  <section class="section dark">
    <div class="container">
      <h2>Choose the right fit</h2>
      <div class="pricing-grid">
        <article class="pricing-card">
          <h3>Open-Source CLIs</h3>
          <div class="price">$0</div>
          <p>Individual MIT kits (<code>al2023-gate</code>, <code>python-pivot</code>, <code>lambda-lifeline</code>) + free in-browser file checker.</p>
          <a class="btn-outline" href="https://github.com/ntoledo319/EOLkits">Clone on GitHub</a>
        </article>
        <article class="pricing-card featured">
          <h3>Offline Migration &amp; Audit Toolkit</h3>
          <div class="price">${tk["price"]}</div>
          <p>Unified air-gapped scanner (HTML/PDF + Jira CSV + SHA-256 attestation), AST codemods, AL2023 layer Dockerfiles, canary rollback IaC, and CAB templates. Unlimited internal company repos.</p>
          <a class="btn-primary" href="{tk["payment_link"]}">Buy Offline Toolkit — ${tk["price"]}</a>
          <p class="small"><a href="/toolkit/sample/">Sample report →</a> · US buyers only · 30-day refund policy</p>
        </article>
        <article class="pricing-card">
          <h3>Hosted Evidence PDF</h3>
          <div class="price">${audit["base"]}</div>
          <p>Zero-install hosted scan of one uploaded repository ZIP returning a 4+ page server-rendered PDF and 30-day <code>/verify/</code> hash record (when upload gate is open).</p>
          <a class="btn-outline" href="/audit/">Check ${audit["base"]} report</a>
          <p class="small"><a href="/audit/sample/">Sample PDF →</a> · US buyers only · 30-day refund policy</p>
        </article>
      </div>
    </div>
  </section>
</main>

<footer class="footer">
  <div class="container">
    <div class="muted small">Toledo Technologies LLC · 2389 Main St. STE 100, Glastonbury, CT 06033, United States · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> · Self-serve Stripe checkouts: US buyers only.</div>
    <div class="muted small"><a href="/">Home</a> · <a href="/migrate/">Deadlines</a> · <a href="/scan/">Free scan</a> · <a href="/audit/">Audit</a> · <a href="/about/">About</a> · <a href="/changelog/">Changelog</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/terms.html#refunds">Refund policy</a> · <a href="/legal/privacy.html">Privacy</a> · <a href="/legal/SECURITY.html">Security</a></div>
  </div>
</footer>
</body>
</html>"""
    )
    return html


def build_toolkit_sample_page():
    """Render the synthetic air-gapped HTML report sample with canonical host substitution."""
    raw = (TEMPLATE_DIR / "toolkit_sample.html").read_text(encoding="utf-8")
    return raw.replace("{SITE_URL}", SITE_URL)


def build_about_page(pricing):
    """Build the /about/ trust and company page."""
    pv = build_pricing_view(pricing)
    tk = pv["toolkit"]
    audit = pv["audit_pdf"]
    return (
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>About EOLkits — Toledo Technologies LLC</title>
<meta name="description" content="EOLkits builds deterministic, primary-source-cited AWS runtime and Amazon Linux deprecation tools. Operated by Toledo Technologies LLC in Glastonbury, Connecticut.">
<link rel="canonical" href="{SITE_URL}/about/">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
"""
        + _og_image_meta()
        + f"""</head>
<body>
<header class="nav">
  <div class="container nav-inner">
    <a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>
    <nav>
      <a href="/migrate/">Deadlines</a>
      <a href="/scan/">Free scan</a>
      <a href="/toolkit/">Toolkit (${tk["price"]})</a>
      <a href="/audit/">Audit</a>
      <a href="/about/">About</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>
<main class="container article">
  <nav class="breadcrumb"><a href="/">Home</a> / <span>About</span></nav>
  <h1>About EOLkits</h1>
  <p>EOLkits builds deterministic static analysis, migration codemods, and source-cited reference guides for teams upgrading off deprecated AWS Lambda runtimes and Amazon Linux 2.</p>

  <section>
    <h2>Engineering principles</h2>
    <ul>
      <li><strong>Primary sources only:</strong> Every tracked deprecation milestone links directly to official AWS documentation, Python PEPs, or Node.js release notes—never recycled secondary blog posts.</li>
      <li><strong>Deterministic output:</strong> Running the same scanner and rule pack on the same source tree produces identical findings and SHA-256 evidence hashes.</li>
      <li><strong>Zero-upload options first:</strong> Both our free browser scanner and the <a href="/toolkit/">${tk["price"]} Offline Migration &amp; Audit Toolkit</a> run locally so proprietary company source code never leaves your environment.</li>
      <li><strong>Explicit scope boundaries:</strong> Static scanners inspect supplied source, IaC, and manifests; they never fabricate live cloud resource counts or speculative downtime-dollar claims.</li>
    </ul>
  </section>

  <section>
    <h2>Products &amp; licensing</h2>
    <ul>
      <li><strong>Open-source CLIs ($0, MIT):</strong> <code>al2023-gate</code>, <code>python-pivot</code>, and <code>lambda-lifeline</code> on <a href="https://github.com/ntoledo319/EOLkits">GitHub</a>.</li>
      <li><strong><a href="/toolkit/">Offline Migration &amp; Audit Toolkit (${tk["price"]} USD)</a>:</strong> Instant-download commercial ZIP pack with unified air-gapped repo/IaC scanner, HTML/PDF + Jira CSV reports, Python 3.12/3.13 &amp; AWS SDK v3 codemods, AL2023 Dockerfiles, and canary rollback IaC. Licensed for unlimited internal repositories of the purchasing individual or company.</li>
      <li><strong><a href="/audit/">Hosted Repository Evidence Report (${audit["base"]} USD)</a>:</strong> Server-gated static scan of one uploaded repository ZIP returning a 4+ page PDF and 30-day <code>/verify/</code> hash lookup.</li>
    </ul>
    <p>Self-serve paid Stripe checkouts on EOLkits are offered to <strong>US buyers only</strong> and include a <strong>30-day full refund policy</strong>.</p>
  </section>

  <section>
    <h2>Operator &amp; contact</h2>
    <table class="facts">
      <tr><th>Operating entity</th><td>Toledo Technologies LLC</td></tr>
      <tr><th>Mailing address</th><td>2389 Main St. STE 100, Glastonbury, CT 06033, United States</td></tr>
      <tr><th>Support &amp; refunds</th><td><a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a></td></tr>
      <tr><th>Source repository</th><td><a href="https://github.com/ntoledo319/EOLkits">github.com/ntoledo319/EOLkits</a></td></tr>
      <tr><th>System status</th><td><a href="/status/">eolkits.com/status/</a></td></tr>
    </table>
  </section>
</main>
<footer class="footer">
  <div class="container">
    <div class="muted small">Toledo Technologies LLC · 2389 Main St. STE 100, Glastonbury, CT 06033, United States · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a></div>
    <div class="muted small"><a href="/">Home</a> · <a href="/changelog/">Changelog</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a> · <a href="/legal/SECURITY.html">Security</a></div>
  </div>
</footer>
</body>
</html>"""
    )


def build_changelog_page():
    """Build the /changelog/ release and rule-pack log."""
    return (
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Changelog — AWS Rule Pack &amp; Releases | EOLkits</title>
<meta name="description" content="Dated release log for EOLkits AWS deprecation rule packs, offline migration toolkit, and verification gates.">
<link rel="canonical" href="{SITE_URL}/changelog/">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
"""
        + _og_image_meta()
        + """</head>
<body>
<header class="nav">
  <div class="container nav-inner">
    <a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>
    <nav>
      <a href="/migrate/">Deadlines</a>
      <a href="/scan/">Free scan</a>
      <a href="/toolkit/">Toolkit ($79)</a>
      <a href="/audit/">Audit</a>
      <a href="/about/">About</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>
<main class="container article">
  <nav class="breadcrumb"><a href="/">Home</a> / <span>Changelog</span></nav>
  <h1>Changelog</h1>
  <p>Material updates to EOLkits rule packs, AWS deprecation schedules, and commercial artifacts.</p>

  <section>
    <h2>2026-11-19 — Rule Pack 2026.11 &amp; Offline Toolkit v1.0.0</h2>
    <ul>
      <li><strong>AWS Lambda schedule sync:</strong> Updated synchronized Lambda create/update block dates across <code>python3.8</code>, <code>python3.9</code>, <code>python3.10</code>, <code>python3.11</code>, <code>nodejs16.x</code>, <code>nodejs18.x</code>, <code>nodejs20.x</code>, <code>nodejs22.x</code>, <code>dotnet8</code>, and <code>provided.al2</code> to <strong>2027-07-29</strong> (Block Function Create) and <strong>2027-08-31</strong> (Block Function Update) per official AWS Lambda runtime documentation.</li>
      <li><strong>Active deprecation transitions:</strong> Marked <code>python3.10</code> (deprecated 2026-10-31), <code>dotnet8</code> (deprecated 2026-11-10), and <code>provided.al2</code> (deprecated 2026-07-31) as actively deprecated, and added dedicated migration and error-fix guides.</li>
      <li><strong>Offline Migration &amp; Audit Toolkit v1.0.0 ($79):</strong> Launched instant-download air-gapped CLI scanner, Python 3.12/3.13 &amp; AWS SDK v3 codemods, AL2023 multi-arch Lambda layer Dockerfiles, and Terraform/SAM canary rollback templates at <a href="/toolkit/">/toolkit/</a>.</li>
      <li><strong>Automated EOL drift watch:</strong> Added daily upstream schedule comparison against published AWS runtime lifecycle feeds before static deployment.</li>
    </ul>
  </section>

  <section>
    <h2>2026-09-09 — Deterministic Web &amp; Privacy CSP Hardening</h2>
    <ul>
      <li>Pinned reproducible build dates, strict first-party Content-Security-Policy headers, and bounded count-only browser scanner telemetry.</li>
      <li>Added PEP 594 Python 3.13 error-fix references (<code>audioop</code>, <code>pipes</code>, <code>aifc</code>).</li>
    </ul>
  </section>

  <section>
    <h2>2026-08-22 — Audit v2 Engine &amp; Sample Manifest</h2>
    <ul>
      <li>Shipped fail-closed Audit v2 static repository report engine with SHA-256 input hashing, deterministic evidence fingerprints, and public sample verification artifacts at <a href="/audit/sample/">/audit/sample/</a>.</li>
    </ul>
  </section>
</main>
<footer class="footer">
  <div class="container">
    <div class="muted small">Toledo Technologies LLC · 2389 Main St. STE 100, Glastonbury, CT 06033, United States · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a></div>
    <div class="muted small"><a href="/">Home</a> · <a href="/about/">About</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></div>
  </div>
</footer>
</body>
</html>"""
    )


def build_index_page(pricing):
    """Build the canonical landing page from source data."""
    pricing_view = build_pricing_view(pricing)
    tk = pricing_view["toolkit"]
    audit = pricing_view["audit_pdf"]
    return (
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EOLkits — AWS Lambda &amp; Amazon Linux 2 EOL Migration Tools</title>
<meta name="description" content="Find and fix deprecated AWS Lambda runtimes (Python 3.10, .NET 8, Node.js 18/20) and Amazon Linux 2 hazards. Free MIT scanners, $79 air-gapped Offline Toolkit, and $299 repository evidence PDFs.">
<link rel="canonical" href="{SITE_URL}/">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
"""
        + _og_image_meta()
        + f"""</head>
<body>
<header class="nav">
  <div class="container nav-inner">
    <a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>
    <nav>
      <a href="/migrate/">Deadlines</a>
      <a href="/scan/">Free scan</a>
      <a href="/toolkit/">Toolkit (${tk["price"]})</a>
      <a href="/audit/">Audit</a>
      <a href="/about/">About</a>
      <a href="https://github.com/ntoledo319/EOLkits" class="btn-ghost">GitHub</a>
    </nav>
  </div>
</header>

<div class="urgency-strip">
  <div class="container">
    <span class="urgency-pill">Nov 2026 AWS Update</span>
    <strong>Python 3.10</strong> (Oct 31) &amp; <strong>.NET 8</strong> (Nov 10) are now deprecated in AWS Lambda · <strong>AL2</strong> ended standard support Jun 30, 2026 · <a href="/lambda-runtime-deprecation-schedule/">View 2027 block schedule →</a>
  </div>
</div>

<main>
  <section class="hero">
    <div class="container hero-split">
      <div>
        <div class="eyebrow">AWS runtime &amp; OS EOLs that break production deploys</div>
        <h1>Audit &amp; clear AWS deprecation debt before deploys lock.</h1>
        <p class="lede">Check SAM, CDK, Terraform, Serverless, and manifests free in your browser without uploading files. Need CAB-ready evidence and codemods behind your firewall? Download the <strong>${tk["price"]} Air-Gapped Offline Toolkit</strong>—or request a <strong>${audit["base"]} hosted repository PDF</strong>.</p>
        <div class="cta-row">
          <a class="btn-primary" href="/toolkit/">Get ${tk["price"]} Offline Toolkit →</a>
          <a class="btn-secondary" href="/scan/">Run free browser scan</a>
          <a class="btn-ghost" href="/migrate/">See AWS deadlines</a>
        </div>
        <p class="market-note">Free MIT CLIs · Instant ${tk["price"]} air-gapped ZIP download (zero source upload) · 30-day full refund policy · Paid checkouts: US buyers only.</p>
      </div>
      <div class="terminal-card" aria-label="EOLkits local scan preview">
        <div class="terminal-bar">
          <span class="terminal-dot r"></span><span class="terminal-dot y"></span><span class="terminal-dot g"></span>
          <span>eolkits — deterministic static evidence</span>
        </div>
        <div class="terminal-body">
          <div class="t-cmd">$ python3 eolkits_offline_audit.py --repo . --out ./cab-pack</div>
          <div class="t-dim">Rule Pack 2026.11 · Zero network calls · Zero code upload</div>
          <div><span class="t-crit">CRITICAL</span> Dockerfile:1 &rarr; amazonlinux:2 (EOL 2026-06-30)</div>
          <div><span class="t-high">HIGH</span> template.yaml:18 &rarr; python3.10 (unpatched 2026-10-31)</div>
          <div><span class="t-high">HIGH</span> Api.csproj:4 &rarr; net8.0 / dotnet8 (unpatched 2026-11-10)</div>
          <div><span class="t-high">HIGH</span> handler.py:2 &rarr; distutils removed in Python 3.12</div>
          <div><span class="t-high">HIGH</span> notify.js:3 &rarr; aws-sdk v2 missing on Node 18/20/24</div>
          <div class="t-ok">&rarr; HTML/PDF report + Jira CSV + SHA-256 attestation ready</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <h2>Open-Source CLI Kits (MIT)</h2>
      <p class="sub">Each standalone CLI scans first and previews changes before touching files.</p>
      <div class="kit-grid">
        <article class="kit-card urgent">
          <div class="kit-deadline">AL2 standard support ended Jun 30, 2026 — migrate now</div>
          <h3>al2023-gate</h3>
          <p class="kit-sub">Amazon Linux 2 &amp; provided.al2 to AL2023</p>
          <p>Find AL2 AMIs, remap dnf/SPAL packages, patch cloud-init, Packer, and Ansible, and generate cutover checklists.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/al2023-gate">Read docs →</a>
        </article>
        <article class="kit-card urgent">
          <div class="kit-deadline">Python 3.10 deprecated Oct 31, 2026 · Block: Jul 29, 2027</div>
          <h3>python-pivot</h3>
          <p class="kit-sub">Lambda Python 3.8–3.11 to 3.12 / 3.13</p>
          <p>Flag removed PEP 632 / PEP 594 stdlib modules, cp312/AL2023 native wheel floors, and IaC runtime strings.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/python-pivot">Read docs →</a>
        </article>
        <article class="kit-card">
          <div class="kit-deadline">Node 18/20 deprecated · .NET 8 deprecated Nov 10, 2026</div>
          <h3>lambda-lifeline</h3>
          <p class="kit-sub">Lambda Node.js 16–22 to 24 (+ multi-runtime inventory)</p>
          <p>Inventory deprecated runtimes across regions, surface aws-sdk v2 &amp; OpenSSL 3 breaks, and stage alias rollbacks.</p>
          <a class="kit-link" href="https://github.com/ntoledo319/EOLkits/tree/main/kits/lambda-lifeline">Read docs →</a>
        </article>
      </div>
    </div>
  </section>

  <section class="section dark" id="pricing">
    <div class="container">
      <h2>Pricing</h2>
      <p class="sub">Start free in your browser or terminal. Upgrade to the ${tk["price"]} air-gapped Offline Toolkit for local CAB reports, codemods, and AL2023 container templates, or use the ${audit["base"]} hosted repository PDF.</p>
      <div class="pricing-grid">
        <article class="pricing-card">
          <h3>Open-Source CLI</h3>
          <div class="price">$0</div>
          <p>All three MIT CLI kits plus the client-side browser scanner and EOL schedule tools.</p>
          <a class="btn-outline" href="https://github.com/ntoledo319/EOLkits">Get source</a>
          <a class="btn-outline" href="/scan/">Browser scan</a>
        </article>
        <article class="pricing-card featured">
          <h3>Offline Toolkit</h3>
          <div class="price">${tk["price"]}</div>
          <p>Instant ZIP download — zero source upload. Air-gapped multi-stack scanner (HTML/PDF report + Jira CSV + SHA-256 attestation), Python 3.12/3.13 &amp; AWS SDK v3 codemods, AL2023 Lambda layer Dockerfiles, canary rollback IaC, and CAB sign-off templates across unlimited internal repos.</p>
          <a class="btn-primary" href="{tk["payment_link"]}">Buy Offline Toolkit — ${tk["price"]}</a>
          <a class="btn-outline" href="/toolkit/">Full specs</a>
          <p class="small"><a href="/toolkit/sample/">See sample air-gapped report →</a> · US buyers only · 30-day refund policy</p>
        </article>
        <article class="pricing-card">
          <h3>Audit PDF</h3>
          <div class="price">${audit["base"]}</div>
          <p>One uploaded repository ZIP or source file: exact file/line evidence, observed reach, remediation order, configured references, and <code>/verify/</code> evidence fingerprint. 30-day full refund policy.</p>
          <a class="btn-outline" href="/audit/">Get the ${audit["base"]} report</a>
          <p class="small"><a href="/audit/sample/">See sample PDF →</a> · US buyers only</p>
        </article>
      </div>
      <p class="sub">EOLkits sells no managed migration. Self-serve paid Stripe checkouts are offered to US buyers only. There is no recurring subscription, live AWS-account inventory service, or automated pull-request bot for sale.</p>
    </div>
  </section>
</main>

<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="brand"><span class="brand-mark">&gt;</span> EOLkits</div>
        <p class="muted">Deterministic AWS deprecation scanners, air-gapped migration toolkits, and primary-source guides.</p>
        <p class="muted small">Toledo Technologies LLC · 2389 Main St. STE 100, Glastonbury, CT 06033, United States · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> · Self-serve paid checkouts: US buyers only.</p>
      </div>
      <div>
        <h5>Products &amp; Tools</h5>
        <a href="/toolkit/">Offline Toolkit (${tk["price"]})</a><br>
        <a href="/audit/">Hosted Audit PDF (${audit["base"]})</a><br>
        <a href="/scan/">Free browser scanner</a><br>
        <a href="/eol-checker/">Runtime EOL checker</a>
      </div>
      <div>
        <h5>Company &amp; Legal</h5>
        <a href="/about/">About</a> · <a href="/changelog/">Changelog</a><br>
        <a href="/migrate/">Deadlines</a> · <a href="/fix/">Error fixes</a><br>
        <a href="/legal/terms.html">Terms</a> · <a href="/legal/terms.html#refunds">Refund policy</a> · <a href="/legal/privacy.html">Privacy</a> · <a href="/legal/SECURITY.html">Security</a> · <a href="/status/">Status</a>
      </div>
    </div>
    <div class="muted small">© 2026 Toledo Technologies LLC. Open-source kits MIT-licensed; commercial toolkit licensed per purchasing organization.</div>
  </div>
</footer>
</body>
</html>"""
    )


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
    <h3 class="eolkits-repo"></h3>
    <p>Check this repository for AWS runtime and platform deprecation risks.</p>
    <a href="{SITE_URL}/audit/?repo=${{encodeURIComponent(repo)}}&utm_source=widget&utm_medium=embed&source=widget" target="_blank" rel="noopener">Run EOLkits audit</a>
    <div class="powered">Powered by EOLkits</div>
  `;
  container.querySelector('.eolkits-repo').textContent = repo;
  script.parentNode.insertBefore(container, script.nextSibling);
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
    """Post-checkout confirmation for active paid SKUs (Offline Toolkit & Audit v2)."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thank you — EOLkits</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="/style.css">
<style>
.thanks-wrap{max-width:740px;margin:0 auto;padding:3rem 1.5rem 4rem}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin:1.25rem 0}
.card a{color:var(--accent);text-decoration:underline}
</style>
</head>
<body>
<main class="thanks-wrap">
<a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>
<h1 id="title" style="margin-top:1rem">Thank you</h1>
<div id="body"></div>
<footer style="margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border);color:var(--ink-muted);font-size:0.875rem"><a href="/">Home</a> · <a href="/toolkit/">Offline Toolkit</a> · <a href="/status/">Status</a> · <a href="/legal/terms.html">Terms</a> · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a></footer>
</main>
<script>
const qp = new URLSearchParams(location.search);
const sku = qp.get('sku') || '';
const title = document.getElementById('title');
const body = document.getElementById('body');
function h(html) {{ body.innerHTML = html; }}
if (sku === 'toolkit') {{
  title.textContent = 'Your Offline Toolkit download is on the way';
  h('<div class="card"><p><strong>Payment confirmed.</strong> Our automated fulfillment service is emailing your unlisted HTTPS download link for <code>AWS-Runtime-EOL-Migration-Toolkit-v1.0.0.zip</code> to the address entered at Stripe Checkout (sent from <code>hello@toledotechnologies.com</code>).</p><p>Unzip locally and run <code>python3 src/eolkits_offline_audit.py --repo /path/to/repo --out ./audit-out</code> on Python 3.10+—zero external dependencies and zero source upload.</p><p>If the email does not arrive in your inbox or spam folder within a few minutes, email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> and we will resend or issue an immediate full refund.</p></div>');
}} else if (sku === 'audit') {{
  title.textContent = 'Your audit is on the way';
  h('<div class="card"><p>Payment received. Your repository evidence PDF is queued for automated generation and email delivery. Delays are possible.</p><p>Its evidence lookup records the input hash, rule-pack version, evidence fingerprint, and observed counts. The PDF itself is not digitally signed.</p><p>If fulfillment cannot complete after retries, the system attempts an automatic refund and surfaces any unresolved refund for operator review.</p></div>');
}} else if (sku === 'pack') {{
  title.textContent = 'Migration Pack is closed';
  h('<div class="card"><p>Migration Pack is not available for purchase. If a legacy payment link charged you, email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> with the Stripe receipt so the payment can be reviewed and refunded.</p></div>');
}} else if (sku === 'drift') {{
  title.textContent = 'Drift Watch is unavailable';
  h('<div class="card"><p>Drift Watch is not open for purchase. If a legacy payment link charged you, email <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> with the Stripe receipt so the payment can be reviewed and refunded.</p></div>');
}} else {{
  h('<div class="card"><p>Payment received. Check your checkout email address for your delivery link or receipt, or contact <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a>.</p></div>');
}}
</script>
</body>
</html>"""
    return _interpolate_api(html)


def build_status_page():
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Status — EOLkits</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:2rem;line-height:1.6}.brand{color:#2563eb;font-weight:600}.svc{display:flex;justify-content:space-between;align-items:center;border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin:.5rem 0}.dot{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;background:#9ca3af}.dot.green{background:#10b981}.dot.red{background:#ef4444}.muted{color:#6b7280;font-size:.85rem}.notice{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:1rem}</style>
</head><body><a href="/" class="brand">← EOLkits</a><h1>System Status</h1>
<p class="muted">Live backend readiness only. Low-volume funnel, commerce, and order details are private operator data. This is not an end-to-end synthetic purchase test.</p>
<p id="feedState" class="notice">Loading the live API status…</p>
<div id="services"><div class="svc"><span><span class="dot" id="dot-storage"></span>Upload/report storage</span><span id="t-storage">unknown</span></div>
<div class="svc"><span><span class="dot" id="dot-stripe"></span>Stripe configuration</span><span id="t-stripe">unknown</span></div>
<div class="svc"><span><span class="dot" id="dot-runner"></span>Job runner</span><span id="t-runner">—</span></div>
<div class="svc"><span><span class="dot" id="dot-email"></span>Email configuration</span><span id="t-email">unknown</span></div></div>
<h2>Product availability</h2><ul id="capabilities"><li>Loading…</li></ul>
<script>
function list(id,data){const el=document.getElementById(id);el.innerHTML='';const entries=Object.entries(data||{});if(!entries.length){el.innerHTML='<li>No capabilities reported</li>';return;}for(const [k,v] of entries){const li=document.createElement('li');li.textContent=k+': '+v;el.appendChild(li);} }
fetch('{API_URL}/api/status',{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject(new Error('HTTP '+r.status))).then(d=>{
  document.getElementById('feedState').textContent='Live API reported '+(d.overall||'unknown')+' at '+(d.timestamp||'unknown time')+'.';
  for(const s of ['storage','stripe','runner','email']){
    const v=(d.components||{})[s];
    if(v){document.getElementById('dot-'+s).className='dot '+(v.ok?'green':'red');document.getElementById('t-'+s).textContent=v.ok?'ready':'not ready';}
  }
  list('capabilities',d.capabilities);
}).catch(e=>{document.getElementById('feedState').textContent='Live status unavailable; all component states remain unknown. '+e.message;list('capabilities',{});});
</script>
<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer></body></html>"""
    return _interpolate_api(html)


def inject_privacy_meta(content: str) -> str:
    """Inject browser-enforced privacy controls into every HTML document.

    GitHub Pages cannot set response headers. Injecting this into every generated
    HTML document keeps query parameters and page paths out of outbound Referer
    headers while retaining the first-party origin for basic attribution. The
    CSP also prevents unreviewed third-party scripts and connections from being
    activated by hosting-layer HTML injection.
    """
    if not re.search(r"<html\b", content, flags=re.IGNORECASE):
        return content
    metas: list[str] = []
    if not re.search(r'<meta\s+name=["\']referrer["\']', content, flags=re.IGNORECASE):
        metas.append('<meta name="referrer" content="origin">')
    if not re.search(
        r'<meta\s+http-equiv=["\']Content-Security-Policy["\']',
        content,
        flags=re.IGNORECASE,
    ):
        metas.append(
            '<meta http-equiv="Content-Security-Policy" content="' + CONTENT_SECURITY_POLICY + '">'
        )
    if not metas:
        return content
    return re.sub(
        r"(<head\b[^>]*>)",
        lambda match: match.group(1) + "\n" + "\n".join(metas),
        content,
        count=1,
        flags=re.IGNORECASE,
    )


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


PODFREEZE_SWITCH_DATE = "2026-12-02"
# The switch date is the maintainer's plan, not a record. Set this to True in
# a one-line commit only after a dated public receipt that trunk refused new
# podspecs on or after PODFREEZE_SWITCH_DATE (the CocoaPods blog or trunk
# banner saying it is done, or a reported `pod trunk push` rejection).
PODFREEZE_FREEZE_CONFIRMED = False


def build_podfreeze_page(today: "date | None" = None, confirmed: "bool | None" = None):
    """podfreeze mirror page (P2.7): carries both copies of the dated block.

    The pre-freeze copy shows until the daily build's date reaches
    PODFREEZE_SWITCH_DATE (2 December 2026, the planned CocoaPods trunk freeze)
    AND PODFREEZE_FREEZE_CONFIRMED is set; from that build on, the post-freeze
    copy is what renders. The pre-freeze copy is worded as the maintainer's plan,
    so it stays true if the switch slips. The inactive copy stays in the
    document as a labelled HTML comment so either variant can be reviewed in any
    daily build. Dates and framing follow the CocoaPods maintainer's own
    announcement (blog.cocoapods.org/CocoaPods-Specs-Repo/), re-read 2026-11-22:
    planned read-only test run 2-6 November 2026, planned permanent freeze
    2 December 2026.
    """
    if today is None:
        today = date.today()
    if confirmed is None:
        confirmed = PODFREEZE_FREEZE_CONFIRMED
    post_freeze = confirmed and today.isoformat() >= PODFREEZE_SWITCH_DATE

    pre_freeze_copy = (
        "<p>The CocoaPods maintainer&rsquo;s plan: from <strong>2 December 2026</strong>, "
        "trunk stops accepting new podspecs, permanently. The maintainer&rsquo;s plan "
        "set a read-only test run for <strong>2&ndash;6 November 2026</strong>.</p>\n"
        "<p>Existing builds keep resolving from the Specs repo on GitHub and the "
        "jsDelivr CDN, so the freeze is a supply-chain event rather than a build "
        "break: a pod with a newly discovered vulnerability has no canonical "
        "coordinate to carry the fix.</p>\n"
    )
    post_freeze_copy = (
        "<p>On <strong>2 December 2026</strong>, CocoaPods trunk stopped accepting new "
        "podspecs, permanently. The maintainer&rsquo;s plan set a read-only test run "
        "for <strong>2&ndash;6 November 2026</strong>.</p>\n"
        "<p>Existing builds keep resolving from the Specs repo on GitHub and the "
        "jsDelivr CDN, so the freeze is a supply-chain event rather than a build "
        "break: a pod with a newly discovered vulnerability has no canonical "
        "coordinate to carry the fix.</p>\n"
    )
    active, inactive, label = (
        (post_freeze_copy, pre_freeze_copy, "pre-freeze")
        if post_freeze
        else (pre_freeze_copy, post_freeze_copy, "post-freeze")
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>CocoaPods trunk freeze — podfreeze | EOLkits</title>\n"
        '<meta name="description" content="CocoaPods trunk read-only from 2 December 2026: the podfreeze tool reads your Podfile.lock and reports which pods can never receive another published version. Mirror of the podfreeze page.">\n'
        '<link rel="canonical" href="' + SITE_URL + '/podfreeze/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n'
        "</head>\n"
        '<body class="container article">\n'
        '<nav class="breadcrumb"><a href="/">Home</a> / <span>CocoaPods trunk freeze</span></nav>\n'
        "<h1>CocoaPods trunk freeze</h1>\n"
        "<p>This page mirrors the podfreeze project, an open-source (MIT) CLI that "
        "reads the <code>SPEC REPOS</code> section of your <code>Podfile.lock</code> "
        "and reports which pods resolved from CocoaPods trunk — the coordinates that "
        "can never receive another published version, including a security fix.</p>\n"
        "<p>Project, browser checker and source: "
        '<a href="https://github.com/ntoledo319/podfreeze">podfreeze on GitHub</a>.</p>\n'
        "<!-- "
        + label
        + " copy (activates on or after "
        + PODFREEZE_SWITCH_DATE
        + " once PODFREEZE_FREEZE_CONFIRMED is set): -->\n"
        "<!--\n" + inactive + "-->\n" + active + '<div class="studio-door">\n'
        "<p><strong>Moving off CocoaPods?</strong> Send your <code>Podfile.lock</code>: "
        "every pod inventoried and a written fixed-scope migration quote. "
        '<a href="https://toledotechnologies.com/brief/?from=podfreeze">Start a brief</a>. '
        "No price is quoted before the scope is agreed in writing.</p>\n"
        "</div>\n"
        '<p class="muted">Source: <a href="https://blog.cocoapods.org/CocoaPods-Specs-Repo/" target="_blank" rel="noopener nofollow">CocoaPods Trunk Read-only Plan</a> — the maintainer\u2019s own announcement.</p>\n'
        '<footer style="margin-top:3rem;color:#6b7280;font-size:.85rem"><a href="/">Home</a></footer>\n'
        "</body>\n</html>\n"
    )


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
    """Derive an AWS runtime identifier (python3.9 / nodejs20.x / dotnet8 / provided.al2)
    from a deprecation entry name, so the scanner's deadlines come straight from the YAML."""
    n = (name or "").lower()
    if "provided.al2" in n:
        return "provided.al2"
    m = re.search(r"python\s*(\d+)\.(\d+)", n)
    if m:
        return f"python{m.group(1)}.{m.group(2)}"
    m = re.search(r"node(?:\.|\s)?js\s*(\d+)", n)
    if m:
        return f"nodejs{m.group(1)}.x"
    m = re.search(r"(?:\.net|dotnet)\s*(\d+)", n)
    if m:
        return f"dotnet{m.group(1)}"
    m = re.search(r"ruby\s*(\d+)\.(\d+)", n)
    if m:
        return f"ruby{m.group(1)}.{m.group(2)}"
    return None


_SCAN_JS = r"""
const $ = (s) => document.querySelector(s);
const RT_VALUE_RE = /^(nodejs\d+\.x|python\d+\.\d+|ruby\d+\.\d+|java\d+|dotnet\d+|dotnetcore\d+\.\d+|go\d+\.x|provided\.al\d+|provided)\b/i;
const CDK_VALUE_RE = /Runtime\.(NODEJS|PYTHON|RUBY|JAVA|DOTNET|GO)_(\d+)(?:_(\d+))?(?:_X)?/i;
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
function runtimeId(value) {
  const cleaned = String(value || '').trim().replace(/^['"]/, '');
  const m = cleaned.match(RT_VALUE_RE);
  return m ? m[1].toLowerCase() : null;
}
function configRecords(c) {
  const records = [], stack = [], lines = c.split(/\r?\n/); let documentId = 0;
  const keyRe = /^([ \t]*)(["']?)([A-Za-z0-9_.-]+)\2\s*:\s*(.*)$/;
  for (let i = 0; i < lines.length; i++) {
    if (/^[ \t]*(?:---|\.\.\.)[ \t]*(?:#.*)?$/.test(lines[i])) { stack.length = 0; documentId++; continue; }
    const m = lines[i].match(keyRe); if (!m) continue;
    const indent = m[1].replace(/\t/g, '        ').length;
    while (stack.length && stack[stack.length - 1][0] >= indent) stack.pop();
    const key = m[3].toLowerCase();
    const raw = m[4].replace(/\s+#.*$/, '').trim().replace(/,$/, '').trim();
    let value = raw;
    if (value.length >= 2 && ((value[0] === '"' && value[value.length - 1] === '"') || (value[0] === "'" && value[value.length - 1] === "'"))) value = value.slice(1, -1);
    const path = stack.slice(-8).map((item) => item[1]).concat([key]);
    records.push({ documentId, line: i + 1, key, value, path });
    if (raw === '' || raw === '{') stack.push([indent, key]);
  }
  return records;
}
function samePath(left, right) { return left.length === right.length && left.every((value, index) => value === right[index]); }
function samDocuments(c) {
  const documents = new Set(); let documentId = 0, pendingIndent = null;
  for (const line of c.split(/\r?\n/)) {
    if (/^[ \t]*(?:---|\.\.\.)[ \t]*(?:#.*)?$/.test(line)) { documentId++; pendingIndent = null; continue; }
    const transform = line.match(/^([ \t]*)["']?Transform["']?\s*:\s*(.*)$/i);
    if (transform) {
      const value = transform[2].replace(/\s+#.*$/, '').trim();
      if (/AWS::Serverless-/i.test(value)) documents.add(documentId);
      pendingIndent = value ? null : transform[1].replace(/\t/g, '        ').length;
      continue;
    }
    if (pendingIndent === null || !line.trim()) continue;
    const indent = (line.match(/^[ \t]*/) || [''])[0].replace(/\t/g, '        ').length;
    if (indent <= pendingIndent) pendingIndent = null;
    else if (/^[ \t]*-[ \t]*["']?AWS::Serverless-/i.test(line)) { documents.add(documentId); pendingIndent = null; }
  }
  return documents;
}
function yamlLambdaRuntimes(c, found) {
  const records = configRecords(c), resources = new Set(), providers = new Set(), sam = samDocuments(c);
  for (const r of records) {
    if (r.key === 'type' && /^(AWS::Lambda::Function|AWS::Serverless::Function)$/i.test(r.value) && r.path.includes('resources')) resources.add(r.documentId + '\u0000' + r.path.slice(0, -1).join('\u0000'));
    if (samePath(r.path, ['provider', 'name']) && r.value.toLowerCase() === 'aws') providers.add(r.documentId);
  }
  for (const r of records) {
    if (r.key !== 'runtime') continue;
    const resourceRuntime = r.path.length >= 3 && samePath(r.path.slice(-2), ['properties', 'runtime']) && resources.has(r.documentId + '\u0000' + r.path.slice(0, -2).join('\u0000'));
    const samGlobal = sam.has(r.documentId) && samePath(r.path, ['globals', 'function', 'runtime']);
    const serverless = providers.has(r.documentId) && (samePath(r.path, ['provider', 'runtime']) || (r.path.length === 3 && r.path[0] === 'functions' && r.path[2] === 'runtime'));
    if (resourceRuntime || samGlobal || serverless) { const id = runtimeId(r.value); if (id) found.add(id); }
  }
}
function jsonLambdaRuntimes(c, found) {
  const stripped = c.trim(); if (stripped.includes('\n') || stripped.length > 1048576 || stripped[0] !== '{') return;
  let document; try { document = JSON.parse(stripped); } catch (e) { return; }
  if (!document || Array.isArray(document) || typeof document !== 'object') return;
  const resources = document.Resources;
  if (resources && typeof resources === 'object' && !Array.isArray(resources)) for (const key in resources) {
    const resource = resources[key], type = resource && resource.Type, properties = resource && resource.Properties;
    if (!/^AWS::(?:Lambda|Serverless)::Function$/i.test(String(type || '')) || !properties || typeof properties !== 'object') continue;
    const id = runtimeId(properties.Runtime); if (id) found.add(id);
  }
  const transforms = Array.isArray(document.Transform) ? document.Transform : [document.Transform];
  const globals = document.Globals && document.Globals.Function;
  if (transforms.some((item) => typeof item === 'string' && item.toLowerCase().startsWith('aws::serverless-')) && globals && typeof globals === 'object') {
    const id = runtimeId(globals.Runtime); if (id) found.add(id);
  }
}
function hclCodeLines(c) {
  const output = []; let block = false, heredoc = null;
  for (const original of c.split(/\r?\n/)) {
    if (heredoc) { const candidate = heredoc[1] ? original.trim() : original; if (candidate === heredoc[0]) heredoc = null; output.push([original, ' '.repeat(original.length)]); continue; }
    const visible = [...original]; let quote = null, escaped = false, i = 0;
    while (i < original.length) {
      const ch = original[i], pair = original.slice(i, i + 2);
      if (block) { visible[i] = ' '; if (pair === '*/') { visible[i + 1] = ' '; block = false; i += 2; continue; } i++; continue; }
      if (quote) { visible[i] = ' '; if (escaped) escaped = false; else if (ch === '\\') escaped = true; else if (ch === quote) quote = null; i++; continue; }
      if (pair === '/*') { visible[i] = visible[i + 1] = ' '; block = true; i += 2; continue; }
      if (pair === '//' || ch === '#') { for (let j = i; j < visible.length; j++) visible[j] = ' '; break; }
      if (ch === '"' || ch === "'") { visible[i] = ' '; quote = ch; }
      i++;
    }
    const code = visible.join(''), marker = code.match(/<<(-?)([A-Za-z_][A-Za-z0-9_]*)/);
    if (marker) heredoc = [marker[2], marker[1] === '-'];
    output.push([original, code]);
  }
  return output;
}
function terraformLambdaRuntimes(c, found) {
  let inside = false, depth = 0, structuralEvents = 0;
  const declaration = /\bresource\s+["']aws_lambda_function["']\s+["'][^"']+["']\s*\{/i;
  for (const pair of hclCodeLines(c)) {
    const original = pair[0], code = pair[1], declarationMatch = inside ? null : original.match(declaration);
    const visibleResource = inside ? -1 : code.search(/\bresource\s+/i);
    const resource = declarationMatch && declarationMatch.index === visibleResource ? declarationMatch : null;
    if (resource) { inside = true; depth = 0; }
    if (!inside) continue;
    let position = resource ? resource.index : 0;
    while (position < code.length) {
      const character = code[position];
      if (character === '{') { depth++; structuralEvents++; }
      else if (character === '}') { depth--; structuralEvents++; }
      else if (depth === 1 && code.slice(position, position + 7).toLowerCase() === 'runtime') {
        const key = code.slice(position).match(/^\bruntime\b\s*=/i);
        if (!key) { position++; continue; }
        const runtime = original.slice(position).match(/^\bruntime\b\s*=\s*["']?([^"'\s}]+)/i), id = runtime && runtimeId(runtime[1]);
        if (id) found.add(id); position += key[0].length; structuralEvents++;
        if (structuralEvents > 100000) return;
        continue;
      }
      if (structuralEvents > 100000) return;
      if (depth <= 0 && character === '}') { inside = false; break; }
      position++;
    }
  }
}
function explicitLambdaRuntimes(c, found) {
  const importedRuntime = /(?:aws-cdk-lib|@aws-cdk)\/aws-lambda|from\s+aws_cdk\.aws_lambda\s+import[^\n]*\bRuntime\b|software\.amazon\.awscdk\.services\.lambda\.Runtime|Amazon\.CDK\.AWS\.Lambda/i.test(c);
  for (const line of c.split(/\r?\n/)) {
    const cli = line.match(/\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)["']?([^"'\s]+)/i); const cliId = cli && runtimeId(cli[1]); if (cliId) found.add(cliId);
    const qualified = line.match(/\bruntime\b\s*[:=(]\s*(?:aws_)?_?lambda\.(Runtime\.[A-Z0-9_]+)/i);
    const imported = importedRuntime && line.match(/\bruntime\b\s*[:=(]\s*(Runtime\.[A-Z0-9_]+)/i);
    const cdk = qualified || imported; const match = cdk && cdk[1].match(CDK_VALUE_RE); const id = match && cdkId(match[1], match[2], match[3]); if (id) found.add(id);
  }
}
function scanIaC(file, c) {
  const f = new Set(), out = [];
  yamlLambdaRuntimes(c, f);
  jsonLambdaRuntimes(c, f);
  terraformLambdaRuntimes(c, f);
  explicitLambdaRuntimes(c, f);
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
    '<p class="scan-door">' + n + ' risk' + (n === 1 ? '' : 's') + ' found. Want them fixed and deployed? Fixed-scope projects from US$7,500. <a href="' + STUDIO_DOOR_URL + '">Describe the upgrade &rarr;</a></p>' +
    '<table class="scan-tbl"><thead><tr><th>Severity</th><th>What</th><th>File</th><th>Deadline / fix</th><th>Detail</th></tr></thead><tbody>' + rows + '</tbody></table>' +
    '<div class="convert-callout"><h3>Need full-repo CAB evidence &amp; codemods without uploading source?</h3><p>Download the <strong>$79 Offline Migration &amp; Audit Toolkit</strong> (instant ZIP via Stripe · stdlib-only local scanner + Jira CSV + Python 3.12/3.13 &amp; AWS SDK v3 codemods + AL2023 Dockerfiles · US buyers only).</p><a class="btn-primary" href="https://buy.stripe.com/9B66oH5s2cFy2l51oE87K0C">Buy $79 Offline Toolkit &rarr;</a> &nbsp;<a class="btn-outline" href="' + SITE_BASE + '/toolkit/">Specs &amp; sample</a> &nbsp;<a class="scan-cta" href="' + auditLink(deadline, kit) + '">See the one-repository evidence report ($299) &rarr;</a></div>' +
    '<p class="scan-interest"><a href="' + INTEREST_URL + '" target="_blank" rel="noopener">Would this report be worth $299? Record qualified public interest on GitHub.</a><br><small>No order or waitlist. Do not disclose project details, code, secrets, company information, or personal data.</small></p>';
}
const dz = $('#dz'), fi = $('#fi'); let acc = [];
function scanDone(fileCount) { try { if (window.umami && typeof window.umami.track === 'function') window.umami.track('scan'); if (typeof window.eolkitsTrack === 'function') window.eolkitsTrack('scan_completed', { sku: 'audit', meta: { finding_count: acc.length, file_count: fileCount } }); } catch (e) {} }
function handle(files) { acc = []; const arr = [...files]; let pending = arr.length; if (!pending) return; arr.forEach((file) => { const r = new FileReader(); r.onload = () => { try { acc = acc.concat(scanFile(file.name, r.result)); } catch (e) {} if (--pending === 0) { render(acc); scanDone(arr.length); } }; r.onerror = () => { if (--pending === 0) { render(acc); scanDone(arr.length); } }; r.readAsText(file); }); }
dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', (e) => { e.preventDefault(); dz.classList.remove('over'); handle(e.dataTransfer.files); });
dz.addEventListener('click', () => fi.click());
fi.addEventListener('change', () => handle(fi.files));
const SAMPLE_DEMO = [
  '# ============================================================',
  '# EOLKITS DEMO SAMPLE — fictional project, labelled, safe to scan',
  '# ============================================================',
  "AWSTemplateFormatVersion: '2010-09-09'",
  'Transform: AWS::Serverless-2016-10-31',
  'Description: Fictional EOLkits demo stack (not a real project)',
  '',
  'Globals:',
  '  Function:',
  '    Runtime: nodejs18.x',
  '    MemorySize: 256',
  '',
  'Resources:',
  '  OrdersApi:',
  '    Type: AWS::Serverless::Function',
  '    Properties:',
  '      CodeUri: src/orders/',
  '      Handler: app.handler',
  '      Runtime: nodejs18.x'
].join('\n');
const sampleBtn = $('#sampleBtn');
if (sampleBtn) sampleBtn.addEventListener('click', () => {
  acc = scanFile('demo-template.yaml', SAMPLE_DEMO);
  render(acc);
  scanDone(1);
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
        '<meta name="description" content="Drop SAM/CDK/Terraform/Serverless, package.json, or requirements files to find tracked AWS Lambda runtime and native-dependency migration risks. File names and contents are not uploaded; bounded aggregate counts may be sent.">\n'
        f'<link rel="canonical" href="{SITE_URL}/scan/">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<script defer src="/track.js"></script>\n' + _og_image_meta() + "<style>"
        "#dz{border:2px dashed var(--border);border-radius:12px;padding:2.5rem 1rem;text-align:center;cursor:pointer;background:var(--bg-card);color:var(--ink)}"
        "#dz.over{border-color:var(--accent);background:rgba(255,92,42,0.08)}"
        ".scan-tbl{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.88rem}"
        ".scan-tbl th,.scan-tbl td{border-bottom:1px solid var(--border);padding:.55rem;text-align:left;vertical-align:top}"
        ".sev-critical td:first-child{color:#ff6b6b;font-weight:700}"
        ".sev-high td:first-child{color:var(--accent);font-weight:700}"
        ".sev-medium td:first-child{color:#eab308;font-weight:700}"
        ".sev-low td:first-child{color:#38bdf8}"
        ".scan-cta{display:inline-block;margin-top:.5rem;padding:.75rem 1.15rem;background:var(--bg);border:1px solid var(--border);color:var(--ink);border-radius:8px;text-decoration:none;font-weight:600}"
        ".scan-interest{margin-top:1rem;padding:1rem;background:var(--bg-card);border:1px solid var(--border);border-radius:8px}"
        ".scan-interest a{color:var(--accent);text-decoration:underline}"
        ".scan-ok{padding:1rem;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.35);border-radius:8px}"
        ".scan-count{font-weight:600;margin-top:1rem}.privacy{color:#4ade80;font-weight:600}"
        "</style>\n</head>\n"
    )
    body = (
        '<body class="container article">\n'
        '<a href="/" class="brand"><span class="brand-mark">&gt;</span> EOLkits</a>\n'
        "<h1>Free AWS runtime &amp; dependency EOL scanner</h1>\n"
        "<p>Drop your infrastructure and dependency files below to find deprecated AWS Lambda runtimes and the "
        "native Node.js&nbsp;24 / Python&nbsp;3.12 dependency risks that can block a migration. "
        '<span class="privacy">File names and contents stay in your browser.</span> '
        "If the verified v2 telemetry service is available, the page sends only file and finding counts—never file names or contents.</p>\n"
        '<div id="dz"><strong>Drop files here</strong><br><small>or click to choose — template.yaml, serverless.yml, *.tf, CDK *.ts, package.json, requirements.txt, pyproject.toml</small>'
        '<input id="fi" type="file" multiple accept=".yaml,.yml,.json,.tf,.ts,.js,.mjs,.txt,.toml" style="display:none"></div>\n'
        '<p><button id="sampleBtn" type="button">Load a sample template (labelled demo)</button></p>\n'
        '<div id="results"></div>\n'
        '<p id="report-scope-link">Need a shareable repository report? <a href="/toolkit/">Download the $79 Offline Toolkit (zero code upload)</a> or <a href="/audit/">Inspect the sample and $299 report scope</a>. A scan with no matches is not proof that your infrastructure is free of deprecation risk.</p>\n'
        "<h2>What it checks</h2>\n<ul>"
        "<li><strong>Lambda runtimes</strong> in SAM, CloudFormation, CDK, Terraform and Serverless Framework — flagged against AWS&rsquo;s published deprecation dates.</li>"
        "<li><strong>Node native dependencies</strong> (sharp, bcrypt, better-sqlite3&hellip;) that need a version bump, rebuild, or replacement before a Node&nbsp;24 migration.</li>"
        "<li><strong>Python wheels</strong> (numpy, pandas, cryptography&hellip;) that need a bump for a Python&nbsp;3.12 runtime.</li>"
        "</ul>\n"
        '<p>Hit a specific error message? See <a href="/fix/">common AWS migration error fixes &rarr;</a></p>\n'
        "<p><small>This free scan covers configured high-impact source patterns. The paid report accepts one repository ZIP or source file and adds exact line evidence, configured references, a remediation order, and explicit limitations. It does not query your AWS account.</small></p>\n"
        + studio_block("eolkits-scan")
    )
    tail = "</body>\n</html>\n"
    return (
        head
        + body
        + "<script>\nconst SITE_BASE = "
        + json.dumps(SITE_URL.rstrip("/"))
        + ";\nconst INTEREST_URL = "
        + json.dumps(AUDIT_INTEREST_URL)
        + ";\nconst STUDIO_DOOR_URL = "
        + json.dumps(STUDIO_MIGRATION_URL + "?from=eolkits-scan")
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


def build_error_pages(fixes, deprecations, _full_pricing):
    """M2: deterministic /fix/<slug> pages keyed on REAL, paste-able error strings.
    Each entry carries a source for its core claim and cross-links the bounded
    scanner, related milestone, and capability-gated Audit path."""
    import html as _h

    if not fixes:
        return {}
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
            + "<style>.fix-err{background:#090c12;border:1px solid var(--border);color:#e2e8f0;padding:.9rem 1rem;border-radius:8px;overflow-x:auto;font-size:.85rem}"
            ".fix-steps li{margin:.35rem 0}.fix-cta{display:inline-block;margin-top:.75rem;padding:.7rem 1.15rem;background:var(--bg);border:1px solid var(--border);color:var(--ink);border-radius:8px;text-decoration:none;font-weight:600}"
            ".fix-rel{background:var(--bg-card);border:1px solid var(--accent);padding:.65rem .9rem;border-radius:8px}.fix-rel a{color:var(--accent);text-decoration:underline}</style>\n"
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
            + '<div class="convert-callout"><h2>Scan &amp; codemod every occurrence locally ($79)</h2>'
            + "<p>Fixing one function by hand rarely clears the whole stack. Download the <strong>$79 Offline Migration &amp; Audit Toolkit</strong> to run air-gapped repo/IaC audits, Python 3.12/3.13 &amp; AWS SDK v3 codemods, AL2023 native wheel Dockerfiles, and canary rollback templates with zero source upload (US buyers only · 30-day full refund policy).</p>"
            + '<p><a class="btn-primary" href="https://buy.stripe.com/9B66oH5s2cFy2l51oE87K0C">Buy $79 Offline Toolkit (Instant Download) &rarr;</a> &nbsp;<a class="btn-outline" href="/toolkit/">Full specs &amp; sample</a></p></div>\n'
            + "<h2>Check configured patterns in your project</h2>\n"
            + '<p>The free <a href="/scan/">EOLkits scanner</a> processes files in your browser and flags selected related patterns in supported IaC and dependency files. File names and contents are not uploaded; bounded aggregate file and finding counts may be sent. It is not a complete source or AWS-account scan.</p>\n'
            + '<p>Prefer a 10-second check? Paste your config into the <a href="/eol-checker/">free AWS EOL checker</a>. Pasted input is not uploaded; bounded first-party usage events may be sent.</p>\n'
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
            + '">Inspect the $299 report sample and availability &rarr;</a></p>\n'
            + studio_block("eolkits-fix")
            + '<footer style="margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--border);font-size:.82rem;color:var(--ink-muted)">Toledo Technologies LLC · 2389 Main St. STE 100, Glastonbury, CT 06033 · <a href="mailto:hello@toledotechnologies.com">hello@toledotechnologies.com</a> · <a href="/about/">About</a> · <a href="/legal/terms.html">Terms</a> · <a href="/legal/privacy.html">Privacy</a></footer>\n'
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
        + studio_block("eolkits-fix")
        + "</body>\n</html>\n"
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
        "toolkit/index.html": build_toolkit_page(pricing),
        "toolkit/sample/index.html": build_toolkit_sample_page(),
        "about/index.html": build_about_page(pricing),
        "changelog/index.html": build_changelog_page(),
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
        "podfreeze/index.html": build_podfreeze_page(),
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
        rendered = normalize_project_links(inject_privacy_meta(content))
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
                normalize_generated_text(normalize_project_links(inject_privacy_meta(html_doc))),
                encoding="utf-8",
            )
            print(f"Rendered: legal/{name}.html")

    print("=" * 40)
    print("Build complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
