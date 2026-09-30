---
id: eolkits-2026-07-13-revenue-loop-v2-operating-doc
title: "REVENUE LOOP v2: an operating document installs a jailed nightly agent with a truth rule, a ship law and a $4,000 clock"
kind: operating-model
scope: project-wide
components: [revenue, ci, docs]
paths: ["AGENTS.md", "revenue/**", "launch/distribution/**", "deploy/grace/cron-deploy-eolkits-web.sh"]
significance: foundational
occurred_at: 2026-07-13
decided_at: 2026-07-13
merged_at: 2026-08-22
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "AGENTS.md, unchanged since 2026-07-13, made a headless agent the project's operator: $4,000 collected profit by Day 28 at $0 spend and at most 60 owner-minutes, a total filesystem jail, truth-only copy, no autonomous contact with humans, a daily ship law and an evidence hierarchy in which only observed dollars count; the next day the owner's no-Upwork/Fiverr rule removed the loop's only demand channel."
claim_ids: [CLM-E3-002, CLM-E3-003, CLM-E3-004, CLM-E3-005, CLM-E3-008, CLM-E3-010, CLM-E3-011, CLM-E3-014, CLM-E3-015, CLM-E3-016, CLM-E3-047, CLM-E3-054, CLM-E4B-001, CLM-E4B-002, CLM-E4B-003, CLM-E4B-004, CLM-E4B-005, CLM-E4A-055]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs]
anchors: ["08ddf1793df9dd5b713d4c7f7a0f0aa3ede603c0", "7f7b5e2a43866b6f1de74a462c04ab51e4c4ccbb", "62ef6f9c59efbcd4a6e1e1944e5cc44d501f5d25", "affbae631cd1b19f362f5fc58a5b552cbce666dd", "2dd09a243626a34a86549e793e0bff9497f4b707", "33855cd224d5571ea439b97b6b5b75d89e35b732"]
related: [eolkits-2026-06-21-autopsy-never-reached-market, eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus, eolkits-2026-07-15-repost-answers-only-demand-test, eolkits-2026-08-22-truthful-evidence-report-rebuild, eolkits-2026-09-04-jail-violations-and-env-recovery-scan]
amends: []
supersedes: [eolkits-2026-06-21-autopsy-never-reached-market]
superseded_by: []
reversed_by: []
status: observed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

AL2 end of support had passed thirteen days earlier with $0; the autopsy and profit projections had framed distribution as the gap; the site self-deployed daily from `marketing-machine-v2`; the June handoff's human unlocks had not happened. The owner's marketing factory had been frozen two days later (CLM-EXT-024). What remained was an agent that could run every night without the owner.

## Intended beneficiaries

The owner, whose time the document budgets to the minute; strangers, whom the document forbids the agent to contact; and a future buyer defined only as someone who pays for a live, listed, purchasable thing.

## Goal, non-goal and definition of success

"$4,000 cumulative collected profit by Day 28. First external dollar … target Day ≤ 7." "Plans, prototypes, and potential score zero. Only live, listed, purchasable things count." (CLM-E3-003; G-06). Non-goals as hard constraints: no spend, no Upwork/Fiverr after 2026-07-14, no autonomous contact with real humans, no full rewrite ("a failure smell"), no fabricated anything.

## Principles affirmed, introduced, weakened or challenged

Introduced in one document: P-02.2 (owner labour as a budget), P-07.2 (truth only), P-08 (do no harm; never fake-fulfil), P-09 (no autonomous human contact), P-10 (the jail outranks the mission), P-11 (dollars > signups > visits > stars); reaffirmed P-01 and P-04. Introduced a tension the document itself names: a ship law ("an analysis-only cycle is a failed cycle") beside an anti-busywork rule ("skip, don't pad").

## Alternatives considered and rejected paths

"Just run more SEO" was rejected for three scored bets (CLM-E3-054's ledger); forty-plus monetisation frames were scored; RapidAPI marked "DEAD". Bet A — Upwork/Fiverr, "the only channel with built-in demand" — was killed on 2026-07-14 when the owner ruled both out; a $79 Gumroad bundle became Bet A′ with the caveat that its KYC might also fail (CLM-E3-008). The document's own calibration: "It cannot make strangers buy … the portfolio needs a distribution-side intervention no autonomous agent can perform alone."

## Decision and rationale

Run a nightly headless Claude routine (06:00 UTC, pushing to the deploy branch) plus a weekly content process under a fixed operating document with six memory files under `revenue/` (ASSETS, OPPORTUNITIES, PLAN, METRICS, HUMAN_QUEUE, DECISIONS). The rationale is stated: sessions are disposable, the ledger is the brain, the owner's job is to burn down the queue every day or two. The 07-13..07-15 commits are owner-authored interactive sessions with Claude co-author trailers (CLM-E3-047); the document is agent-drafted under the owner's instructions quoted in the ledger.

## Implementation and evidence anchors

08ddf1793df9dd5b713d4c7f7a0f0aa3ede603c0 (2026-07-13: AGENTS.md, six ledgers, first date corrections); 7f7b5e2a43866b6f1de74a462c04ab51e4c4ccbb (2026-07-14: Bet A killed, forecast "$0–600"); 62ef6f9c59efbcd4a6e1e1944e5cc44d501f5d25 (routine stood up); affbae631cd1b19f362f5fc58a5b552cbce666dd (HANDOFF-2026-07-15: "the bottleneck is DISTRIBUTION, not the product"; demand at these prices "UNPROVEN", CLM-E3-010); 2dd09a243626a34a86549e793e0bff9497f4b707 (live $299 Checkout URL verified, CLM-E3-011); 33855cd224d5571ea439b97b6b5b75d89e35b732 (2026-07-20: egress block root-caused as organisation policy, CLM-E3-016). AGENTS.md is byte-identical from this commit to HEAD (CLM-E4B-001).

## Expected outcome

A first external dollar within a week and $4,000 by 2026-08-10, with the owner spending less than an hour.

## Observed outcome

Thirty-one nightly cycles from 07-15 to 08-14, all with web access blocked (CLM-E3-016); twenty dev.to drafts; a stream of truth fixes; $0 at every entry; the owner's core batch of publish steps unactioned for 32 days; the Day-28 window closed on 2026-08-10 with "no natural stop condition" (CLM-E3-030). The document outlived the mission it described: the August rebuild restarted the clock without editing it (CLM-E4A-055), and the September Claude cycles cited rules that are not in it (CLM-E4B-005; CON-022). Its jail rule was enforced to the point of terminating productive cycles on 2026-09-04.

## Tradeoffs, debt and follow-ups

The two-lineage divergence from `main` became total; the ledgers grew to thousands of lines and were compacted on 2026-08-22; the ship law produced a week of one-line cross-link commits once the backlog was exhausted (CLM-E3-029). The agents' evidence discipline is also the reason this history can be written: every night's entry says what was observed and what was not.

## Unresolved questions

What the owner's own brief to Cycle 0 said beyond the quoted lines; whether the owner ever read HANDOFF-2026-07-15 before its deletion; whether the routine's instruction set after 2026-08-22 lived outside git.
