---
id: eolkits-2026-08-22-legacy-commerce-retirement
title: "Retiring the legacy rails: a 410 tombstone over the Cloudflare Worker, six Stripe prices archived by an audited workflow, and the invention of one-use push authorisation"
kind: security
scope: legacy-rails
components: [worker, ci, pricing]
paths: ["apps/worker/**", ".github/workflows/retire-legacy-cloudflare.yml", ".github/workflows/retire-legacy-stripe.yml", "pricing.yml"]
significance: high
occurred_at: 2026-08-22
decided_at: 2026-08-22
merged_at: 2026-08-25
released_at: 2026-08-25
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "The pre-rename Cloudflare Worker was still publicly healthy with live Stripe on 2026-08-22; a workflow deployed a tombstone over it, and on 2026-08-25 — under a new pattern of owner-attributed, one-use push authorisation — an audited workflow archived all six historical Stripe prices, including the canonical $299 one, so that no path could create a charge for a product the project could not fulfil."
claim_ids: [CLM-E4A-030, CLM-E4A-031, CLM-E4A-039, CLM-E4A-040, CLM-E4A-054, CLM-E1-034, CLM-E1-062, CLM-E2-009, CLM-E4B-008, CLM-E4B-026]
source_ids: [SRC-repo-git]
anchors: ["db12e12ccb3a5d7ab5ad4a011f4a6f9a47121307", "e437b2b94a16c4a478b1e127d6aea8f2bbb68295", "2505becd0e42e0fbee322d2aca4d059d4cff214d", "0159dc1a53d5ff21fccc02e794443c9a7bbdc2a5", "60ae1985a297a115a3118b5a5ee748214aaf9fe3", "84ad57b24bf23e632de4feff29a8b7196bc80361", "a75343f344e91ee1bcf68d85382db62adad686f7", "1e9e6072c058d51801defa374ae9b90df38f9b1b", "cf94235ea913f1c828ce9a63aecd27779669bab1", "75d99dc5a4d2de4aa55829330ff2ec40277aa80b"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-06-08-cloudflare-to-grace-runtime, eolkits-2026-07-14-billing-honesty-sku-retirement, eolkits-2026-08-22-truthful-evidence-report-rebuild, eolkits-2026-08-30-fail-closed-relaunch-recovery]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: closed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The Worker declared live on 2026-05-02 (CLM-E1-034) had been "legacy/reference only" since June (CLM-E2-009) but was never turned off: on 2026-08-22 it answered health checks with Stripe in live mode (CLM-E4A-030). The deployed GRACE API still had charge-capable handlers for retired SKUs, and six historical Payment Links existed. Stripe identifiers had been committed to `pricing.yml` since April (not reproduced here).

## Intended beneficiaries

Any stranger holding an old link; the owner, whose Stripe account is shared across projects.

## Goal, non-goal and definition of success

No path can create a new charge for a product that cannot be fulfilled. Non-goal: deleting the Worker (a tombstone preserves the URL and returns 410 with `retired: true`); asking the owner to click through the Stripe dashboard (rejected as error-prone, D22). Success: public 410s verified; every price archived; the run green.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-08 (do no harm) and P-15 (retire, don't rewrite). Introduced a governance mechanism rather than a principle: D33's "owner-attributed, one-use push authorization" — a temporary path-limited push trigger plus a unique commit-message phrase, so an agent using the connected repository-owner identity could run two prepared production-mutating workflows without reading machine credentials (CLM-E4A-039). The ledger itself calls this "a narrow audited transport … not a reusable confirmation bypass", in tension with D29's argument the day before that such actions must be owner-dispatched (the E4a review's contradiction 10).

## Alternatives considered and rejected paths

Owner dashboard clicks (rejected); deleting the Worker (rejected in favour of a tombstone); leaving prices active and relying on the closed API (rejected because a Payment Link bypasses the API). A preflight was added so the run would fail on any unexpected active Payment Link, because archiving a Price can deactivate links using its Product (CLM-E4A-040).

## Decision and rationale

Close the money surfaces in the order of blast radius: Worker first, then the catalogue. The stated rationale is that the old rails could still take money for products the rebuild had just declared not for sale. The historian notes that archiving the canonical $299 price meant the "one paid offer" also had no live price from 2026-08-25, which PR #25 later formalised with a runtime-supplied price id (CLM-E4B-008).

## Implementation and evidence anchors

db12e12ccb3a5d7ab5ad4a011f4a6f9a47121307 … e437b2b94a16c4a478b1e127d6aea8f2bbb68295 / 2505becd0e42e0fbee322d2aca4d059d4cff214d (2026-08-22 tombstone workflow and public probes showing `retired: true`); 0159dc1a53d5ff21fccc02e794443c9a7bbdc2a5, 60ae1985a297a115a3118b5a5ee748214aaf9fe3, 84ad57b24bf23e632de4feff29a8b7196bc80361 (the owner-gated Stripe retirement workflow: exact repo, main ref, owner as actor and triggering actor, typed phrase, audit of six prices, four products, six links, CLM-E4A-031); a75343f344e91ee1bcf68d85382db62adad686f7 (link preflight); 1e9e6072c058d51801defa374ae9b90df38f9b1b, cf94235ea913f1c828ce9a63aecd27779669bab1, 75d99dc5a4d2de4aa55829330ff2ec40277aa80b (2026-08-25 one-use authorisation, the run, and the trigger's removal). Production run ids are recorded in the ledgers; the run logs were not retrieved by this audit.

## Expected outcome

No legacy charge possible; the Worker's Stripe binding removed; owner left with key rotation and webhook cleanup.

## Observed outcome

Public 410s on the Worker; six prices archived and the Worker's Stripe binding removed (ledger-reported, runs green per the GitHub API). Account-key rotation and webhook cleanup remained owner-only and were later "excluded from every autonomous action by explicit owner direction" (CLM-E4B-026). The September credential sweep found no live secret in this repository (CLM-EXT-029).

## Tradeoffs, debt and follow-ups

Reopening checkout needs a fresh Price; the one-use authorisation pattern was reused three more times (PRs #26, #29, #42) and each time removed within minutes; the shared Stripe account's other projects are the reason `metadata.project=rupture` still matters.

## Unresolved questions

Whether the "retired Stripe credential" the ledgers keep excluding is the Worker binding or an account-level key, and whether it was rotated outside the repository.
