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

## Cycle 2026-07-22 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-22 | **WebFetch outage confirmed persistent (8th consecutive cycle: 07-15,-16,-18,-19,-20,-21,-22)** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no new diagnosis run, went straight to the no-new-fetch content path. |
| 2026-07-22 | **Shipped: dev.to article 11** (`11-node-decoder-routines-unsupported.md`), sourced entirely from the already-verified `fixes.yml` entry (`node-error-decoder-routines-unsupported`, `source_url: nodejs.org/api/crypto.html`) — no new external fetch. Canonical → the real, registered `/fix/node-error-decoder-routines-unsupported/` page. | Frontmatter validated against `publish_devto.py`'s own parser this cycle; all 11 articles parse correctly (title/canonical_url/4-tag-max), no duplicate titles; confirmed non-duplicative of article 06 (different OpenSSL 3 error — build-time MD4 hash vs. runtime key decoding). |
| 2026-07-22 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-22 | **dev.to articles staged on branch: 11** (was 10 as of 07-21) | `launch/distribution/devto/01`–`11`. |

## Cycle 2026-07-23 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-23 | **WebFetch outage confirmed persistent (9th consecutive cycle: 07-15,-16,-18,-19,-20,-21,-22,-23)** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no new diagnosis run, went straight to the no-new-fetch content path. |
| 2026-07-23 | **Found (unlogged until now): a separate process pushed `fix(site): correct live blog Node-20 block dates...`** (commit `ab660bc`, 2026-07-22) correcting the last stale "Sep 30, 2026" mentions in `launch/blog-post.md` + the blog index to the already-established Feb 1 / Mar 3 2027 dates | Read the commit diff directly this cycle; consistent with D3, no conflict. |
| 2026-07-23 | **Shipped: dev.to article 12** (`12-lambda-importmoduleerror-triage.md`), sourced entirely from the already-verified `fixes.yml` entry (`lambda-runtime-importmoduleerror-cannot-find-module`) — no new external fetch. Canonical → the real, registered `/fix/lambda-runtime-importmoduleerror-cannot-find-module/` page. | Frontmatter validated against `publish_devto.py`'s own parser this cycle; all 12 articles parse correctly, no duplicate titles; confirmed non-duplicative of articles 05 (aws-sdk-specific) and 09 (glibc-specific) — this is a triage/decision-tree piece routing to both rather than repeating them. |
| 2026-07-23 | **Regression check:** `apps/web` `test_determinism.py` 4/4 + `test_surge.py` 4/4 still green (jail-local `python3.12` venv, deleted after use) — confirms the unrelated `ab660bc` blog-date commit didn't break the build. | Ran directly this cycle. |
| 2026-07-23 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-23 | **dev.to articles staged on branch: 12** (was 11 as of 07-22) | `launch/distribution/devto/01`–`12`. |

## Cycle 2026-07-24 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-24 | **WebFetch outage confirmed persistent (10th consecutive cycle: 07-15,-16,-18 through -24)** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no new diagnosis run, went straight to the no-new-fetch content path. |
| 2026-07-24 | **Shipped: dev.to article 13** (`13-al2023-dnf-unable-to-find-a-match.md`), sourced entirely from the already-verified `fixes.yml` entry (`amazon-linux-2023-dnf-unable-to-find-a-match`, `source_url: docs.aws.amazon.com/linux/al2023/ug/package-management.html`) — no new external fetch. Canonical → `/fix/amazon-linux-2023-dnf-unable-to-find-a-match/`, confirmed already referenced from the live `apps/web/build.py` AL2 checklist page. | Frontmatter validated against `publish_devto.py`'s own parser this cycle; all 13 articles parse correctly (4 tags each), no duplicate titles; confirmed non-duplicative of article 01 (one-line overview mention only). |
| 2026-07-24 | **Truth/harm sweep: no new issue found** | Reviewed all commits since the 07-23 audit — only automated `chore(status)` synthetic checks and dependency-bump commits from other routines; no fulfillment/checkout-path change to review. |
| 2026-07-24 | **Regression check:** `apps/web` `test_determinism.py` 4/4 + `test_surge.py` 4/4 green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-07-24 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-24 | **dev.to articles staged on branch: 13** (was 12 as of 07-23) | `launch/distribution/devto/01`–`13`. |

## Cycle 2026-07-25 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-25 | **Proxy status checked (11th consecutive cycle since the outage started 07-15)** | `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []` (empty, same as D19/D20) — per D17's root cause this doesn't mean the policy lifted, just that nothing hit the denied path yet. Went straight to the no-new-fetch content path, no re-diagnosis. |
| 2026-07-25 | **Truth/harm sweep: no new issue found** | `git log f60a892..HEAD` was empty before this cycle's commit — no other routine landed commits since the 07-24 audit. |
| 2026-07-25 | **Shipped: dev.to article 14** (`14-al2023-iptables-service-not-found.md`), sourced entirely from the already-verified `fixes.yml` entry (`amazon-linux-2023-iptables-service-not-found`, `source_url: docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html`) — no new external fetch. Canonical → `/fix/amazon-linux-2023-iptables-service-not-found/`, confirmed already linked from the live `apps/web/build.py` AL2 checklist page (line 1293). | Commit `52fe7e9`. Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 14 articles — 4 tags each, zero parse errors, zero duplicate titles; confirmed non-duplicative (zero "iptables" hits in articles 01–13). |
| 2026-07-25 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (via `pytest` — caught that a bare `python3 test_determinism.py` silently no-ops with exit 0, a false-pass trap) + `test_surge.py` 4/4 green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-07-25 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-25 | **dev.to articles staged on branch: 14** (was 13 as of 07-24) | `launch/distribution/devto/01`–`14`. |

## Cycle 2026-07-26 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-26 | **Proxy status checked (12th consecutive cycle since the outage started 07-15)** | `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []` (empty, same as 07-25). Per D17's root cause, went straight to the no-new-fetch content path, no re-diagnosis. |
| 2026-07-26 | **Truth/harm sweep: no new issue found** | `git log db5d4e6..HEAD` was empty before this cycle's commit — no other routine landed commits since the 07-25 audit. |
| 2026-07-26 | **Shipped: dev.to article 15** (`15-python312-smtpd-asyncore-removed.md`), sourced entirely from the already-verified `fixes.yml` entries (`python-no-module-named-smtpd`, `python-no-module-named-asyncore`, `source_url: docs.python.org/3/whatsnew/3.12.html`) — no new external fetch. Canonical → `/fix/python-no-module-named-smtpd/`, confirmed a live generated page (`build_error_pages` in `apps/web/build.py` generates a `/fix/<slug>/` page for every `fixes.yml` entry). | Commit `560941c`. Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 15 articles — 4 tags each, zero parse errors, zero duplicate titles; confirmed non-duplicative (zero "smtpd"/"asyncore" hits in articles 01–14). |
| 2026-07-26 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (via `pytest`) + `test_surge.py` 4/4 (via direct script run — it has no pytest-collectible tests) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-07-26 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-26 | **dev.to articles staged on branch: 15** (was 14 as of 07-25) | `launch/distribution/devto/01`–`15`. |
| 2026-07-26 | **No-fetch dev.to backlog nearly exhausted** | Only 2 uncovered `fixes.yml` entries remain with a dedicated-deep-dive gap: `amazon-linux-2023-ntpd-service-not-found`, `amazon-linux-2023-python2-command-not-found`. |

## Cycle 2026-07-27 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-27 | **WebFetch re-tested — 13th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch content path. |
| 2026-07-27 | **Found + verified (unlogged until now): article 16 shipped by a separate process 07-26** (`3d623cc`, node-sass Lambda breakage) | Verified canonical slug, non-duplication, and fact accuracy (LibSass EOL, matches `sass-lang.com/blog/libsass-is-deprecated/` already in `fixes.yml`) this cycle. |
| 2026-07-27 | **Backlog re-scan: 12 `fixes.yml` entries still uncovered** (was believed to be ~2) | Full grep of all 27 `fixes.yml` slugs against all article `canonical_url`s — see PLAN.md cycle log for the list. |
| 2026-07-27 | **Shipped: dev.to article 17** (`17-al2023-python2-command-not-found.md`), sourced entirely from the already-verified `fixes.yml` entry (`amazon-linux-2023-python2-command-not-found`) — no new external fetch. Canonical → `/fix/amazon-linux-2023-python2-command-not-found/`, confirmed live and cross-linked from the AL2 checklist page (`build.py:1295`). | Commit `0a0e7a2`. Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 17 articles — tags ≤4 each, zero parse errors, zero duplicate titles; confirmed non-duplicative (article 01 only has a one-line mention). |
| 2026-07-27 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-07-27 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship + backlog audit only. |
| 2026-07-27 | **dev.to articles staged on branch: 17** (was 15 as of 07-26; article 16 found this cycle, article 17 shipped this cycle) | `launch/distribution/devto/01`–`17`. |

## Cycle 2026-07-28 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-28 | **WebFetch re-tested — 14th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []` (empty). Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch content path. |
| 2026-07-28 | **Truth/harm sweep: no new issue found** | `git fetch origin marketing-machine-v2` showed no new commits ahead of the branch tip this cycle started from — no other routine landed commits since the 07-27 audit. |
| 2026-07-28 | **Shipped: dev.to article 18** (`18-al2023-ntpd-service-not-found.md`), sourced entirely from the already-verified `fixes.yml` entry (`amazon-linux-2023-ntpd-service-not-found`, `source_url: docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html`) — no new external fetch. Canonical → `/fix/amazon-linux-2023-ntpd-service-not-found/`, confirmed live and cross-linked from the AL2 checklist page (`build.py:1293`). | Commit `1173106`. Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 18 articles — 4 tags each, zero parse errors, zero duplicate titles; confirmed non-duplicative (article 01 only has a one-line overview mention). |
| 2026-07-28 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-07-28 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-28 | **dev.to articles staged on branch: 18** (was 17 as of 07-27) | `launch/distribution/devto/01`–`18`. |
| 2026-07-28 | **No-fetch dev.to backlog: 11 `fixes.yml` entries remain uncovered** | Full list in DECISIONS D25; next candidate `amazon-linux-extras-command-not-found`. |

## Cycle 2026-07-29 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-29 | **WebFetch re-tested — 15th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` shows a fresh `connect_rejected` entry for `example.com:443` timestamped this cycle. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch content path. |
| 2026-07-29 | **Truth/harm sweep: no new issue found** | `git log 217f14b..HEAD` was empty before this cycle's commit — no other routine landed commits since the 07-28 audit. |
| 2026-07-29 | **Shipped: dev.to article 19** (`19-amazon-linux-extras-command-not-found.md`), sourced entirely from the already-verified `fixes.yml` entry (`amazon-linux-extras-command-not-found`, `source_url: docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html`) — no new external fetch. Canonical → `/fix/amazon-linux-extras-command-not-found/`, confirmed live and cross-linked from the AL2 checklist page (`build.py:1292`). | Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 19 articles — 4 tags each, zero parse errors, zero duplicate titles; confirmed non-duplicative (articles 01/13 only have passing mentions, no dedicated deep dive). |
| 2026-07-29 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-07-29 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship only. |
| 2026-07-29 | **dev.to articles staged on branch: 19** (was 18 as of 07-28) | `launch/distribution/devto/01`–`19`. |
| 2026-07-29 | **No-fetch dev.to backlog: 10 `fixes.yml` entries remain uncovered** | Full list in DECISIONS D25/D26; next candidate `python-no-module-named-distutils`. |

## Cycle 2026-07-30 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-30 | **WebFetch re-tested — 16th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch content path. |
| 2026-07-30 | **Truth/harm sweep: no new issue found** | `git log 800d69a..HEAD` was empty before this cycle's commit — no other routine landed commits since the 07-29 audit. |
| 2026-07-30 | **Backlog correction: 9 of 10 "remaining" `fixes.yml` entries were already covered** | Re-read articles 02/03/04 in full — each already gives dedicated paragraph- or section-level coverage (exact error text + fix) to `python-no-module-named-{distutils,imp}`, `collections-has-no-attribute-mapping`, `datetime-utcnow-deprecated`, `python-no-module-named-{cgi,telnetlib,crypt,lib2to3}`, and `node-module-version-mismatch`. Only `node-punycode-module-deprecated` had zero prior mentions (`grep -rl punycode launch/distribution/devto/*.md` → no hits before this cycle). |
| 2026-07-30 | **Shipped: dev.to article 20** (`20-node-punycode-module-deprecated.md`), sourced entirely from the already-verified `fixes.yml` entry (`node-punycode-module-deprecated`, `source_url: nodejs.org/api/punycode.html`) — no new external fetch. Canonical → `/fix/node-punycode-module-deprecated/`, confirmed live (auto-generated per `build_error_pages`). | Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 20 articles — 4 tags each, zero parse errors, zero duplicate titles, zero duplicate canonical URLs. |
| 2026-07-30 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green in a jail-local **`python3.12`** venv (deleted after use) | First attempt with a default `python3 -m venv` (resolves to 3.11 on this box) hit a real pre-existing `build.py:1977` f-string/backslash SyntaxError that only Python 3.12+ tolerates — not a regression from this cycle's change, but a trap for future cycles: pin the venv to `python3.12` explicitly. |
| 2026-07-30 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship + backlog audit only. |
| 2026-07-30 | **dev.to articles staged on branch: 20** (was 19 as of 07-29) | `launch/distribution/devto/01`–`20`. |
| 2026-07-30 | **No-fetch dev.to backlog: exhausted** | All 27 `fixes.yml` entries now have dedicated or paragraph-level article coverage — see DECISIONS this cycle for the full accounting. Next content ship needs either working WebFetch or a non-padding angle (index/synthesis piece). |

## Cycle 2026-07-31 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-07-31 | **WebFetch re-tested — 17th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch content path. |
| 2026-07-31 | **Truth/harm sweep: no new issue found** | `git log 461add4..HEAD` was empty before this cycle's commit — no other routine landed commits since the 07-30 audit. |
| 2026-07-31 | **Shipped: dev.to article 21** (`21-runtime-upgrade-error-map.md`), a synthesis piece (not a per-slug deep dive) linking all 25 existing `/fix/` pages by migration path — sourced entirely from already-verified `fixes.yml` data, no new external fetch. Canonical → `/fix/` hub page (previously unused as a canonical target — checked). | Commit `24c3edc`. Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 21 articles — zero parse errors, zero duplicate titles, zero duplicate canonical URLs; all 25 `/fix/<slug>/` links cross-checked against `fixes.yml` — all real. |
| 2026-07-31 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green in a fresh jail-local `python3.12` venv (deleted after use) | Ran directly this cycle. |
| 2026-07-31 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content ship (synthesis angle) only. |
| 2026-07-31 | **dev.to articles staged on branch: 21** (was 20 as of 07-30) | `launch/distribution/devto/01`–`21`. |

## Cycle 2026-08-01 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-01 | **WebFetch re-tested — 18th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch path. |
| 2026-08-01 | **Truth/harm sweep found a real live bug via a deeper check (not just the commit-diff sweep)** | `apps/web/content/fixes.yml`'s `lambda-nodejs-runtime-no-longer-supported` entry (live `/fix/` page) claimed "nodejs16.x and earlier are already blocked" — contradicted by this repo's own already-verified data (`kits/lambda-lifeline/README.md`, dev.to article 07): nodejs16.x shares the delayed Q1-2027 block dates (Feb 1 create / Mar 3 update 2027), not already blocked. |
| 2026-08-01 | **Shipped: truth fix** | Commit `668f505` — corrected the `fixes.yml` cause text to match the verified cluster dates. Re-verified: full site rebuild renders the corrected text on the live page, zero `{API_URL}` leaks, `test_determinism.py` 4/4 + `test_surge.py` 4/4 green (jail-local `python3.12` venv, deleted after use). |
| 2026-08-01 | **Shipped: dev.to article 22** (`22-why-did-my-aws-deploy-break-no-code-changes.md`) — symptom-first framing ("nothing changed in git, why did this break"), distinct from article 21's migration-path framing. Sourced entirely from already-verified `deprecations.yml` data — no new external fetch. Canonical → `/eol-checker/` (previously unused as a canonical target, confirmed live). | Same commit `668f505`. Frontmatter validated — all 22 articles unique titles/canonicals, ≤4 tags, zero parse errors. |
| 2026-08-01 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a truth fix + content ship. |
| 2026-08-01 | **dev.to articles staged on branch: 22** (was 21 as of 07-31) | `launch/distribution/devto/01`–`22`. |

## Cycle 2026-08-02 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-02 | **WebFetch re-tested — 19th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch path. |
| 2026-08-02 | **Truth/harm sweep (full-content re-read, not commit-diff) found 4 more live instances of the recurring superseded-date bug** — root `README.md` (3 instances: lines 25, 51, 165 — the most-visible file in the whole public repo) + `kits/lambda-lifeline/docs/ROLLBACK.md` (1 instance) + a 5th self-contradiction inside `kits/lambda-lifeline/README.md` itself (table correct since 07-13, prose sentence at line 46 never fixed). | Read all 27 `fixes.yml` entries in full (zero new bugs there) + repo-wide grep for "Sep 30/Aug 31 2026" variants. See DECISIONS D30. |
| 2026-08-02 | **Shipped: all 5 instances corrected** to the AWS-authoritative Feb 1, 2027 / Mar 3, 2027 dates across `README.md`, `kits/lambda-lifeline/README.md`, `kits/lambda-lifeline/docs/ROLLBACK.md`. | 3 files changed. Post-fix grep confirms zero remaining stale-date hits in `README.md`/`kits/`/`apps/`/`action.yml`. |
| 2026-08-02 | **Regression check:** `kits/lambda-lifeline` `npm test` 24/24 + `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-02 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a truth fix on public-facing docs only, no dev.to article this cycle (truth fix outranked a 23rd content piece). |
| 2026-08-02 | **dev.to articles staged on branch: 22** (unchanged from 08-01 — no new article this cycle) | `launch/distribution/devto/01`–`22`. |

## Cycle 2026-08-03 (cloud routine) — Day 21 §8 gate
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-03 | **WebFetch re-tested — 20th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden; `$HTTPS_PROXY/__agentproxy/status` `recentRelayFailures: []`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch path. |
| 2026-08-03 | **Day-21 §8 gate recomputed: $0 collected, $4,000 gap, unchanged since Day 0. No pivot warranted** — none of the 3 bets have actually gone live in the distribution sense (all publish steps are owner-gated and unactioned 21 days running); the §8 repositioning clause applies to underperforming live bets, not un-launched ones. See DECISIONS D31. | Re-read all 3 bets' HUMAN_QUEUE gating status this cycle. |
| 2026-08-03 | **Found (unlogged until now): a separate process pushed dev.to article 23** (`23-node-module-version-mismatch-lambda.md`, commit `ffac09f`, 2026-08-02 13:11 UTC) — verified canonical slug real, but flagged as a padding-adjacent duplicate of already-shipped article 02 content per D26's prior finding on this exact topic. Logged, not reverted (see DECISIONS D31). | Read the commit + compared against article 02 directly this cycle. |
| 2026-08-03 | **Truth/harm sweep (full-content, extending D30's scope to files D30 hadn't checked) found 13 more live instances of the recurring superseded-2026-date bug across 8 files** — `HANDOFF.md` (1), `PROFIT-PROJECTIONS.md` (2, incl. a fabricated standalone "Sep 30 2026" catalyst), `launch/show-hn-final.md` (2), `launch/hn-replies.md` (1), `launch/social.md` (2), `launch/outreach.md` (2, one actively coaching future outreach to "lead with Sep 30"), `ledger/internal/thread-answers.md` (4 — the highest-risk find: a live, reusable answer-template file meant to seed future real re:Post/SO replies), plus a correction banner (not a rewrite) added to the dated historical artifact `research/phase1_findings.md` (3 instances, left as historical record). | See DECISIONS D31 for full per-file detail and reasoning. |
| 2026-08-03 | **Shipped: all 13 instances corrected** across the 7 direct-edit files to the AWS-authoritative Feb 1/Mar 3, 2027 (Q1-2027 cluster, nodejs16/18/20 + python3.8/9/10) and Jul 31/Aug 31, 2027 (python3.11) dates; correction banner added to `research/phase1_findings.md`. | 8 files changed. Post-fix repo-wide grep confirms zero remaining stale-date hits outside the DECISIONS/ASSETS/METRICS/PLAN history logs and the two dev.to articles (07, 22) that correctly quote the myth as the thing being debunked. |
| 2026-08-03 | **Regression check:** `kits/lambda-lifeline` `npm test` 24/24 + `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-03 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a Day-21 gate recompute (no pivot) + a truth fix on public-facing/outreach docs only, no new dev.to article this cycle (13-instance truth-fix sweep outranked a 24th content piece). |
| 2026-08-03 | **dev.to articles staged on branch: 23** (was 22 as of 08-02; article 23 found this cycle, pushed by a separate process 08-02, not shipped by this cycle) | `launch/distribution/devto/01`–`23`. |

## Cycle 2026-08-04 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-04 | **WebFetch re-tested — 21st consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis, went straight to the no-new-fetch path. |
| 2026-08-04 | **Swept the two remaining unswept surfaces D30/D31 flagged (`apps/vscode-extension`, `apps/github-action`) — both clean** | `scanner.ts`'s hardcoded Python/Node deprecation dates cross-checked line-by-line against `rules/public/deprecations.yml` — exact match, no bug. |
| 2026-08-04 | **A repo-wide grep beyond the two flagged surfaces found the same recurring superseded-date bug in a new layer: the committed `docs/` build snapshot** — `docs/blog/migrating-lambda-nodejs-20-to-22/index.html` (title, H1, blockquote, TL;DR list, one body paragraph — 4 passages) still had the pre-07-22-correction dates, because the box's daily cron rebuilds+rsyncs `docs/` to the live site but never pushes the rebuild back to git. | See DECISIONS D32 for the root-cause trace via `deploy/grace/cron-deploy-eolkits-web.sh` + `HANDOFF-2026-07-15.md`. |
| 2026-08-04 | **Shipped: targeted patch of all 4 stale passages** to match `launch/blog-post.md`'s already-corrected wording exactly (Feb 1 / Mar 3, 2027 cliffs) — not a full rebuild-and-commit (precedent against that per D14/D28). | 1 file changed: `docs/blog/migrating-lambda-nodejs-20-to-22/index.html`. Post-fix grep: zero remaining stale-date hits in `docs/`; repo-wide re-check confirms the only 2 remaining matches are the already-reviewed exceptions (correction-bannered historical table, myth-debunking article 07). |
| 2026-08-04 | **Regression check:** `kits/lambda-lifeline` `npm test` 24/24 + `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-04 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a truth fix on a public-repo build artifact only, no new dev.to article this cycle (truth fix outranked a 24th content piece). |
| 2026-08-04 | **dev.to articles staged on branch: 23** (unchanged from 08-03) | `launch/distribution/devto/01`–`23`. |

## Cycle 2026-08-05 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-05 | **WebFetch re-tested — 22nd consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-05 | **Truth/harm sweep found nothing new — extended `docs/` check clean** | Repo-wide grep for every known superseded-date variant (2026 Sep/Aug, Jan/Feb, Nov/Dec, and the older Apr/Jun/Jul schedule) outside `revenue/` found only already-reviewed exceptions. `deprecations.ics` + `lambda-runtime-deprecation-schedule/index.html` both correct. `fixes.yml` still 27 entries — no new content source. |
| 2026-08-05 | **Explored and rejected an unverifiable content angle** | `kits/lambda-lifeline`'s codemod has an undocumented Buffer.toString/streams `highWaterMark` claim this agent couldn't verify with WebFetch down; declined to ship it per §2.5. The `assert`→`with` rule is already covered in article 02 (non-duplication check). |
| 2026-08-05 | **Shipped: cross-linked all 27 `/fix/` pages to `/eol-checker/`** | Commit `3314d93`. A site-quality/conversion improvement (not truth-fix, not new content) — both those categories are exhausted this cycle. Verified via full rebuild: 27/27 pages carry the link, zero `{API_URL}` leaks; `test_determinism.py` 4/4 + `test_surge.py` 4/4 green (jail-local `python3.12` venv, deleted after use). |
| 2026-08-05 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle. |
| 2026-08-05 | **dev.to articles staged on branch: 23** (unchanged from 08-03/08-04 — no new article this cycle) | `launch/distribution/devto/01`–`23`. |

## Cycle 2026-08-06 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-06 | **WebFetch re-tested — 23rd consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → still HTTP 403 Forbidden. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-06 | **Truth/harm sweep found nothing new** | `git log 87a61ba..HEAD` empty before this cycle's commit — no other routine landed commits since 08-05. `fixes.yml` still 27 entries, `deprecations.yml` still 8 active deprecations — no new content candidate on either axis. |
| 2026-08-06 | **Shipped: cross-linked all 8 `/migrate/` pages + index to `/eol-checker/`, index also to `/fix/`** | Commit `90a06ae`. The exact next candidate D33 flagged. Verified via full rebuild: 8/8 migrate pages + index carry the new link, zero `{API_URL}` leaks; `test_determinism.py` 4/4 + `test_surge.py` 4/4 + `kits/lambda-lifeline` `npm test` 24/24 green (jail-local `python3.12` venv, deleted after use). |
| 2026-08-06 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle. |
| 2026-08-06 | **dev.to articles staged on branch: 23** (unchanged — no new article this cycle, site-quality ship instead) | `launch/distribution/devto/01`–`23`. |

## Cycle 2026-08-07 (cloud routine)
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-07 | **WebFetch re-tested — 24th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → `EGRESS_BLOCKED` (explicit error type this time, same permanent egress-policy denial per D17). Consistent with D17's root cause — no re-diagnosis, went straight to the no-new-fetch path. |
| 2026-08-07 | **Truth/harm sweep found nothing new** | `git log 90a06ae..HEAD` empty before this cycle's commit — no other routine landed commits since 08-06. `fixes.yml` still 27 entries — no new content candidate. |
| 2026-08-07 | **Shipped: cross-linked dev.to article 21 + Gumroad `MIGRATION-PLAYBOOK.md` to `/eol-checker/`** | Commit `ad4893a`. The exact next candidate D34 flagged (article 22 already had the link; article 21 and the playbook didn't). Verified: bundle rebuild clean (164K/137 files, unchanged), article 21 frontmatter still parses; `test_determinism.py` 4/4 + `test_surge.py` 4/4 + `kits/lambda-lifeline` `npm test` 24/24 green (jail-local `python3.12` venv, deleted after use). |
| 2026-08-07 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle. |
| 2026-08-07 | **dev.to articles staged on branch: 23** (unchanged — no new article this cycle, existing article 21 edited in place instead) | `launch/distribution/devto/01`–`23`. |

## Cycle 2026-08-08 (cloud routine) — Day 26
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-08 | **WebFetch re-tested via the tool itself — 25th consecutive cycle blocked** | `WebFetch` on `https://example.com` → `EGRESS_BLOCKED` error type (same as 08-07). Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-08 | **Truth/harm sweep found nothing new** | Repo-wide grep for every known superseded-date variant outside `revenue/` found only 3 already-reviewed, correctly-contextual exceptions. `fixes.yml` still 27 entries, dev.to still 23 articles — no new content-source growth. No new commits from other routines since `b8a542b`. |
| 2026-08-08 | **Shipped: cross-linked all 3 `/vs/` comparison pages + the `/vs/` index to `/eol-checker/`** | Commit `d76cfb4`. Verified via full rebuild: 4/4 pages carry the link, zero `{API_URL}` leaks; `test_determinism.py` 4/4 + `test_surge.py` 4/4 + `kits/lambda-lifeline` `npm test` 24/24 green (jail-local `python3.12` venv, deleted after use). |
| 2026-08-08 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a site-quality cross-link, same category as the last 3 cycles. |
| 2026-08-08 | **dev.to articles staged on branch: 23** (unchanged — no new article this cycle) | `launch/distribution/devto/01`–`23`. |
| 2026-08-08 | **Day 26 of 28 — only 2 days remain in the original window.** | HUMAN_QUEUE core batch still fully unactioned; no observed buyer signal. |

## Cycle 2026-08-09 (cloud routine) — Day 27
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-09 | **WebFetch re-tested — 26th consecutive cycle blocked** | `WebFetch` on `https://example.com` → `EGRESS_BLOCKED`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-09 | **Truth/harm sweep found nothing new** | `git log f8011ec..HEAD` empty before this cycle's commit. `fixes.yml` still 27 entries, dev.to still 23 articles. Superseded-date grep found only the 3 already-reviewed exceptions. |
| 2026-08-09 | **Checked the remaining page builders D36 flagged; correctly declined to force a redundant CTA** | `build_audit_page` and `build_al2_vs_al2023_page` already lead with a `/scan/` free-tool CTA before the paid ask — adding `/eol-checker/` too would be redundant, not a gap. |
| 2026-08-09 | **Shipped: cross-linked all 3 kit READMEs to `/eol-checker/`** | Commit `f4a29e9`. A real, previously-unswept gap — the READMEs jumped straight from the free/paid table to a Stripe buy link with no free-tool step, unlike every other paid-adjacent page on the site. |
| 2026-08-09 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24 green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-09 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a site-quality cross-link on a new surface (kit READMEs). |
| 2026-08-09 | **dev.to articles staged on branch: 23** (unchanged — no new article this cycle) | `launch/distribution/devto/01`–`23`. |
| 2026-08-09 | **Day 27 of 28 — only 1 day remains in the original window.** | HUMAN_QUEUE core batch still fully unactioned; no observed buyer signal. |

## Cycle 2026-08-10 (cloud routine) — Day 28, end of original window
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-10 | **WebFetch re-tested — 27th consecutive cycle blocked** | `EGRESS_BLOCKED` on `https://example.com`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-10 | **Found + verified: a separate process pushed dev.to article 24** (`24-imdsv2-401-metadata-migration.md`, commit `b2902ff`, 2026-08-09 15:17 UTC) | Verified canonical target `/migrate/imdsv1-enforcement/` is real (auto-generated from `deprecations.yml`'s "IMDSv1 Enforcement" entry via `build.py`'s unconditional per-entry page loop; slug matches exactly). Confirmed non-duplicative (zero prior imdsv2/169.254.169.254 mentions). |
| 2026-08-10 | **Truth/harm sweep found nothing new** | `git log e549323..b2902ff` = only the article-24 commit; repo-wide stale-date grep found only the 2 already-reviewed exceptions. |
| 2026-08-10 | **Shipped: cross-linked the VS Code extension marketplace README to `/eol-checker/`** | Commit `5560eb4`. Same gap pattern as the 08-09 kit-README fix — the paid-CTA section had no free-tool step before it. GitHub Action README checked and correctly excluded (not the same funnel shape); root README already leads with `/scan`. |
| 2026-08-10 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24 green | Jail-local `/usr/bin/python3.12` venv, deleted after use. |
| 2026-08-10 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content verification + a site-quality cross-link only. |
| 2026-08-10 | **dev.to articles staged on branch: 24** (was 23 as of 08-09; article 24 found this cycle, pushed by a separate process 08-09) | `launch/distribution/devto/01`–`24`. |
| 2026-08-10 | **Day 28 of 28 — the original 28-day window closes today.** Collected = $0, gap = $4,000, unchanged end-to-end. HUMAN_QUEUE core batch unactioned the full window. Loop continues past Day 28 (no natural stop condition; see DECISIONS D38). | — |

## Cycle 2026-08-11 (cloud routine) — Day 29, first cycle past the original window
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-11 | **WebFetch re-tested — 28th consecutive cycle blocked** | `EGRESS_BLOCKED` on `https://example.com` (neutral control). Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-11 | **Truth/harm sweep found one more instance of the recurring superseded-date bug, in a spot D32's sweep missed** | `docs/blog/index.html` (the committed blog *index* snapshot's post excerpt, separate from the individual post page D32 already fixed) still read "...before the Sep 30 cliff." Confirmed `build.py`'s `build_blog_index()` source was already correct — only the stale committed `docs/` artifact lagged (same cron-never-repushes-docs/ root cause as D32). |
| 2026-08-11 | **Shipped: targeted 1-line patch** to `docs/blog/index.html` matching the already-correct source wording ("Feb 1 / Mar 3, 2027 block cliffs") | Repo-wide grep (incl. ISO/slash date-format variants, checked fresh this cycle) confirms zero remaining stale-date hits beyond the 3 already-reviewed correct exceptions. |
| 2026-08-11 | **Also swept `apps/pre-commit`, the GitHub Action's PR-comment CTA, and 6 unreviewed `ledger/internal/*.md` files** — no action needed | `apps/pre-commit` has no README to cross-link; the Action's PR comment already leads with direct paid CTAs and the Action itself *is* the free-scan step (an `/eol-checker/` link there would be redundant, per D37's reasoning); the ledger files are internal-only and carry no live superseded-date instance. |
| 2026-08-11 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24 green (jail-local `python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-11 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a narrow truth-fix + a negative-result sweep only. |
| 2026-08-11 | **dev.to articles staged on branch: 24** (unchanged from 08-10) | `launch/distribution/devto/01`–`24`. |
| 2026-08-11 | **Day 29 — first cycle past the original 28-day window.** HUMAN_QUEUE core batch still fully unactioned; no observed buyer signal. Agent-side autonomous surfaces (truth fixes, no-fetch content, site cross-linking) are thin but not fully dry — today's find shows a careful re-sweep can still surface a real (if narrow) issue. | — |

## Cycle 2026-08-12 (cloud routine) — Day 30
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-12 | **WebFetch re-tested — 29th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → `EGRESS_BLOCKED`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-12 | **Truth/harm sweep found nothing new via commit diff** (`git log 6fbbce4..HEAD` empty before this cycle's commit) but a fresh homepage-card sweep found a new stale-urgency bug: the root `/` "Live Kits" section badged `al2023-gate` with `class="kit-card urgent"` + a hardcoded `Jun 30, 2026` deadline — presented as a live countdown 6.5 weeks after that date already passed. | Grepped `apps/web/build.py` + `docs/style.css` (`.kit-card.urgent` = red-highlighted styling) to confirm the framing; the homepage had never been checked for this specific bug pattern before. |
| 2026-08-12 | **Shipped: corrected badge** to `AL2 EOL passed Jun 30, 2026 — unpatched now`, reusing D8's already-established honest post-EOL phrasing from `kits/al2023-gate/README.md`. Kept the `urgent` red styling (still accurate — unpatched EOL'd OS in prod is genuinely urgent). | 1 file changed: `apps/web/build.py`. Confirmed via grep this was the only hardcoded instance of the stale badge text. |
| 2026-08-12 | **Regression check:** `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) green (jail-local `/usr/bin/python3.12` venv, deleted after use); full rebuild confirmed the fix renders on `docs/index.html`, zero `{API_URL}` leaks (rebuild output discarded per convention); `kits/lambda-lifeline` `npm test` 24/24 green. | Ran directly this cycle. |
| 2026-08-12 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a truth fix on the homepage (the most-visible page) only, no new dev.to article this cycle (truth fix outranked a 25th content piece). |
| 2026-08-12 | **dev.to articles staged on branch: 24** (unchanged from 08-10/08-11 — no new article this cycle) | `launch/distribution/devto/01`–`24`. |

## Cycle 2026-08-13 (cloud routine) — Day 31
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-13 | **WebFetch re-tested — 30th consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → `EGRESS_BLOCKED`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-13 | **Checked `build_scan_page` and the `/vs/` pages for D40's "hardcoded past-tense date styled urgent" pattern — both clean** | `build_scan_page` pulls all runtime dates dynamically from `deprecations.yml`; `/vs/` pages carry no EOL/block-date claims at all. Also checked the sample-audit-report page (which does show hardcoded 2026/2027 dates) — correctly marked "SAMPLE — redacted/fictional" throughout, dates phrased factually, no bug. |
| 2026-08-13 | **Shipped: closed the 3-cycle-old open item — added a free `/eol-checker/` mention to `launch/gumroad/LISTING-COPY.md`** | Re-examined D35's original "might dilute the $79 offer" concern: the listing already links to two bigger competing asks ($299/$1,499) in the same paragraph, so the concern didn't hold up. One sentence added ahead of those mentions, matching the free-tool-first pattern every other content surface already has. |
| 2026-08-13 | **Regression check:** `launch/gumroad/build_bundle.sh` re-run clean (164K/137 files, unchanged); `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24 green (jail-local `/usr/bin/python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-13 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a content polish on an already-built, still-owner-gated SKU (Bet A′). |
| 2026-08-13 | **dev.to articles staged on branch: 24** (unchanged — `fixes.yml` still 27 entries, no new no-fetch candidate) | `launch/distribution/devto/01`–`24`. |
| 2026-08-13 | **Day 31 — 3 days past the original 28-day window (closed 08-10).** HUMAN_QUEUE core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10) still fully unactioned, 31 days running; no observed buyer signal. With the LISTING-COPY.md item now closed, the DECISIONS backlog has no other specifically-named open content item — the next genuinely new agent-side lever most likely needs working WebFetch or new `fixes.yml`/`deprecations.yml` entries. | — |

## Cycle 2026-08-14 (cloud routine) — Day 32
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-14 | **WebFetch re-tested — 31st consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → `EGRESS_BLOCKED`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-14 | **Truth/harm sweep found nothing new via the usual grep** but a **full call-graph trace (not a copy-level read) found a live financial-harm gap D14 only partially closed** | `POST /api/drift/checkout` in `apps/grace-api/eolkits_grace/app.py` still created a real, subscription-mode Stripe Checkout Session for a $19/mo product (`handle_drift_watch_setup`) that is a confirmed no-op stub — D14 (2026-07-16) removed the frontend `/drift/` checkout form and audit-success upsell, but never closed the backend endpoint that actually charges the card. Anyone who still had the URL (bookmark, old link, cached reference) could have been billed monthly forever for nothing. |
| 2026-08-14 | **Finished the D37–D41 deferred CTA-redundancy check for `build_index_page`/`build_pack_page` — both confirmed clean** | Both already lead with an equivalent free-tool CTA (`/scan/`) before any paid ask; no `/eol-checker/` gap. Closes the last open cross-link item. |
| 2026-08-14 | **Shipped: closed the drift-checkout endpoint at the source** | `apps/grace-api/eolkits_grace/app.py`'s `/api/drift/checkout` now returns `410` instead of opening a Stripe subscription; `apps/web/build.py`'s `build_success_page()` dead `sku==='drift'` branch now tells a stray visitor to request a refund instead of falsely confirming an active subscription. 3 files changed. |
| 2026-08-14 | **Regression check:** `apps/grace-api` 38/38 (pytest, one test rewritten to assert the new refusal behavior) + `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24, all green (jail-local `/usr/bin/python3.12` venv, version confirmed, deleted after use) | Ran directly this cycle. |
| 2026-08-14 | **Production status: code-only until the owner's next VPS redeploy of `eolkits-api`** | Same `apps/grace-api`-is-not-on-the-git-push-path constraint D14/D16/D19 already established. The endpoint stays live in production until that redeploy — added an immediate 2-minute interim mitigant to HUMAN_QUEUE (deactivate the Stripe Price in the dashboard, doesn't need VPS access). |
| 2026-08-14 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a do-no-harm fix that *closes* a payment rail, plus a negative-result CTA check. |
| 2026-08-14 | **dev.to articles staged on branch: 24** (unchanged — `fixes.yml` still 27 entries, `deprecations.yml` still 8, no new no-fetch candidate) | `launch/distribution/devto/01`–`24`. |
| 2026-08-14 | **Day 32 — 4 days past the original 28-day window (closed 08-10).** HUMAN_QUEUE core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10) still fully unactioned, 32 days running; no observed buyer signal. This cycle is evidence a full call-graph trace (not just a copy/cross-link re-read) can still surface a real, higher-severity gap even after 30+ consecutive sweep cycles — "agent-side levers are thin" is not the same as "exhausted." | — |

## Cycle 2026-08-15 (cloud routine) — Day 33
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-15 | **WebFetch re-tested — 32nd consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → `EGRESS_BLOCKED`. Consistent with D17's root cause (standing egress-policy denial) — no re-diagnosis. |
| 2026-08-15 | **Traced remaining paid/webhook endpoints for a second "frontend removed, backend still live" bug — clean** | `/api/audit/checkout`, `/api/pack/checkout` both gate on real pre-conditions before charging; `/api/license/inquiry` doesn't charge; `/webhook/stripe`, `/webhook/github` verify signatures; `/partners/{slug}/audit` requires a verified paid Stripe session. No repeat of the D42 bug class. |
| 2026-08-15 | **Truth/harm sweep found nothing new via the usual grep** | Only the 2 already-reviewed correct exceptions. `fixes.yml` still 27 entries, `deprecations.yml` still 8 active + 2 historical, dev.to still 24 articles. |
| 2026-08-15 | **Found and fixed a live instance of D40's bug class (stale present-tense EOL framing) on two head-term SEO pages not previously checked at this level** | `build_al2_checklist_page` + `build_al2_vs_al2023_page` in `apps/web/build.py` — 4 instances of "Amazon Linux 2 reaches end of life on {date}" for a date ~7 weeks past, corrected to past tense. |
| 2026-08-15 | **Also corrected `revenue/ASSETS.md`'s own product table, which still showed Drift Watch as "Stripe link ✅ live"** | Contradicted D42 (2026-08-14), which closed that checkout endpoint the prior cycle. |
| 2026-08-15 | **Regression check:** `apps/grace-api` 38/38 (pytest) + `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24, all green | Jail-local `/usr/bin/python3.12` venv, deleted after use. Full rebuild confirmed the fix renders on both pages, zero `{API_URL}` leaks; `docs/` rebuild output discarded per convention. |
| 2026-08-15 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a truth fix on 2 SEO landing pages + an internal-record correction, plus a negative-result endpoint-trace sweep. |
| 2026-08-15 | **dev.to articles staged on branch: 24** (unchanged — `fixes.yml` still 27 entries, no new no-fetch candidate) | `launch/distribution/devto/01`–`24`. |
| 2026-08-15 | **Day 33 — 5 days past the original 28-day window (closed 08-10).** HUMAN_QUEUE core batch still fully unactioned, 33 days running; no observed buyer signal. | — |

## Cycle 2026-08-16 (cloud routine) — Day 34
| Timestamp (UTC) | Observation | Evidence |
|---|---|---|
| 2026-08-16 | **WebFetch re-tested — 33rd consecutive cycle blocked** | `WebFetch` on `https://example.com` (neutral control) → `EGRESS_BLOCKED`. Consistent with D17's root cause — no re-diagnosis. |
| 2026-08-16 | **Found + fixed a live truth bug one layer deeper than any prior sweep: the shared `description:` field in `rules/public/deprecations.yml`** | 2 entries (Amazon Linux 2 EOL, IMDSv1 Enforcement) had present/future-tense descriptions for already-passed dates, propagating verbatim into 5 spots per `/migrate/` page plus the RSS feed and ICS calendar. See DECISIONS D44. |
| 2026-08-16 | **Same-cycle sweep found + fixed 6 more instances of the identical bug across `README.md` (the most-visible file in the repo), `launch/DISTRIBUTION-KIT.md` (current send-ready outreach kit), `launch/distribution/fast-cash/README.md`, 2 dev.to article source files, and `launch/show-hn-final.md`** | Commit pending. `README.md`'s "Next up: Amazon Linux 2" tagline was also factually stale on a second axis (no longer the nearest future deadline). |
| 2026-08-16 | **Regression check:** full rebuild + `apps/web` `test_determinism.py` 4/4 (pytest) + `test_surge.py` 4/4 (direct run) + `kits/lambda-lifeline` `npm test` 24/24, all green (jail-local `/usr/bin/python3.12` venv, deleted after use) | Ran directly this cycle. |
| 2026-08-16 | **collected dollars unchanged** | $0. No new listing/payment-rail change this cycle — a 7-file truth-fix sweep only. |
| 2026-08-16 | **dev.to articles staged on branch: 24** (unchanged — 2 existing articles corrected in place, no new article; `fixes.yml` backlog still exhausted) | `launch/distribution/devto/01`–`24`. |
| 2026-08-16 | **Day 34 — 6 days past the original 28-day window (closed 08-10).** HUMAN_QUEUE core batch still fully unactioned, 34 days running; no observed buyer signal. | — |

_Next update: after the owner burns down any HUMAN_QUEUE item, record the first real listing/install/dollar here._
