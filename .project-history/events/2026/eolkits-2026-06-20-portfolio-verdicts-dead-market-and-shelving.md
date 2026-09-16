---
id: eolkits-2026-06-20-portfolio-verdicts-dead-market-and-shelving
title: "Outside the repository: the owner's portfolio calls the paid arm a dead market, then a first wedge, then shelves it"
kind: external-constraint
scope: project-wide
components: [launch, revenue]
paths: ["launch/**", "pricing.yml", "revenue/**"]
significance: high
occurred_at: 2026-06-20
decided_at: 2026-06-29
merged_at: null
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "Between 2026-06-05 and 2026-07-15 the owner's business records ranked EOLkits the fastest path to a first dollar, sent five cold emails, killed the paid self-serve arm as a dead market, pitched it as a fundraising wedge, allocated it 30% of marketing effort, shelved the cold-sales campaign by adversarial board and froze the factory; none of these verdicts was reconciled with the others or written into the repository."
claim_ids: [CLM-EXT-005, CLM-EXT-006, CLM-EXT-007, CLM-EXT-009, CLM-EXT-010, CLM-EXT-014, CLM-EXT-015, CLM-EXT-016, CLM-EXT-017, CLM-EXT-019, CLM-EXT-021, CLM-EXT-022, CLM-EXT-023, CLM-EXT-024, CLM-EXT-038, CLM-EXT-036, CLM-EXT-013, CLM-EXT-039]
source_ids: [SRC-bizops-audit-service, SRC-bizops-root, SRC-marketing-arm, SRC-tc-master-portfolio, SRC-tc-truth-register, SRC-tc-truth-audit, SRC-allocation-brief, SRC-outreach-al2, SRC-mind-status-docs]
anchors: ["PR-free external record; see sources.yml locators for each owner document"]
related: [eolkits-2026-06-21-autopsy-never-reached-market, eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-08-22-truthful-evidence-report-rebuild]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: closed
confidence: strongly_supported
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

A ten-day portfolio monetisation sprint (2026-05-27 to 06-06) had put EOLkits in its top three with a twelve-month base forecast of $20,000 (CLM-EXT-005). On 2026-06-05 an ops agent patched 38 broken calls-to-action directly on the live VPS site and reclassified the product from "landing 404 / blocked" to "live / sellable now" (CLM-EXT-006); the same day's offer documents called it "#1 — fastest path to a first dollar" with every Stripe link returning 200 in live mode (CLM-EXT-007). Five AL2/EOLkits cold emails went out that day (CLM-EXT-009); 42 named AL2 leads were loaded on 2026-06-11 (CLM-EXT-010). The AL2 deadline was 25 days away.

## Intended beneficiaries

The owner's portfolio, deciding where a solo operator's hours should go; the leads themselves were the nominal audience of the campaign.

## Goal, non-goal and definition of success

The June docs' definition: "a stranger pays without a call", one paid audit before the cliff, and — repeated in four documents — verify one real $299 purchase before driving volume (CLM-EXT-008; G-12). The 2026-06-29 board's definition for the free CLI: 25+ stars, or 10+ genuine installs, or one unsolicited inbound within ~90 days (CLM-EXT-023; G-11). Non-goals, from the board: never cold, never buyer-intent SEO chasing, never imply production-readiness or compliance, never ship a migration PR against a stranger's production.

## Principles affirmed, introduced, weakened or challenged

Affirmed externally: "taking money and not delivering is the worst failure mode" (the June delivery-workflow docs) — the same principle the repository later wrote as P-08; open-core with the free CLI as funnel (P-17). Challenged: the founding market thesis itself — the 2026-06-20 validation held that AWS Transform and Amazon Q perform the same modernisation free, so the paid self-serve arm was "a dead market" (CLM-EXT-015).

## Alternatives considered and rejected paths

A $1,500 paid-ads plan centred on EOLkits was prepared and never activated. The 2026-06-29 board recorded a dissent ("improve the campaign — target the company not the commit author; sell a compliance artifact") and overruled it; a channel-buyer (MSP) lead was parked; the option of one opt-in launch (Show HN or r/devops) was explicitly left open (CLM-EXT-021).

## Decision and rationale

Sequence, not decision: 06-20 the paid arm is killed; 06-22 the Truth Register lists "EOLkits-paid" among nine dead offers while the same week's MASTER-PORTFOLIO presents the paid SKUs as "the first wedge" for a ~$150K ask (CLM-EXT-016); 06-26 the allocation brief ranks EOLkits #1 at 30%, contingent on the purchase test (CLM-EXT-019); 06-29 a 29-agent adversarial board shelves the cold-sales campaign as "structurally dead for this operator", keeping only the free MIT CLI as a $0 funnel (CLM-EXT-021) and executing the verdict in data — every non-Connecticut lead set to `held`, CRM contacts parked (CLM-EXT-022); 07-15 the marketing factory is frozen with "EOLkits-paid" recorded as validated dead; 07-23 a safety override de-authorises every campaign from sending (CLM-EXT-024). All of these are agent-authored deliberations under the owner's direction, not market tests; the owner's adopted position is not stated.

## Implementation and evidence anchors

Owner documents only (see `sources.yml`: SRC-bizops-audit-service, SRC-marketing-arm VALIDATION.md and _FROZEN.md, SRC-tc-truth-register, SRC-tc-master-portfolio, SRC-allocation-brief, SRC-outreach-al2 BOARD-VERDICT and STATUS). The repository carries no commit for any of these decisions; the 2026-07-13 operating document's rules against cold outreach and its bounded owner-labour budget are the nearest in-repo echo.

## Expected outcome

Each document expected something different: a first dollar within days; a raise; a redirection of hours to services; a free CLI accruing stars.

## Observed outcome

Zero replies to any cold send (CLM-EXT-009); no EOLkits cold sends after 2026-06-29; $0 revenue in every source. No later external document records whether the 90-day gates were measured. The repository's August rebuild reads as a response to the same evidence, but no external document says so — the link is the historian's inference (CON-010). The legal-entity question the board raised ("no-entity, no-insurance") was answered in-repo only on 2026-08-31 when legal pages named an LLC (CLM-EXT-038, CON-025).

## Tradeoffs, debt and follow-ups

The June pricing ladder ($299/$399/$599, $1,499, $14,999/yr, $19/mo) lived on in owner documents long after the repository retired it; the "one real purchase test" became a standing blocker restated by every later handoff and never performed (G-12). The freeze removed the only owner-side distribution capacity the product ever had.

## Unresolved questions

Which verdict the owner adopted; whether the 25-stars/10-installs/1-inbound gate was ever checked; whether the parked MSP lead or the "one opt-in launch" was ever revisited.
