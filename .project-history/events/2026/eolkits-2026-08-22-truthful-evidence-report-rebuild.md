---
id: eolkits-2026-08-22-truthful-evidence-report-rebuild
title: "The truthful evidence report: one 338-file commit retires the five-SKU business, the bots and every prior handoff, and restarts the $4,000 clock behind a closed checkout"
kind: reversal
scope: project-wide
components: [grace-api, runner, worker, web, ci, revenue, legal, launch]
paths: ["pricing.yml", "README.md", "HANDOFF.md", "SECURITY.md", "legal/**", "apps/grace-api/**", "apps/runner/**", "apps/worker/**", ".github/workflows/**", "revenue/**", "launch/**", "docs/status/**"]
significance: foundational
occurred_at: 2026-08-22
decided_at: 2026-08-22
merged_at: 2026-08-22
released_at: 2026-08-25
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "On 2026-08-22 an agent session under the owner's git identity rebuilt EOLkits around the only offer it judged could be made truthful and bounded — a $299 static repository evidence report — deleting the commerce code, the GitHub-App runner, the publishers, five bot workflows and seven narrative documents, adding a server-side checkout kill switch (default off), 410s for every retired product, an explicit not-for-sale list, and a seven-step Stripe test-mode gate as the new definition of done."
claim_ids: [CLM-E4A-004, CLM-E4A-005, CLM-E4A-006, CLM-E4A-007, CLM-E4A-008, CLM-E4A-009, CLM-E4A-010, CLM-E4A-011, CLM-E4A-014, CLM-E4A-015, CLM-E4A-016, CLM-E4A-017, CLM-E4A-018, CLM-E4A-019, CLM-E4A-020, CLM-E4A-021, CLM-E4A-041, CLM-E4A-042, CLM-E4A-055, CLM-E4A-056, CLM-E4A-057, CLM-E4A-058, CLM-E4A-059, CLM-E4A-060, CLM-E4A-001, CLM-E4A-002, CLM-E3-056]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-github-prs]
anchors: ["d772637a8df2fca900550a3de650a4a9af702b5d", "fee84eb6f5523364751e185423efa3e8e8897ed1", "85c9f43e330a668779e1de60c80ed5023a90129d", "3fc38e5cb18faeea33284caffe3405602b44abd1", "7d0e281f5b439d9410ad1ec6e4b6e2ec20b47f56"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-07-14-billing-honesty-sku-retirement, eolkits-2026-06-21-autopsy-never-reached-market, eolkits-2026-08-22-free-surfaces-made-truthful, eolkits-2026-08-22-legacy-commerce-retirement, eolkits-2026-08-30-fail-closed-relaunch-recovery]
amends: []
supersedes: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-07-14-billing-honesty-sku-retirement]
superseded_by: []
reversed_by: []
status: observed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

Thirty-nine loop days and four months live with $0; a nightly agent still finding false or stale public claims every cycle and unable to reach the web for 38 cycles (CLM-E4A-001, CLM-E4A-002); a live site advertising Migration Pack, Organization License, Drift Watch, "unsupported blast-radius/cost claims, and done-for-you PR fulfillment", a "universal December 31" date and a refund-on-CI-failure promise that had never been tested (CLM-E4A-014); Drift Watch still chargeable on the deployed API; hourly synthetic status commits publishing hard-coded zeros; an owner queue unactioned for 39 days. The June autopsy had already diagnosed "build-as-procrastination" and the wrong hero SKU (CLM-E4A-056). The pressure was internal audit evidence, not an external event.

## Intended beneficiaries

A buyer who can be told exactly what a $299 report is and is not; the owner, whose remaining steps were rewritten as an evidenced gate; and every stranger who would otherwise have met a claim the code could not honour.

## Goal, non-goal and definition of success

Goal, in D30's later restatement: "collect substantial profit from a truthful EOLkits offer with $0 spend and near-zero owner labor". Definition of done: the seven-step Stripe test-mode gate on the real deployment — immutable upload and preflight, checkout with verified webhook, one job producing a real PDF, Resend delivery, signed download, refund path, evidence recorded (CLM-E4A-010; G-09). New target: $4,000 by 2026-09-19 as fifteen $299 sales with Day-7/14/21/28 falsifiers (CLM-E4A-017; G-08). Explicit non-goals, printed on README, HANDOFF, SECURITY and the terms: Migration Pack, Drift Watch, Organization License, partner white-labelling and the public GitHub App are "closed research or private-bet" and not for sale (CLM-E4A-011); the report does not inventory AWS accounts, prove exploitability, estimate downtime or cost, or carry a digital signature.

## Principles affirmed, introduced, weakened or challenged

Introduced P-07.3 (truthful by construction), P-12.2 (one artifact, one price, one gate), P-16.2 (fail closed before money), P-05.2 (tests and commits are release evidence, not market signal; CLM-E4A-060) and P-15 (preserve history: an "ours" merge over the synthetic main instead of a force push, CLM-E4A-020). Retired in practice: the April autonomy catalogue (P-02) and the surge ladder (P-12). Left untouched: AGENTS.md itself, so the operating doc's Day-28 mission and the plan's 09-19 target coexist (CLM-E4A-055; CON-027).

## Alternatives considered and rejected paths

Forty-two monetisation frames were scored; every legacy multi-SKU frame, including selling the $1,499 Migration Pack, was disqualified as "App, preflight, PR, CI/refund proof absent" (CLM-E4A-016). D1 rejected the premise that profitability had been established: "high gross margin per hypothetical sale is not profitability or demand" (CLM-E4A-015). Surge pricing was rejected as customer-controlled; a GHCR image and local Docker builds were rejected for containment reasons; force-pushing over `main` was rejected (D11).

## Decision and rationale

Cut the catalogue to what the truth rule could cover and gate money behind evidence. The rationale is stated in the rewritten ledgers rather than the commit (the commit is subject-only, CLM-E4A-004): the live site "still advertised unavailable products and unsafe claims" and "only one paid deliverable can be made truthful and bounded today: a static evidence PDF". The historian's reading of authorship: an agent session (Codex) operating under the owner's identity and direction; the ledgers address "the active Codex thread" (CLM-E4A-041; CON-020). The session disclosed its own containment slips rather than hiding them (CLM-E4A-042).

## Implementation and evidence anchors

d772637a8df2fca900550a3de650a4a9af702b5d (338 files, +17,089/−23,664): deleted HANDOFF-2026-06-08/06-23/07-15, SEO-GRACE-HANDOFF, BENCHMARK, AUTOPSY, PROFIT-PROJECTIONS and the internal "mission complete" ledgers (CLM-E4A-005); deleted the Worker's commerce modules, `migration_pr.py`, `sandbox_e2e.py`, the dev.to/Hashnode/email publishers and the Gumroad script (CLM-E4A-006); added `EOLKITS_AUDIT_CHECKOUT_ENABLED` (default false), a readiness gate and `/api/capabilities` (CLM-E4A-007); 410 for Pack, Drift Watch, App install, org-license inquiry and `/partners/*` (CLM-E4A-008); `pricing.yml` reduced to one $299 tier with payment links removed (CLM-E4A-009); benchmark, ics, blog-loop, seo-pages and search-console workflows deleted and status-synth stripped of its commit step (CLM-E4A-018); upload cap 10 MiB, rate limits, retention expiries, ≥32-byte secrets (CLM-E4A-057); `launched.txt` archived as "not approved for publication" (CLM-E4A-058); status data replaced by explicit null/unknown (CLM-E4A-059); a compacted sixteen-decision ledger. fee84eb6f5523364751e185423efa3e8e8897ed1 ("retire synthetic main history", ours-merge) and 85c9f43e330a668779e1de60c80ed5023a90129d (the identical-tree copy published to `main` through the GitHub object API at 02:26 EDT, with the last rupture-bot commit 3fc38e5cb18faeea33284caffe3405602b44abd1 and the loop's Day-39 commit 7d0e281f5b439d9410ad1ec6e4b6e2ec20b47f56 as parents, CLM-E4A-021). The bots' last commits all precede it (CLM-E4A-019).

## Expected outcome

Pages serving only truthful copy the same day; the seven-step gate run by the owner within days; fifteen sales by 2026-09-19.

## Observed outcome

GitHub Pages served the repaired site on 2026-08-22 and the custom domain caught up on 2026-08-25 through the still-running box cron (see eolkits-2026-08-22-free-surfaces-made-truthful). The bot era ended: 3,253 automation commits stop here. The GRACE API was never redeployed in the window; the gate has never been run; purchases remain 0 at HEAD; the ledgers record it every day (CLM-E4B-061). The rebuild's own reviews then found the live host had an unauthenticated upload path, which produced the 2026-08-30 recovery.

## Tradeoffs, debt and follow-ups

History was preserved in git but erased from the working tree: every prior intent document survives only via `git show` (which is why this history recovers them). Reopening checkout later required a fresh Stripe Price because the retirement archived the canonical one. Legal facts (HQ-1), key rotation (HQ-2), GRACE deployment and the gate (HQ-3/4) moved to the owner queue and were still open on 2026-09-04 (CLM-E4A-054).

## Unresolved questions

What the owner instructed the session and whether the owner reviewed the deletions; whether the "three independent specialist reviews" D30 cites were separate agents; whether the owner intends to run the gate at all.
