# EOLkits release handoff

Checkout is **open** as of 2026-09-20. `eolkits.com/api/capabilities` returns
`audit.checkout_enabled: true, reason: "ready"` and `/api/status` returns
`stripe: {ok: true, mode: "live"}`. The paid product is the **$299 static
repository evidence report**.

What that does and does not establish, stated plainly:

- **Fulfillment ran for the first time in this product's history** on 2026-09-20,
  inside the live container: `generate_audit_package` produced a real
  21,624-byte PDF carrying an evidence hash. Report generation works.
- A 30-day refund policy is published.
- Local tests and a working static site still do not establish a purchase path.
  No purchase has ever been made and **$0.00 has ever been collected**, so the
  checkout → webhook → email → download chain has never been exercised by a
  real buyer.
- **Residual risk, unfixed:** a trivial input yields 0 findings and 2 pages. A
  buyer whose repository has nothing wrong pays $299 for an empty report. The
  next improvement is to gate paid checkout on the free scan having found
  something.

The GitHub Pages mirror (`ntoledo319.github.io/EOLkits/`) was a genuine second
checkout — it carried `const API='https://eolkits.com'` and opened the same $299
buy form — and was disabled on 2026-09-20; it now returns 404. `eolkits.com` is
the single till.

**This branch is not mergeable as it stands.** `fix/storefront-audit-20260919`
is not a fast-forward of `origin/main`: that branch (`5fb63503` when this was
written) carries three commits this branch does not. Its first commit,
`6f6e2549`, is a snapshot of 90 uncommitted
files taken from the owner's working tree — not work produced by that pass. It
must not be merged until decision D-004 is answered.

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

**Status, 2026-09-20 — this gate was not met before checkout opened.** Production
runs with audit checkout enabled and live Stripe keys. Of the seven outcomes
above, only the report-rendering half of (3) is recorded: a real PDF with an
evidence hash, produced inside the live container from a supplied input. Items
(1), (2), (4), (5), (6) and (7) are still unrecorded — no completed Checkout, no
verified webhook, no delivery to an operator address, no signed download record,
no refund reconciliation, no retention sweep evidence. The till stays open by
owner direction because delivery demonstrably produces a report and a refund
policy is published; treat the six open items as the work queue, not as passed.

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
