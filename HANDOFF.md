# EOLkits release handoff

**Current as of August 22, 2026.** This file replaces the obsolete pre-launch
handoff. Revenue state and owner-only work are tracked in `revenue/`; do not use
old launch documents as operating instructions.

## What is safe to ship now

- The free local scanners, browser scanner, GitHub Action, documentation, and
  static site.
- The Audit v2 backend **with checkout disabled**.
- The existing GitHub Marketplace Action identity, updated from a reviewed `v2`
  release after CI passes.

## What is not available

Migration Pack, Drift Watch, Organization License, the public GitHub App, and
partner/white-label fulfillment are closed research concepts. Their legacy
checkout paths must remain closed. Do not publish the archived copy in `launch/`
or accept payment for those concepts.

## The paid-product gate

The only proposed paid product is a $299 static repository evidence report.
Checkout must remain disabled until all of the following are evidenced in Stripe
test mode on the real deployment shape:

1. immutable upload and bounded archive preflight;
2. Checkout completion and verified Stripe webhook;
3. one-and-only-one job claim and real PDF rendering;
4. Resend delivery to an operator-owned address;
5. signed download and evidence lookup matching the PDF metadata;
6. failed-fulfillment refund initiation and reconciliation; and
7. source/report retention sweeps.

The exact deployment and test procedure is in `deploy/grace/README.md`. Keep
`EOLKITS_AUDIT_CHECKOUT_ENABLED=0` until that procedure passes. The static page
also hides checkout unless `/api/capabilities` reports Audit v2 ready.

## Owner actions

`revenue/HUMAN_QUEUE.md` is the sole current checklist. It includes exact links,
ordering, and a total time budget. In particular, legacy Stripe Payment Links
must be archived before paid traffic is possible, and old DEV posts need manual
review because autonomous posting or editing is prohibited.

## Verification

The complete local and CI matrix is documented in `README.md` and
`.github/workflows/test.yml`. A green unit suite is necessary but is not evidence
that payment, email, DNS, or production routing works; those require the live
test-mode exercise above.
