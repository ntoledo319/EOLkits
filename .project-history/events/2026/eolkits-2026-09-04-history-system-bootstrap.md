---
id: eolkits-2026-09-04-history-system-bootstrap
title: "Bootstrap of the living-history system (reconstruction of 2026-04-28 to 2026-09-04)"
kind: bootstrap
scope: project-wide
components: [docs, ci]
paths: ["PROJECT_HISTORY.md", "docs/history/**", ".project-history/**", "scripts/project_history.py", "tests/test_project_history.py", ".github/workflows/history.yml", ".github/PULL_REQUEST_TEMPLATE.md", "AGENTS.md"]
significance: high
occurred_at: 2026-09-04
decided_at: 2026-09-04
merged_at: null
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-05
summary: "A read-only archaeology of all 3,599 reachable commits, 58 PRs, 4 releases and the owner's portfolio records produced this evidence-linked history plus a deterministic tool, CI checks and an agent continuity contract; nothing was committed by the reconstruction itself."
claim_ids: [CLM-EXT-029, CLM-EXT-030, CLM-EXT-033, CLM-E4A-055]
source_ids: [SRC-repo-git, SRC-commit-index, SRC-github-api, SRC-purge-report, SRC-purge-ledgers, SRC-historian]
anchors: ["71c78a1192ce8e83f955f3b53f1595449d4c9ff7", "05435fd26157dd1bd763e6e9fb1b4ecd39a7cecb"]
related: [eolkits-2026-09-01-credential-sweep-left-repo-unrewritten]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: implemented
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The repository had no history system. Its intent lived in handoff documents that were repeatedly deleted (2026-05-02, 2026-08-22), in agent-authored ledgers under `revenue/`, in commit messages, and in owner records outside the repository. 3,253 of 3,599 commits were automation noise. Each new agent session reconstructed context from scratch, and the operating document (AGENTS.md, unchanged since 2026-07-13) still described a mission whose clock had been restarted twice (CLM-E4A-055).

## Intended beneficiaries

Future maintainers and coding agents starting work in this repository; the owner, who should not have to narrate the past again.

## Goal, non-goal and definition of success

Goal: one canonical, evidence-linked reading path (`PROJECT_HISTORY.md`) rendered from curated chapters and structured ledgers, with a tool that validates, renders deterministically, assesses new work and audits drift. Non-goals: rewriting product code; producing a commit diary; auto-generating interpretation. Success: the independent verifier passes; every cited SHA resolves; render is byte-stable; secrets absent.

## Principles affirmed, introduced, weakened or challenged

Introduced P-14: material decisions are recorded as event capsules with distinct occurred/decided/merged/released/recorded dates; backfills are labelled; closed events are append-mostly; the tool never authors prose.

## Alternatives considered and rejected paths

Recording per-commit changelog entries (rejected: 3,006 regeneration commits would dominate); a third-party YAML dependency (rejected: the project's policy forbids new dependencies for tooling; a strict YAML subset parser was written instead); running pytest (rejected for the policy command because pytest is not installed system-wide; unittest is used, and the test file remains pytest-collectable).

## Decision and rationale

Install the structure required by the shared contract; machine-index every commit; divide deep reading by era across six read-only sub-reviews; reconcile contradictions centrally; write all narrative by hand from the claim ledger.

## Implementation and evidence anchors

Audit anchor HEAD 71c78a1192ce8e83f955f3b53f1595449d4c9ff7 on branch codex/workspace-env-scan-20260904; root 05435fd26157dd1bd763e6e9fb1b4ecd39a7cecb. Artifacts: `docs/history/*`, `.project-history/*`, `scripts/project_history.py`, `tests/test_project_history.py`, `.github/workflows/history.yml`, `.github/PULL_REQUEST_TEMPLATE.md`, AGENTS.md §14. The credential-purge check confirmed no rewrite of this repository (CLM-EXT-029, CLM-EXT-030, CLM-EXT-033).

## Expected outcome

Agents load `docs/history/ORIENTATION.md` and `context` output before work, and declare `history:recorded`, `history:none` or `history:defer` afterwards; CI enforces the declaration and drift checks once the branch is pushed.

## Observed outcome

Local validation, the 22 unit tests, a byte-stable double render, a clean full audit and the lead's independent verifier all passed at the close of the reconstruction (2026-09-05 UTC; the anchors and counts are those of 2026-09-04, and no commit was added in between). The CI workflow has not yet run: it activates only when these files are pushed to GitHub.

## Tradeoffs, debt and follow-ups

The pre-existing modified `.gitignore` in the working tree was left untouched as present-tense work. E3 and E4b reviews were folded in as they arrived; any later evidence should be added as amendments, not silent edits. The monthly gardener writes a drift report but never a narrative.

## Unresolved questions

Whether the owner wants the history committed on this Codex branch or on main; whether future agents will honour the continuity contract without harness enforcement.
