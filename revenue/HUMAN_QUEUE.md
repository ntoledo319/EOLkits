# Batched owner queue — maximum 34 minutes

Last reconciled August 27 after Codex used the connected repository-owner
identity to complete the exact Stripe retirement and publish
`rupture.rupture-vscode@1.1.0`. Stripe run `32840968816` passed every bounded
audit, mutation, cleanup, and tombstone step. VS run `32841331222` passed every
exact-SHA, test, package, identity, and publication step. Both temporary
one-shot triggers were removed immediately; the permanent workflows are again
manual-only. No owner dispatch or run monitoring remains.

Daily VS/acquisition evidence is also autonomous now. Public run `33028483868`
passed at reconciled commit `2d19a797`; inspected artifact `9629312207` keeps
cumulative Marketplace counters separate from qualified interest and dollars.
No owner telemetry step is queued.

The custom host still injects `https://stats.saiditright.com/script.js` into
every tested page. The generated CSP deployed on August 26 and blocks that exact
external script, but the raw injection remains and verifier `32946397287` is
correctly red. Custom-domain IndexNow must remain blocked. This privacy fix is
part of HQ-3. The smallest useful owner batch is the residual Stripe
credential cleanup in HQ-2 plus the GitHub Marketplace UI action in HQ-5: five
minutes total.

Codex also removed two obsolete untagged v2 release drafts, retained only the
canonical draft, corrected the repository description, and routed the repository
homepage to the verified free-first Pages surface. No owner cleanup or metadata
action remains for those items.

Do the HQ-2 key rotation first because historical Cloudflare versions can retain
secret snapshots. Then do HQ-5 so the repaired, fail-closed Pages funnel starts
receiving GitHub Marketplace distribution. Complete HQ-1, HQ-3, HQ-4, and
finally HQ-7. The VS acquisition release is complete; distribution state is not
a checkout-safety gate, and checkout remains closed until HQ-7. No old handoff
or launch file is authoritative.

## HQ-1 — supply truthful seller/legal and cost facts (3 minutes)

Why human-only: only the owner knows the legal seller/controller identity,
address, governing-law choice, tax posture, actual Stripe account/pricing
configuration, and whether the shared GRACE host adds any incremental cost.

Steps:

1. Reply to the active Codex thread with the exact seller/legal name, business
   mailing address, governing jurisdiction, support/privacy email, and whether
   EOLkits adds $0 incremental monthly cost to GRACE.
2. From https://dashboard.stripe.com/settings, report the account country,
   standard-versus-custom pricing status, charge/presentment currency, and
   settlement currency. Do not share keys, customer data, or screenshots.
3. If any value is unknown or the cost is above $0, say so. Checkout stays off;
   do not guess. Recompute the sale target from the actual fee schedule before
   HQ-7.

Direct files: legal/terms.md and legal/privacy.md.

## HQ-2 — finish retired Stripe credential cleanup (3 minutes)

Why human-only: Codex completed and verified the exact catalog closure, but no
connected Stripe account tool can rotate keys or edit webhook endpoints.

Steps:

1. Evidence is already green at
   https://github.com/ntoledo319/EOLkits/actions/runs/32840968816. Do not rerun
   the retirement workflow: its exact six Prices and approved Payment Links are
   inactive, settlement/subscription/schedule checks are clear, and the current
   Worker Stripe binding was removed.
2. Open https://dashboard.stripe.com/apikeys and rotate/revoke
   the legacy live key used by the old Worker/GRACE deployment. Historical
   Cloudflare versions retain old secret snapshots, so deleting the current
   Worker binding is not account-level revocation. Keep transaction history.
   Create/configure a distinct least-privilege production key only during HQ-3.
3. In https://dashboard.stripe.com/webhooks, remove only the endpoint pointing
   to the retired Cloudflare Worker after HQ-3 proves the replacement test
   webhook. Do not remove unrelated endpoints.

## HQ-3 — deploy Audit v2 closed and prove test fulfillment (15 minutes)

Why human-only: GRACE SSH access plus Stripe/Resend secrets and test Checkout UI.

Steps:

1. Open deploy/grace/README.md in this repository and follow “Deploy checkout
   closed” exactly with EOLKITS_AUDIT_CHECKOUT_ENABLED=0.
2. The static product-copy repair already passed scheduled verifier runs
   `32626994756`, `32705925984`, and `32825272945`; do not repeat that work.
   On the GRACE host, locate the Caddy/proxy/template/post-processing rule that
   injects `https://stats.saiditright.com/script.js` and remove it. This script
   is not an authorized EOLkits analytics provider. Do not replace it with a
   different third-party tag.
3. Deploy the current reviewed `marketing-machine-v2` head with checkout still
   disabled and require its tree to match canonical `main`. Verify raw HTML on
   `/`, `/audit/`, `/pack/`, `/drift/`, and `/success/` contains the generated
   `Content-Security-Policy` meta and contains no cross-origin script. Rerun
   “Verify GRACE static release” and require green before continuing.
4. Confirm the deployed commit SHA and that public /api/capabilities reports
   report_version 2.0 with checkout_enabled false.
5. Follow “Test-mode E2E deployment” using the separate test Compose project,
   test Stripe keys, an operator-owned delivery email, and Stripe's test card.
6. Capture evidence of: presign, immutable PUT, Checkout completion, verified
   webhook, exactly one job, real PDF, Resend delivery, signed download, matching
   verification lookup, and source/report retention.
7. Exercise failed fulfillment and confirm a full exact-payment refund is
   initiated, correlated by refund ID/amount, and either succeeds or remains
   visibly pending for reconciliation.
8. Tear down only the separate test project. Leave production checkout off.

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
   This is the sole canonical draft created by green run `32604619021`; Codex
   already deleted the two obsolete untagged drafts.
2. Verify it is v2.0.0 targeting green commit `a9cdcaeb`. Public `v2` points to
   green commit `9c231b58`, whose `action.yml` and `apps/github-action/` files are
   byte-identical to the draft target. Check
   “Publish this Action to the GitHub Marketplace,” keep the existing
   Marketplace identity, and publish with 2FA. Do not create a second listing
   or a second release. Stop if its Action files differ from public `v2`.
3. Verify
   https://github.com/marketplace/actions/rupture-aws-deprecation-check shows
   v2.0.0 and the bounded release copy.

Official instructions:
https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace

## Completed automatically — HQ-6 VS listing update (0 minutes)

Codex published the exact `rupture.rupture-vscode@1.1.0` candidate from pinned
commit `a9cdcaeb` in green owner-attributed run `32841331222`. The publisher log
records `Published rupture.rupture-vscode v1.1.0.` The one-shot trigger was
removed in remote commit `a8e8b45c`; the restored workflow is dispatch-only and
also contains the Bash quoting repair discovered during preflight. The official
Gallery index now reports v1.1.0 with a fresh 103-install / 166-download
baseline. By August 27 it showed 103 installs / 183 downloads; the +17
cumulative downloads and zero install growth are not qualified demand or
revenue. No owner action is queued.

## HQ-7 — enable the only checkout (1 minute)

Why human-only: this begins accepting real customer money.

Prerequisites: HQ-1 through HQ-4 complete, zero unresolved refund/fulfillment
alerts, the exact production commit is verified, the generated CSP is live, and
the GRACE verifier confirms no external script injection. HQ-2 has left all six
historical Prices inactive, and HQ-6 is complete. HQ-5 should still happen for
distribution, but its public listing state does not affect checkout safety.

Steps:

1. Reactivate only the canonical $299 Audit Price
   `price_1TRoGjDL3cQl851oiIWR5JIa`; do not reactivate any other Price and do not
   create a public Payment Link.
2. Set EOLKITS_AUDIT_CHECKOUT_ENABLED=1 in the reviewed production environment.
3. Redeploy only the Audit service and set repository variable
   AUDIT_CHECKOUT_EXPECTED=true.
4. Verify /api/capabilities reports Audit 2.0 ready, then confirm the static form
   appears and creates one $299 input-bound Checkout Session.

Estimated current owner total: 34 minutes. This leaves a 26-minute reserve for
unrecorded prior owner work or one failed authentication attempt; do not exceed
60 minutes without changing the plan.
