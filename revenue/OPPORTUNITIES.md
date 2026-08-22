# OPPORTUNITIES — Ranked monetization frames (Cycle 0, 2026-07-13)

Method (§5 divergence): enumerated ≥7 frames per asset cluster **before** judging, scored each on
**T** (days→first $), **H** (owner-minutes), **D** (distribution: marketplace-included ≫ platform-listed ≫ owned-audience),
**U** (realistic 4-wk revenue after fees), **R** (risk). Ranking law: built-in-distribution **and** built-in-payments
frames win; owned-audience organic loses **unless the audience already exists — it does not here.**

## Verified platform facts (July 2026 — the fee/latency reality that sets T/H/U/R)
| Platform | Fee | Built-in payments? | Owner unlock (KYC/publish) | Live latency | Scriptable |
|---|---|---|---|---|---|
| ~~Upwork / Fiverr~~ **RULED OUT** | — | — | Owner won't do Upwork (ongoing time) / can't verify on Fiverr (2026-07-14) | — | — |
| **VS Code Marketplace** | $0 | ❌ (Free/Free-Trial only) | MS acct + Azure DevOps PAT → `vsce publish` | minutes–hours | yes (token) |
| **Open VSX** | $0 | ❌ | Eclipse acct + Publisher Agreement → `ovsx publish` | ~instant | yes (token) |
| **GitHub Marketplace — Action** | $0 | ❌ (Actions can't charge) | Web-UI publish **from the existing repo** (root action.yml present; monorepo OK — verified) w/ release | instant | web-UI only |
| **GitHub Marketplace — App** | GitHub 5% / dev 95% | ✅ | Org/publisher **verification** + bank/tax | days–weeks | — |
| **Gumroad** | 10% + $0.50 (Merchant of Record) | ✅ | Acct + payout; MoR handles sales tax | instant | API |
| **Lemon Squeezy** | 5% + $0.50 (+surcharges), MoR | ✅ | Acct + KYC + payout; MoR handles tax | short | API |
| **PyPI / npm** | $0 | ❌ | Acct + 2FA + API token (or Trusted Publishing) | 1–5 min | twine/CI |
| **RapidAPI** | **25%** + PayPal fees | ✅ | PayPal-only payout; W-9 on request | ~immediate | API |

**RapidAPI = DEAD** (suit 2/5): Nokia-acquired, user base collapsed 4M→"thousands," and EOLkits is a
scan/PR service, not a per-call REST API (would need a new hosted endpoint). Skip.

## Ranked opportunities (across all assets)
| # | Frame | Asset | T | H | D | U (4wk, after fees) | Why / risk |
|---|---|---|---|---|---|---|---|
| ~~1~~ | ~~Upwork/Fiverr productized gig~~ **KILLED 2026-07-14** | — | — | — | — | — | Owner: no Upwork (ongoing time), no Fiverr (KYC won't clear). See DECISIONS D7. |
| **1′** | **Gumroad "AWS EOL Migration Toolkit" bundle** | kits + playbook + templates | ~7 | 10 | platform-listed (MoR payments) | ~$70/sale | One-time setup, no per-job time (fits owner). Volume/first-dollar play. **→ Bet A′ — bundle built + verified 2026-07-18, owner-minutes now ~10 (down from 15).** |
| **2** | **$1,499 Migration Pack** (real PR, CI-fail auto-refund) | kits + grace-api + runner + github-app | 10 | 40 | owned-audience (today) | **$1,455 / sale** | 3 sales clear $4k. Fulfillment path UNVERIFIED. **→ Bet B** |
| 3 | **Sell placement:** VS Code + Open VSX extension → $299 audit | apps/vscode-extension | 10 | 45 | platform-listed | ~$290 | 30M VS Code + 300M/mo Open VSX (Cursor/VSCodium). Cold-install→buy is slow. **→ Bet C** |
| 4 | **Sell output:** $299 Audit via the live surge-priced site | apps/web + grace-api | 5 | 5 | owned-audience | $0–290 | Already live; gated purely on qualified traffic. |
| 5 | **Sell placement:** GitHub Action on Marketplace | apps/github-action | 14 | 5 | platform-listed | ~$300 | Peak-intent (CI failure). Lists directly from the existing repo (no dedicated repo — verified); can't charge. |
| 6 | **Sell the code:** CLIs on PyPI + npm w/ in-CLI CTA | 3 kits | 15 | 20 | platform-listed | ~$150 | Makes README `pip install` real; embeds CTA at max-urgency. New pkgs rank low. |
| 7 | **Sell placement:** dev.to canonical backlinks | launch/distribution | 4 | 5 | platform-listed | ~$150 | Already wired; converts dev.to authority into eolkits.com backlinks. Gated on DEVTO key on box. |
| 8 | **White-label:** grace-api `/partners/*` Stripe-Connect reseller (70/30) | apps/grace-api | 21 | 45 | owned-audience | ~$250 | Fully coded, unmarketed. One AWS MSP brings its own client book. Medium-term. |

## Other frames enumerated (scored, not selected)
- **Sell a bundle:** all 3 kits + audit templates as one Gumroad/Lemon Squeezy "AWS EOL Migration Toolkit" download ($49–99). Built-in payments, weak built-in distribution. U low; a fast *first-dollar* fallback if Upwork stalls.
- **Sell a component:** extract the canary-deploy-with-alarm-rollback engine as a standalone library. High build cost, unclear buyer. Deferred.
- **Sell access (SaaS):** hosted multi-account scanner. Requires the API productized + hosting; grace-api is fulfillment-shaped, not per-call. Deferred.
- **Sell a service artifact (Org License $14,999/yr):** enterprise; long cycle, needs sales motion. Not a 28-day driver.
- **Sell output (Drift Watch $19/mo):** recurring; needs an install base first. Compounding, post-day-28. **UPDATE
  2026-07-16:** its live self-serve checkout was pulled (DECISIONS D14) — fulfillment is a no-op stub, so this frame
  is now dormant until someone actually builds IAM-role-based weekly re-scanning; not an active near-term opportunity.

## Reviewed (no change) — cycles 2026-07-19 through 2026-07-30
Ranking and frame scores unchanged: no new platform fact, fee change, or bet re-scoring this window. Frame #7
(dev.to canonical backlinks) is the one actively compounding — 20 articles staged as of 2026-07-30, still gated
on `DEVTO_API_KEY` confirmation (HQ-11) for the auto-publish cron to actually post them. **2026-07-30 (D27):** the
no-fetch `fixes.yml` backlog that fed this frame's cadence is now exhausted — 9 of the 10 "remaining" entries
tracked since D26 turned out to already be covered inside existing articles (content-level check, not just
canonical-link grep); only the punycode entry was a genuine gap and it shipped this cycle. Sustaining this frame's
cadence past article 20 needs either working WebFetch (still blocked) or new `fixes.yml` entries.

## Reviewed (no change) — 2026-08-01
Ranking and frame scores unchanged — no new platform fact this cycle. Frame #7 (dev.to canonical backlinks) is now
at 22 articles (21: migration-path synthesis, 22: symptom-first synthesis — both non-padding angles on the same
exhausted per-slug backlog, D28/D29). Considered checking whether Hashnode (`launch/distribution/publish_hashnode.py`,
built but never wired into the box cron or logged in this file) was an unexploited second free backlink channel —
it is not: `launch/distribution/README.md` already documents that Hashnode's publishing API went paid on
2026-05-13, so it correctly stays unused. No new frame identified this cycle; the deeper-sweep truth fix (D29) was
higher-leverage than a third content angle.

## Reviewed (no change) — 2026-08-21 (Day 39)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship (correcting a stale
`python-snappy` cp312 classification in frame #2's own kit output, plus syncing that and D48's prior fix into the
`apps/web` `/scan/` page's duplicate table and a re:Post answer template — see DECISIONS D49) is a correctness
fix on already-active bets' own product output, not a frame re-evaluation. Frame #1′ (Gumroad) and frame #3
(VS Code/Open VSX placement) remain owner-gated; frame #7 (dev.to backlinks) stays at 25 articles with the
per-slug/synthesis backlog exhausted.

## Reviewed (no change) — 2026-08-19 (Day 37)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship (reframing
`launch/DISTRIBUTION-KIT.md`'s pre-deadline sequencing/titles + `launch/distribution/email/template.md`'s example
finding to the honest post-AL2-deadline state, see DECISIONS D47) is a truth/framing fix on owner-facing
distribution-copy assets, not a frame re-evaluation. Frame #1′ (Gumroad) and frame #3 (VS Code/Open VSX placement)
remain owner-gated; frame #7 (dev.to backlinks) stays at 25 articles with the per-slug/synthesis backlog exhausted.

## Reviewed (no change) — 2026-08-15 (Day 33)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ships (a stale-EOL-framing truth
fix on 2 SEO landing pages, and a negative-result endpoint-trace sweep for a repeat of D42's checkout-bug class) are
truth/harm fixes, not a frame re-evaluation. Frame #1′ (Gumroad) and frame #3 (VS Code/Open VSX placement) remain
owner-gated; frame #7 (dev.to backlinks) stays at 24 articles with the per-slug/synthesis backlog exhausted.

## Reviewed (no change) — 2026-08-14 (Day 32)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship (closing the live
`/api/drift/checkout` financial-harm gap, see DECISIONS D42) is a do-no-harm fix on the dormant Drift Watch frame
(already noted below as "dormant until someone actually builds IAM-role-based weekly re-scanning"), not a frame
re-evaluation — it makes that dormancy actually safe (no charge possible) rather than changing its ranking.

## Reviewed (no change) — 2026-08-17 (Day 35)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship was a truth fix (a
self-contradictory "Live deadline" label for the passed AL2 date, in `README.md`/`launch/social.md`/
`launch/outreach.md` — see DECISIONS D45), not a frame re-evaluation.

## Reviewed (no change) — 2026-08-13 (Day 31)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship (a free-tool cross-link
added to the Gumroad listing copy, closing a 3-cycle-old open item; see DECISIONS D41) is a content/conversion
polish on frame #1′ (Gumroad bundle), not a frame re-evaluation. Frame #1′ remains fully built (since D15,
2026-07-18) and owner-gated on HQ-1′/2′; frame #3 (VS Code/Open VSX) remains owner-gated; frame #7 (dev.to
backlinks) stays at 24 articles with the per-slug/synthesis backlog exhausted.

## Reviewed (no change) — 2026-08-12 (Day 30)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship was a homepage stale-urgency
truth fix (the `al2023-gate` kit card's "Jun 30, 2026" badge, 6.5 weeks past and still styled urgent/red — see
DECISIONS D40), not a frame re-evaluation.

## Reviewed (no change) — 2026-08-04
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle swept the last two unswept public
surfaces (VS Code extension, GitHub Action) clean, then found + fixed the recurring superseded-date bug in a new
layer (the committed `docs/` build snapshot, see DECISIONS D32) — a truth/harm fix, not a frame re-evaluation.

## Reviewed (no change) — 2026-08-03 (Day-21 §8 gate)
Ranking and frame scores unchanged. This was the formal Day-21 gate (§8: Day 7/14/21) — recomputed the gap
($0 collected, $4,000 gap, unchanged) and evaluated repositioning per the "≥5 live days with zero signal" rule.
Conclusion: no pivot warranted, since none of the 3 bets have actually gone live in the distribution sense yet
(every publish step remains owner-gated and unactioned 21 days running) — the gate clause is for underperforming
live bets, not un-launched ones. See DECISIONS D31 for the full reasoning. This cycle's ship was a 13-instance
truth-fix sweep (8 files), not a frame re-evaluation.

## Reviewed (no change) — 2026-08-02
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle was a truth/harm sweep (5 more
instances of the recurring superseded-2026-date bug found and fixed in `README.md`/`lambda-lifeline`, see DECISIONS
D30), not a frame re-evaluation.

## Reviewed (no change) — 2026-08-05
Ranking and frame scores unchanged — no new platform fact this cycle. Both standing fallback categories (truth-fix
sweep, no-fetch dev.to content) came up exhausted on the same cycle for the first time; shipped a third,
still-legitimate category instead (internal cross-linking / conversion, `/fix/` pages → `/eol-checker/`, see
DECISIONS D33) rather than force either. Not a frame re-evaluation — frame #3 (VS Code/Open VSX placement) and
frame #7 (dev.to backlinks) are unchanged and still owner-gated/exhausted respectively.

## Reviewed (no change) — 2026-08-07
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle closed the exact gap D34 flagged
(dev.to article 21 + Gumroad `MIGRATION-PLAYBOOK.md` now cross-link `/eol-checker/`, see DECISIONS D35), not a
frame re-evaluation.

## Reviewed (no change) — 2026-08-10 (Day 28, end of original window)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle verified a separately-pushed
dev.to article (24, IMDSv2) and closed the VS Code extension README's free-tool-CTA cross-link gap (see DECISIONS
D38) — a content/site-quality ship, not a frame re-evaluation. The Day-28 end-of-window read is unchanged from
D31/D36/D37: frame #1′ (Gumroad) and frame #3 (VS Code/Open VSX placement) remain owner-gated and unactioned;
frame #7 (dev.to backlinks) is the one still actively compounding (24 articles staged). The honest constraint
below is unchanged — see D38 for the formal end-of-window note.

## Reviewed (no change) — 2026-08-11 (Day 29)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship (a 1-line truth fix in a
stale `docs/` build artifact) was a truth/harm sweep, not a frame re-evaluation. First cycle past the original
28-day window; the honest constraint below is unchanged.

## Reviewed (no change) — 2026-08-16 (Day 34)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ships (a truth fix in the
shared `deprecations.yml` description field, propagating to `/migrate/` pages + RSS + ICS, and a 6-file sweep of
the same bug across `README.md`/outreach drafts/2 dev.to sources — see DECISIONS D44) are truth/harm fixes, not a
frame re-evaluation.

## Reviewed (no change) — 2026-08-22 (Day 40)
Ranking and frame scores unchanged — no new platform fact this cycle. This cycle's ship (fixing wrong block-create/
block-update dates in `python-pivot`'s `RUNTIME_TABLE` and its README's headline deadline table — the largest
single-instance urgency overstatement found in the 39-cycle date-bug history, see DECISIONS D50) is a truth/harm
fix, not a frame re-evaluation.

## The honest constraint that dominates all of this
Every payment-enabled channel is **first-publish KYC-gated** (marketplaces need identity/bank). No autonomous
$0 action reaches a *ready buyer* inside 28 days. The frames that can actually collect $4k (Upwork gig, Migration
Pack) both require the owner to open one account and/or click publish. That is the entire ballgame — see HUMAN_QUEUE.
