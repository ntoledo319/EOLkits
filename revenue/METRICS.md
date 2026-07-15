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
