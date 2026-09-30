# Goals and definitions of success

This chapter follows every goal the project set for itself from proposal to its present state. The structured lifecycle lives in [`.project-history/doctrine/goals.yml`](../../.project-history/doctrine/goals.yml); this is the narrative reading of it. A goal's definition of success is never rewritten after the fact: when the definition changed, a new goal superseded the old one, and the chain is shown here.

Two conventions. "Said" is what a document declared at the time; "outcome" is what the evidence shows. And the project's own evidence hierarchy — dollars, then signups, then visits, then stars (P-11) — is applied to its goals as well: a goal whose success was defined in shipped surfaces is recorded as such, and not confused with one defined in money.

## The lineage at a glance

| Goal | Proposed | Statement (abridged) | Definition of success (as stated) | State on 2026-09-04 |
|---|---|---|---|---|
| G-01 | 2026-04-28 | $25k in seven days from three deadline kits | one sale in 48h; $25,000 in 7 days | abandoned next day |
| G-02 | 2026-04-29 | five-SKU autonomous webhook business | 15 acceptance items; $9k–$22k week one | superseded; $0 |
| G-03 | 2026-05-02 | a Show HN inside a deadline window | an HN URL in `launched.txt` | abandoned; two rejections; archived 08-22 |
| G-04 | 2026-05-21 | deadline-priced audits before AL2 EOL | one paid audit before 06-30 | abandoned 06-21; $0 |
| G-05 | 2026-06-21 | fourteen-day faceless conversion sprint | $300–3,000, 50+ leads, one Drift sub | abandoned; never measured |
| G-06 | 2026-07-13 | Revenue Loop v2: $4,000 by Day 28 | $4,000 collected by 08-10; first dollar ≤ Day 7 | superseded; $0 |
| G-07 | 2026-07-22 | Eve's four-week sprint | $4,000 by 08-19 | abandoned; never merged |
| G-08 | 2026-08-22 | fifteen $299 evidence reports | $4,000 by 09-19; Day-7/14/21/28 gates | blocked; checkout closed; $0 |
| G-09 | 2026-08-22 | prove the paid path before opening it | seven-step Stripe test-mode gate green | blocked; owner steps |
| G-10 | 2026-08-22 | demand evidence on free surfaces | per-bet falsifiers; one reposition | measured; +1 install on a noisy counter |
| G-11 | 2026-06-29 | external re-appraisal of the free CLI | 25 stars / 10 installs / 1 inbound in ~90 days | active; unmeasured externally |
| G-12 | 2026-06-05 | verify one real $299 purchase | purchase delivered by email, then refunded | blocked; never done |
| G-13 | 2026-09-04 | a living history | validate/render/audit/verifier pass; declarations enforced | active |

Thirteen goals; eight concern money; the dollar figure is the same $4,000 three times with three different clocks; the observed revenue against all of them is $0.

## How the definition of success moved

### From a number to a checklist (April 2026)

The first goal was a number without a mechanism: "$25k goal", "floor viability: 1 sale of any kind in 48h", set by a hosted agent for a repository that was three hours old (CLM-E1-003). Nobody could have measured it: checkout links were placeholders (CLM-E1-012). The next day's runbook replaced the number with fifteen acceptance items — four live checkout flows, a nightly benchmark, a valid ICS feed, determinism and mutation gates, a signed release, an App-opened PR, a Marketplace Action, a VS Code extension, a green status page, a submitted Show HN — and attached a forecast ($9k–$22k "realistic") conditioned on the last three (CLM-E1-019). This is the first and most consequential drift: success became a list of shipped surfaces. Most of the list was green by 2026-05-03 (CLM-E1-046). None of it was a sale. The habit of declaring "Mission Complete" against build scope rather than commerce began here (CLM-E1-012, CLM-E2-066) and was named, in June, as "confusing shipping code with making money".

### From a checklist to a date (May–June 2026)

G-03 and G-04 tied success to calendars: a Show HN in a window, an audit before Amazon Linux 2 end of support. The Show HN window slipped six times (CLM-E2-036) and two submissions were rejected by a platform rule the project had never checked (CLM-E2-031). The deadline goal was disowned before the deadline arrived: "a business whose demand arrives in 9-day spikes separated by multi-month deserts is not a business" (CLM-E2-063). The definition of success in the autopsy's replacement (G-05) is the first with a measurable funnel — a Day-14 revenue band, a lead count, a subscription — and the first to name what it depended on: "5-minute human unlocks" (CLM-E2-046). No number was ever recorded against it.

Outside the repository, the owner's portfolio set two definitions of its own in the same weeks: one real $299 purchase before driving traffic (G-12, repeated in four documents, CLM-EXT-008) and a 90-day gate for the free CLI (G-11, CLM-EXT-023). The first was never performed. The second was never reported measured.

### From a date to a clock (July 2026)

G-06 is the most precisely defined goal the project ever had: $4,000 *collected* (not booked) profit by Day 28, first external dollar by Day 7, "only live, listed, purchasable things count", with a rule that plans and prototypes score zero (CLM-E3-003). It is also the goal whose own instrument admitted it could not be met: on Day 1 the owner ruled out the one channel with built-in demand and the plan re-forecast "$0–600" (CLM-E3-008); the loop's leading indicator was a counter hard-coded to zero (CLM-E3-043); every payment-enabled channel was "first-publish KYC-gated" behind owner steps that stayed unactioned for 32 days (CLM-E3-054, CLM-E3-057). The Day-28 window closed on 2026-08-10 with the ledger noting there was "no natural stop condition" (CLM-E3-030). Eve's parallel G-07, the same $4,000 on a different clock, never left its branch.

### From a clock to a gate (August–September 2026)

G-08 kept the $4,000 and moved the deadline to 2026-09-19, computed as fifteen $299 sales (CLM-E4A-017); the operating document was not updated, so the project has carried two Day-28 clocks since (CON-027). What is new is G-09: success is first the seven-step Stripe test-mode gate on the real deployment, and checkout stays off until it is green (CLM-E4A-010). This is the first definition of success in the project's life that is about *proof of delivery* rather than shipped surfaces or a sale count, and it answers G-12's standing question directly. It is blocked on owner steps (HQ-A, HQ-C) as of HEAD (CLM-E4B-060).

G-10 is the free-surface companion: per-bet falsifiers with a mechanical rule — five live days of zero signal allows one reposition, then replacement (CLM-E4B-011). It is the only goal in the history that has been *measured* and found wanting on schedule: the VS extension failed its gate on 2026-08-30, spent its one reposition on 2026-08-31, and "passed" on 2026-09-04 by one install against a counter that flickers by one (CLM-E4B-039; CON-024). The next reading is due 2026-09-05.

### The goal this history adds (September 2026)

G-13 is the history system's own goal: agents load orientation before work and declare impact after it; render is byte-stable; the gardener finds no unrecorded material work. It is active as of this reconstruction and has not yet been exercised by CI.

## What the goal ledger reveals

**The target never learned from the outcome.** $25k, then $9k–$22k, then $300–$3,000, then $4,000, then $4,000, then $4,000. The forecasts fell; the last figure was carried across three regimes while the observed number stayed at zero. The 2026-08-22 ledger is the first to reject the arithmetic behind it: "high gross margin per hypothetical sale is not profitability or demand" (CLM-E4A-015) — and then kept the target.

**Success migrated from money to proof.** The most durable goals at HEAD (G-09, G-10, G-12) are about verifying that the machine works and that anyone wants it, which is what the June autopsy and the June owner documents had both asked for. It took eleven weeks for the repository's goals to say what the owner's documents said in early June.

**Every money goal was owner-gated at the last step.** The runbook's operator-only handoff, the June human unlocks, the July Human Queue, the September HQ-A/HQ-C — each regime's definition of success ended at a click the owner did not make. The goals were written by agents for a solo owner whose time was the scarcest input and whose absence the ledgers record without blame (P-02.2).

**Non-goals held better than goals.** The refusals — $0 spend, no cold spam, no vote rings, no fake fulfilment, no LLM prose on public pages — were honoured across every era with few breaches (see [IDEOLOGY.md](IDEOLOGY.md)). The project was more consistent about what it would not do than about what it would achieve.

## Cross-references

- Principles governing these goals: [IDEOLOGY.md](IDEOLOGY.md) and [`.project-history/doctrine/principles.yml`](../../.project-history/doctrine/principles.yml).
- The decision arcs that set or ended each goal: [DECISION_MAP.md](DECISION_MAP.md).
- Contested readings of outcomes: [`.project-history/contradictions.yml`](../../.project-history/contradictions.yml) (CON-010, CON-023, CON-024, CON-027).
