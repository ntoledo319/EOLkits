# METRICS — Timestamped evidence ledger (§8)

Evidence hierarchy: **dollars > signups > visits > stars.** Only *observed* numbers appear here — no estimates.

## Collected dollars
| Date | SKU | Gross | Fees | Net | Source |
|---|---|---|---|---|---|
| — | — | $0 | — | **$0** | No purchase has ever been collected. |

**Cumulative collected profit = $0.00 · Gap to $4,000 = $4,000.00**

## Observed evidence — Cycle 0 (2026-07-13)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-13 | **eolkits.com is LIVE** | Fetched homepage: headline "AWS runtime & OS EOLs that break production"; prices $299/$1,499/$19/$14,999 shown; 30-day guarantee. |
| 2026-07-13 | **Self-deploy cron still running** | `eolkits.com/status/data.json` `generated: 2026-07-13T00:00:00Z` — box cron is current. |
| 2026-07-13 | **All systems ok** | status data.json: Stripe ok, Worker ok, Runner ok, Email ok, GitHub ok. |
| 2026-07-13 | **Funnel counters at zero** | status: audits(7d)=0, PRs(7d)=0, Drift subs=0, rules in pack=0. |
| 2026-07-13 | **Kits run** | `al2023-gate`, `python-pivot`, `lambda-lifeline` CLIs all execute `--help` from source (verified). |
| 2026-07-13 | **Tests green (verified live)** | al2023-gate 48/48, python-pivot 44/44, **lambda-lifeline 24/24** (after this cycle's date fix), apps/web 4/4 + surge 4/4. |
| 2026-07-13 | **VS Code extension packages** | `vsce package` → valid `eolkits-vscode-1.0.0.vsix`, 18 files, 23.86 KB (compiles via tsc). |
| 2026-07-13 | **Stripe rails live** | `pricing.yml` has live payment links for all paid SKUs; `test_mode: false`. **End-to-end purchase still UNVERIFIED.** |

## "Shipped & good" — live-site verification (2026-07-15)
| Check | Result |
|---|---|
| All sitemap URLs live | **54/54 return HTTP 200** (curl sweep) |
| Content quality | No `{API_URL}` / placeholder-text / TODO leaks (the "placeholder" hits are the email input's `placeholder=` attr) |
| **Money rail (the key test)** | ✅ **WORKS in prod** — `POST /api/audit/checkout` → HTTP 200 → `{"url":"https://checkout.stripe.com/c/pay/cs_live_…"}`. A real **live** Stripe checkout session is created; a buyer reaches a genuine Stripe payment page. (Only the post-payment PDF/email link is still untested — needs a real $299 purchase, HQ-6.) |
| Price | $299 standard (code + `test_surge_tier_matches_pricing`) |
| Lighthouse (home, desktop) | **SEO 100, Agentic 100**, Accessibility 81; Best-Practices score was an audit artifact (452s degraded run; **zero** console errors/warnings/issues confirmed independently) |
| Visual quality | Professional dark landing page, proof-first, clear CTAs + trust line (screenshot on file) |

## Distribution actions taken (the demand test)
| Date | Action | Status |
|---|---|---|
| 2026-07-15 | **Owner posted all 3 drafted re:Post answers** (AL2 EOL migration, Lambda py3.9 EoL, AL2 motd-date) — the first real distribution action | **LIVE, pending re:Post moderation** |
| — | Baseline at post time (`/status/data.json` 2026-07-15T00:00Z): **0 audits, 0 PRs, 0 subs** | any tick up = first buyer signal |

**Watch:** `eolkits.com/status` — first `checkout_click` (buyer imminent) → first `audits delivered > 0` (first dollar). The daily 2 AM routine also reports this each run.

## Traffic / installs / signups
| Metric | Value | As of |
|---|---|---|
| eolkits.com pageviews (track.js) | not yet instrumented into a public counter | — |
| `checkout_click` events | 0 (none observed) | 2026-07-13 |
| VS Code Marketplace installs | 0 (not published) | 2026-07-13 |
| Open VSX installs | 0 (not published) | 2026-07-13 |
| PyPI / npm downloads | 0 (not published) | 2026-07-13 |
| dev.to articles staged on branch | **7** (`01`–`07`; `07` "Node 20 real deadline" authored 2026-07-14 — auto-publishes via box cron, canonical → eolkits.com) | 2026-07-14 |
| high-intent `/fix` error pages | **27** (added 4 verified-accurate 2026-07-14: AL2023 iptables.service, py3.12 smtpd, py3.12 asyncore, OpenSSL3 DECODER) — box rebuilds from `fixes.yml` on deploy | 2026-07-14 |
| free interactive tool | **`/eol-checker/`** built 2026-07-14 — paste config/click runtimes → live block/EOL dates (client-side, nothing uploaded); deterministic, funnels to /scan + /audit. A linkable/shareable backlink asset (the #1 new-domain bottleneck) | 2026-07-14 |
| GitHub Marketplace (Action) | not listed | 2026-07-13 |

## Listings / rails status
| Thing | Status |
|---|---|
| eolkits.com commerce pages | ✅ live |
| Stripe payment links (5 SKUs) | ✅ live |
| Email fulfillment (Resend) | ✅ verified (prior work) |
| VS Code Marketplace | ⛔ submission-ready, publish HUMAN-gated (HQ-7) |
| Open VSX | ⛔ HUMAN-gated (HQ-8) |
| GitHub Marketplace (Action) | ⛔ HUMAN-gated (HQ-10) |
| GitHub App (Pack fulfillment) | ⛔ not registered (HQ-4) |
| PyPI / npm | ⛔ publish HUMAN-gated (HQ-9) — but **de-risked 2026-07-14**: names free, wheels build + `twine check` PASS + install-and-run verified; commands in `launch/PUBLISH-CHECKLIST.md` |
| Upwork / Fiverr gig | ⛔ HUMAN-gated (HQ-1/2) |
| Gumroad "AWS Runtime EOL Migration Toolkit" ($79) | ⛔ **bundle built + verified 2026-07-18**, publish HUMAN-gated (HQ-1′/HQ-2′, ~10 min) |

## Cycle 2026-07-15 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-15 | **Tooling outage noted:** WebFetch 403'd on every tested URL (AWS docs, repost.aws, endoflife.date, `example.com` control) | Sandbox/proxy issue, not an AWS block. No new AWS date claims were shipped this cycle as a result — see PLAN + DECISIONS D11. |
| 2026-07-15 | **Truth fix shipped:** fabricated "Team $999 / Enterprise $2,499" tiers (+ fake bundle, Slack, on-call, `eolkits-kits.com`, `support@eolkits-kits.dev`) removed from all 3 kit READMEs | Commit `915ebb1`. Repo-wide grep (md/py/yml/html/ts/js/mjs) confirms no other live occurrence. |
| 2026-07-15 | **Regression check:** lambda-lifeline `npm test` still 24/24 after README edit | Ran directly this cycle. |
| 2026-07-15 | **collected dollars unchanged** | $0. No payment-rail or listing change this cycle — this was a truth/conversion fix on already-live pages, not a new SKU. |

## Cycle 2026-07-16 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-16 | **WebFetch/direct fetch still down** (3rd consecutive cycle) — `WebFetch` on `https://example.com` (neutral control) returned HTTP 403; a direct `curl` through the environment proxy also 403'd (`CONNECT tunnel failed`) on `example.com` and the AWS docs URL | `WebSearch` (separate backend) does work, but URL-resolution can't be confirmed — per the outage rule, skipped new answer-backlog/dev.to drafting this cycle. |
| 2026-07-16 | **Found + fixed a live truth/do-no-harm issue:** `drift_watch` ($19/mo) had a fully-live self-serve checkout (`/drift/` → `/api/drift/checkout`) and an active upsell on the audit success page, but fulfillment (`apps/runner/main.py handle_drift_watch_setup`) is a complete no-op — no IAM validation, no scan, no delta PDF, ever. A subscriber would be charged monthly, indefinitely, for nothing. | Read `apps/runner/main.py` + `apps/grace-api/eolkits_grace/app.py` directly this cycle. |
| 2026-07-16 | **Shipped:** replaced the live checkout with an honest "coming soon" waitlist page; removed the Drift Watch upsell from the audit success flow; marked README "(coming soon)" | Commit `2a843b9`. |
| 2026-07-16 | **Regression check:** apps/web `test_determinism.py` 4/4 + `test_surge.py` 4/4 still green after the build.py edit (local rebuild via jail-local Python 3.12 venv, no `{API_URL}` leaks) | Ran directly this cycle; venv deleted after use. |
| 2026-07-16 | **collected dollars unchanged** | $0. This was a solicitation/truth fix on a stubbed SKU, not a new payment-rail change. |
| 2026-07-16 | **re:Post batch-1 answers status unchanged** — no new moderation/approval signal observed this cycle (not independently checkable without fetch access) | See D12; owner posted 2026-07-15, still pending as of last check. |

## Cycle 2026-07-18 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-18 | **WebFetch/proxy outage confirmed persistent (4th cycle), root cause identified** | `$HTTPS_PROXY/__agentproxy/status` shows `recentRelayFailures` with `connect_rejected` / "gateway answered 403 to CONNECT (policy denial or upstream failure)" for both `example.com` and `docs.aws.amazon.com` — a gateway-level policy denial, not an AWS block or a transient blip. Skipped new re:Post-answer/dev.to drafting per the standing outage rule. |
| 2026-07-18 | **Shipped: Gumroad bundle built and verified** | `launch/gumroad/build_bundle.sh` runs clean → `eolkits-migration-toolkit.zip`, 164K, 137 files, no secrets/`.env`/`.git` leaked (checked via `unzip -l` + grep). Playbook + attributions + 3 kit sources included. Not yet published (owner step). |
| 2026-07-18 | **collected dollars unchanged** | $0. This is a pre-publish asset build, not a new live listing — Gumroad account (HQ-1′) + publish click (HQ-2′) are still owner-gated. |

## Cycle 2026-07-19 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-19 | **WebFetch/proxy outage confirmed persistent (5th consecutive cycle)** | `WebFetch` on `https://example.com` and directly on `docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html` both still HTTP 403, even though `$HTTPS_PROXY/__agentproxy/status`'s `recentRelayFailures` was empty this time (unlike D15). `WebSearch` (separate backend) works but returned the exact superseded 2026 Lambda-block dates D3 already corrected — confirms search-only verification is unsafe for new date claims. Skipped new re:Post-answer/dev.to drafting per the standing outage rule. |
| 2026-07-19 | **Shipped: org_license license-key email delivery fix** | Commit `edfba40` — `_store_license` now emails the generated key via the existing Resend `send_email` path (mirrors audit-PDF delivery); a broken "verify" link (pointing at a static page with no JS) was caught and corrected to the real `/api/license/verify` JSON endpoint during self-review. 2 new regression tests; full grace-api suite 38/38 green (jail-local venv, deleted after use). |
| 2026-07-19 | **Production status unchanged** | Fix is code-only until the owner's next `eolkits-api` VPS redeploy — `apps/grace-api` is not on the auto-deploy path. Logged in HUMAN_QUEUE HQ-5b, folded into the existing HQ-4 SSH trip so it's not a new standalone ask. |
| 2026-07-19 | **collected dollars unchanged** | $0. This is a fulfillment-integrity fix on an unsold SKU (no org_license purchase has ever occurred), not a new live listing or payment-rail change. |

## Cycle 2026-07-20 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-20 | **WebFetch outage root-caused as a permanent policy denial (6th consecutive cycle: 07-15,-16,-18,-19,-20)** | `/root/.ccr/README.md`: "403/407 from the proxy: the destination host is not allowed by your organization's egress policy for this session. Do not retry or route around it." Confirms this is a fixed environment configuration (registries allowlisted, general web denied), not a transient fault — see DECISIONS D17. |
| 2026-07-20 | **No new truth/harm gap found** in a fresh audit of `apps/runner/main.py` handlers vs. `grace-api/app.py` dispatch — `handle_license_key`/`handle_drift_watch_setup` confirmed dead code, not live bugs. | Read directly this cycle; known gap surface (D16) stays closed. |
| 2026-07-20 | **Shipped: dev.to article 09** (`09-lambda-glibc-version-not-found.md`), sourced entirely from the already-verified `fixes.yml` entry — no new external fetch. Canonical → the real, registered `/fix/lambda-glibc-version-not-found/` page. | Frontmatter validated against `publish_devto.py`'s own parser this cycle; all 9 articles parse correctly. |
| 2026-07-20 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship + a root-cause finding, not a new SKU. |
| 2026-07-20 | **dev.to articles staged on branch: 9** (was 7 as of 07-14; article 08 shipped 07-19 by a separate process, unlogged until this cycle; article 09 shipped this cycle) | `launch/distribution/devto/01`–`09`. |

## Cycle 2026-07-21 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-21 | **WebFetch outage confirmed persistent (7th consecutive cycle: 07-15,-16,-18,-19,-20,-21)** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403; `$HTTPS_PROXY/__agentproxy/status` showed an empty `recentRelayFailures` this time (like D16), consistent with D17's root cause that this is a standing egress-policy denial, not a per-request fault worth re-diagnosing each cycle. |
| 2026-07-21 | **Shipped: dev.to article 10** (`10-python-asyncio-has-no-attribute-coroutine.md`), sourced entirely from the already-verified `fixes.yml` entry — no new external fetch. Canonical → the real, registered `/fix/python-asyncio-has-no-attribute-coroutine/` page. | Frontmatter validated against `publish_devto.py`'s own parser this cycle; all 10 articles parse correctly; confirmed non-duplicative via grep against articles 01–09. |
| 2026-07-21 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-21 | **dev.to articles staged on branch: 10** (was 9 as of 07-20) | `launch/distribution/devto/01`–`10`. |

_Next update: after the owner burns down any HUMAN_QUEUE item, record the first real listing/install/dollar here._
