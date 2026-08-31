# Batched owner queue — authoritative August 30, 2026 — maximum 43 minutes

_Re-verified August 31, 2026: HQ-5's release-draft link (id `375063073`, tag
`v2.0.0`, slug `untagged-ea8be73c7a7d9b6c45e7`) was checked against the live
GitHub API and is still current — no repair needed this cycle. No other item
below changed._

Codex owns the repository, CI, branch synchronization, release-draft
preparation, monitoring, and evidence review. The items below are the only
remaining actions because they require production-host credentials, legal facts,
account ownership, a platform agreement/2FA ceremony, or communication as the
owner. Do them in order. Do not use any older launch handoff.

## HQ-0 — contain the public stale upload service now (3 minutes)

Why human-only: no GRACE SSH/control credential is available locally or in the
repository's GitHub Actions secrets.

Steps:

1. On the GRACE host, open the reviewed checkout of this repository.
2. Install `deploy/grace/Caddyfile.eolkits-emergency-containment.block` before
   the existing EOLkits proxy rules and reload Caddy using the host's existing
   unprivileged deployment procedure.
3. Run the first verification block in `deploy/grace/README.md`. Require upload
   GET/POST/PUT and checkout/event mutations to return 503, obsolete App routes
   to return 410, and the Stripe webhook route to remain proxied.
4. Leave checkout off. Stop and report only the failing route/status if any
   postcondition differs; do not improvise a broader firewall rule.

## HQ-1 — provide seller, legal, and actual-cost facts (3 minutes)

Why human-only: only the owner can attest to identity, address, jurisdiction,
tax/cost posture, and the account's negotiated Stripe pricing.

Steps:

1. Reply in this Codex thread with the legal seller/controller name, business
   mailing address, governing jurisdiction, support/privacy email, and whether
   EOLkits adds exactly $0 incremental monthly cost to GRACE.
2. In <https://dashboard.stripe.com/settings>, check account country,
   standard-versus-custom pricing, presentment currency, and settlement
   currency. Report only those facts—never keys, customer data, or screenshots.
3. If any fact is unknown or cost is nonzero, say so. Checkout remains off and
   the target math will be recomputed.

## HQ-2 — revoke the retired production credential (3 minutes)

Why human-only: key rotation and webhook ownership require Stripe account
control. The exact catalog retirement itself is already green in run
<https://github.com/ntoledo319/EOLkits/actions/runs/32840968816>.

Steps:

1. Open <https://dashboard.stripe.com/apikeys> and revoke/rotate the legacy live
   key used by the retired Worker or stale GRACE service. Historical Cloudflare
   versions can retain secret snapshots; removing a current binding was not
   account-level revocation.
2. Keep all transaction history. Do not reactivate any old Price or Payment Link.
3. After HQ-3 proves the replacement test webhook, remove only the webhook
   endpoint that targets the retired Cloudflare Worker at
   <https://dashboard.stripe.com/webhooks>. Do not remove unrelated endpoints.

## HQ-3 — deploy Audit v2 closed and prove fulfillment (16 minutes)

Why human-only: this needs GRACE access and private Stripe-test/Resend values;
the repository capability audit found neither deploy transport nor a complete
runtime bundle.

Steps:

1. Follow `deploy/grace/README.md` from “Safe rollout order” through the complete
   checkout-closed deployment. Use the final green main tree only.
2. Build the image and run `python -m eolkits_grace.preflight` without the
   production volume. Then run `bash deploy/grace/snapshot-api-volume.sh`; it
   stops the exact old container, creates a restricted SHA-256-checked snapshot,
   and restarts it on failure.
3. Deploy with `EOLKITS_AUDIT_CHECKOUT_ENABLED=0`. Replace the emergency block
   with `Caddyfile.eolkits-api.block` only after loopback health, status, and
   capability probes prove Audit report version 2.0 and checkout false.
4. Remove the Caddy/template/post-processing rule that injects
   `https://stats.saiditright.com/script.js`. Do not replace it with another
   third-party tag. Deploy the reviewed static tree and require raw HTML on `/`,
   `/audit/`, `/pack/`, `/drift/`, and `/success/` to contain the generated CSP
   and no cross-origin script.
5. Use the separate test Compose project and Stripe test card to prove presign,
   immutable PUT, signed webhook, exactly one job, real PDF, Resend delivery,
   signed download, matching verification lookup, retention, and full-refund
   handling on forced failure. Tear down only the test project.
6. Leave production checkout off and report the deployed full commit SHA plus
   pass/fail only; never post hostnames, tokens, customer data, or secret values.

## HQ-4 — unpublish the false DEV corpus (10 minutes)

Why human-only: unpublishing is communication as the owner.

Steps:

1. Open <https://dev.to/dashboard>.
2. Unpublish all 25 EOLkits posts. The local copies are quarantined, but the live
   corpus still contains unsupported telemetry/account-wide claims, obsolete
   links, and at least two documented lifecycle-date errors.
3. Do not edit, replace, or publish a new promotional post in this batch.

## HQ-5 — publish the canonical GitHub Marketplace v2 release (2 minutes)

Why human-only: GitHub requires the owner to accept the developer agreement,
select the Marketplace checkbox, and complete 2FA.

Steps:

1. Draft-synchronization run
   <https://github.com/ntoledo319/EOLkits/actions/runs/33294414373> is green.
   Open the sole private draft (release id `375063073`) at
   <https://github.com/ntoledo319/EOLkits/releases/tag/untagged-ea8be73c7a7d9b6c45e7>.
   GitHub regenerates this `untagged-<hex>` slug every time the draft is
   resynced by `prepare-marketplace-v2.yml` (it already changed once between
   the prior batch and this one), so if that exact link 404s, instead open
   <https://github.com/ntoledo319/EOLkits/releases> and click the one draft
   titled "Rupture AWS Deprecation Check v2.0.0" — do not open any other
   release or draft.
2. Confirm the draft says v2.0.0 and targets the same green commit as public
   `v2` (currently `47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8`). Select “Publish
   this Action to the GitHub Marketplace,” retain the existing listing
   identity, and publish with 2FA. Do not create another draft, release, or
   listing.
3. Confirm <https://github.com/marketplace/actions/rupture-aws-deprecation-check>
   shows v2.0.0. Stop if the commit identities differ.

## HQ-6 — remove repository configuration races (3 minutes)

Why human-only: the connected GitHub integration can update code/refs but does
not have repository-administration permission for Pages or rulesets.

Steps:

1. At <https://github.com/ntoledo319/EOLkits/settings/pages>, set Build and
   deployment Source to **GitHub Actions** so the legacy `main/docs` publisher
   cannot race the reviewed Pages workflow.
2. At <https://github.com/ntoledo319/EOLkits/settings/rules>, create one active
   branch ruleset targeting the default branch and `v2`; block branch deletion
   and force pushes. Do not require a paid GitHub feature or change visibility.

## HQ-7 — create the new catalog and enable the only checkout (3 minutes)

Why human-only: this creates a live Stripe catalog object and begins accepting
real customer money.

Prerequisites: HQ-0 through HQ-4 are complete; no refund/fulfillment alert is
open; raw custom-host HTML is injection-free; Audit 2.0 test delivery and refund
evidence are green. HQ-5/HQ-6 improve distribution and resilience but are not
allowed to weaken these safety gates.

Steps:

1. In Stripe live mode, create one new Product named for **EOLkits Audit v2** and
   one active, one-time **USD $299.00** Price. Do not reuse/reactivate
   `price_1TRoGjDL3cQl851oiIWR5JIa` or any other retired Price. Do not create a
   public Payment Link.
2. Put only the new exact IDs into `EOLKITS_AUDIT_PRODUCT_ID` and
   `EOLKITS_AUDIT_PRICE_ID`; set `EOLKITS_AUDIT_CHECKOUT_ENABLED=1`.
3. Run the documented no-volume, network-enabled preflight. It must attest exact
   identity, object types, live/active state, one-time USD 29900 amount, and the
   expanded Product. Redeploy only if it passes.
4. Set repository variable `AUDIT_CHECKOUT_EXPECTED=true`; verify health/status,
   `/api/capabilities`, the public form, and one $299 input-bound Checkout
   Session. Do not self-charge in live mode.

Estimated owner labor: **43 minutes**, leaving 17 minutes within the 60-minute
cap for one failed login or host-specific reload step.
