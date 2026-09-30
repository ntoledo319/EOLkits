---
id: eolkits-2026-06-11-rupture-renamed-eolkits
title: "Rupture becomes EOLkits: a name chosen off-repo, executed by two agents nine minutes apart, and never fully applied"
kind: rename
scope: project-wide
components: [docs, web, github-action, vscode-extension, ci]
paths: ["README.md", "action.yml", "apps/vscode-extension/package.json", "launch/REPO-RENAMED.md", ".github/workflows/release.yml"]
significance: high
occurred_at: 2026-05-31
decided_at: null
merged_at: 2026-06-11
released_at: 2026-06-11
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "The product name EOLkits first appears in the tree on 2026-05-31, the README flips on 2026-06-08, and the GitHub repository was renamed on 2026-06-11 between two commits that pointed links in opposite directions; the rename's rationale is not stated anywhere in the repository, and the Rupture identity survives wherever a marketplace slug would be lost."
claim_ids: [CLM-E2-006, CLM-E2-007, CLM-E2-024, CLM-E2-025, CLM-E2-026, CLM-E2-027, CLM-E2-028, CLM-E2-003, CLM-EXT-002, CLM-EXT-012, CLM-EXT-028, CLM-E4A-035, CLM-E4B-021, CLM-E4A-027, CLM-E1-003, CLM-EXT-004, CLM-EXT-040]
source_ids: [SRC-repo-git, SRC-github-releases, SRC-mind-status-docs, SRC-tc-truth-register, SRC-tc-registry]
anchors: ["6741fd3e494a9662f8debed0a99811d916fedc86", "3c5b48f5f7f530456272ed83c7a13c157eca5691", "af7226841e4827114e6e6fb9cb61cb08d98fa8ef", "da6dc36cf4383291a329330557dc523d7495704c", "f3d3dea620d22ffffd5606c7623c4e18b642f195", "8641432f899dcb045e5d918fe1b7df0057e5ed41"]
related: [eolkits-2026-04-28-rupture-mission-launch, eolkits-2026-06-08-cloudflare-to-grace-runtime, eolkits-2026-08-22-free-surfaces-made-truthful]
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

"Rupture" was the mission's word for a deadline event and the brand from the first commit (CLM-E1-003). The owner's late-May notes show a domain-naming exercise for "Project: Rupture (B2B Developer Tools)" whose core value was "AWS is breaking your production on a specific date"; candidates included DeprecationFix.com, RuptureKit.com and EOL-kits-style names, and the product catalogue then records "Rebrand complete (formerly Rupture)" (CLM-EXT-002). In the repository the pressure was mechanical: the Marketplace action slug derived from "Rupture …" returned 404 at the expected `eolkits-aws-deprecation-check` address, and docs pointed at `ntoledo319/EOLkits` URLs before any such repository existed (CLM-E2-007).

## Intended beneficiaries

Search users and marketplace browsers, for whom "EOL" names the problem and "kits" the shape; the owner's portfolio, which needed one canonical name.

## Goal, non-goal and definition of success

One canonical name and URL set, consistent launch copy, and the instruction "Do NOT 'fix' links back to Rupture" (CLM-E2-027). Not a goal: renaming marketplace identities that would lose their install base — a constraint that surfaced only in August.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-07 (truth in copy): the same hour's commits softened the mutation-testing and Stryker claims to match CI (CLM-E2-024, CLM-E2-025). Challenged by practice: the rename was never a principle, and its incompleteness (Stripe metadata `project=rupture`, ICS UIDs, the `rupture-bot` committer, the `rupture.rupture-vscode` publisher, the "Rupture AWS Deprecation Check" Action title, the local directory `active/Rupture`) is the clearest case of semantic drift in the project.

## Alternatives considered and rejected paths

At 08:16Z on 2026-06-11 an owner session (af7226841e4827114e6e6fb9cb61cb08d98fa8ef) chose the opposite — point everything at Rupture because the EOLkits links were "dead". Six minutes later "EOLkits Agent" finished the rename repo-wide and tagged v1.1.0, noting that `gh repo view ntoledo319/Rupture` now resolved to EOLkits (CLM-E2-025, CLM-E2-026). Both were correct at the moment they ran (CON-008). In August a new EOLkits VS Code publisher was considered and rejected in favour of keeping `rupture.rupture-vscode`, which already had ~100 installs (CLM-E4A-035).

## Decision and rationale

Rename the product and repository to EOLkits; keep Rupture wherever renaming would break a public identifier. The repository states only the mechanical reasons (canonical repo name, unique Marketplace action name); the naming rationale exists solely in the owner's off-repo notes. The historian infers from those notes that the new name was chosen for legibility to "senior devs" and search, not because "Rupture" had failed.

## Implementation and evidence anchors

6741fd3e494a9662f8debed0a99811d916fedc86 (2026-05-31, first six files carrying the name); 3c5b48f5f7f530456272ed83c7a13c157eca5691 (2026-06-08, README title and 71-file sweep); af7226841e4827114e6e6fb9cb61cb08d98fa8ef (08:16Z reversal); da6dc36cf4383291a329330557dc523d7495704c (08:22Z, 44 files); f3d3dea620d22ffffd5606c7623c4e18b642f195 (v1.1.0 tag, release created the same second with Sigstore signatures and SBOMs, CLM-E2-028); 8641432f899dcb045e5d918fe1b7df0057e5ed41 (`launch/REPO-RENAMED.md`). Stripe objects had been tagged `metadata.project=rupture` on 2026-05-22 and kept that tag (CLM-E2-003).

## Expected outcome

A clean identity for the launch that was still expected the following day.

## Observed outcome

The GitHub rename worked and the redirect was verified by 2026-06-22 (CLM-EXT-012). The v2.0.0 draft release of 2026-08-22 is still titled "Rupture AWS Deprecation Check v2.0.0" (CLM-E4A-027); the extension was repositioned in 2026-08-31 under the old publisher id (CLM-E4B-021); the owner's 2026-09-01 registry still names the project "Rupture" with description "EOLkits" and `canonical_status: unresolved` (CLM-EXT-028).

## Tradeoffs, debt and follow-ups

Two names for the life of the project; a local checkout path that contradicts the remote; marketplace identities frozen under the old brand. Every later agent had to learn that "Rupture" and "EOLkits" are the same thing, which is one of the reasons this history exists.

## Unresolved questions

Where and why exactly "EOLkits" was chosen (only the naming exercise survives); who "the launch automation" was on 2026-06-11; whether the owner intends to keep the Rupture marketplace identities permanently.
