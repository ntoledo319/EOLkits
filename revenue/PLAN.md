/home/nick/Development/active/Rupture
# Revenue plan — reset August 22, 2026

## Reality

Collected revenue is $0. Profitability has not been established. The repository
had a broad, apparently automated product suite, but only one paid deliverable
can be made truthful and bounded today: a static evidence PDF derived from one
repository ZIP or supported source file.

The custom site observed on August 25 now closes unavailable products and serves
the truthful single-$299 static funnel. Its hosting layer nevertheless injects
an unreviewed analytics script into every tested page. The August 26 static
deployment added the generated meta CSP and blocks that exact external script,
but the raw injection remains, the verifier is red, and a host-controlled inline
injection could bypass that containment. The domain remains unsafe for checkout
until the injection is removed. Code passing tests is not evidence that Stripe,
Resend, DNS, storage, privacy, or refund operations work together.

## Target and arithmetic

Target: $4,000 cumulative collected profit by September 19, 2026.

Stripe's published US standard online-card fee is 2.9% + $0.30 for domestic
cards, plus 1.5% for international cards and another 1% when currency conversion
is required. At a $299 price:

- domestic processing fee: $8.97; domestic net: $290.03;
- international-plus-conversion fee: $16.45; conservative net: $282.55;
- 14 no-refund domestic sales: $4,060.42;
- 15 domestic sales with one full refund: $4,051.45, but the same mix using
  international cards plus conversion nets only $3,939.25; and
- 16 international-plus-conversion sales with one full refund: $4,221.50,
  including the additional $0.30 refund fixed fee in Stripe's July 2026 policy.

The provisional operating target is therefore **16 initial sales**, not 15.
This is a target, not a forecast, and still assumes a US standard-pricing Stripe
account plus $0 incremental GRACE hosting cost. The owner must confirm account
country, actual fee schedule, charge/settlement currency, and hosting cost before
checkout opens; the target must be recomputed if any assumption differs.

Source: https://stripe.com/pricing (checked August 27, 2026).

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
- Channel-attribution hypothesis: three of the portfolio's Audit sales arrive
  through the Action = $870.09 net. These are a subset of Bet B's paid-unit
  total, not additive revenue, and this is not observed demand.
- Falsifier: after five full live days, zero external Action runs or zero
  attributable Audit page views. Reposition once; replace after four more live
  days with no signal.

### Bet B — Heavy: $299 repository evidence report

- Offer: one static source-analysis PDF with exact file/line matches, observed
  counts, cited sources, an input SHA-256, evidence fingerprint, remediation
  order, and explicit limitations.
- Funnel: Action, VS extension, browser scanner, and cited fix/deadline pages →
  Audit sample → capability-gated upload → Stripe → PDF/email/download.
- Grounded 28-day planning hypothesis: eight total sales across every channel =
  $2,320.24 net. That leaves a $1,679.76 gap to the target. Six additional
  domestic no-refund sales would close it; the conservative operating buffer
  instead needs eight additional initial sales to reach 16 total. Current
  evidence does not justify forecasting those eight.
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
- Distribution state: v1.1.0 is public on the existing
  `rupture.rupture-vscode` listing; no owner action remains for this release.
- Channel-attribution hypothesis: two of the same portfolio Audit sales arrive
  through VS/search = $580.06 net. They are not additive to Bet B's total, and
  this is unobserved.
- Falsifier: after five full v1.1.0 days, zero install growth and zero external
  VS-attributed qualified-interest authors triggers one repositioning;
  four more zero-signal days stop promotion and leave only the free utility.

## Sequence

1. Keep the reviewed repository repair on main without rewriting remote history;
   synthetic commits and obsolete publishing automation are stopped.
2. Keep the completed exact Stripe retirement closed. Workflow run `32840968816`
   deactivated all six historical Prices, proved the bounded session/
   subscription/schedule state, removed the current Worker binding, and left
   the Worker as an HTTP 410 tombstone. The owner must still rotate/revoke the
   account key because historical Cloudflare versions retain secret snapshots.
3. Keep the honest GitHub Pages fallback, tested `v2` Action branch, and public
   VS v1.1.0 release green. The owner publishes the sole canonical v2.0.0 draft
   into the existing GitHub Marketplace listing; obsolete drafts are gone.
4. Deploy Audit v2 with checkout disabled and complete the full Stripe test-mode
   operational gate. Remove the hosting-layer analytics injection, deploy the
   generated CSP, and require the custom-domain verifier to pass first.
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

Collected profit: **$0**. Gap: **$4,000**. Checkout: **closed**. This is the
workspace evidence ledger, not a claim about account-wide Stripe activity that
the workspace cannot observe.

The exact Stripe retirement and VS v1.1.0 publication are complete. The official
Gallery moved from the 103-install/166-download release baseline to 103 installs
and 183 downloads by 2026-08-27T00:32Z: +17 cumulative downloads and zero
install growth. The latest acquisition observation still shows zero qualified
issues, zero external authors, zero VS-attributed qualified authors, zero public
external `@v2` references, one star, and zero forks. Downloads can include
update/package fetches; none of these values is a sale.

GitHub Marketplace still exposes v1.1.0 and no public v2.0.0 release. Exact
preflight cleanup removed the two obsolete untagged release drafts. Canonical
private draft `375063073` remains the sole draft, targets `a9cdcaeb`, and
still requires the owner's Marketplace agreement, checkbox, and 2FA. Repository
metadata now avoids the overbroad “unpatched” claim and points its homepage to
the verified free-first Pages surface.

The custom host deployed the static CSP at 07:17 UTC on August 26, but raw HTML
on all five tested pages still contains the host-injected
`stats.saiditright.com` script. Scheduled verifier `32946397287` correctly
failed on that injection. `/api/capabilities` and `/api/status` still return
404, `/health` still exposes the legacy filesystem/SQLite/inline service, and
the latest capability audit remains `deploy_transport=false` /
`runtime_bundle=false`. Do not weaken the verifier, notify IndexNow for the
custom host, or enable payment.

Daily exact VS telemetry plus qualified-interest measurement is now public and
validated by run `33028483868` / artifact `9629312207`. The next autonomous gate
is the August 30 five-full-day V1 falsifier check; daily observations continue in
the meantime. The next owner actions, in required order, remain: legacy Stripe
key rotation, then Marketplace publication; truthful legal facts; GRACE v2
checkout-closed deployment plus injection removal and complete test/refund E2E;
DEV unpublication; then the exact $299 checkout enablement. Do not create another
product, claim cumulative downloads as demand, or substitute repository polish
for those cash-path gates.

## Cycle note — August 27, 2026 (cloud, egress-restricted)

This cycle's outbound fetch to external domains (including the neutral control
`example.com` and the two domains the standing repost-answers priority and
AWS-date verification duty need, `example.com`/`docs.aws.amazon.com`/
`repost.aws`) returned `EGRESS_BLOCKED`/403. Per AGENTS.md's fallback, no new
repost-answers batch or dev.to draft was produced — see DECISIONS D42. Shipped
a smaller, verifiable, in-jail fix instead: `rules/public/deprecations.yml`
was missing a tracked `nodejs16.x` entry that the free scanner engine and
`fixes.yml` already carry correctly (Q1-2027 block cluster, same AWS source
already cited by every sibling entry). Added it, rebuilt the static site, and
confirmed `pytest -q apps/web` passes 35/35 with the CI env vars. This is a
free-acquisition-surface correctness fix, not a cash-path change: HQ-1 through
HQ-5 and HQ-7 are unchanged and still require the owner. Collected profit
remains $0; gap remains $4,000.

## Cycle note — August 28, 2026 (cloud, egress-restricted)

Repeated the egress test: `WebFetch` on `example.com` and a direct proxy
`curl` to both `example.com` and `docs.aws.amazon.com` all returned
`EGRESS_BLOCKED`/HTTP 403, confirmed as a domain-level block (proxy itself is
up per `$HTTPS_PROXY/__agentproxy/status`). Per AGENTS.md's fallback, no new
repost-answers batch or dev.to draft was produced — see DECISIONS D43.

Shipped a different in-jail fix: `apps/web/BUILD_DATE`, the single date every
generated countdown/ICS-timestamp/sitemap-lastmod/status-timestamp derives
from, had not been bumped since the initial 2026-08-22 repair commit despite
five subsequent content cycles — every "days until deadline" on the live site
was silently overstating runway by 6 days. Bumped it to 2026-08-28, rebuilt,
and confirmed `pytest -q apps/web` is still 35/35 with the CI env vars; the
diff is entirely date-derived (e.g. shared `/migrate/` countdowns moved
163→157 days). Nothing currently alerts on this drift, so future cycles should
keep bumping `BUILD_DATE` whenever they ship, and periodically otherwise.

Also evaluated extending the nodejs16.x-style fix to the scanner's two "bonus"
runtimes (`ruby3.2`, `dotnet6`) and declined: unlike nodejs16.x, they have no
second corroborating source file and can't be freshly verified against
`docs.aws.amazon.com` this cycle. Left as a deferred, recorded gap rather than
publishing an unverified date. HQ-1 through HQ-5 and HQ-7 are unchanged and
still require the owner. Collected profit remains $0; gap remains $4,000.

## Strict blocker state — 2026-08-22T23:47:26Z

This is the third consecutive goal turn ending at the same external-authority
boundary. Fresh public evidence still shows zero Stripe-retirement runs, no new
VS publish run, VS v1.0.0, GitHub Marketplace v1.1.0, no public v2.0.0 release,
HTTP 404 for GRACE capabilities, zero qualified issues, and $0 collected.

The goal remains $4,000 collected profit; it is not complete. No safe legal
autonomous task can make checkout live or publish under the owner's identities.
Resume immediately when any owner queue item changes external state. The fastest
resume event is a run URL from HQ-2; next are publication of the canonical
GitHub draft or dispatch of guarded VS v1.1.0. Until one occurs, do not replace
the blocked cash path with product polish, another offer, or synthetic demand.

## Resumed cycle state — 2026-08-25T10:07:45Z

This cycle shipped a real customer-visible security improvement, so it is not an
analysis-only cycle. Pages is live with CSP containment, the canonical GRACE
feed carries the same exact tree, and unsafe custom-domain search notification
is mechanically blocked. The remaining custom-host deployment/privacy step is
folded into HQ-3 rather than creating another product bet.

Workspace-observed collected profit remains **$0** and the target gap remains
**$4,000**. No authenticated Stripe dashboard result appeared, so $0 is the
workspace evidence ledger—not a claim that the unseen account has no charges.
There are still 0 qualified issues and 0 paid reports; VS remains v1.0.0 and the
GitHub Marketplace remains v1.1.0. Bet A's first five-full-day checkpoint stays
2026-08-27 20:29 UTC.

Highest-leverage next action is unchanged: HQ-2 exact Stripe closure/key
rotation, immediately followed by HQ-5 and HQ-6 in the same eight-minute owner
batch. Then HQ-3 removes the injected script, deploys Audit v2 checkout-closed,
and proves end-to-end test fulfillment. Do not enable HQ-7 or rerun custom-domain
IndexNow until both the live CSP and absence of external scripts are verified.

## Hands-off execution state — 2026-08-25T11:21:00Z

The external state materially advanced. Exact Stripe retirement run
`32840968816` is green, including the independent final containment audit and
Worker secret/tombstone cleanup. Exact VS publication run `32841331222` is green
and its public v1.1.0 package is downloadable. The official Gallery index
exposed v1.1.0 at 11:21:39 UTC with a 103-install / 166-download baseline. Both
temporary authorization triggers were removed; permanent publication workflows
are manual-only again. Restoration head `a8e8b45c` has tree `cb5a151b`, and every
workflow on that head passed.

Workspace-observed collected profit is still **$0** and the gap is still
**$4,000**. Checkout remains **closed**. The completed Stripe audit establishes
the bounded catalog/session/subscription state, but the workspace still cannot
observe account-wide charges or rotate the account key. There are still zero
qualified Audit issues and zero paid reports. VS publication creates
distribution, not revenue.

Next actions, in leverage order:

1. Measure VS listing counters and qualified VS-attributed interest from the
   fresh 103-install / 166-download v1.1.0 baseline.
2. Keep only the irreducible two-minute GitHub Marketplace checkbox/agreement/
   2FA action in HQ-5; Codex already verified its canonical private draft.
3. Rotate the retired Stripe account key in HQ-2. Codex already completed the
   dispatch, run review, cleanup verification, and public Worker probes.
4. Supply legal facts, remove the injected host script, deploy GRACE v2 with
   checkout closed, and prove the complete test/refund path. Repository audit
   `32840796298` confirms no current deploy transport or runtime bundle exists.
5. Unpublish the false DEV corpus, then enable only the exact $299 Audit Price
   after every checkout gate is green.

The owner queue is reduced from 37 to 34 minutes and contains no monitoring or
VS action. Bet A's checkpoint remains August 27 20:29 UTC. V1's new five-day
checkpoint is August 30 11:15 UTC. Do not count the successful publisher run,
extension package availability, installs, downloads, or CI as collected money.

## Cycle note — August 29, 2026 (cloud, egress-restricted)

`marketing-machine-v2` was absent from `origin` at cycle start; merged commit
`0c9dfec` had already folded its unique work into `main` (the branch
`deploy-pages.yml` actually deploys from), so the branch was recreated from
`main` per the runbook's already-merged-PR case. See DECISIONS D44. Main was
already current: `BUILD_DATE` was today's date, 35/35 `apps/web` tests green,
and a rebuild produced no `docs/` drift.

Egress was blocked again (`example.com`/`docs.aws.amazon.com` both 403
through the proxy), so no new repost-answers batch or dev.to draft was
produced, per AGENTS.md's fallback. Shipped a second finding in the
already-quarantined DEV corpus instead: article 04's timeline table has the
wrong `python3.10` deprecation date (2026-03-31 instead of 2026-10-31, per
this repo's own two already-corroborated sources). Documented it in
`launch/distribution/devto/README.md` alongside article 24's existing note;
did not edit the archived draft itself.

No cash-path state changed. Collected profit remains **$0**; the gap remains
**$4,000**. HQ-1 through HQ-5 and HQ-7 are unchanged and still require the
owner. Next highest-leverage action is still the same owner batch (HQ-2 then
HQ-5/HQ-6, then HQ-3/HQ-1/HQ-4/HQ-7) — repository work has no further
verifiable-without-fetch truth gaps found this cycle.

## Cycle note — August 30, 2026, 06:16 UTC (cloud, egress-restricted)

Egress was blocked for the fourth consecutive cycle (`example.com` and
`docs.aws.amazon.com` both 403 through the configured proxy; proxy status
confirmed up). Per AGENTS.md's fallback, no new repost-answers batch or dev.to
draft was produced. `BUILD_DATE` was already current and a full rebuild showed
no drift; an entry-by-entry cross-check of `deprecations.yml` against
`PHASE_DATES`/`fixes.yml` and a fresh date scan of all 25 quarantined DEV
drafts found no further date errors beyond the two already logged.

Shipped instead: `revenue/HUMAN_QUEUE.md`'s HQ-5 release link had gone stale
within the same recovery cycle — a `prepare-marketplace-v2.yml` resync nine
minutes after HUMAN_QUEUE.md was last written regenerated the draft's
`untagged-<hex>` URL slug, so the owner's next click on the irreducible HQ-5
action (the fastest remaining route to a first dollar) would have 404'd.
Verified via the GitHub API that the draft (id `375063073`) still says v2.0.0
and targets `47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8`, matching both `v2` and
`marketing-machine-v2`; corrected the link, recorded the durable release id,
and added a Releases-list fallback since the slug will keep regenerating on
future resyncs. See DECISIONS D50. No cash-path state changed. Collected
profit remains $0; the gap remains $4,000. HQ-0 through HQ-4, the now-corrected
HQ-5, and HQ-6/HQ-7 are otherwise unchanged and still require the owner.

## Recovery cycle — August 30, 2026

The from-the-top audit rejected the premise that this was already a profitable
business. Workspace-observed revenue and profit are still **$0**, no paid report
has been observed, and no current demand signal supports adding SKUs or raising
the $299 price. The profit target gap remains **$4,000**.

This cycle's highest-leverage recovery is:

1. keep every paid route closed and immediately block the stale public upload
   surface at Caddy;
2. merge the fully verified recovery branch through green CI, then fast-forward
   `main`, `marketing-machine-v2`, and public `v2` without force;
3. synchronize the one canonical private v2.0.0 release draft to that green
   tree, leaving only the agreement/Marketplace checkbox/2FA click to the owner;
4. deploy Audit v2 checkout-closed only after a mutation-free image preflight
   and stopped-volume snapshot; remove the hosting injection; run the isolated
   real Stripe-test/Resend/refund exercise;
5. create one new v2-only live $299 Product/Price, pass GET-only catalog
   attestation, then enable checkout; and
6. publish the Marketplace release, remove the false DEV corpus, and let the
   read-only acquisition gates decide whether K1/V1 continue.

The repository now contains the emergency proxy block, safe snapshot tool,
pre-mutation startup validation, retired-Price denial, live catalog attestation,
public-v2 consumer monitor, automatic VS falsifier, and fail-closed status
monitor required by that sequence. GRACE access and runtime secrets are absent
from repository automation, so deployment/identity actions remain in the Human
Queue instead of being guessed or bypassed.

## Recovery ship result — 2026-08-30T05:21:42Z

Recovery PR [#25](https://github.com/ntoledo319/EOLkits/pull/25) merged as
`47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8`. Its full pull-request suite and
all merge-triggered release, deterministic, property, public-consumer, and Pages
checks passed. `main`, `marketing-machine-v2`, and public `v2` were then
fast-forwarded without force to that exact commit; raw public `@v2/action.yml`
resolves.

One-use draft run
[33294414373](https://github.com/ntoledo319/EOLkits/actions/runs/33294414373)
passed. Canonical release `375063073` is the only v2 draft, now has tag
`v2.0.0`, targets exact public-v2 commit `47cd9eae...`, is private/non-prerelease,
and has zero assets. The one-use push trigger is removed in this finalization
tree, restoring owner-confirmed manual dispatch only.

Collected revenue and profit remain **$0**; the gap remains **$4,000**; checkout
remains **closed**. Repository work is no longer the launch blocker. The owner
must now execute `HUMAN_QUEUE.md`, beginning with the three-minute emergency
GRACE containment. Marketplace publication needs only the required agreement,
checkbox, and 2FA ceremony; live checkout stays forbidden until the closed v2
deploy, injected-script removal, full test/refund proof, legal facts, DEV cleanup,
and new catalog attestation pass.

## Cycle note — August 31, 2026 (cloud, egress-restricted)

Egress was blocked for the fifth consecutive cycle (`example.com` and
`docs.aws.amazon.com` both 403 through the configured proxy; proxy status
confirmed up). Per AGENTS.md's fallback, no new repost-answers batch or dev.to
draft was produced. `main` was confirmed an ancestor of `marketing-machine-v2`
(no repeat of the prior silent-divergence pattern). `BUILD_DATE` was one day
stale; bumped and rebuilt, 35/35 `apps/web` tests green, diff entirely
date-derived.

Shipped the highest-leverage in-jail fix found this cycle: `kits/lambda-lifeline`'s
live-scan runtime tables had no `python3.8` entry, so scanning a real AWS
account with a Lambda function on that runtime would falsely report it as
healthy. Two independent internal sources (python-pivot's `RUNTIME_TABLE` and
`rules/public/deprecations.yml`'s existing entry) already agreed on the exact
dates, meeting this project's own corroboration bar. Fixed with a new
regression-test fixture case; 28/28 Node tests and 3/3 property tests stayed
green; `npm pack --dry-run` still reports 24 release files. This is a
correctness fix to the free product's actual detection logic (K1's underlying
engine), not a documentation- or SEO-page-only change — see DECISIONS D52.

HQ-5's release-draft link was re-verified via the GitHub API and still matches
`HUMAN_QUEUE.md` exactly (no repair needed, unlike the prior two cycles). No
cash-path state changed. Collected profit remains $0; the gap remains $4,000.
HQ-0 through HQ-7 are unchanged and still require the owner. Next
highest-leverage action remains the same owner batch (HQ-0 through HQ-7 in
order) — no further verifiable-without-fetch correctness gap was found this
cycle beyond what was shipped.
