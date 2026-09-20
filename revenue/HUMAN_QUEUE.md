# Current owner queue

Snapshot: September 10, 2026. These are the remaining private-access, account and
execution-policy prerequisites. Completed static analytics work is recorded in
[METRICS](METRICS.md); engineering tasks live in [MAINTENANCE](../docs/MAINTENANCE.md).
The full former queue and its account observations are
[archived unchanged](archive/2026-09-10/HUMAN_QUEUE.md).

Estimated remaining owner effort is **42 minutes** if every item is needed.
This is an estimate, not measured cumulative labor; usable imported access may
replace several steps. Do not treat the historical 60-minute total budget as
remaining untouched without reconciling actual owner time.

## HQ-P — unblock already-authorized publication (2 minutes)

**What/why:** reviewed maintenance publication was rejected before execution by
an execution-policy control, even after owner authorization. Another verbal
approval or a different transport does not resolve that control.

1. Open the session's command-permission controls and enable the exact rejected
   maintenance-branch push identified in [MAINTENANCE](../docs/MAINTENANCE.md).
2. Resume the task; the agent must obtain fresh CI, complete the separate
   maintenance PR and ordered dependency updates, and keep broad PR #63 open.
   The larger cleanup is locally verified and remains a reviewable working tree.

[Repository pull requests](https://github.com/ntoledo319/EOLkits/pulls).

## HQ-0 — make existing private configuration available (2 minutes)

**What/why:** required runtime/payment configuration was absent from the last
workspace inventory; files elsewhere are outside the normal workspace boundary.

1. In Dolphin, enable hidden files (`Ctrl+H`) and locate existing EOLkits/GRACE
   environment files. Copy them into `tmp/owner-env-import/` under this checkout.
2. Use copies, not symlinks. Keep the files private and ignored; do not paste
   values or callback URLs into chat. Reply only that the import is ready.

The private inbox is `tmp/owner-env-import/` in this checkout. The agent validates
capabilities without printing secrets and removes any queue steps they satisfy.
The excluded retired Stripe credential must not be copied or changed.

## HQ-A — verify/contain the stale upload service (3 minutes)

**What/why:** the last recorded API probe did not establish Audit v2. Host runtime
configuration and a controlled rollout are required; the analytics repair does
not attest API readiness.

1. On the controlled GRACE checkout, follow the [safe rollout order](../deploy/grace/README.md#safe-rollout-order).
2. If the old upload/checkout surface remains active, install the reviewed
   containment block and validate/reload Caddy as documented.
3. Verify expected 503 mutation and 410 retired-route responses while retaining
   the webhook route. Leave checkout off and record only route/status evidence.

## HQ-B — confirm seller/account economics (2 minutes)

**What/why:** actual account country, fee schedule/currencies and incremental
hosting cost require owner knowledge; public standard fees cannot establish them.

1. Open [Stripe settings](https://dashboard.stripe.com/settings). Supply only
   account country, standard/custom pricing, charge and settlement currencies.
2. Confirm EOLkits' incremental GRACE cost, including whether it is exactly $0.
   Recompute the target using those facts before accepting payment.

## HQ-C — closed rollout, isolated fulfillment proof and indexing (18 minutes)

**What/why:** this requires the private production/test configuration, an
operator-owned delivery address and account-controlled indexing tools.

1. Follow [the closed deployment procedure](../deploy/grace/README.md#deploy-checkout-closed)
   from a reviewed green commit, starting with its dry-run. Keep checkout off.
2. Complete all seven outcomes in [HANDOFF](../HANDOFF.md) using the separate
   test Compose project/volume. Record commit, sanitized evidence and pass/fail;
   preserve production data and never use live payment keys in the test project.
3. Verify the current static guards remain green. The first-party tracker repair
   is already complete; do not reintroduce the external script.
4. In [Google Search Console](https://search.google.com/search-console), select
   `eolkits.com`, resubmit its sitemap and request the relevant updated pages.
   An accepted request is not evidence that stale search snippets disappeared.

## HQ-D — review/remove unsupported public DEV copy (10 minutes)

**What/why:** author-controlled public communications need the owner's action;
25 EOLkits posts were last observed, but that is a dated count.

1. Open [DEV dashboard](https://dev.to/dashboard) and review the currently public
   EOLkits posts against the [quarantined corpus](../launch/distribution/devto/README.md).
2. Return unsupported posts to drafts; do not publish replacements in this batch.
3. Check [the public profile](https://dev.to/ntoledo319) and record what remains.

## HQ-E — publish the reviewed Marketplace release (2 minutes)

**What/why:** Marketplace agreement acceptance and any 2FA are account attestations.

1. Open [releases](https://github.com/ntoledo319/EOLkits/releases). Locate the
   canonical private v2.0.0 draft (last recorded release ID 375063073).
2. Have the agent reverify its current target against protected `v2` and green CI;
   archived draft URLs and commit targets may be stale. Select the Marketplace
   checkbox for the existing listing, accept the agreement and finish 2FA.
3. Confirm the version on [the existing listing](https://github.com/marketplace/actions/rupture-aws-deprecation-check).

## HQ-G — enable the sole live catalog after every gate (3 minutes)

**What/why:** only after HQ-A through HQ-D and the fulfillment/economic gates
are complete may the owner accept real customer money. HQ-E adds distribution
and cannot substitute for the commerce gates.

1. In [Stripe Products](https://dashboard.stripe.com/products), create one Audit v2
   Product and a one-time USD $299 Price. Do not reuse retired prices or create
   a public Payment Link.
2. Supply only the new IDs through private runtime configuration. With the
   intended checkout configuration, run the mutation-free
   [live-catalog preflight](../apps/grace-api/eolkits_grace/preflight.py). The
   closed deployment wrapper intentionally cannot enable checkout.
3. After preflight passes, have the operator apply the reviewed live configuration
   and set `AUDIT_CHECKOUT_EXPECTED=true`. Verify health, readiness, the public
   form and input-bound checkout without self-charging in live mode. Record evidence.

Historical price retirement is already recorded; it is not an unfinished task.
Retired Stripe credential rotation/revocation remains explicitly excluded and
must not be represented as completed.
