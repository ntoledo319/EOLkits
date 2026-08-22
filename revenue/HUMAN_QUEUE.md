# Batched owner queue — maximum 41 minutes

Last reconciled August 22 after publishing and verifying the exact legacy
Stripe-retirement workflow. The workflow has not been owner-dispatched.

Do HQ-2 first because the stale GRACE API can still mint live Checkout Sessions,
then HQ-5 because it repairs existing distribution. Complete HQ-1, HQ-3, HQ-4,
HQ-6, and finally HQ-7. Checkout remains closed until HQ-7. No old handoff or
launch file is authoritative.

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
   The still-active box-side deploy now follows the verified truthful tree. If
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
2. Immediately unpublish “401 from 169.254.169.254 — fixing EC2 instances after
   the IMDSv2 enforcement deadline”; its universal December 31, 2025 deadline is
   not supported by current AWS documentation.
3. Review the remaining 24 EOLkits posts. Immediately unpublish any post that claims live
   Migration Pack/automatic PR, Organization License, Drift Watch, AWS-account
   scanning, guaranteed timing, cost/blast-radius estimates, or an active
   checkout that is not currently true.
4. Technical posts may remain only if their dates and remediation claims match
   current primary sources and paid-product links point to the gated Audit page.
5. Do not add new promotional posts in this batch.

## HQ-5 — publish the prepared GitHub Marketplace draft (2 minutes)

Why human-only: Marketplace developer agreement, 2FA, and release checkbox.

Steps:

1. After final main CI is green, open the private prepared draft directly:
   https://github.com/ntoledo319/EOLkits/releases/tag/untagged-db9a4617f412abd63d2d
2. Verify it is v2.0.0 targeting commit `8748cf6a`, check “Publish this Action to
   the GitHub Marketplace,” keep the existing Marketplace identity, and publish
   with 2FA. Do not create a second listing or a second release.
3. Verify
   https://github.com/marketplace/actions/rupture-aws-deprecation-check shows
   v2.0.0 and the bounded release copy.
4. On https://github.com/ntoledo319/EOLkits/settings, remove any repository
   description claiming Amazon Linux 2 instances are necessarily “unpatched.”

Official instructions:
https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace

## HQ-6 — publish the verified VSIX (5 minutes)

Why human-only: publisher identity and Marketplace authentication.

Steps:

1. Open https://marketplace.visualstudio.com/manage/publishers/ and create or
   verify the eolkits publisher.
2. Follow https://code.visualstudio.com/api/working-with-extensions/publishing-extension
   to create the currently supported Marketplace credential. Microsoft says
   global PATs retire December 1, 2026, so prefer the documented Entra path where
   available.
3. Add the credential as repository secret VSCE_PAT, then run the “Publish VS
   Code Extension” workflow from main.
4. Verify the listing installs version 1.0.0 and links only to the free tools and
   capability-gated Audit.

## HQ-7 — enable the only checkout (1 minute)

Why human-only: this begins accepting real customer money.

Prerequisites: HQ-1 through HQ-6 complete, zero unresolved refund/fulfillment
alerts, and the exact production commit is verified. HQ-2 intentionally leaves
all six historical Prices inactive.

Steps:

1. Reactivate only the canonical $299 Audit Price
   `price_1TRoGjDL3cQl851oiIWR5JIa`; do not reactivate any other Price and do not
   create a public Payment Link.
2. Set EOLKITS_AUDIT_CHECKOUT_ENABLED=1 in the reviewed production environment.
3. Redeploy only the Audit service and set repository variable
   AUDIT_CHECKOUT_EXPECTED=true.
4. Verify /api/capabilities reports Audit 2.0 ready, then confirm the static form
   appears and creates one $299 input-bound Checkout Session.

Estimated current owner total: 41 minutes. This leaves a 19-minute reserve for
unrecorded prior owner work or one failed authentication attempt; do not exceed
60 minutes without changing the plan.
