---
id: eolkits-2026-07-14-billing-honesty-sku-retirement
title: "Billing honesty: two SKUs that charged real money for nothing, three agents with three remedies, and a fix that reached production only by archiving the prices"
kind: pricing
scope: grace-api
components: [grace-api, runner, web, pricing]
paths: ["pricing.yml", "apps/grace-api/**", "apps/runner/**", "apps/web/templates/**"]
significance: foundational
occurred_at: 2026-07-14
decided_at: 2026-07-16
merged_at: 2026-08-22
released_at: 2026-08-25
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "Between 2026-07-14 and 08-14 the project discovered that Drift Watch ($19/mo) and Org License ($14,999/yr) had live Stripe checkout with stub fulfilment and that a Migration Pack path could charge $1,499 and deliver nothing; the site checkout was pulled, an agent persona named Eve deleted both SKUs on a branch that never merged, the nightly routine closed the live endpoint 23 days later, and the retired prices were archived in Stripe only on 2026-08-25."
claim_ids: [CLM-E3-022, CLM-E3-023, CLM-E3-024, CLM-E3-025, CLM-E3-031, CLM-E3-032, CLM-E3-033, CLM-E3-034, CLM-E3-035, CLM-E3-037, CLM-E3-038, CLM-E3-039, CLM-E3-041, CLM-E3-042, CLM-E3-045, CLM-E3-056, CLM-E3-058, CLM-E1-027, CLM-E4A-012, CLM-E4A-013, CLM-E4A-040, CLM-E3-036, CLM-E3-040]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs]
anchors: ["23516eef93b1b714435d3ce7e800cd7d1db3d2ef", "2a843b918042743a8a32e715902cc376705b3a08", "edfba40fb5a872f6257402986a1e9c34f1286255", "cdb460ecc96a1da59735eb4dd9ab44c8bad9c1d7", "587d5d4d6a7d95167c455cb24cdae524bc283fd1", "1abb8f26e7c2f1265d792e8ce78ea2baa405fd99", "a75343f344e91ee1bcf68d85382db62adad686f7"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-08-22-truthful-evidence-report-rebuild, eolkits-2026-08-22-legacy-commerce-retirement]
amends: []
supersedes: []
superseded_by: [eolkits-2026-08-22-truthful-evidence-report-rebuild]
reversed_by: []
status: superseded
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The April runbook priced five SKUs before they could fulfil: the migration-PR runner was a stub on the day it was sold (CLM-E1-027); Drift Watch's checkout and upsell were added on 2026-06-08 with a no-op `handle_drift_watch_setup` (CLM-E3-022); Org License generated a real key on payment and never sent it (CLM-E3-023). The pricing ladder at the start of July was unchanged since 2026-06-11 (CLM-E3-025). The operating document's "do no harm" rule and "NEVER fake-fulfill" made this a violation the moment it was noticed.

## Intended beneficiaries

The stranger who might have been "charged monthly forever for nothing" — the operating doc's phrase — and, by extension, the project's claim to be trustworthy.

## Goal, non-goal and definition of success

Goal: no path can create a charge for a product that cannot be delivered. Non-goal, stated by the routine: implementing the fulfilment, "a multi-day feature" with "the security sensitivity of assuming a customer's IAM role". Success was defined only negatively — nothing blows up on traffic.

## Principles affirmed, introduced, weakened or challenged

Introduced P-08 in code. Affirmed P-12's "displayed price equals charged price" by removing prices that had no product behind them. Challenged the April autonomy premise (P-02): the SKUs existed because the runbook required every tier to fulfil itself by webhook, and two of them never could.

## Alternatives considered and rejected paths

Three remedies from three agents, never reconciled in discussion (CON-015): the routine fixed Org License delivery on 2026-07-19 (edfba40fb5a872f6257402986a1e9c34f1286255); Eve deleted both SKUs from `pricing.yml`, API, runner and site on 2026-07-22 (cdb460ecc96a1da59735eb4dd9ab44c8bad9c1d7); the August rebuild marked them "Product research only" with 410 responses. Asking the owner to click through the Stripe dashboard was queued (HQ-5) and later rejected as error-prone in favour of an audited workflow (CLM-E4A-040).

## Decision and rationale

Stop selling first, decide the product later. The routine's 2026-07-16 site change replaced Drift Watch's self-serve checkout with a "coming soon" waitlist (2a843b918042743a8a32e715902cc376705b3a08); the 2026-07-14 fix closed the Migration Pack money-loss path where a blank installation id dead-lettered the job and skipped the refund (23516eef93b1b714435d3ce7e800cd7d1db3d2ef, CLM-E3-024). Eve's rationale is quoted in her commit: "fulfillment was never implemented — they charged a card and delivered nothing" (CLM-E3-033).

## Implementation and evidence anchors

As above, plus: 587d5d4d6a7d95167c455cb24cdae524bc283fd1 (2026-08-10, Eve's branch merged by the owner only into a local branch built on the stale `origin/main` lineage — "NOT DEPLOYED" — with README corrections dropping the "30-day money-back" claim, CLM-E3-038, CLM-E3-039); 1abb8f26e7c2f1265d792e8ce78ea2baa405fd99 (2026-08-14: the routine finds `POST /api/drift/checkout` still live on the deploy lineage and returns 410, rewriting the test that had asserted the harmful behaviour, CLM-E3-031); a75343f344e91ee1bcf68d85382db62adad686f7 (2026-08-25 Stripe preflight before six prices were archived).

## Expected outcome

No further exposure; a clean catalogue for the launch that Eve's sprint planned for August.

## Observed outcome

No charge is evidenced in any era. No grace-api change of July reached the VPS during July or August (CLM-E3-042); the live endpoint was closed on the domain only when the Stripe prices were archived on 2026-08-25 (CON-018). Eve made three commits and vanished after 2026-07-22 (CLM-E3-032); her launch pack, dev.to draft and sprint plan stayed on an orphan branch (CLM-E3-037). The routine on the deploy lineage never mentions the branch and re-fixed the same endpoint 23 days later (CLM-E3-041).

## Tradeoffs, debt and follow-ups

Two conflicting treatments of Org License; a committed `docs/` artefact on Eve's branch contrary to the source-only convention (CLM-E3-035); hand-maintained fixes applied to both lineages on the same morning (CLM-E3-058). The arc is the direct lineage of the August "truthful evidence report" rebuild, which retired the whole catalogue rather than repairing it.

## Unresolved questions

Whether any Drift Watch or Org License payment link was ever used; why the 08-10 merge was made onto the stale lineage and abandoned; whether Eve's sprint was consciously dropped or simply overtaken.
