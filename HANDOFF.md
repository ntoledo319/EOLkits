# EOLkits release handoff

Checkout remains closed. The only planned paid product is a **$299 static
repository evidence report**; local tests and a working static site do not
establish a functioning purchase or delivery path.

Use [maintenance](docs/MAINTENANCE.md) for engineering and publication work,
[the owner queue](revenue/HUMAN_QUEUE.md) for private access/account actions, and
[the evidence ledger](revenue/METRICS.md) for dated observations. The six prior
revenue ledgers are preserved [byte for byte](revenue/archive/2026-09-10/README.md).

## Release surfaces

The free CLIs, browser scanner, GitHub Action, editor extension, and generated
site are independent release surfaces. A green reviewed revision can be released
through its existing channel. Preserve the Marketplace identities and supported
runtime versions; local changes are not published releases.

Audit v2 can be deployed with checkout disabled using the guarded
[GRACE rollout procedure](deploy/grace/README.md). The September 10 first-party
analytics repair passed both static guards; that resolves the earlier external
script/CSP blocker only. It does not establish the backend version or commerce
readiness. Dependency publication and PR #63 verification remain in the current
maintenance inventory.

Migration Pack, Drift Watch, Organization License, partner white-labeling, and
the public GitHub App remain unavailable. Their checkout paths stay closed.
Historical Stripe prices were retired; do not reactivate them or use archived
launch copy as an operating procedure.

## Required paid-product evidence

Before enabling production checkout, record all seven outcomes from the isolated
Stripe test-mode deployment described in [the deployment guide](deploy/grace/README.md#test-mode-e2e-deployment):

1. An immutable upload and bounded archive preflight.
2. Completed Checkout and a verified Stripe webhook.
3. Exactly one job claim producing a real PDF.
4. Resend delivery to an operator-owned address.
5. A signed download and verification record matching the PDF metadata.
6. Failed-fulfillment refund initiation and reconciliation.
7. Source and report retention sweeps.

Production must continue to reject test keys. Keep
`EOLKITS_AUDIT_CHECKOUT_ENABLED=0` until these outcomes, seller/account facts,
real fees, zero incremental hosting cost, and the separate live-catalog preflight
are verified. The static form also requires a successful `/api/capabilities`
readiness response. Record evidence without credentials or customer data.

## Verification and resumption

Run `python3 scripts/verify.py all`; use the
[development guide](docs/development.md) for prerequisites. CI additionally
checks the actual container images and runtime matrix. Neither substitutes for
the deployment exercise above.

At handoff, identify the exact reviewed commit, local checks, remote CI state,
publication state, and outstanding access requirements separately. Preserve
`history/cited-objects` and `archive/*` tags. Keep the revenue loop disabled until
its network prerequisite is verified; do not manufacture publication by changing
dates or regenerating identical artifacts.
