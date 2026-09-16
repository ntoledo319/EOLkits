---
id: eolkits-2026-07-15-repost-answers-only-demand-test
title: "The only demand test: three answers on AWS re:Post, a content flywheel that could not verify itself, and a Day-28 window that closed at $0"
kind: experiment
scope: launch
components: [launch, revenue, web]
paths: ["launch/distribution/**", "launch/gumroad/**", "revenue/**", "docs/status/**"]
significance: high
occurred_at: 2026-07-15
decided_at: 2026-07-15
merged_at: 2026-08-22
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "The one real distribution act of the revenue loop was the owner pasting three drafted answers to AWS re:Post on 2026-07-15; everything else — twenty dev.to drafts auto-published without review or fact-check, a $79 Gumroad bundle never listed, five marketplace publishes never clicked — waited on owner steps, while the loop's own leading indicator was a counter hard-coded to zero; the Day-28 window closed on 2026-08-10 with $0 and no stop condition."
claim_ids: [CLM-E3-012, CLM-E3-013, CLM-E3-015, CLM-E3-016, CLM-E3-017, CLM-E3-018, CLM-E3-019, CLM-E3-020, CLM-E3-026, CLM-E3-027, CLM-E3-028, CLM-E3-029, CLM-E3-030, CLM-E3-043, CLM-E3-044, CLM-E3-053, CLM-E3-057, CLM-EXT-025, CLM-EXT-026]
source_ids: [SRC-repo-git, SRC-openclaw-launch]
anchors: ["649f3467d426ceafcabe85435d577d94b38a1126", "ab7046b356ece95d59c3a7d28a208acefffd8cb4", "565cccec4b347ed0ac42d81a440bc77c76d3a9d3", "cd0e1967e7cb33c2aefe21652704bec0a915a318", "a93ff2f28081e615d73df585989ae895e15181e1", "4080f55d9ad0c213ae8a27a392ba5aa5fbc34902", "2bcf1eacd441f43df12010ea6f20231c8a6e8416", "3314d93ff2174cd34fbe918f24268f9f888f06b6"]
related: [eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-07-14-billing-honesty-sku-retirement, eolkits-2026-08-22-free-surfaces-made-truthful]
amends: []
supersedes: []
superseded_by: [eolkits-2026-08-22-free-surfaces-made-truthful]
reversed_by: []
status: superseded
confidence: strongly_supported
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

"~0 qualified traffic has reached the working funnel"; the money rail had just been verified live (CLM-E3-011); the operating document forbade cold email and DMs and demanded an externally visible change every night. The only "closest-to-a-buyer, $0, TOS-clean move" the routine could find was answering questions where buyers already were.

## Intended beneficiaries

Engineers asking AL2 and Lambda runtime questions on AWS re:Post; readers of dev.to; buyers of a $79 bundle who would never pay $299.

## Goal, non-goal and definition of success

Goal: the first `checkout_click` on `/status`, watched as the leading indicator (CLM-E3-043); a first dollar from any channel. Non-goals: posting anything autonomously to a human forum ("draft-never-post"), bulk outreach, "manufacturing busywork to imply otherwise".

## Principles affirmed, introduced, weakened or challenged

Affirmed P-09 for forum answers (drafts only; the owner posted). Weakened P-09 and P-07.2 for dev.to: articles were published under the owner's account by the VPS cron with `published: true`, no per-article review and — because egress was blocked — no external fact-check (CLM-E3-017, CLM-E3-018, CLM-E3-020; CON-013). Exposed P-11: the counters the loop baselined as "0/0/0 observed" were constants in both the build seed and the workflow (CLM-E3-043), and the bot's own status file said the backend was down every day (CLM-E3-044).

## Alternatives considered and rejected paths

Stack Overflow answers were drafted as backlog only; Lemon Squeezy was scored but Gumroad chosen for the bundle; selling the bundle through the site's own Stripe rail was written into the plan as the fallback if Gumroad's KYC failed (CLM-E3-026). At the Day-21 gate and Day-28 close, a pivot was rejected as applicable only to "underperforming live bets" — every bet was still blocked on unactioned owner steps (CLM-E3-030).

## Decision and rationale

Draft ten answers, hand three to the owner, restock automatically; keep the flywheel fed with sourced articles; build the bundle end to end and queue its listing. The rationale was the ship law and the belief that backlinks from dev.to's authority were the answer to "the #1 new-domain bottleneck" (CLM-E3-028). The historian notes that the routine's reading of own-content publishing as not "contact" was defensible under the document's letter and was reversed by the next regime.

## Implementation and evidence anchors

649f3467d426ceafcabe85435d577d94b38a1126, ab7046b356ece95d59c3a7d28a208acefffd8cb4 and 565cccec4b347ed0ac42d81a440bc77c76d3a9d3 (2026-07-15: drafts, "owner posted", auto-restock); cd0e1967e7cb33c2aefe21652704bec0a915a318 (2026-07-18 Gumroad bundle); a93ff2f28081e615d73df585989ae895e15181e1 (PUBLISH-CHECKLIST with verified one-time commands for PyPI, npm, VS Code Marketplace, Open VSX and the Action Marketplace, none executed, CLM-E3-027); 4080f55d9ad0c213ae8a27a392ba5aa5fbc34902 and the Sunday article commits (CLM-E3-015); 3314d93ff2174cd34fbe918f24268f9f888f06b6 (the first of a week of one-line cross-link commits, CLM-E3-029); 2bcf1eacd441f43df12010ea6f20231c8a6e8416 (2026-08-10 Day-28 close). An OpenClaw workspace outside the repository prepared a parallel dev.to article and publisher on 2026-07-23 that also never had a key (CLM-EXT-025).

## Expected outcome

Approval of the answers, a trickle of qualified traffic, a first click, then a first bundle sale.

## Observed outcome

No approval, traffic or click signal was ever recorded; re:Post drafting stalled for 31 cycles because the routine could not fetch new threads (CLM-E3-016). Whether articles 05–24 were live on dev.to during July is unknown in-repo (CLM-E3-019); the August ledgers later report 25 posts public with "seven reactions and zero comments combined" (CLM-E4B-066). The Gumroad bundle stayed owner-gated all era and its build script was deleted on 2026-08-22. The core batch of owner steps was recorded unactioned for 32 days (CLM-E3-057). $0 at the Day-28 close (CLM-E3-012).

## Tradeoffs, debt and follow-ups

A published corpus of agent-written articles with at least two wrong dates (CLM-E4A-051) that the owner is still asked to unpublish (HQ-D); padding duplicates the routine itself flagged (CLM-E3-053); a demand test whose instrument could not register a result. The August rebuild replaced the counter with `null`, the beacon with a GitHub issue form, and the publisher with quarantine.

## Unresolved questions

Whether the three re:Post answers were approved and read; whether `DEVTO_API_KEY` was on the box in July; the source of "78 of the last 81 submissions were spam".
