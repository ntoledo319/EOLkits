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

_Next update: after the owner burns down any HUMAN_QUEUE item, record the first real listing/install/dollar here._
