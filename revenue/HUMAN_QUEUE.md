# Batched owner queue — maximum 37 minutes

Last reconciled August 22 after publishing the engine-generated sample report,
advancing public `v2` to green product commit `9c231b58`, recovering the existing
VS Marketplace identity, and correcting the canonical private GitHub draft.
The Stripe workflow has not been owner-dispatched; neither Marketplace update
is public. HQ-6 no longer requires a new publisher or credential, reducing its
estimate by four minutes. Repository commit `a9cdcaeb` and its full release/VS
package run `32604619029` are green; the publication workflow now requires exact
owner identity and typed confirmation.

Do HQ-2 first because the stale GRACE API can still mint live Checkout Sessions
and the exact audit may stop on anomalous commerce state. Then do HQ-5 and HQ-6
in the same sitting so the repaired, fail-closed Pages funnel starts receiving
Marketplace distribution. Complete HQ-1, HQ-3, HQ-4, and finally HQ-7. HQ-5 and
HQ-6 are acquisition releases, not checkout-safety gates; checkout remains
closed until HQ-7. No old handoff or launch file is authoritative.

## HQ-1 — supply truthful seller/legal and cost facts (3 minutes)

Why human-only: only the owner knows the legal seller/controller identity,
address, governing-law choice, tax posture, and whether the shared GRACE host
adds any incremental cost.

Steps:

1. Reply to the active Codex thread with the exact seller/legal name, business
   mailing address, governing jurisdiction, support/privacy email, and whether
   EOLkits adds $0 incremental monthly cost to GRACE.
2. If any value is unknown or the cost is above $0, say so. Checkout stays off;
   do not guess.

Direct files: legal/terms.md and legal/privacy.md.

## HQ-2 — authorize exact Stripe closure and rotate the legacy key (5 minutes)

Why human-only: the workflow requires the repository owner's identity and exact
confirmation; account-level Stripe-key rotation is an owner credential action.

Steps:

1. Open
   https://github.com/ntoledo319/EOLkits/actions/workflows/retire-legacy-stripe.yml,
   choose **Run workflow** on `main`, enter
   `RETIRE_EXACT_EOLKITS_STRIPE_2026_08_22`, and run it. Do not select another
   branch.
2. Require a green run whose summary reports all six exact live Prices inactive,
   zero approved active Payment Links, zero matching open/recent-completed
   Checkout Sessions, zero future subscriptions/schedules, and zero unexpected
   EOLkits Product prices/links. A red run intentionally preserves the Stripe
   binding for review: stop and give the run URL to Codex; do not cancel a
   subscription, expire a Session, or refund a charge from guesswork.
3. After a green run, open https://dashboard.stripe.com/apikeys and rotate/revoke
   the legacy live key used by the old Worker/GRACE deployment. Historical
   Cloudflare versions retain old secret snapshots, so deleting the current
   Worker binding is not account-level revocation. Keep transaction history.
   Create/configure a distinct least-privilege production key only during HQ-3.
4. In https://dashboard.stripe.com/webhooks, remove only the endpoint pointing
   to the retired Cloudflare Worker after HQ-3 proves the replacement test
   webhook. Do not remove unrelated endpoints.

## HQ-3 — deploy Audit v2 closed and prove test fulfillment (15 minutes)

Why human-only: GRACE SSH access plus Stripe/Resend secrets and test Checkout UI.

Steps:

1. Open deploy/grace/README.md in this repository and follow “Deploy checkout
   closed” exactly with EOLKITS_AUDIT_CHECKOUT_ENABLED=0.
2. First inspect the scheduled “Verify GRACE static release” run after 07:35 UTC.
   The still-active box-side deploy now follows final-tree feed commit
   `0780909c`. If
   that run passes, do not run a redundant static rsync. If it fails, use
   `deploy/grace/ship-web.sh` with the documented `GRACE_HOST` and
   `GRACE_WEBROOT`, inspect its dry-run, then rerun it with `--apply`. Verify
   https://eolkits.com no longer advertises Migration Pack, Organization
   License, Drift Watch, automatic PRs, or estimated impact.
3. Confirm the deployed commit SHA and that public /api/capabilities reports
   report_version 2.0 with checkout_enabled false.
4. Follow “Test-mode E2E deployment” using the separate test Compose project,
   test Stripe keys, an operator-owned delivery email, and Stripe's test card.
5. Capture evidence of: presign, immutable PUT, Checkout completion, verified
   webhook, exactly one job, real PDF, Resend delivery, signed download, matching
   verification lookup, and source/report retention.
6. Exercise failed fulfillment and confirm a full exact-payment refund is
   initiated, correlated by refund ID/amount, and either succeeds or remains
   visibly pending for reconciliation.
7. Tear down only the separate test project. Leave production checkout off.

## HQ-4 — remove false DEV promotion (10 minutes)

Why human-only: platform posting/editing is a communication as the owner.

Steps:

1. Open https://dev.to/dashboard.
2. Unpublish all 25 EOLkits posts as one batch. The repository copies are now
   individually quarantined, but that does not alter the already-live DEV posts.
   The corpus contains unqualified account-wide/zero-telemetry/closed-product
   claims and obsolete `eolkits.com` canonicals; article 24 additionally invents
   a universal December 31, 2025 IMDSv2 enforcement deadline.
3. Do not edit or republish during this batch. A later post may return only after
   its dates and scope match current primary sources and its links point to the
   verified Pages funnel.
4. Do not add new promotional posts in this batch.

## HQ-5 — publish the prepared GitHub Marketplace draft (2 minutes)

Why human-only: Marketplace developer agreement, 2FA, and release checkbox.

Steps:

1. After final main CI is green, open the private prepared draft directly:
   https://github.com/ntoledo319/EOLkits/releases/tag/untagged-0866963caf3f06db98a1
   This is the canonical draft created by green run `32604619021`; do not publish
   either older untagged draft.
2. Verify it is v2.0.0 targeting green commit `a9cdcaeb`. Public `v2` points to
   green commit `9c231b58`, whose `action.yml` and `apps/github-action/` files are
   byte-identical to the draft target. Check
   “Publish this Action to the GitHub Marketplace,” keep the existing
   Marketplace identity, and publish with 2FA. Do not create a second listing
   or a second release. Stop if its Action files differ from public `v2`.
3. Verify
   https://github.com/marketplace/actions/rupture-aws-deprecation-check shows
   v2.0.0 and the bounded release copy.
4. On https://github.com/ntoledo319/EOLkits/settings, remove any repository
   description claiming Amazon Linux 2 instances are necessarily “unpatched.”

Official instructions:
https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace

## HQ-6 — update the existing VS listing in place (1 minute)

Why human-only: starting the workflow changes a public Marketplace listing under
the owner's publisher identity. The existing listing and repository credential
have already published successfully; no new publisher or listing is needed.

Steps:

1. Open
   https://github.com/ntoledo319/EOLkits/actions/workflows/publish-vscode.yml,
   choose **Run workflow** on `main`, type
   `PUBLISH_RUPTURE_VSCODE_1_1_0` into the confirmation field, and run it while
   signed in as repository owner `ntoledo319`. Do not change the package
   publisher/name or create `eolkits.eolkits-vscode`. The workflow rejects a
   collaborator dispatch, a collaborator rerun, another branch, or another
   confirmation value, and packages only the already-green release commit
   `a9cdcaeb` even if later ledger commits exist on `main`.
2. Require a green run, then verify
   https://marketplace.visualstudio.com/items?itemName=rupture.rupture-vscode
   shows v1.1.0 with EOLkits display branding and links to the verified Pages
   Audit. The workflow refuses a different technical identity.
3. If publication fails for an expired or missing credential, stop and give the
   run URL to Codex. Only that evidence reopens credential renewal; do not create
   a second publisher or listing.

## HQ-7 — enable the only checkout (1 minute)

Why human-only: this begins accepting real customer money.

Prerequisites: HQ-1 through HQ-4 complete, zero unresolved refund/fulfillment
alerts, and the exact production commit is verified. HQ-2 intentionally leaves
all six historical Prices inactive. HQ-5 and HQ-6 should happen immediately for
distribution, but their public listing state does not affect checkout safety.

Steps:

1. Reactivate only the canonical $299 Audit Price
   `price_1TRoGjDL3cQl851oiIWR5JIa`; do not reactivate any other Price and do not
   create a public Payment Link.
2. Set EOLKITS_AUDIT_CHECKOUT_ENABLED=1 in the reviewed production environment.
3. Redeploy only the Audit service and set repository variable
   AUDIT_CHECKOUT_EXPECTED=true.
4. Verify /api/capabilities reports Audit 2.0 ready, then confirm the static form
   appears and creates one $299 input-bound Checkout Session.

Estimated current owner total: 37 minutes. This leaves a 23-minute reserve for
unrecorded prior owner work or one failed authentication attempt; do not exceed
60 minutes without changing the plan.
