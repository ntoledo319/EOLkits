# Current operating decisions

Earlier pivots, incidents, authorizations and competing interpretations are
preserved in [the complete decision archive](archive/2026-09-10/DECISIONS.md) and
[project history](../PROJECT_HISTORY.md). This file states the decisions needed
to resume current work; it does not rewrite their history.

1. **Keep one bounded paid offer.** Only the $299 static repository evidence
   report is planned. The free scanners remain useful and MIT-licensed. New free
   features do not reopen legacy commercial promises.
2. **Keep checkout closed until proved.** Real deployment, immutable input,
   webhook/job handling, PDF/email/download, refunds and retention must satisfy
   [HANDOFF](../HANDOFF.md). No tests, static guard or synthetic event proves a sale.
3. **Preserve compatibility.** Keep VS Code 1.85 support and the supported
   TypeScript/typescript-eslint range. Node 26 API types and incompatible major
   bumps were declined with evidence. Refresh CI before merging other upgrades.
4. **Preserve the analytics repair.** Serve the tracker first-party through
   `/_stats/`; keep CSP strict. The September 10 repair supersedes the old
   injection blocker, while backend/payment readiness remains separate.
5. **Respect publication policy.** The exact prior push failed with
   `approval required by policy, but AskForApproval is set to Never` despite
   owner authorization. Do not retry through another transport or infer success.
   [MAINTENANCE](../docs/MAINTENANCE.md) tracks publication and PR dispositions.
6. **Keep the normal workspace boundary.** The one-time external-script/SSH
   exception covered the documented analytics repair only. It is not a general
   credential-search or host-administration exception. No spend or autonomous
   customer contact; retired Stripe credential rotation/revocation remains
   excluded at the owner's direction.
7. **Keep history and pause signals.** Preserve `history/cited-objects` and
   `archive/*` tags. Keep the revenue loop disabled until neutral-control network
   verification succeeds. Blocked work may stop without cosmetic publication.
8. **Consolidate without evidence loss (September 10).** Copy all six current
   ledgers byte for byte, including uncommitted updates, into
   [the dated archive](archive/2026-09-10/README.md) with hashes before replacing
   active summaries. Keep one [engineering inventory](../docs/MAINTENANCE.md)
   and one [owner queue](HUMAN_QUEUE.md); archived instructions are historical.

9. **Complete the requested roadmaps locally.** All ten kit features are implemented
   with scoped inputs and explicit live/apply options. Full local verification
   passed. Preserve this reviewable working tree without a new commit under the
   blocked-cycle rule; resume the already-authorized publication only when the
   command-policy rejection is removed. No transport workaround is authorized.

10. **Keep the till open, and say what is not proved (September 20).** This
    supersedes decision 2, "Keep checkout closed until proved". Checkout opened
    on `eolkits.com` with live Stripe keys before the HANDOFF gate passed. The
    reason it stays open: fulfillment was exercised for the first time in the
    live container that day and produced a real 21,624-byte PDF with an evidence
    hash, and a 30-day refund policy is published — closing a working till
    removes the capacity to sell. The reason this is not "proved": no purchase
    has ever been made, $0.00 has ever been collected, and steps 1, 2, 4, 5, 6
    and 7 of the fulfillment gate are unrecorded. Decision 2 remains the correct
    description of the period before this date.

11. **Run one till, not two (September 20).** The GitHub Pages mirror was a
    second live checkout against the same backend, not a marketing copy. It was
    disabled; `ntoledo319.github.io/EOLkits/` returns 404. Publish paid surfaces
    to `eolkits.com` only; do not re-enable Pages for anything that can take
    money.

12. **Gate paid checkout on a finding before selling harder (September 20).** A
    trivial input yields 0 findings and 2 pages, so a buyer with nothing wrong
    can pay $299 for an empty report. Until paid checkout is gated on the free
    scan having found something, do not increase traffic to the buy form, and
    keep the free-scan-first wording on every paid surface.

13. **Do not merge `fix/storefront-audit-20260919` (September 20).** The branch
    is pushed but is not a fast-forward of `origin/main` (12 ahead, 3 behind at
    `5fb63503`), and its first commit `6f6e2549` is a snapshot of 90 uncommitted
    files lifted from the owner's working tree rather than work authored by that
    pass. It is blocked on owner decision D-004.

