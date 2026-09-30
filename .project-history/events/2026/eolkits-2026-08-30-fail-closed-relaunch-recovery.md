---
id: eolkits-2026-08-30-fail-closed-relaunch-recovery
title: "Recovery from the top: PR #25 makes the only paid offer fail closed before any production mutation, and the one-use push trigger becomes a pattern"
kind: security
scope: grace-api
components: [grace-api, deploy, ci, vscode-extension]
paths: ["apps/grace-api/**", "deploy/grace/**", ".github/workflows/prepare-marketplace-v2.yml", ".github/workflows/retire-legacy-cloudflare.yml", ".github/workflows/public-v2-consumer.yml", ".github/workflows/acquisition-evidence.yml", "pricing.yml"]
significance: foundational
occurred_at: 2026-08-30
decided_at: 2026-08-30
merged_at: 2026-08-30
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "A branch literally named for undoing the mess opened the last era: the GRACE API now validates secrets and GET-attests a v2-only Stripe price before touching SQLite, the old $299 price is hard-retired, an emergency Caddy block and a volume snapshot script exist, production-mutating workflows lost their push triggers, a scheduled consumer proves the public v2 Action installs, and a five-day install-growth falsifier was set for the extension — while two agent lines then diverged from the same base."
claim_ids: [CLM-E4B-006, CLM-E4B-007, CLM-E4B-008, CLM-E4B-009, CLM-E4B-010, CLM-E4B-011, CLM-E4B-012, CLM-E4B-013, CLM-E4B-014, CLM-E4B-015, CLM-E4B-016, CLM-E4B-017, CLM-E4B-018, CLM-E4B-027, CLM-E4B-028, CLM-E4B-049, CLM-E4B-065, CLM-EXT-034]
source_ids: [SRC-repo-git, SRC-github-prs, SRC-github-api, SRC-github-releases]
anchors: ["90722cd7311ed5ef535c7c2a6cfd7beee6f096fe", "47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8", "172161d8164940ac62940a75a27ac741db3ba86f", "91b92af513265261483113b6e290fa1ee37176b5", "6d1ae6bec74266eeb348087f8725bd1ab5e3af39", "3edc2a73518a8e0faded0c058651866890c44030", "79e3a87158612b949b80dfb2d8adf968820ba9c5", "68652e345998af910a0d15eed979bacecac55de2"]
related: [eolkits-2026-06-08-cloudflare-to-grace-runtime, eolkits-2026-08-22-truthful-evidence-report-rebuild, eolkits-2026-08-22-legacy-commerce-retirement, eolkits-2026-08-25-host-injected-analytics-contained, eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening]
amends: []
supersedes: [eolkits-2026-06-08-cloudflare-to-grace-runtime]
superseded_by: []
reversed_by: []
status: observed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The live custom host was "a stale backend with an unauthenticated upload path" plus the injected analytics script; the public `@v2` ref had been deleted in the 08-29 branch churn (CLM-EXT-034); draft-sync and Cloudflare-retirement workflows still ran on ordinary pushes; the app import migrated SQLite before secret validation; the old $299 price id still sat in `pricing.yml` (PR #25's stated premises, CLM-E4B-006). The Day-7 falsifiers had already failed (CLM-E4A-053).

## Intended beneficiaries

The first real buyer, who must not be able to pay into a system that cannot deliver; the owner, whose remaining production steps were converted into scripts with guards.

## Goal, non-goal and definition of success

"Makes the only paid offer fail closed before any production-state mutation and restores durable distribution monitoring" (PR #25). Non-goal: rewriting remote history — "Preserve the audited marketing history". Success: green CI on an immutable tree; `v2`, `main` and `marketing-machine-v2` at the same commit; checkout still closed.

## Principles affirmed, introduced, weakened or challenged

Introduced P-16.2 in its final form: a mutation-free `validate_runtime_preflight()` (secrets plus optional GET-only Stripe catalogue attestation) runs before directories are created or the store is opened (CLM-E4B-007). Affirmed P-15 (no rewrite; `v2` recreated without force) and P-06 (Caddy containment block: uploads and mutations 503, retired App routes 410, webhook still proxied, CLM-E4B-009). Extended P-05.2 with a mechanical falsifier: `VSCODE_SIGNAL_GATE_AT`, passing only on install delta > 0 or a qualified VS-attributed author (CLM-E4B-011).

## Alternatives considered and rejected paths

Rewriting history (rejected, D50); ambient push triggers (rejected as unsafe); asking the owner for a routine dispatch to retarget the Marketplace draft (rejected as "waste of the scarce human budget", D50) — so PR #26 added a push trigger keyed on `github.event.before == 47cd9eae…`, and PR #27 removed it seven minutes later (CLM-E4B-013, CLM-E4B-014). Rebase of the diverging Claude line (rejected, D51/D56: preserve both commit lines).

## Decision and rationale

Fail closed, then recover distribution monitoring, then let the owner deploy. The rationale is the operating document's harm rule applied to production state; the historian notes that this PR is the point where the June architecture (fail closed on configuration) finally became fail closed on money, and that the deployment itself still awaited the owner.

## Implementation and evidence anchors

90722cd7311ed5ef535c7c2a6cfd7beee6f096fe (remote PR #25 head, tree identical to local 172161d8164940ac62940a75a27ac741db3ba86f — the object-API transport of CLM-E4B-028) merged 2026-08-30T05:11Z as 47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8, which is also `origin/v2` (CLM-E4B-012): `preflight.py`, `config.py`, `pricing.py` (`RETIRED_PRICE_SKUS`, `runtime_price_env: EOLKITS_AUDIT_PRICE_ID`, CLM-E4B-008), `stripe_client.py`, `store.py`; Caddy block; `snapshot-api-volume.sh`; push triggers stripped (CLM-E4B-010); `public-v2-consumer.yml`; the VS gate. 91b92af513265261483113b6e290fa1ee37176b5 / 6d1ae6bec74266eeb348087f8725bd1ab5e3af39 (PRs #26/#27). 3edc2a73518a8e0faded0c058651866890c44030 (a Claude cycle repairing a stale draft slug nine minutes after it was written, CLM-E4B-016); 79e3a87158612b949b80dfb2d8adf968820ba9c5 and 68652e345998af910a0d15eed979bacecac55de2 (the two-line merges of 08-30 and 09-01, zero code conflicts, CLM-E4B-017).

## Expected outcome

An immutable, green base from which the owner deploys the closed API and runs the gate; a Marketplace draft that tracks the verified SHA.

## Observed outcome

Merged and green; `v2` at the merge commit; draft 375063073 retargeted and still a draft at HEAD (CLM-E4B-015); nothing deployed to GRACE — the host remained pre-v2 through 2026-09-04 (CLM-E4B-065); repository secrets are exactly the Cloudflare pair and the VSCE token, corroborating that no production credential exists in CI (CLM-E4B-049). The Claude cycles on the recreated branch reported an organisation-level egress block for the 4th through "ninth+" consecutive cycle and shipped only scanner fixes and date bumps (CLM-E4B-018).

## Tradeoffs, debt and follow-ups

Everything production-side moved to the Human Queue (HQ-A install the Caddy block, HQ-C deploy); the one-use trigger pattern recurred in PRs #29 and #42; renumbered D-ids across the two lines (CON-019). `main` was never force-updated and the repository shows no rewrite artefacts (CLM-E4B-027).

## Unresolved questions

Whether the owner will run `deploy-api-closed.sh`; what the retired Stripe credential is and whether it was rotated.
