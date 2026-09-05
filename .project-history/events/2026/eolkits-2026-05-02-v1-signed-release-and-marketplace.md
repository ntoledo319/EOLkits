---
id: eolkits-2026-05-02-v1-signed-release-and-marketplace
title: "Launch hardening, the signed v1.0.0 release, the Marketplace 'v1' tag — and a launch that never fired"
kind: release
scope: project-wide
components: [ci, worker, runner, github-action, vscode-extension, launch]
paths: [".github/workflows/release.yml", "action.yml", "apps/runner/**", "launch/**", "HANDOFF.md"]
significance: high
occurred_at: 2026-05-02
decided_at: 2026-05-02
merged_at: 2026-05-02
released_at: 2026-05-02
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "On 2026-05-02 the project declared live checkout, published a Sigstore-signed v1.0.0 and a Marketplace 'v1' tag, made the CI trust signals runnable, and left only 'operator-only' steps; then all non-bot activity stopped for eleven days and the Show HN window passed."
claim_ids: [CLM-E1-034, CLM-E1-035, CLM-E1-036, CLM-E1-037, CLM-E1-038, CLM-E1-039, CLM-E1-040, CLM-E1-041, CLM-E1-042, CLM-E1-043, CLM-E1-044, CLM-E1-045, CLM-E1-046, CLM-E1-047, CLM-E1-048, CLM-E1-049, CLM-E1-050, CLM-E1-051, CLM-E1-052, CLM-E1-058, CLM-E1-059, CLM-E1-062, CLM-E1-063, CLM-E1-033, CLM-E2-029, CLM-E2-030]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-github-releases, SRC-aider-untracked]
anchors: ["fbe596e8291b862a93d24a274d105517da0d54f7", "9a213d2fa01bc2f9332e91e258f3d9b5d00ee759", "4d834b80c2567740c178cfc0dc61bbdce12620b7", "c00f505dbd5f7f44b19ebe54532981b23bc29778", "c206391be043804931d01de7f87df74be1c67363", "c0d02835b6dc27e2c1f7adedd2ff44cfc27f175e", "da645e78187db67808a9548e2e98d952958474d8", "958f6f3a1a571815f0d408b38bffac634b364fe0"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts]
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

The three "blocking credentials" gate (Stripe, Cloudflare, GitHub App) was the declared blocker; the verification workflows were red or could not run; a Show HN was pencilled for Tuesday 2026-05-05. An attempt on 2026-04-30 to hand an external operator-handoff document to aider on Azure-hosted models failed four times on configuration and left only untracked chat logs (CLM-E1-033).

## Intended beneficiaries

Prospective buyers arriving from Show HN and the GitHub Marketplace; the owner, who was to be left with a short list of clicks.

## Goal, non-goal and definition of success

Flip to live checkout, make every trust-signal workflow green, publish signed artifacts, list the Action on the Marketplace, ship the VS Code extension, leave only operator-only steps (CLM-E1-034, CLM-E1-044). The runbook's two-builder reproducibility check was dropped in favour of wheels/sdist/npm-pack with inline SBOM stubs (CLM-E1-035).

## Principles affirmed, introduced, weakened or challenged

Affirmed: signed releases and SBOMs as trust signals (P-05). Weakened: the "Reproducible Release" name survived without a reproducibility check, Python SBOMs listed zero components (CLM-E1-035, CLM-E1-036); the mutation gate the copy promised was made non-blocking the next day (CLM-E1-046); the "12 public repos, 0 findings" benchmark appeared only after a workflow change counted empty scanner output as a pass (CLM-E1-037, CLM-E1-038). Reversed: the day-one "no X/LinkedIn/cold outreach" directive and the runbook's "no pre-staked comments" cut both gave way to social posts, outreach templates and a reply playbook (CLM-E1-058).

## Alternatives considered and rejected paths

A live-AWS scan as the runner's gate "could never pass" in CI without credentials; the runner was switched to static IaC + codemod on 2026-05-04 (CLM-E1-048). The autonomous "no reply playbook" posture was replaced by a human-voiced eleven-reply kit (CLM-E1-050).

## Decision and rationale

Declare launch mode and cut the planning corpus down to a single "FINAL HANDOFF" (CLM-E1-044). The rationale, as the documents put it, was that everything technical was done and only owner clicks remained. The historian notes that the handoff itself contradicted this: readiness.md admitted the GitHub App credentials were all missing and were "the only true blockers" (CLM-E1-043), and HANDOFF.md still sold a "$499 Solo Kit" that pricing.yml had replaced three days earlier (CLM-E1-045).

## Implementation and evidence anchors

fbe596e8291b862a93d24a274d105517da0d54f7 ("launch hardening and live worker cutover", 96 files); six CI commits ending at 9a213d2fa01bc2f9332e91e258f3d9b5d00ee759, tagged v1.0.0 (annotated tag 4d834b80c2567740c178cfc0dc61bbdce12620b7; release with 24 signed assets at 09:43Z); root action.yml and lightweight tag `v1` on c00f505dbd5f7f44b19ebe54532981b23bc29778 (release 22:54Z; CLM-E1-040, CLM-E1-041); c206391be043804931d01de7f87df74be1c67363 wiring the migration-PR runner to real GitHub App tokens; c0d02835b6dc27e2c1f7adedd2ff44cfc27f175e deleting the runbook; da645e78187db67808a9548e2e98d952958474d8 and 958f6f3a1a571815f0d408b38bffac634b364fe0 (sandbox PR, launch kit).

## Expected outcome

Show HN on 2026-05-05, Marketplace tile live, first sales in the week.

## Observed outcome

A release existed; the Marketplace tile was still 404 on 2026-05-03 (CLM-E1-047); a bot-opened PR on a sandbox repository was reported (CLM-E1-048, CLM-E1-049); launched.txt stayed "not yet submitted"; no non-bot commit exists between 2026-05-04 03:02 and 2026-05-15 (CLM-E1-051, CLM-E1-052). The VS Code extension was reported published but only rediscovered as such in August (see eolkits-2026-08-22-free-surfaces-made-truthful).

## Tradeoffs, debt and follow-ups

Launch copy carried claims ahead of the code — Babel/libcst AST codemods over regex, a gated mutation score, a shared library (CLM-E1-059) — that later eras had to retract. The GitHub App webhook target moved three times in three days as the Worker's account was corrected (CLM-E1-062). The planning corpus survives only in history.

## Unresolved questions

Why activity stopped after 2026-05-04; whether the sandbox PR merged and whether the App secrets ever reached the Worker; what the off-repo operator handoff document instructed.
