# Batched owner queue — authoritative August 31, 2026 — maximum 40 minutes

_September 1, 2026: reconciled two parallel cycles' queues (one on
`marketing-machine-v2`, one on `main`) after they diverged from the same
August 30 recovery base. `main`'s HQ-A..HQ-G renumbering and VS v1.2.0
publication are newer and authoritative for overall state; this branch's
release-link durable-ID/fallback note is preserved in HQ-E below since the
`untagged-<hex>` slug has already regenerated twice on ordinary resyncs._

Codex completed every operation reachable through the repository and connected
GitHub authority. VS Code v1.2.0 is public. The exact v2 GitHub release draft is
ready. The remaining actions require production-host access, owner account
attestations, DEV author authority, repository-administration permission, or
payment-account control that is not present in the workspace or connected
tools. Do them in this order; do not use an older handoff.

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

## HQ-B — supply the four missing commercial facts (3 minutes)

Why human-only: public sources establish Toledo Technologies LLC, Connecticut,
and `hello@toledotechnologies.com`; they do not establish a business mailing
address, the contract's chosen governing jurisdiction, the account's actual
Stripe fee/currency facts, or incremental GRACE cost.

Steps:

1. Reply in this Codex thread with the business mailing address and the state or
   country that should govern the EOLkits terms.
2. Open <https://dashboard.stripe.com/settings>. Report the account country,
   standard-versus-custom pricing, presentment currency, and settlement
   currency. Never send a key, customer record, callback URL, or screenshot.
3. State whether EOLkits adds exactly $0 of monthly cost to the existing GRACE
   host. If not, provide only the incremental monthly amount.

## HQ-C — deploy Audit v2 closed and prove fulfillment (16 minutes)

Why human-only: this requires GRACE access and private Stripe-test/Resend
values. The repository capability audit found neither deploy transport nor a
complete runtime bundle.

Steps:

1. Follow `deploy/grace/README.md` from “Safe rollout order” through the
   checkout-closed deployment, using the final green `main` commit.
2. Build the image and run `python -m eolkits_grace.preflight` without the
   production volume. Then run
   `bash deploy/grace/snapshot-api-volume.sh`; it stops the exact old
   container, creates a restricted SHA-256-checked snapshot, and restarts the
   old container on failure.
3. Deploy with `EOLKITS_AUDIT_CHECKOUT_ENABLED=0`. Replace the emergency block
   with `deploy/grace/Caddyfile.eolkits-api.block` only after loopback health,
   status, and capability probes prove report version 2.0 and checkout false.
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

## HQ-F — remove the two GitHub configuration races (3 minutes)

Why human-only: the connected GitHub integration and scoped workflow token can
change repository content but have no repository-administration authority.
The bounded API attempt made no changes: the public ruleset list remains empty,
and the merge still triggered GitHub's legacy dynamic Pages build.

Steps:

1. At <https://github.com/ntoledo319/EOLkits/settings/pages>, set Build and
   deployment Source to **GitHub Actions**.
2. At <https://github.com/ntoledo319/EOLkits/settings/rules>, create one active
   branch ruleset targeting the default branch and `v2`; block branch deletion
   and force pushes. Do not change repository visibility or enable a paid
   feature.

## HQ-G — create the new catalog and enable the only checkout (3 minutes)

Why human-only: this creates live payment objects and begins accepting customer
money. No connected Stripe authority exists.

Prerequisites: HQ-A through HQ-D are complete; legal/cost math is updated from
HQ-B; the custom host is injection-free; Audit v2 capability, delivery, refund,
and retention evidence is green; and no fulfillment/refund alert is open.
HQ-E and HQ-F improve distribution and resilience but cannot weaken these
commerce gates.

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

Estimated owner labor: **40 minutes**, leaving 20 minutes within the 60-minute
cap. Completed repository work and public VS Code v1.2 publication require no
owner time.
