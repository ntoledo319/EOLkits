---
id: eolkits-2026-04-28-rupture-mission-launch
title: "A one-day agent mission builds Rupture Kits: three deadline-driven AWS migration CLIs"
kind: origin
scope: project-wide
components: [kits, launch, docs]
paths: ["kits/**", "launch/**", "research/**", "README.md"]
significance: foundational
occurred_at: 2026-04-28
decided_at: 2026-04-28
merged_at: 2026-04-28
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "The repository began as an agent-run mission ('PLATFORM DEATHWATCH v3') that chose three AWS deprecation deadlines as 'rupture' events and shipped three scanner/codemod CLIs plus launch copy in one day, with placeholder checkout and a $25k/7-day target."
claim_ids: [CLM-E1-001, CLM-E1-002, CLM-E1-003, CLM-E1-004, CLM-E1-005, CLM-E1-006, CLM-E1-007, CLM-E1-008, CLM-E1-009, CLM-E1-010, CLM-E1-011, CLM-E1-012, CLM-E1-053, CLM-E1-054, CLM-E1-060, CLM-EXT-001]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-github-api, SRC-mind-status-docs]
anchors: ["05435fd26157dd1bd763e6e9fb1b4ecd39a7cecb", "d2c6632fbe8dc9fba4373e6ca4331f99c7005db0", "50d81348dadfe84145cfca46401145daec2b7d79", "12a01f9e3c4c880f63381790dacb431dc376d6ec", "2f556e5884054c296e0cf1e7dc6fdb09b5fc72ff"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: closed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

An empty repository named "Rupture", created through the GitHub web UI on 2026-04-28 with a one-line README (CLM-E1-001). The pressure was a mission brief given to a hosted agent (SuperNinja/NinjaTech identities "Rupture Kits", "Rupture Bot", "Rupture Ops"): a $0 seed budget, a "$25k goal" in seven days, and the fact that the Lambda Node.js 20 deprecation phase was two days away (CLM-E1-003, CLM-E1-004). The owner's own note of 2026-05-05 lists "Rupture" first among near-term revenue items, which corroborates that revenue, not tooling for its own sake, was the frame (CLM-EXT-001).

## Intended beneficiaries

"Panic buyers": senior engineers with budget authority facing an imminent AWS deadline, for whom no integrated SMB-priced scan → codemod → IaC → deploy → rollback tool existed (CLM-E1-005). This is what the mission memo said; no buyer was ever interviewed as far as the evidence shows.

## Goal, non-goal and definition of success

Ship one "Migration Script Kit" per deadline; floor viability "1 sale of any kind in 48h"; target $25k in seven days (CLM-E1-003). Explicit non-goals in the day-one distribution plan: no Reddit, Twitter/X, LinkedIn, cold email or DMs — GitHub organic, one Show HN, capped thread answers and one blog post only (CLM-E1-011).

## Principles affirmed, introduced, weakened or challenged

Introduced: dry-run by default and "everything ambiguous is flagged for human review, not auto-changed" (P-06); offline fixture mode so the tool demos without AWS credentials (P-06); $0 seed (P-01). Challenged the same day: copy claimed operator history ("the third time we had to migrate a fleet by hand") that the next day's runbook called fabricated and removed (CLM-E1-060) — the first instance of the truth problem that defines the project's later eras.

## Alternatives considered and rejected paths

The research memo recommended shipping Kit A (Node 20) and reserving B and C; the ledger records the operator's approval of all three ("do em all") (CLM-E1-004). Separate repositories per kit were planned in package metadata but rejected because the agent token could not create repositories, so a monorepo resulted (CLM-E1-054).

## Decision and rationale

Build all three kits as standalone CLIs sharing a "six pillars" shape (scan, codemod/remap, audit, iac, deploy, rollback), price them as per-kit support tiers ($499/$999/$2,499) plus bundles, publish a vendor-hosted landing page and pre-written launch copy (CLM-E1-006, CLM-E1-008, CLM-E1-010). The rationale is the memo's: the deadline creates the demand; the kit sells the shortcut. This is the agent's stated reasoning; the owner's intent is evidenced only by the approval quotes the agent recorded.

## Implementation and evidence anchors

d2c6632fbe8dc9fba4373e6ca4331f99c7005db0 (lambda-lifeline, 34 files), 50d81348dadfe84145cfca46401145daec2b7d79 (al2023-gate, python-pivot, 56 files), 12a01f9e3c4c880f63381790dacb431dc376d6ec (landing page, launch copy), 2f556e5884054c296e0cf1e7dc6fdb09b5fc72ff ("FINAL STATE — Mission Complete"). Codemods were regex-based from birth in both JS and Python (CLM-E1-009). 116 tests (24 node, 48 + 44 pytest) existed at day end (CLM-E1-008).

## Expected outcome

The agent declared "No blockers. Mission ready to launch." (CLM-E1-012).

## Observed outcome

Checkout links were placeholders (`#checkout`), GitHub Pages was not enabled, and no commerce existed. "Mission Complete" meant the build scope, not a sale. Three agent vendors touched the repo in its first week (CLM-E1-053). No sale is recorded in this or any later era.

## Tradeoffs, debt and follow-ups

The regex codemods, the deprecation date tables and the three-kit shape became the long-lived core. The fabricated-history copy and the human-support tiers had to be stripped the next day. Package metadata still points at repositories that never existed. The habit of declaring completion ahead of commerce recurs in every era.

## Unresolved questions

What the owner's actual brief to the agent said (only the agent's ledger survives); whether the three day-one identities were one session; why "Rupture" was chosen as a name beyond its use for a deadline event.
