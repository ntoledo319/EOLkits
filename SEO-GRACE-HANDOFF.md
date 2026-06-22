# EOLkits — Deprecation-SEO Renderer & GRACE Deployment Handoff

_Last updated: 2026-06-08. Scope: the deterministic deprecation-SEO renderer
(`apps/web/`) and its **live deployment on GRACE** (`https://eolkits.com`). This
document explains what GRACE is, how the EOLkits site runs on it, the defect
cluster that was breaking the live site, exactly what was fixed, what remains,
and the precise operator steps to ship the fix to GRACE._

> **One-line status:** The web build was still wired for GitHub Pages
> (`ntoledo319.github.io/EOLkits`) while production had moved to **GRACE at the
> root domain `eolkits.com`**. That mismatch was silently breaking the entire
> live SEO site (wrong canonicals, 404 stylesheet, 404 internal links, wrong
> sitemap/robots/llms, raw-markdown legal pages). All of that is **fixed in the
> working tree and validated** — it goes live the moment `docs/` is synced to the
> GRACE static web root (see **§7 Deploy to GRACE**).

---

## 1. What is GRACE?

**GRACE** is the self-hosted VPS + control-plane that now runs EOLkits in
production. It replaced the original Cloudflare stack (Workers/KV/R2/Queues),
which is now **legacy/reference only** (`apps/worker/`).

GRACE has three moving parts that matter here:

| Part | What it is |
|---|---|
| **Host VPS** | A single Ubuntu box running **Docker** + **host Caddy** (TLS, reverse proxy, static file serving). |
| **Control plane** | `https://graceai.love` — GRACE's API/dashboard. Lists and controls "satellites" via `GET /api/v1/satellites`. |
| **Satellite agent** | A host-side Python agent that GRACE drives to `status` / `logs` / `restart` / `redeploy` each satellite. Actions are allow-listed per satellite. |

A **satellite** is one deployable unit GRACE knows about. EOLkits runs as **two
satellites that share the `eolkits.com` domain**:

| Satellite | Kind | Serves | Backed by |
|---|---|---|---|
| **`eolkits`** | `static` | The public site (everything the SEO renderer produces) | Host Caddy `file_server` from **`/var/www/eolkits`** |
| **`eolkits-api`** | `compose` | Paid fulfillment: Stripe/GitHub webhooks, uploads, audit reports, Migration-Pack jobs, partner/support endpoints | Docker Compose project `eolkits-api` (FastAPI, `apps/grace-api/`) on `127.0.0.1:8120` |

### 1.1 How a request to `eolkits.com` is routed

Host Caddy owns the `eolkits.com, www.eolkits.com` server block. It splits
traffic by path (see `deploy/grace/update_caddy_samehost.py`, which is the
canonical generator of this block):

```caddy
eolkits.com, www.eolkits.com {
    encode zstd gzip

    # Paid API paths -> the eolkits-api compose service on localhost
    @eolkitsApi path /health /api/* /upload/* /webhook/* /pack/install \
                     /support/* /partners/signup /partners/verify/* /partners/*/audit
    handle @eolkitsApi {
        reverse_proxy 127.0.0.1:8120
    }

    # Everything else -> the static SEO site
    handle {
        root * /var/www/eolkits
        file_server
    }
}
```

**Consequence that drove every bug in this handoff:** every URL that is *not* one
of the API paths above — `/`, `/migrate/*`, `/audit/`, `/pack/`, `/style.css`,
`/sitemap.xml`, `/robots.txt`, `/llms.txt`, `/legal/*`, `/vs/*` — is served as a
**static file from `/var/www/eolkits` at the domain root**. There is **no
`/EOLkits/` path prefix** on GRACE (that prefix only ever existed on GitHub
Pages' project-site URL). So a build that emits `/EOLkits/style.css` or a
`github.io` canonical is simply wrong for GRACE.

### 1.2 State model (no Cloudflare)

The `eolkits-api` satellite keeps all state on the VPS, not in Cloudflare:

- **Uploads + generated report PDFs** → local filesystem volume (`/data/eolkits`, Docker volume `eolkits_api_data`). Replaces R2.
- **Idempotency keys, jobs, verification records, license keys** → **SQLite** under the data dir. Replaces KV.
- **Job execution** → FastAPI `BackgroundTasks` + an inline runner (`EOLKITS_INLINE_RUNNER=1`). Replaces Queues.

`GET /health` reflects this: `{"ok":true,"env":"production","storage":"filesystem","database":"sqlite","runner":"inline"}` (verified live).

### 1.3 The GRACE files in this repo

Everything needed to (re)wire EOLkits on GRACE lives in **`deploy/grace/`**:

| File | Purpose |
|---|---|
| `README.md` | The API-satellite apply runbook. |
| `docker-compose.eolkits-api.yml` | Compose definition for `eolkits-api` (port `127.0.0.1:8120→8080`, env from `.env.production`, data volume). |
| `Caddyfile.eolkits-api.block` | The `@eolkitsApi` reverse-proxy block to insert into the live Caddyfile. |
| `update_caddy_samehost.py` | Idempotent installer that rewrites the `eolkits.com` Caddy block to the same-host shape in §1.1. |
| `satellites.eolkits-api.yaml` | The satellite manifest entry to append to `grace-backend/config/satellites.yaml`. |
| `satellite-agent.eolkits-api.py.snippet` | The `SATELLITES` dict entry for the host satellite agent (allow-listed actions). |

> Note: these files cover the **API** satellite. The **static** `eolkits`
> satellite (`/var/www/eolkits`) predates them and is operator-managed — its
> deploy step is **not yet scripted in the repo** (see §7.1, the "deploy gap").

---

## 2. What "the deprecation-SEO renderer" is

A **deterministic, zero-LLM static site generator**. Source of truth:

- **`rules/public/deprecations.yml`** — every tracked AWS deprecation (name, service, deadline `date`, `severity`, `kit`, breaking changes, and a primary `url` citation).
- **`pricing.yml`** — SKUs, prices, and Stripe payment links per tier.

Pipeline: **`apps/web/build.py`** + Jinja templates in **`apps/web/templates/`** →
writes **`docs/`**, which is exactly what `/var/www/eolkits` should contain.

What it emits, per build:
- One `/migrate/<slug>/` guide per deprecation (TechArticle + BreadcrumbList + FAQPage JSON-LD, OG/Twitter, cited facts, deterministic urgency + surge pricing computed from the deadline date).
- A `/migrate/` hub, `/audit/`, `/pack/`, `/license/`, `/partners/`, `/status/`, `/blog/`, `/vs/*` comparison pages, the home page.
- `sitemap.xml`, `robots.txt`, `llms.txt` (the AI-search citation surface), `deprecations.ics`, and rendered `legal/*.html`.

**Invariant:** output must be **byte-for-byte deterministic across rebuilds on the
same UTC day** (the only varying value is the date-granular build date), and
**every fact must carry its `source_url`**. No model output is ever embedded.
Determinism is now enforced by `apps/web/test_determinism.py` (build twice → equal),
which also closed a prior gap where the build leaked sub-second wall-clock
timestamps into migrate pages / RSS / ICS / the status seed.

**Regeneration cadence:** `.github/workflows/seo-pages.yml` rebuilds nightly and
commits `docs/`. `.github/workflows/deploy-pages.yml` publishes `docs/` to the
**legacy GitHub Pages mirror** on push to `main`.

---

## 3. The defect cluster (what was breaking the live site)

Root cause: **the GRACE migration updated the worker (`wrangler.toml` → `eolkits-*`)
but never updated the web build.** `apps/web/build.py` still hard-coded GitHub
Pages, so the live GRACE site was built with the wrong domain and a `/EOLkits`
path prefix that does not exist on GRACE.

All of the following were **confirmed against the live site** (`curl https://eolkits.com/...`):

| # | Defect | Live impact |
|---|---|---|
| **A** | `SITE_URL = ntoledo319.github.io/EOLkits`; canonical/OG/JSON-LD URLs all pointed there | Google told the real page lives on **another domain** → de-indexes/duplicates `eolkits.com`. The single worst SEO defect. |
| **B** | `PROJECT_BASE_PATH="/EOLkits"` + `normalize_project_links()` prepended `/EOLkits` to every root-relative link | `/EOLkits/style.css` → **404** (site rendered **unstyled**); `/EOLkits/migrate/...`, nav, related links all **404**. |
| **C** | `sitemap.xml.j2` **hard-coded** github.io and ignored `site_url`; missing `vs/`, `license/`, `partners/`, `blog/`; had a `/#pricing` fragment; legal URLs 404'd | Crawlers sent to the wrong host and couldn't discover real pages. |
| **D/E** | `robots.txt` `Sitemap:` and all of `llms.txt` pointed to github.io | Search + AI engines (the llms.txt product surface) cited the legacy host. |
| **F** | Legal pages were **raw Markdown** `shutil.copy`'d to `.html` (no `<title>`/meta/canonical); footer/checkout linked extensionless `/legal/terms` which **404'd** | Broken, unindexable legal pages; dead Terms/Privacy links sitewide. |
| **G** | `build_vs_page()` canonical hard-coded github.io (bypassed `site_url`) | Comparison pages canonicalized to the legacy host even after A. |
| **H** | `search-console.yml` + `status-synth.yml` referenced the **old repo name `/Rupture`** on github.io | Wrong sitemap submitted to Google; status probes hit the wrong host. |
| **I** | `pricing.yml` `urls:` block → github.io | Stale source-of-truth (consumed by worker/checkout/emails). |

---

## 4. What was fixed (this change set)

All changes are in the **working tree only — not committed/pushed** (left for your review).

Source files changed: `apps/web/build.py`, `apps/web/templates/sitemap.xml.j2`,
`apps/web/templates/migrate.html.j2`, `pricing.yml`,
`.github/workflows/search-console.yml`, `.github/workflows/status-synth.yml`,
plus the **31 regenerated files under `docs/`**.

1. **Keystone — domain is now correct and env-configurable** (`build.py`):
   ```python
   PROJECT_BASE_PATH = os.environ.get("EOLKITS_BASE_PATH", "")           # was "/EOLkits"
   SITE_URL          = os.environ.get("EOLKITS_SITE_URL", "https://eolkits.com")  # was github.io
   ```
   `normalize_project_links()` is now a **no-op when the base path is empty**, so
   root-relative links stay root-relative on GRACE. This single change fixes
   defects **A, B, D, E** and most of **C** (canonical, OG, JSON-LD, robots, llms,
   and every internal link).
   - **Reversible:** a GitHub Pages project build is still possible via
     `EOLKITS_BASE_PATH=/EOLkits EOLKITS_SITE_URL=https://ntoledo319.github.io/EOLkits python3 apps/web/build.py`.
   - `API_URL` was already `https://eolkits.com` — left unchanged.

2. **Sitemap rewritten** (`sitemap.xml.j2` + `build_sitemap()`): uses `{{ site_url }}`
   at root, adds `vs/` + each comparison page, `license/`, `partners/`, `blog/`,
   `status/`, and the four real `legal/*.html` URLs; dropped the invalid
   `/#pricing` fragment. (Defect C.)

3. **`vs/` canonical** now uses `SITE_URL` (`build_vs_page`). (Defect G.)

4. **Legal pages are now real HTML** — added a deterministic, stdlib-only
   `md_to_html()` (headings/bold/links/lists/paragraphs) with proper
   `<title>`/meta-description/canonical/stylesheet; footer/checkout links updated
   to `/legal/*.html`. (Defect F.)

5. **`pricing.yml` `urls:`** → `https://eolkits.com/...`. (Defect I.)

6. **CI workflows** retargeted off the old `/Rupture` github.io path to
   `eolkits.com` (`search-console.yml` GSC property + sitemap + pings;
   `status-synth.yml` `PAGES_URL` default). (Defect H.)

### 4.1 Validation performed (all green)

```
python3 apps/web/build.py        # exit 0
python3 feed/publish.py          # exit 0
grep -rn "ntoledo319.github.io" docs/      -> 0
grep -rn 'href="/EOLkits' docs/            -> 0
canonical (migrate) -> https://eolkits.com/migrate/amazon-linux-2-eol/
canonical (vs)      -> https://eolkits.com/vs/herodevs/
robots.txt Sitemap  -> https://eolkits.com/sitemap.xml
sitemap.xml         -> 22 eolkits.com <loc>, 0 github.io
legal/*.html        -> real HTML w/ <title> + canonical (terms, privacy, dpa, SECURITY)
JSON-LD             -> TechArticle + BreadcrumbList + FAQPage all parse valid
determinism         -> double-build diff = 0 non-timestamp content lines
```

---

## 5. Deferred / not yet done

The audit ran as a multi-agent workflow; **2 of 6 dimensions completed**
(`domain-canonical`, `seo-structured-data` — which cover all critical/high bugs
above) before the run hit the **API session limit**. The other 4 dimensions had
started surfacing **lower-severity** items. **Resolved** (2026-06-21):

- ✅ **Surge date/countdown mismatch:** the day count ran to the nearest
  enforcement date (block-update) while the headline/countdown/facts interpolated
  the raw `date` (block-create), which is often already past. `nearest_enforcement()`
  now returns `(days, date)` and every date-paired display uses that date; the
  checkout link also carries it so the charged surge price matches what's shown.
  Day math is date-only (no wall-clock-hour dependence).
- ✅ **`apps/web/templates/vs.html.j2` dead template** — deleted (vs pages are
  built by `build_vs_page()` in Python).
- ✅ **`og:image`/`twitter:image`** — added to migrate/fix/scan; `build.py` now
  emits a deterministic `docs/og-default.png` (1200×630). _(Placeholder solid-color
  card; swap for designed art without touching the meta tags.)_
- ✅ **Meta descriptions** on migrate pages capped to ≤158 chars on a word boundary.

**Still deferred** (genuinely lower value, untouched):

- **a11y/contrast** on `severity-badge`/banner; **conversion/content** polish.
- **Higher-value schema**: `Organization` + `WebSite` on the home page,
  `Product`/`Offer` for the paid tiers.
- **`ics.yml`** still emits `/Rupture` + the old product name in its standalone
  generator (the `build.py` `.ics` output is already correct).

To finish these autonomously, **resume the stopped workflow after the limit
resets** — completed agents return from cache, only the 4 failed dimensions +
plan/fix/validate re-run live:

```
Workflow({ scriptPath: ".../workflows/scripts/eolkits-seo-grace-audit-fix-wf_0d818950-7b5.js",
           resumeFromRunId: "wf_0d818950-7b5" })
```

---

## 6. Open decisions (need an owner)

1. **GitHub Pages mirror.** `deploy-pages.yml` still publishes `docs/` to
   `ntoledo319.github.io/EOLkits`. With the fix, that mirror now correctly
   canonicalizes to `eolkits.com` (so it consolidates SEO rather than competing),
   but its internal links won't resolve under the `/EOLkits` project path. Cleanest
   long-term: **retire `deploy-pages.yml`** (mirror GRACE only) **or** point its
   GH Pages custom domain at a non-conflicting host. Not auto-changed — it touches
   external publishing.
2. **`pricing.yml` `urls:` consumers.** The web build does not read this block,
   but `apps/worker/*` (legacy) and Stripe setup scripts might. Grep before relying
   on it in any still-live consumer.

---

## 7. Deploy to GRACE (operator steps)

> **Prerequisite:** SSH access to the GRACE VPS as the deploy user (`ubuntu`),
> and (for satellite registration) access to the GRACE backend host.

### 7.1 Ship the fixed static site — **this is what makes the fixes go live** ⭐

The static `eolkits` satellite serves **`/var/www/eolkits`**. The fixed pages are
in this repo's `docs/`. There is currently **no repo automation** for this sync
(the "deploy gap"). Do it explicitly:

```bash
# 0) From your workstation, rebuild to be safe (targets eolkits.com by default):
cd /path/to/Rupture
python3 apps/web/build.py && python3 feed/publish.py

# 1) Sync docs/ -> the GRACE static web root. --delete removes stale files
#    (e.g. the old raw-markdown legal copies). Dry-run first:
rsync -avn --delete docs/ ubuntu@<grace-host>:/var/www/eolkits/    # preview
rsync -av  --delete docs/ ubuntu@<grace-host>:/var/www/eolkits/    # apply

# 2) Caddy serves files directly; no reload needed for content changes.
```

> If you prefer the site be deployed from a server-side checkout, have GRACE pull
> the repo and run the same rebuild, then point the static satellite's web root at
> the produced `docs/`. Either way the bytes in `/var/www/eolkits` must be the
> fixed `docs/`.

### 7.2 Verify the live static site

```bash
curl -sI https://eolkits.com/style.css | head -1                       # expect 200 (was 404)
curl -s  https://eolkits.com/migrate/ | grep -o 'rel="canonical"[^>]*' # expect eolkits.com
curl -sI https://eolkits.com/migrate/                                  # 200
curl -sI https://eolkits.com/legal/terms.html                         # 200, real HTML
curl -s  https://eolkits.com/robots.txt                               # Sitemap: https://eolkits.com/sitemap.xml
curl -s  https://eolkits.com/sitemap.xml | grep -c eolkits.com         # 22, and: grep -c github.io == 0
curl -s  https://eolkits.com/llms.txt | grep -m1 migrate/             # eolkits.com link
```

### 7.3 The API satellite (`eolkits-api`) — already live; redeploy only if needed

Per `deploy/grace/README.md`:

```bash
# On the VPS, in a SEPARATE site root (do NOT touch /var/www/eolkits):
sudo mkdir -p /home/ubuntu/sites/eolkits-api
sudo rsync -a --delete /path/to/Rupture/ /home/ubuntu/sites/eolkits-api/
cd /home/ubuntu/sites/eolkits-api
cp deploy/grace/docker-compose.eolkits-api.yml docker-compose.yml
# Ensure .env.production exists (STRIPE_KEY, STRIPE_WEBHOOK_SECRET, GITHUB_APP_ID,
# GITHUB_APP_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET, RESEND_API_KEY, PUBLIC_SITE_URL,
# PUBLIC_API_URL=https://eolkits.com, EOLKITS_API_PORT=8120)
sudo docker compose -p eolkits-api --env-file .env.production up -d --build
curl -sf http://127.0.0.1:8120/health
```

### 7.4 Caddy same-host routing (one-time; already applied in prod)

```bash
sudo python3 deploy/grace/update_caddy_samehost.py   # idempotent; rewrites the eolkits.com block
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
curl -sf https://eolkits.com/health                  # API path -> 200 JSON
```

### 7.5 Satellite registration (one-time; already applied in prod)

```bash
# Append deploy/grace/satellites.eolkits-api.yaml to grace-backend/config/satellites.yaml
# Add deploy/grace/satellite-agent.eolkits-api.py.snippet to the host agent SATELLITES dict
# Restart the GRACE backend + satellite agent (snapshot-first), then:
curl -sf https://graceai.love/api/v1/satellites      # expect BOTH: eolkits (static) + eolkits-api (compose)
```

### 7.6 Rollback (static site)

The static deploy is just files. To roll back, re-sync the previous `docs/`
(e.g. `git checkout <prev> -- docs && rsync ... /var/www/eolkits/`). Take a
snapshot/tarball of `/var/www/eolkits` before §7.1 if you want a fast revert:
`sudo tar czf /tmp/eolkits-webroot-$(date +%F).tgz -C /var/www eolkits`.

---

## 8. Quick reference

| Thing | Value |
|---|---|
| Production domain (canonical) | `https://eolkits.com` (GRACE, served at **root**) |
| Static web root | `/var/www/eolkits` (satellite `eolkits`) |
| API service | `127.0.0.1:8120` (compose `eolkits-api`, `apps/grace-api/`) |
| API path allow-list | `/health /api/* /upload/* /webhook/* /pack/install /support/* /partners/*` |
| Build (GRACE default) | `python3 apps/web/build.py` |
| Build (legacy GH Pages) | `EOLKITS_BASE_PATH=/EOLkits EOLKITS_SITE_URL=https://ntoledo319.github.io/EOLkits python3 apps/web/build.py` |
| Control plane | `https://graceai.love/api/v1/satellites` |
| Determinism gate | build twice → only timestamp lines may differ |
| Legacy / do-not-deploy | `apps/worker/` (Cloudflare) |
```
