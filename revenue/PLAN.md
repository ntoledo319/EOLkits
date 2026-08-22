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
- Owner work: open the already-prepared private v2.0.0 draft, check the existing
  Marketplace listing, and publish it with 2FA. The tested `@v2` branch already
  works for direct installs.
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
- Owner work: one dispatch and verification against the already-public
  `rupture.rupture-vscode` listing; no new publisher or listing.
- 28-day planning hypothesis: two Audit sales = $580.06 net. This is unobserved.
- Falsifier: after five full v1.1.0 days, zero install/download growth and zero
  external VS-attributed qualified-interest authors triggers one repositioning;
  four more zero-signal days stop promotion and leave only the free utility.

## Sequence

1. Keep the reviewed repository repair on main without rewriting remote history;
   synthetic commits and obsolete publishing automation are stopped.
2. Run the owner-gated exact Stripe retirement. It validates and deactivates all
   six historical catalog Prices—including $299 while fulfillment is closed—and
   only the six approved Payment Link URLs; any charge/session/subscription/
   schedule anomaly stops the containment claim. Rotate/revoke the account key
   afterward because old Cloudflare versions retain secret snapshots. The
   verified live `rupture-worker` itself is already a tested HTTP 410 tombstone.
3. Keep the honest GitHub Pages fallback and tested `v2` Action branch green;
   immediately after Stripe containment, the owner publishes the canonical
   v2.0.0 draft into the existing Marketplace listing and dispatches the guarded
   in-place VS update. These distribution releases do not wait for checkout.
4. Deploy Audit v2 with checkout disabled and complete the full Stripe test-mode
   operational gate.
5. Supply the truthful legal/controller values and remove the false public DEV
   corpus, then enable Audit checkout only
   if every gate is green and incremental hosting cost is $0.
6. Measure dollars, purchases, checkout starts, qualified Audit views, Action
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

Collected profit: **$0**. Gap: **$4,000**. Checkout: **closed**.

The strongest autonomous conversion repair is now public. Main contains green
product commit `9c231b58`, and the installable `v2` ref resolves to it; the verified Pages
funnel exposes an actual four-page report created by the paid report engine,
its entirely fictional ZIP input, and a hash/evidence manifest:

- https://ntoledo319.github.io/EOLkits/audit/
- https://ntoledo319.github.io/EOLkits/audit/sample/eolkits-sample-report.pdf
- https://ntoledo319.github.io/EOLkits/audit/sample/fictional-repository.zip
- https://ntoledo319.github.io/EOLkits/audit/sample/eolkits-sample-report.json

The public PDF is 29,392 bytes with SHA-256
`855c793c8b2735f54fad08465f05c50943cb7908fd194b43dacf0eca9c423d9a`.
The replacement release, determinism, property, custom Pages, and built-in Pages
workflows passed. The first Pages attempt failed because native WeasyPrint/font
stacks can serialize an equivalent PDF differently; the corrected gate preserves
the published artifact's exact hash and compares every renderer-independent
engine field. That failure is recorded, not hidden.

The current canonical private v2.0.0 Marketplace draft was created by green run
`32604619021` at commit `a9cdcaeb`; its Action files are byte-identical to public
`v2` at `9c231b58`. An older direct draft URL in the owner queue was stale and has
been replaced. The Marketplace itself still advertises v1.1.0.
The GRACE static feed now points at two-parent commit `0780909c` with the exact
final tree, but `eolkits.com` still serves Migration Pack/Drift Watch copy and
`/api/capabilities` returns 404 until the next observed deploy or owner rollout.

Observed demand remains zero: 0 qualified issues, 0 paid reports, 1 repository
star, 0 forks, and $0 collected. Bet A's first five-full-day falsifier remains
2026-08-27 20:29 UTC; internal downloads and release probes do not move it.

The strongest recovered distribution asset is the existing
`rupture.rupture-vscode` listing: it is v1.0.0, adjacent queries returned a
100–101 install-counter range, and downloads were 162. The published version
sends users to a dead `/Rupture/audit` URL. Repository commit `a9cdcaeb` now
contains the fully green v1.1.0 candidate, which preserves that identity and
legacy user settings/commands, repairs the verified Audit route, and measures
only user-submitted, findings-qualified VS interest. Marketplace v1.1.0 is not
public yet, and the approximate counters are not demand or revenue.

Public guard commit `32d01c2f` pins publication to exact green candidate
`a9cdcaeb`, rejects non-owner dispatch/reruns and wrong confirmation values, and
passed release, determinism, property, and Pages CI. This closes the repository
release gate; it does not mean v1.1.0 has been published.

Highest-leverage next action is the five-minute HQ-2 exact Stripe closure/key
rotation because the audit may expose anomalous commerce state. Immediately
afterward, use the same owner sitting for the three-minute HQ-5/HQ-6 distribution
batch: publish the canonical GitHub draft and dispatch the owner-guarded in-place
VS update. Both releases route to the fail-closed Pages funnel and can start
acquisition before commerce opens. Then complete legal facts, the closed GRACE
fulfillment proof, and false-post removal before enabling the single $299 Price.
Do not create another VS publisher, add a product, lower the price, or call
installs/auto-updates demand evidence.
