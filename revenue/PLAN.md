/home/nick/Development/active/Rupture
# Revenue plan — reset August 22, 2026

## Reality

Collected revenue is $0. Profitability has not been established. The repository
had a broad, apparently automated product suite, but only one paid deliverable
can be made truthful and bounded today: a static evidence PDF derived from one
repository ZIP or supported source file.

The live site observed on August 21 still advertised unavailable products and
unsafe claims. This repair closes those offers, ships a truthful static funnel,
and keeps Audit checkout off until its real deployment completes the operational
gate. Code passing tests is not evidence that Stripe, Resend, DNS, storage, or
refund operations work together.

## Target and arithmetic

Target: $4,000 cumulative collected profit by September 19, 2026.

Stripe's published US domestic online-card fee is 2.9% + $0.30. At a $299 price:

- processing fee per successful sale: $8.97;
- net per sale before refunds: $290.03;
- 14 no-refund sales: $4,060.42; and
- 15 initial sales with one full refund: $4,051.45 because the original $8.97
  processing fee is not returned.

The operating target is therefore 15 initial sales, not 14. This arithmetic is
a target, not a forecast. It assumes the existing GRACE capacity adds $0
incremental hosting cost; the owner must confirm that before checkout opens.

Source: https://stripe.com/pricing (checked August 22, 2026).

## Portfolio

### Bet A — Fast: existing GitHub Marketplace Action to Audit

- Offer: free, bounded repository checks from the existing Marketplace listing;
  each report links to the $299 Audit availability page.
- Funnel: GitHub Marketplace search/listing → workflow run → actual finding →
  bounded job-summary link → Audit upload → Stripe Checkout.
- Distribution advantage: the listing already exists at
  https://github.com/marketplace/actions/rupture-aws-deprecation-check.
- Owner work: publish the reviewed v2 release through the existing listing.
- 28-day planning hypothesis: three Audit sales = $870.09 after processing fees.
  This is not observed demand.
- Falsifier: after five full live days, zero external Action runs or zero
  attributable Audit page views. Reposition once; replace after four more live
  days with no signal.

### Bet B — Heavy: $299 repository evidence report

- Offer: one static source-analysis PDF with exact file/line matches, observed
  counts, cited sources, an input SHA-256, evidence fingerprint, remediation
  order, and explicit limitations.
- Funnel: Action, VS extension, browser scanner, and cited fix/deadline pages →
  Audit sample → capability-gated upload → Stripe → PDF/email/download.
- 28-day planning hypothesis: eight sales = $2,320.24 net. Fourteen no-refund
  sales clear the target; current evidence does not justify forecasting fourteen.
- Falsifier: 100 qualified Audit page views with zero checkout starts, or 20
  valid checkout starts with zero purchases. Test one price/trust change, then
  replace rather than rationalize.
- Mandatory gate: test-mode checkout → verified webhook → exactly one job →
  real PDF → Resend delivery → signed download → matching verification record,
  plus a failed-fulfillment refund/reconciliation exercise.

### Bet C — Compounding: VS Marketplace + honest search corpus

- Offer: free local VS scanner and primary-source fix/deadline pages; both route
  relevant users to the same Audit page.
- Funnel: VS Marketplace/editor search and organic error searches → local
  finding or answer page → Audit sample/availability.
- Owner work: one publisher authentication and publish action.
- 28-day planning hypothesis: two Audit sales = $580.06 net. This is unobserved.
- Falsifier: after nine live days, zero extension installs and zero attributable
  Audit views; stop extension promotion and retain it only as a free utility.

## Sequence

1. Keep the reviewed repository repair on main without rewriting remote history;
   synthetic commits and obsolete publishing automation are stopped.
2. Keep the honest GitHub Pages fallback green; the owner creates the `v2` tag
   from final main while publishing the existing Marketplace Action release.
3. Archive legacy Stripe links and remove the legacy Cloudflare commerce route.
4. Deploy Audit v2 with checkout disabled and complete the full Stripe test-mode
   operational gate.
5. Update the existing GitHub Marketplace listing and publish the tested VSIX.
6. Supply the truthful legal/controller values, then enable Audit checkout only
   if every gate is green and incremental hosting cost is $0.
7. Measure dollars, purchases, checkout starts, qualified Audit views, Action
   usage, and extension installs. Do not count tests, commits, posts, or stars as
   demand.

## Gates

- Day 7 — August 29: any bet live at least five days with no external signal
  gets one positioning/channel change.
- Day 14 — September 5: replace a repositioned bet after four more live days
  with no signal; recompute the gap from collected dollars.
- Day 21 — September 12: if collected profit and qualified funnel evidence
  cannot mathematically close the remaining gap, report that plainly. Do not
  reopen unproved high-ticket products.
- Day 28 — September 19: report collected profit, processor fees, refunds, and
  incremental costs only.

## Current gap and next action

Collected profit: $0. Gap: $4,000. Checkout: closed. The repaired release is on
main and its five initial GitHub workflows passed, including container and Pages
jobs. Highest-leverage next action: complete the owner queue's live-domain and
real payment/fulfillment gates, then publish the `v2` Marketplace release. The
live `eolkits.com` deployment is not yet repaired. No outbound message, bid,
post, or customer commitment is authorized.
