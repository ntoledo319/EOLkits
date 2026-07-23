# ASSETS — Audit of every codebase in WORKSPACE_ROOT (Cycle 0, 2026-07-13)

Product: **EOLkits** — a productized AWS end-of-life (EOL) migration service. One product, many sellable
surfaces. Live at **https://eolkits.com** (self-deploying daily from branch `marketing-machine-v2`).
Repo public: `ntoledo319/EOLkits`. All paid tiers have **live Stripe payment links** (see `pricing.yml`).

Verified this cycle by reading manifests + running CLIs/tests directly (not trusting stale README badges).

---

## The product ladder (what a stranger can buy today)
| SKU | Price | Delivery | Rail |
|---|---|---|---|
| CLI (3 kits) | Free (MIT) | `git clone` | — |
| **Audit PDF** | **$299** (→$399 within 30d / $599 within 7d of a deadline) | Email ≤5 min | Stripe link ✅ live |
| **Migration Pack** | **$1,499** | Real PR on customer repo; auto-refund if CI fails | Stripe link ✅ live |
| Drift Watch | $19/mo | Weekly re-scan + delta PDF | Stripe link ✅ live |
| Org License | $14,999/yr | License key email | Stripe link ✅ live |

---

## Cluster 1 — The kits (free CLIs; the top of the funnel and the paid-fulfillment engine)

### `kits/al2023-gate` (Python CLI)
- **What:** Scans an AWS account for Amazon Linux 2 resources and generates Packer templates, Ansible rewrites, cloud-init diffs, and per-service migration runbooks (ASG/EKS/ECS/Beanstalk) to move to AL2023.
- **Completeness:** ✅ 48/48 pytest pass. 6 commands (scan/remap/packer/cloudinit/ansible/runbook). Offline fixtures. CLI runs via `PYTHONPATH=src python3 -m al2023_gate.cli` (verified).
- **Deploy target:** PyPI (not yet published; `pip install -e .` works from source). Repo already public.
- **License:** MIT, zero required deps (boto3 optional, Apache-2.0). No copyleft. Safe to sell/bundle.
- **The one paid capability:** the Packer generator + resource-specific runbooks replace the 4–8h of manual audit/template work AWS consultancies bill day-rate for.
- **Smallest sellable unit:** the $299 Audit PDF (this kit's output, packaged for one account).
- **Note:** AL2 EOL (Jun 30 2026) is **now past** → reframe from countdown to "unpatched CVEs + AWS Extended Support cost." pyproject description still says "before Jun 30, 2026 EOL" (update on PyPI publish).

### `kits/python-pivot` (Python CLI)
- **What:** Finds every Python Lambda, rewrites 3.12 breakages in source + IaC (SAM/CDK/Terraform/Serverless), audits native-wheel compatibility (30+ pkgs), runs a staged canary with CloudWatch-alarm auto-rollback.
- **Completeness:** ✅ 44/44 pytest pass. 6 commands (scan/codemod/audit/iac/deploy/rollback). CLI verified.
- **Deploy target:** PyPI (unpublished). License: MIT, zero required deps. Safe to sell.
- **The one paid capability:** canary deploy that *refuses to run without an alarm ARN* — a safety harness that removes the "3 a.m. pager" risk of a prod runtime upgrade.
- **Smallest sellable unit:** $299 Audit PDF (scan+audit output for one account).
- **Note:** Live urgency = Python 3.10 deprecation Oct 31 2026 (patches stop); block dates Feb 1 / Mar 3 2027.

### `kits/lambda-lifeline` (Node.js ESM CLI)
- **What:** Takes Lambda teams from unknown Node-runtime exposure to Node 22 under a staged canary + alarm rollback; covers code rewrites, native-binary dep audit, CA-cert fixes, IaC patching.
- **Completeness:** ✅ **24/24 tests pass** (fixed this cycle — see DECISIONS). 8 commands. CLI verified.
- **Deploy target:** npm (unpublished). License: MIT; deps `@aws-sdk/*` Apache-2.0. Safe to sell.
- **The one paid capability:** native-binary ABI audit (sharp/bcrypt/better-sqlite3/etc. → exact Node-22 min versions) + alarm-gated canary — the two most common Node-upgrade failure modes, eliminated.
- **Smallest sellable unit:** $299 Audit PDF.
- **Note:** Dates were **stale/wrong (Sep 30 2026)** and are now **corrected to the AWS-authoritative Feb 1 / Mar 3 2027** block window across `src/scan`, banner, README, tests (see DECISIONS — a §2.5 truth fix).
- **Note (2026-07-15):** README's "paid tiers" (Solo $499/Team $999/Enterprise $2,499 + a $999/$1,999/$4,997 bundle,
  Slack channel, pairing sessions, on-call, `support@eolkits-kits.dev`) were **fabricated — no such SKU, domain, or
  fulfillment exists.** Replaced with the real Audit PDF ($299) / Migration Pack ($1,499) ladder linking to the live
  eolkits.com Stripe checkout (see DECISIONS D11). Same fix applied to al2023-gate and python-pivot READMEs.

---

## Cluster 2 — Web funnel (SEO/AEO asset; the storefront)
### `apps/web` — deterministic static-site generator (`build.py` + Jinja2 + YAML)
- **What:** ~2,573-line Python SSG that generates the entire eolkits.com: commerce pages, 23 verbatim-error `/fix` pages, 9 `/migrate` deadline pages, `/vs` competitor pages, SVG badges, RSS, sitemap, `llms.txt`, `track.js` pageview beacon.
- **Completeness:** ✅ 4 pytest (byte-deterministic rebuilds, OG validity) + `test_surge.py` (4 assertions, surge-collapse LB-3 fix) all pass (verified). Source of truth = `rules/public/deprecations.yml` + `pricing.yml`.
- **Deploy target:** GRACE VPS (live). Self-deploys daily. Also GitHub Pages-capable.
- **License:** MIT/first-party. Safe.
- **The one paid capability (indirect):** it *converts* — surge-aware pricing, proof-first + guarantee copy; it is the machine that turns a stranger into a $299/$1,499 checkout.
- **Smallest sellable unit:** N/A (it's the funnel, not the product). Verified: `deprecations.yml` dates are **correct** (Node/Python blocks Feb 1 / Mar 3 2027 per AWS) — left unchanged.
- **`launch/distribution/`:** dev.to publisher (12 articles as of 2026-07-23, canonical→eolkits.com), fast-cash Upwork/Fiverr/re:Post playbook, X threads, value-first email kit, video scripts.

---

## Cluster 3 — API + payments (the money + delivery engine)
### `apps/grace-api` (FastAPI, on the GRACE VPS)
- **What:** Accepts Stripe payments for all 5 SKUs and auto-delivers each (audit PDF email; migration PR; license key) ≤5 min, with idempotent webhook handling and CI-failure auto-refund.
- **Completeness:** ✅ 35 tests. Stripe + Resend (email **verified/fixed** in prior work). SQLite + filesystem state. **UNVERIFIED end-to-end:** no real $299 or $1,499 purchase has ever been run (the last un-derisked link).
- **Deploy target:** GRACE VPS (live), reverse-proxied under `/api/* /webhook/* /pack/* …`.
- **License:** MIT/first-party. Safe.
- **The one paid capability:** turns a Stripe checkout into a delivered hash-anchored audit PDF automatically — this is the "sell output" money event.
- **`pricing.yml`:** all Stripe product/price IDs + payment links present and live (test_mode: false).
- **Note (2026-07-16):** `drift_watch` fulfillment (`apps/runner/main.py handle_drift_watch_setup`) is a complete
  no-op stub (no IAM validation, no scan, no delta PDF) — its live self-serve checkout was **pulled from the website**
  this cycle (see DECISIONS D14) since selling it delivered nothing, recurringly.
- **Update (2026-07-19):** `org_license` fulfillment (`_store_license` in `grace-api/app.py`) generated + stored a
  genuine license key but never emailed it to the buyer — **fixed this cycle** (commit `edfba40`, DECISIONS D16):
  now sends the key via the existing Resend `send_email` path (same pattern as audit-PDF delivery), with the
  job-queue's existing retry/dead-letter handling covering send failures. 2 regression tests added (38/38 green).
  Neither `apps/grace-api` nor `apps/runner` deploy on the `git push` auto-deploy path — only `apps/web` does; this
  fix needs an **owner VPS redeploy of `eolkits-api`** to take effect in production (queued, see HUMAN_QUEUE).

---

## Cluster 4 — Ecosystem placements (marketplace-distributed intercepts → funnel to paid)
### `apps/vscode-extension` — **publish-ready this cycle**
- **What:** Local scanner; flags deprecated Lambda runtimes / AL2 AMIs inline in the editor (CFN/Terraform/JS/TS/Python), tree view + report webview, "Get full audit" → eolkits.com/audit (utm-tagged).
- **Completeness:** ✅ Compiles (tsc), packages to a valid 23.9 KB `.vsix` (verified). Publisher id `eolkits`. **This cycle:** added icon + marketplace README + metadata (`pricing:Free`, galleryBanner, keywords), and **corrected wrong Python EOL dates + Node20 message** in `scanner.ts` (§2.5 truth fix). Honest — runs locally, nothing uploaded.
- **Deploy target:** VS Code Marketplace + Open VSX (both free; **NO native paid** — monetization stays on external Stripe). Human-gated on first publish (publisher account + token).
- **The one paid capability:** it's a *placement* — funnels editor users to the $299 audit at the moment they type a deprecated runtime.

### `apps/github-action` (+ root `action.yml`) — listing-ready
- **What:** Composite Action; runs all 3 kits in a caller's CI, posts a Markdown scan report as a PR comment with CTAs to audit/pack. Tags v1/v1.0.0/v1.1.0 exist. `action.yml` at repo root (required for Marketplace).
- **Completeness:** ✅ Ready. Deploy: GitHub Marketplace (free; Actions **cannot charge** — funnel only). Human-gated on web-UI publish + a dedicated public repo (monorepo action can't be listed directly).
- **The one paid capability:** reaches an engineer at peak intent (a CI failure blocking a merge).

### `apps/github-app` — opens the Migration-Pack PR
- **What:** GitHub App that opens the real migration PR on a customer repo (the $1,499 Pack fulfillment). **Not registered** (no App ID/key on the box). Paid GitHub Apps: GitHub keeps 5%, dev 95%.
- **The one paid capability:** the automated PR is the $1,499 deliverable; also the trust anchor for the auto-refund guarantee.

### `apps/pre-commit` — hook registry placement (minor). Funnel only.

---

## Cluster 5 — Supporting / infra
- **`apps/runner`** — Dockerized job runner: generates SHA-256-anchored audit PDFs (WeasyPrint) and opens migration PRs via GitHub App. Core to Pack/Audit fulfillment. E2E unverified.
- **`apps/worker`** — **retired** Cloudflare Worker (superseded by grace-api). Historical only. Do not revive.
- **`apps/widget`** — embeddable scan widget (`widget.js` served). Minor placement asset.

---

## Cluster 6 — Packaged distribution (new sellable surface, not a new codebase)
### `launch/gumroad/` — built 2026-07-18
- **What:** packages the 3 free CLIs (source, unmodified) + an original `MIGRATION-PLAYBOOK.md` + `ATTRIBUTIONS.md`
  into a Gumroad-ready zip via `build_bundle.sh`, plus complete listing copy (`LISTING-COPY.md`) for a **$79**
  "AWS Runtime EOL Migration Toolkit" SKU. This is Bet A′'s deliverable.
- **Completeness:** ✅ build script verified to run clean (164KB / 137 files, no secrets, `dist/` gitignored).
  Publish itself is owner-gated (Gumroad account + KYC + click) — see HUMAN_QUEUE HQ-1′/HQ-2′.
- **License:** re-packages the already-MIT/Apache-2.0-clean kits; no new dependencies. ATTRIBUTIONS generated.
- **The one paid capability:** the consolidated playbook + one-download convenience — the underlying tools stay
  free/MIT on GitHub, so what's sold is packaging + curation, not exclusivity.
- **Smallest sellable unit:** this bundle IS the smallest sellable unit for this frame (no further decomposition
  useful at $79).

## License hygiene (pre-publish §9)
All kits MIT; runtime deps are Apache-2.0 (boto3, @aws-sdk/*). **No copyleft contamination.** An ATTRIBUTIONS
file + AI-provenance disclosure must be generated before any paid packaging that a marketplace requires.
