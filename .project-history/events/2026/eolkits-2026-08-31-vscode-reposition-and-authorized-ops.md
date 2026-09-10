---
id: eolkits-2026-08-31-vscode-reposition-and-authorized-ops
title: "The one permitted reposition: VS extension v1.2.0 as 'AWS Lambda EOL Scanner', a legal operator named, and an owner-authorised one-use platform-operations run that could not do the admin work"
kind: product
scope: vscode-extension
components: [vscode-extension, legal, ci]
paths: ["apps/vscode-extension/**", "legal/**", ".github/workflows/publish-vscode.yml", ".github/workflows/authorized-platform-ops.yml", ".github/workflows/acquisition-evidence.yml"]
significance: high
occurred_at: 2026-08-31
decided_at: 2026-08-31
merged_at: 2026-08-31
released_at: 2026-08-31
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "After the v1.1.0 five-day gate returned failed_reposition_required (103 installs, zero growth), the operating document's single allowed reposition was spent on renaming and re-keywording the extension around the exact Lambda runtime-upgrade job; legal pages named Toledo Technologies LLC as operator; and an explicit owner instruction to execute every queued platform operation except a Stripe key rotation produced a one-use workflow that published v1.2.0 but found no DEV key and no admin-scope token."
claim_ids: [CLM-E4B-020, CLM-E4B-021, CLM-E4B-022, CLM-E4B-023, CLM-E4B-024, CLM-E4B-025, CLM-E4B-026, CLM-E4B-041, CLM-E4B-064, CLM-E4B-066, CLM-E4B-070, CLM-EXT-038]
source_ids: [SRC-repo-git, SRC-github-prs, SRC-github-api]
anchors: ["1356051cdbd8c2a93f64e6926bf0770629e7e689", "8a394c7942f3d1e603dd5836b9ab99a0bf75aa57", "0290f490cf62f185121991580a05c21e779eee2a", "23762f3f7a8e7ccc61b76c7fef4a00d1fa7fec99", "1f48d4fe354f369899548caf2e81b34d739a62bd", "130f316e5e25e2afc014a507d9997f48c7dd0ff1", "5cce3bb909689bbed8f0752312d0a84fbe4c89f7", "88b3249952e09f5f612e44bd58e343ebae7ba9b4", "92ffddbf04fc050fdf52760b84e628bd3a710a68", "a297ea4a18c535a27b6bcad1c4a40d4ed08b974e"]
related: [eolkits-2026-08-22-free-surfaces-made-truthful, eolkits-2026-08-30-fail-closed-relaunch-recovery, eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening, eolkits-2026-06-20-portfolio-verdicts-dead-market-and-shelving]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: observed
confidence: strongly_supported
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The gate PR #25 had built evaluated at 2026-08-30T11:15Z: 103 installs, 0 growth, 0 qualified authors → `failed_reposition_required` (CLM-E4B-020). AGENTS.md §8 permits exactly one reposition after five live days with zero signal; the extension still carried its May-era name and a dead `/Rupture/audit` link. Legal pages said only "based in Connecticut". Twenty-five DEV posts with known date errors were still public and the Pages source and branch protection were owner-only settings.

## Intended beneficiaries

Developers searching the VS Code Marketplace for the job they actually have — upgrading a Lambda runtime — rather than for a brand; readers of the legal pages, who are owed an operator's name.

## Goal, non-goal and definition of success

Reposition "around the exact AWS Lambda runtime-upgrade job": new display name, keywords (nodejs20, nodejs18, python3.9, aws sdk v2, sam), a first-scan path — not a new SKU or a higher price (D53; CLM-E4B-064 records the later reaffirmation). For the operations run: publish 1.2.0, unpublish the DEV posts, switch Pages to workflow builds, create a protective ruleset — "only if a recognised secret authenticates; print no values" (CLM-E4B-023). Non-goal, by owner direction: rotating the retired Stripe credential (CLM-E4B-026).

## Principles affirmed, introduced, weakened or challenged

Affirmed the "one reposition then replace" rule literally (later not re-spent on v1.3.0, D64) and P-04: "Do not bypass those boundaries, scrape browser sessions, exploit the host, or reinterpret broad authorization" (D54). Affirmed P-13 in a qualified way: naming an LLC operator is not a founder persona. Reused the one-use push authorisation pattern (P-15's audited-transport corollary).

## Alternatives considered and rejected paths

A new SKU or price rise (rejected: the gate is "not evidence for a higher price or another product"); a new publisher id (rejected again; the identity `rupture.rupture-vscode` is fixed, CLM-E4B-021); waiting for the owner to dispatch (rejected as human budget).

## Decision and rationale

Spend the reposition on the free surface and use the owner's explicit instruction as the authority for a bounded, self-removing workflow. The ledger's rationale: "free surface shipped, paid surface stays closed" (D55). The historian notes that the run's inability to change admin settings on 08-31 was contradicted four days later (CON-021), which means the boundary the agents respected on this day was a property of the token they held, not of the account.

## Implementation and evidence anchors

PR #28 (1356051cdbd8c2a93f64e6926bf0770629e7e689 with a mis-built docs tree for a non-canonical Pages environment, repaired by 8a394c7942f3d1e603dd5836b9ab99a0bf75aa57, CLM-E4B-022; local 0290f490cf62f185121991580a05c21e779eee2a; merged 23762f3f7a8e7ccc61b76c7fef4a00d1fa7fec99 at 23:14Z); PR #29 (1f48d4fe354f369899548caf2e81b34d739a62bd / 130f316e5e25e2afc014a507d9997f48c7dd0ff1, merged 5cce3bb909689bbed8f0752312d0a84fbe4c89f7 at 23:23Z: a 269-line `authorized-platform-ops.yml` gated on `before == 23762f3f…` plus the publish trigger); runs 33450455161 and 33450455146 completed successfully as push events (CLM-E4B-024); PR #30 (88b3249952e09f5f612e44bd58e343ebae7ba9b4 / 92ffddbf04fc050fdf52760b84e628bd3a710a68, merged a297ea4a18c535a27b6bcad1c4a40d4ed08b974e at 23:38Z) removed the workflow and trigger and reset the gate to 2026-09-05T23:27:55Z (CLM-E4B-025).

## Expected outcome

v1.2.0 public; DEV posts gone; Pages and ruleset set; a fresh five-day install series.

## Observed outcome

Publication reported successful (Marketplace not queried by this audit); DEV: no key, so the 25 posts stayed public with "seven reactions and zero comments" (CLM-E4B-066); Pages and ruleset: not changed, "token lacked admin" — done on 2026-09-04 by other means (CLM-E4B-041). The Marketplace Action listing still showed v1.1.0 (CLM-E4B-070). The legal entity question from June (CLM-EXT-038) is answered on the page, not in a record of formation.

## Tradeoffs, debt and follow-ups

The reposition is spent: the policy's next step on a failed gate is replacement. Contra, Fiverr and Upwork were re-listed as rejected and RapidAPI queued as a possible Bet C (CLM-E4B-064). Whether v1.2.0 and later v1.3.0 are actually live is reported, not verified.

## Unresolved questions

Whether the Marketplace shows 1.2.0/1.3.0; whether the DEV posts will ever be unpublished; how the owner's instruction was transmitted (no transcript in the repository).
