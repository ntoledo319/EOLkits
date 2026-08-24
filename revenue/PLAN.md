/home/user/EOLkits
# Revenue plan — reset August 22, 2026

Note (2026-08-23 cloud cycle): WORKSPACE_ROOT above is corrected from a stale
prior-cycle local-machine path (`/home/nick/Development/active/Rupture`,
recorded by an earlier local run) to this cycle's actual repo root. This
session is a fresh isolated cloud checkout with no access to that local
machine, the GRACE VPS, or local secrets — see D25 in DECISIONS.md.

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
- Owner work: one publisher authentication and publish action.
- 28-day planning hypothesis: two Audit sales = $580.06 net. This is unobserved.
- Falsifier: after nine live days, zero extension installs and zero attributable
  Audit views; stop extension promotion and retain it only as a free utility.

## Sequence

1. Keep the reviewed repository repair on main without rewriting remote history;
   synthetic commits and obsolete publishing automation are stopped.
2. Keep the honest GitHub Pages fallback and tested `v2` Action branch green;
   the owner publishes the prepared v2.0.0 draft into the existing Marketplace
   listing.
3. Run the owner-gated exact Stripe retirement. It validates and deactivates all
   six historical catalog Prices—including $299 while fulfillment is closed—and
   only the six approved Payment Link URLs; any charge/session/subscription/
   schedule anomaly stops the containment claim. Rotate/revoke the account key
   afterward because old Cloudflare versions retain secret snapshots. The
   verified live `rupture-worker` itself is already a tested HTTP 410 tombstone.
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
main through the project-path/CI follow-ups. The replacement release workflow,
determinism and property gates, both container builds, and both GitHub Pages
deployment mechanisms passed. A public probe verified `/EOLkits` navigation,
the split API origin, and closed-product tombstones. The tested `v2` Action ref
is now publicly installable at the final `db32bdfb` acquisition commit; Action,
repository, kit, and future VS links route to the verified Pages funnel. The
honest private v2.0.0 Marketplace draft is synchronized to the same commit.
Highest-leverage next action is the owner's five-minute exact Stripe workflow/
key-rotation task because the stale GRACE API still exposes charge-capable POST
routes. The two-minute Marketplace agreement/2FA publish step follows immediately
to start measuring external distribution while the live-domain and real
payment/fulfillment gates are completed.
The exposed pre-rename Cloudflare Worker is no longer a payment bypass: public
health reports `retired: true`, its commercial and webhook paths return HTTP
410, and retirement workflow run `32591848083` passed. The old-account token
could not see a unique `eolkits.com` zone, but public DNS resolves directly to
GRACE; the Worker tombstone remains safe even if a route is reintroduced.
The active GRACE static deploy feed was safely converged on the verified main
tree at commit `c3112151`; its next observed run is expected near 07:17 UTC and
a repository workflow will verify the public domain at 07:35 UTC. Until that
probe passes, `eolkits.com` is still not counted as repaired. The API/payment
deployment remains owner-authenticated and checkout remains closed. Repository
automation also proved it has neither a known GRACE deploy transport nor the
complete runtime-secret bundle, so that identity boundary cannot be hidden in a
push. Main commit `e4109e3e` contains the reviewed Stripe closure; its Worker,
release, determinism, property, Pages, and tombstone workflows passed. The
owner-only production Stripe workflow itself has not run. No outbound message,
bid, post, or customer commitment is authorized.

Main commit `db32bdfb` now exposes a backend-independent price-qualified signal:
only a real browser/Action finding exposes a public GitHub issue form that
requires the exact $299 scope and purchase consideration. Read-only run
`32596830945` preserved the first observation; Pages, release, determinism,
property, Marketplace-draft, and public `v2` verification are green. Baseline
observed values remain zero qualified issues, zero external public `@v2` code
references, zero paid reports, and $0 collected. Bet A's five-day gate begins at
2026-08-22 20:29 UTC while checkout telemetry remains dormant behind the v2
capability handshake. The owner priority stays HQ-2 → HQ-5 → closed v2
deployment; demand instrumentation does not make the stale API safe to charge.

Cloud cycle 2026-08-23: no new owner action was added and no code/infra
changed. The prior cycle's stated blockers are unchanged and this cycle could
not independently re-check them (no VPS/local/Stripe access from this
checkout). This cycle's highest-leverage in-jail, $0, no-human-contact ship
was restocking the K1/A1 answer backlog: two fresh, verified, help-first
drafts appended to `launch/distribution/repost-answers.md` (Batch 3) for real,
currently open AWS re:Post threads found via live search this cycle — a
Node.js 18 Lambda@Edge-replica Health Dashboard confusion, and a CodeBuild
GitHub Actions runner defaulting to AL2 instead of AL2023. Both route to the
verified Pages funnel, not the unconfirmed custom domain (see D25). Owner
work remains unchanged: HQ-2 through HQ-7 in that order, plus now optionally
pasting the two new Batch 3 answers (no new owner minutes required until they
choose to paste them; posting is their action, not a queue item with a
deadline). Collected profit remains $0; gap remains $4,000.

Cloud cycle 2026-08-24: another isolated cloud checkout, no code/infra
changed, no new owner-queue item added. WebFetch was again `EGRESS_BLOCKED`
for a neutral control; WebSearch worked and was used, cross-checked across
multiple independent results per finding (see D26). This cycle's
highest-leverage in-jail, $0, no-human-contact ship was one more restock of
the K1/A1 answer backlog: one fresh, unique, help-first draft appended to
`launch/distribution/repost-answers.md` (Batch 4) for a real, currently open
AWS re:Post thread (`QUowJJh-50R3KbxGrZ2YNsCA`, a Python 3.9 Lambda
`Runtime.Unknown` INIT-phase failure caused by an automatic runtime-version
bump breaking a native dependency). Several other candidate threads found
this cycle already had substantive community answers and were skipped rather
than padded (D26). Owner work remains unchanged: HQ-2 through HQ-7 in that
order, plus optionally pasting the new Batch 4 answer whenever convenient.
Collected profit remains $0; gap remains $4,000.

Main commit `951fd4b6` adds the strongest remaining autonomous discovery action:
an official-protocol IndexNow workflow for the verified Pages corpus. It checks
the already-public ownership key, confines submissions to the `/EOLkits/`
prefix, caps the batch, maps ordinary pushes to changed/deleted HTML, and treats
HTTP 200/202 only as receipt. Bootstrap run `32597777674` accepted the 51-URL
sitemap batch; every release/Pages/property/determinism gate also passed. Fresh
acquisition run `32597777625` still observed 0 qualified issues, 0 external
public `@v2` references, no v2.0.0 public release, 1 star, and 0 forks. Therefore
the next leverage remains owner HQ-2 then HQ-5; do not build another SKU or move
the August 27 falsifier forward because of an indexing notification.
