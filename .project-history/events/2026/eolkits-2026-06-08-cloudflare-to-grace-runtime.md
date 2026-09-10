---
id: eolkits-2026-06-08-cloudflare-to-grace-runtime
title: "The paid runtime moves from Cloudflare Workers to the owner's GRACE VPS, and 'live' is declared before delivery could work"
kind: architecture
scope: grace-api
components: [grace-api, worker, runner, deploy]
paths: ["apps/grace-api/**", "deploy/grace/**", "apps/worker/**", "pricing.yml"]
significance: foundational
occurred_at: 2026-06-08
decided_at: null
merged_at: 2026-06-08
released_at: 2026-06-09
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "Between 2026-05-31 and 2026-06-08 the fulfilment API was rewritten as a FastAPI service on the owner's self-hosted VPS with fail-closed configuration, webhook dedupe and auto-refund; it was declared deployed and live on 2026-06-09, two weeks before its email path was found to have never worked."
claim_ids: [CLM-E2-005, CLM-E2-008, CLM-E2-009, CLM-E2-010, CLM-E2-011, CLM-E2-013, CLM-E2-014, CLM-E2-015, CLM-E2-016, CLM-E2-017, CLM-E2-018, CLM-E2-019, CLM-E2-020, CLM-E2-022, CLM-E2-043, CLM-E2-055, CLM-E2-064, CLM-EXT-003, CLM-EXT-006, CLM-EXT-008, CLM-E2-021, CLM-E2-023, CLM-E2-058]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-mind-status-docs, SRC-bizops-audit-service, SRC-bizops-root]
anchors: ["3c5b48f5f7f530456272ed83c7a13c157eca5691", "ea7ad320628db958deeb7bb39882e5d45f1f3cdc", "bb70c18075aa1b6790013a3b1b228614b288c49b", "38a4392327a8afafa87b985a6ee473ec570819b9", "d845545808d55e1d18a86fdfa0a38240295d8fd3", "a65387ec7eea937954c7db9ad231e127ab58f877", "465d3419ec0d7937cc8e3c233319c58046914318", "528e6bbdb4e54d1f09002ef47acdc45f392a04f6"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-06-11-rupture-renamed-eolkits, eolkits-2026-08-22-legacy-commerce-retirement, eolkits-2026-08-30-fail-closed-relaunch-recovery]
amends: []
supersedes: []
superseded_by: [eolkits-2026-08-30-fail-closed-relaunch-recovery]
reversed_by: []
status: superseded
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The April Worker depended on Cloudflare R2 for audit-PDF delivery, and R2 was "not enabled on account"; on 2026-05-31 the plan was still an R2 redeploy once the owner enabled it (CLM-E2-005). The live commerce pages emitted literal `{API_URL}` placeholders — checkout was broken on the public site (CLM-E2-011). Outside the repository, the owner's notes record eolkits.com going from "never-deployed" on Vercel to a static site on the GRACE VPS around 2026-05-28 (CLM-EXT-003), and a portfolio-wide push had ranked EOLkits "#1 fastest path to a first dollar" on 2026-06-05 (CLM-EXT-007).

## Intended beneficiaries

The audit buyer, who needed a PDF to arrive; the owner, who already paid for the VPS and could host at $0 marginal cost (P-01).

## Goal, non-goal and definition of success

Goal: `eolkits-api` as a compose "satellite" on GRACE behind Caddy, `/health` 200 on same-host routing, webhooks at eolkits.com, fail-closed secrets. Non-goal, stated in the new HANDOFF: "Do not wire new production traffic" to the Cloudflare Worker, now "legacy/reference only" (CLM-E2-009). Success: the checklist in HANDOFF-2026-06-08, which left "run a live test Stripe payment" unchecked (CLM-E2-017).

## Principles affirmed, introduced, weakened or challenged

Introduced P-16 (fail closed in production): missing secrets abort, Checkout Sessions are validated against `pricing.yml` before fulfilment, webhooks deduplicated, refunds idempotent, uploads SSRF-blocked (CLM-E2-010). Introduced the pricing rule "displayed price always equals charged price" with passed deadlines at standard (CLM-E2-064; P-12). Weakened P-05: the handoff declared the path "verified end-to-end" while its own checklist admitted no purchase had been made (CON-007).

## Alternatives considered and rejected paths

Enabling R2 — documented as the blocker for weeks and then abandoned ("R2 was never enabled"). No written comparison of Cloudflare versus self-hosting exists in the repository; the decision was taken off-repo between 2026-05-22 and 2026-06-05 (the HANDOFF header claims a 2026-06-05 update for which no commit exists, CON-008's sibling in the E2 handoff). The Worker was retained rather than deleted, which is why it still answered with live Stripe on 2026-08-22.

## Decision and rationale

Move the fulfilment loop onto infrastructure the owner controlled and had already paid for, and harden it on the way. The rationale in the handoff is operational (R2 blocked; same-host routing simpler) and financial ($0). The historian adds that this also moved deployment into an environment only the owner's machine could reach by SSH, creating a "deploy gap" the repository could not close by itself (CLM-E2-018, CLM-E2-022).

## Implementation and evidence anchors

3c5b48f5f7f530456272ed83c7a13c157eca5691 (2026-06-08, 129 files: `apps/grace-api/`, `deploy/grace/`, `deploy-worker.yml` deleted, README title becomes EOLkits); ea7ad320628db958deeb7bb39882e5d45f1f3cdc (same day: server-routed checkout, `/api/events` funnel table, Drift Watch $19/mo, Audit→Pack upsell); bb70c18075aa1b6790013a3b1b228614b288c49b and 38a4392327a8afafa87b985a6ee473ec570819b9 (2026-06-09: pricing file missing from the image; crash loop on a migration ordering bug); d845545808d55e1d18a86fdfa0a38240295d8fd3 (HANDOFF-2026-06-08 "DEPLOYED & LIVE"); a65387ec7eea937954c7db9ad231e127ab58f877 (SEO-GRACE-HANDOFF describing GRACE as VPS + control plane + satellites); ship script and daily box cron 2026-06-22.

## Expected outcome

A hardened paid path that would deliver an audit PDF within minutes of payment and refund a failed Migration Pack automatically.

## Observed outcome

The API answered on 2026-06-09. On 2026-06-21 `send_email` was found to report failure by return value, so every failed send had counted as success (CLM-E2-043); on 2026-06-23 the Resend sending domain was found never verified — "a paying customer would have received nothing" (CLM-E2-055). External owner records through 2026-06-26 repeat that delivery was never verified end to end (CLM-EXT-008). No purchase ever exercised the path. The service later doubled as the studio's lead bus (see eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus) and, on 2026-08-25, was found still serving the pre-rebuild code with an unauthenticated upload path (CLM-E4B-065).

## Tradeoffs, debt and follow-ups

Two deployment environments (a Mac with SSH; agents without) and no in-repo deploy automation for the API; the Worker left alive with live Stripe until the 2026-08-22 tombstone; the deployed API drifting from `main` for the rest of the history (CON-018). The fail-closed shape of this service is the direct ancestor of the 2026-08-30 preflight.

## Unresolved questions

Who executed the 2026-06-09 deploy and from where; what the VPS actually ran after 2026-06-21 (the `vps-live-state-20260621` snapshot is the last pin); whether any lead or event row was ever written by a stranger.
