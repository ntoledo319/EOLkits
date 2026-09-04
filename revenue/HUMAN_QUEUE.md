# Batched owner queue — authoritative September 4, 2026 — maximum 38 minutes

_A resumed discovery-boundary audit at `2026-09-04T12:30:43Z` added the one
missing exact repository topic (`github-actions`) and reverified the same draft
target. VS search position, repository metadata, connected hosting inventory,
GitHub sponsor policy, and Marketplace publication requirements exposed no
additional autonomous path to payment. No queue item was completed or added;
the maximum remains 38 minutes. The excluded retired-credential action remains
outside this queue._

_Re-verified through GitHub's live API on September 4, 2026: HQ-E's release
link (id `375063073`, tag `v2.0.0`, slug
`untagged-ea8be73c7a7d9b6c45e7`) remains the sole canonical private draft. Its
exact 40-character target is
`47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8`, which equals the protected public
`v2` branch. No other item's external state has been observed to change; do not
treat this note as new owner action._

_September 1, 2026: reconciled two parallel cycles' queues (one on
`marketing-machine-v2`, one on `main`) after they diverged from the same
August 30 recovery base. `main`'s HQ-A..HQ-G renumbering and VS v1.2.0
publication are newer and authoritative for overall state; this branch's
release-link durable-ID/fallback note is preserved in HQ-E below since the
`untagged-<hex>` slug has already regenerated twice on ordinary resyncs._

Codex completed every operation currently reachable through the repository and
connected GitHub authority. VS Code v1.3.0 is public, its exact package and
five-sample Gallery evidence are verified, and its publisher is manual-only
again. The exact v2 GitHub release draft is ready. Repository Pages now uses
GitHub Actions, and active ruleset `22266277` blocks default-branch/`v2`
deletion and force pushes; former HQ-F is complete with no owner labor. The
remaining actions require production-host access, owner account attestations,
DEV author authority, or payment-account control that is not present in the
workspace or connected tools. Do them in this order; do not use an older
handoff.

The retired Stripe credential revocation/rotation action is explicitly excluded
at the owner's direction. It was not attempted, is not included in the time
budget below, and must not be treated as completed.

## HQ-A — contain the stale public upload service (3 minutes)

Why human-only: five non-invasive access routes were exhausted. Repository
secrets expose neither GRACE deployment transport nor the runtime bundle; no
local host credential or control token exists; both direct Caddy admin probes
time out; and no connected host-management capability is available.

Steps:

1. On the GRACE host, open the reviewed checkout of this repository.
2. Install
   `deploy/grace/Caddyfile.eolkits-emergency-containment.block` before the
   existing EOLkits proxy rules, then reload Caddy through the host's existing
   unprivileged deployment procedure.
3. Run the first verification block in `deploy/grace/README.md`. Require upload
   GET/POST/PUT and checkout/event mutations to return 503, obsolete App routes
   to return 410, and the Stripe webhook route to remain proxied.
4. Leave checkout off. If a postcondition differs, report only the route and
   status; do not improvise a broader firewall rule.

## HQ-B — supply the remaining commercial facts (2 minutes)

Why human-only: Connecticut's official business registry establishes Toledo
Technologies LLC's public mailing address, and the terms now use Connecticut
law while preserving mandatory consumer protections. Public sources cannot
establish the Stripe account's actual fee/currency facts or incremental GRACE
cost.

Steps:

1. Open <https://dashboard.stripe.com/settings>. Report the account country,
   standard-versus-custom pricing, presentment currency, and settlement
   currency. Never send a key, customer record, callback URL, or screenshot.
2. State whether EOLkits adds exactly $0 of monthly cost to the existing GRACE
   host. If not, provide only the incremental monthly amount.

## HQ-C — deploy Audit v2 closed, prove fulfillment, and repair indexing (18 minutes)

Why human-only: this requires GRACE access and private Stripe-test/Resend
values. No host transport or host-management capability is available to the
workspace or connected tools; the guarded runtime bundle is now complete.

Steps:

1. In the clean host checkout at `/home/ubuntu/sites/eolkits-api`, check out the
   final green `main` commit. Run
   `deploy/grace/deploy-api-closed.sh --sha <full-green-main-sha>` without
   `--apply`. Require the guarded dry-run to pass and review its bounded plan.
2. Repeat the exact command with `--apply`. It pins the reviewed SHA, validates
   the current deployment and private env file, builds the digest-pinned image,
   runs the no-volume checkout-closed preflight, snapshots the exact production
   volume, deploys with checkout forced off, verifies all loopback capability
   gates, and restores the prior image automatically if a post-deploy gate
   fails. Do not restore a volume automatically.
3. Replace the emergency block with
   `deploy/grace/Caddyfile.eolkits-api.block` only after the wrapper proves
   report version 2.0, exact build SHA, healthy dependencies, and checkout
   false. Validate the complete Caddy config with Caddy 2.8 or newer before
   reload; the reviewed block suppresses signed-upload URLs from access logs.
4. Remove the host rule that injects
   `https://stats.saiditright.com/script.js`. Do not replace it with another
   third-party tag. Require raw HTML on `/`, `/audit/`, `/pack/`,
   `/drift/`, and `/success/` to contain the generated CSP and no
   cross-origin script.
5. Use the separate test Compose project and a Stripe test card to prove
   presign, immutable PUT, signed webhook, exactly one job, a real PDF, Resend
   delivery, signed download, matching verification lookup, retention, and
   full-refund handling on forced failure. Tear down only the test project.
6. Leave production checkout off. Reply with the deployed full commit SHA and
   pass/fail only—never host credentials, tokens, or customer data.
7. Only after the injected script is absent and the reviewed custom-host sitemap
   is live, open Google Search Console for `eolkits.com`, resubmit
   `https://eolkits.com/sitemap.xml`, and request reindexing for `/audit/` and
   `/lambda-runtime-deprecation-schedule/`. This is needed because public search
   still shows retired $1,499 and “email in 5 minutes” snippets. Do not request
   indexing while the host fails its injection gate.

## HQ-D — unpublish the 25 false DEV posts (10 minutes)

Why human-only: the owner has no DEV API key in repository secrets and no DEV
connector is available. Unpublishing is an owner-account communication action.

Steps:

1. Open <https://dev.to/dashboard>.
2. Revert all 25 EOLkits posts to drafts. The exact public-author API check still
   returns 25 posts; the local corpus is quarantined and documents unsupported
   telemetry/account claims, obsolete links, and two known date errors.
3. Refresh <https://dev.to/ntoledo319> and confirm no EOLkits posts remain
   public. Do not edit, replace, or publish promotional content in this batch.

## HQ-E — publish the canonical GitHub Marketplace v2 release (2 minutes)

Why human-only: GitHub requires the account holder to accept its developer
agreement, select the Marketplace checkbox, and complete 2FA. The Releases API
does not perform those account-holder attestations.

Steps:

1. Open the sole private draft (release id `375063073`, currently at slug
   `untagged-ea8be73c7a7d9b6c45e7`):
   <https://github.com/ntoledo319/EOLkits/releases/tag/untagged-ea8be73c7a7d9b6c45e7>.
   GitHub regenerates this `untagged-<hex>` slug every time the draft is
   resynced by `prepare-marketplace-v2.yml` (it has already changed twice
   across prior cycles), so if that exact link 404s, instead open
   <https://github.com/ntoledo319/EOLkits/releases> and click the one draft
   titled "Rupture AWS Deprecation Check v2.0.0" (release id `375063073`) —
   do not open any other release or draft.
2. Confirm tag `v2.0.0`, target
   `47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8`, no assets, and the existing
   release notes. Select “Publish this Action to the GitHub Marketplace,” keep
   the existing listing identity, accept the agreement if shown, and publish
   with 2FA. Do not create another release or listing.
3. Confirm
   <https://github.com/marketplace/actions/rupture-aws-deprecation-check>
   shows v2.0.0. Stop if the target commit differs.

## HQ-G — create the new catalog and enable the only checkout (3 minutes)

Why human-only: this creates live payment objects and begins accepting customer
money. No connected Stripe authority exists.

Prerequisites: HQ-A through HQ-D are complete; legal/cost math is updated from
HQ-B; the custom host is injection-free; Audit v2 capability, delivery, refund,
and retention evidence is green; and no fulfillment/refund alert is open.
HQ-E improves distribution but cannot weaken these commerce gates. Repository
Pages and release-branch protections are already complete.

Steps:

1. In Stripe live mode, create one Product named **EOLkits Audit v2** and one
   active, one-time **USD $299.00** Price. Do not reuse or reactivate
   `price_1TRoGjDL3cQl851oiIWR5JIa` or another historical Price. Do not create
   a public Payment Link.
2. Put only the new IDs into `EOLKITS_AUDIT_PRODUCT_ID` and
   `EOLKITS_AUDIT_PRICE_ID`; set
   `EOLKITS_AUDIT_CHECKOUT_ENABLED=1`.
3. Run the documented no-volume, network-enabled preflight. It must attest
   exact identity, object types, live/active state, one-time USD 29900 amount,
   and the expanded Product. Redeploy only after it passes.
4. Set repository variable `AUDIT_CHECKOUT_EXPECTED=true`; verify health,
   status, `/api/capabilities`, the public form, and one input-bound $299
   Checkout Session. Do not self-charge in live mode.

Estimated owner labor: **38 minutes**, leaving 22 minutes within the 60-minute
cap. Completed repository work and public VS Code v1.3 publication require no
owner time. No owner action in this queue asks for the excluded retired Stripe
credential rotation/revocation.
