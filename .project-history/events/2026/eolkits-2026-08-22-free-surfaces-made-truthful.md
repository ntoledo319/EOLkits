---
id: eolkits-2026-08-22-free-surfaces-made-truthful
title: "Free surfaces first: the v2 branch, a private Marketplace draft, Pages as the canonical host, a real sample report, and the extension that was public all along"
kind: interface
scope: project-wide
components: [github-action, vscode-extension, web, ci, docs]
paths: ["action.yml", "apps/github-action/**", "apps/vscode-extension/**", ".github/workflows/deploy-pages.yml", ".github/workflows/prepare-marketplace-v2.yml", ".github/workflows/publish-vscode.yml", ".github/workflows/acquisition-evidence.yml", ".github/ISSUE_TEMPLATE/**", "docs/sample/**"]
significance: high
occurred_at: 2026-08-22
decided_at: 2026-08-22
merged_at: 2026-08-22
released_at: 2026-08-25
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "The same day as the rebuild, a chain of thirteen decisions published main without a repository credential, fixed a GitHub Pages race, created the public v2 branch and a private v2.0.0 draft, re-pointed every acquisition link to the Pages host, replaced the mock sample with a PDF from the production path, moved demand measurement to a GitHub issue form, and discovered the VS Code extension had been public since May under the Rupture publisher with ~100 installs — then stopped at 'the third consecutive goal turn ending on the same owner-authority boundary'."
claim_ids: [CLM-E4A-022, CLM-E4A-025, CLM-E4A-026, CLM-E4A-027, CLM-E4A-028, CLM-E4A-029, CLM-E4A-032, CLM-E4A-033, CLM-E4A-034, CLM-E4A-035, CLM-E4A-036, CLM-E4A-037, CLM-E4A-052, CLM-E4A-053, CLM-E1-039, CLM-E1-047, CLM-EXT-020, CLM-EXT-027]
source_ids: [SRC-repo-git, SRC-github-releases, SRC-github-api]
anchors: ["07c73a49b3f5caa9f8255086080cb520af8c040e", "f4ef711e022ce032a31d15f2fb0ab845b2225e91", "ede2bc60e62d73c9e6c9485c6aeed2b5b2b93384", "9d369ccbb516f5578665f3edfaae618c1a88b111", "ef2a0aff1f28feb04c90a7baf938d5e7e07c7ac5", "c311215121fe3a76241632500154ac457d964eab", "dcdd388b3c5a60b6786806f7c90b61d59e8df9d0", "ef4e22ebb4c0bfbe48386c6fcdad827332d08aeb", "1b7e415ba72d453a423b02098a770288d9a257e9", "762e2338a6165e653a5ad0fe5ccabeb03d504a02", "eee6a91a85f0fac33fb4eec55f9a67f37cb9be24", "8c482156d104b9a279447c53b0261dc7e8b2c8ed", "13b7cb4dd26c44b8b219887f669765d7254b6c72"]
related: [eolkits-2026-08-22-truthful-evidence-report-rebuild, eolkits-2026-05-02-v1-signed-release-and-marketplace, eolkits-2026-06-11-rupture-renamed-eolkits, eolkits-2026-07-15-repost-answers-only-demand-test, eolkits-2026-08-31-vscode-reposition-and-authorized-ops]
amends: [eolkits-2026-05-02-v1-signed-release-and-marketplace]
supersedes: [eolkits-2026-07-15-repost-answers-only-demand-test]
superseded_by: []
reversed_by: []
status: observed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The rebuilt README documented `uses: ntoledo319/EOLkits@v2` before any `v2` ref existed (CLM-E4A-026); the Marketplace listing was stale at v1.1.0; the custom domain still served retired products; the public sample was a mock; the extension was believed unpublished because it had been searched for under the new name (CLM-E4A-035). The jailed shell had no GitHub credential and force pushes were forbidden, so `main` could only be advanced by publishing identical trees through the connected GitHub app (CLM-E4A-022).

## Intended beneficiaries

Anyone installing the free Action or extension — the surfaces that carry the project's reputation and, under P-17, its only permitted acquisition path; the owner, who was to be left with one Marketplace checkbox.

## Goal, non-goal and definition of success

Make every free distribution surface truthful and installable "without impersonating the owner", and measure demand honestly. Non-goals: a new EOLkits VS Code publisher (rejected, D28); beacons on a stale backend (rejected, D23); publishing the Marketplace release, which requires the owner's agreement click. Success: both Pages mechanisms publishing identical bytes; a real sample; a v2 ref; zero false claims.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-17 (free tools are distribution), P-15 (advance refs with force=false; the "ours" merge pattern reused to feed the box cron, CLM-E4A-029), P-05.2 (an issue form counted by a read-only workflow as the only demand signal; IndexNow recorded "as receipt, never as demand", CLM-E4A-032, CLM-E4A-033). Amended the May release event: the extension publication that May's ledger had "reported" was real, under `rupture.rupture-vscode` v1.0.0 (CLM-E1-039 → CLM-E4A-035).

## Alternatives considered and rejected paths

D30 lists the alternatives re-checked at the owner-authority blocker: the prepared Audit checkout, both existing marketplaces, historical Stripe links, alternate free hosting, another digital marketplace, direct service or licensing — all rejected or owner-gated (CLM-E4A-037).

## Decision and rationale

Ship what needs no owner authority, in an order that leaves one click. The rationale is D19's: the custom domain could not be trusted yet, so Pages became canonical for every link (CLM-E4A-028). The historian notes that the object-API publishing transport was a workaround for the jail, not a preference, and that it duplicated every local commit as a mirror on `main` one to three minutes later.

## Implementation and evidence anchors

07c73a49b3f5caa9f8255086080cb520af8c040e / f4ef711e022ce032a31d15f2fb0ab845b2225e91 (Pages race: committed `docs/` becomes the `/EOLkits` artefact, root-domain variant generated by the GRACE ship script, CLM-E4A-025); ede2bc60e62d73c9e6c9485c6aeed2b5b2b93384 and 9d369ccbb516f5578665f3edfaae618c1a88b111 (public `v2` branch and the path-triggered draft workflow; the draft "Rupture AWS Deprecation Check v2.0.0" created 23:13Z by github-actions, CLM-E4A-027); ef2a0aff1f28feb04c90a7baf938d5e7e07c7ac5 (links re-pointed); c311215121fe3a76241632500154ac457d964eab (feeding the box cron); dcdd388b3c5a60b6786806f7c90b61d59e8df9d0 ("[Audit interest]" issue form and daily counter); ef4e22ebb4c0bfbe48386c6fcdad827332d08aeb (51 URLs to IndexNow); 1b7e415ba72d453a423b02098a770288d9a257e9 and 762e2338a6165e653a5ad0fe5ccabeb03d504a02 (real sample PDF via `generate_audit_package()`, which exposed a false critical finding in the engine, CLM-E4A-034); eee6a91a85f0fac33fb4eec55f9a67f37cb9be24 (extension identity recovered); 8c482156d104b9a279447c53b0261dc7e8b2c8ed (publish workflow locked to the owner as actor with typed confirmation) and 13b7cb4dd26c44b8b219887f669765d7254b6c72 (D30).

## Expected outcome

Installs of a truthful v2 Action and extension; qualified "[Audit interest]" issues as the first demand signal; a Marketplace v2 once the owner clicks.

## Observed outcome

By 2026-08-29: v2 branch and draft exist, 51 URLs submitted, sample real, VS extension candidate green; $0, 0 qualified issues, 1 star, 103 installs (+0), GitHub Marketplace still v1.1.0, v2.0.0 still a private draft (CLM-E4A-052). The Bet A and V1 falsifiers reached their "reposition once" thresholds by 08-29 (CLM-E4A-053). The draft is still unpublished at HEAD, and the public description now reads "Optional $299 repository evidence report is capability-gated" (CLM-EXT-027).

## Tradeoffs, debt and follow-ups

Mirror commits doubled the human history of late August; the draft's URL slug regenerates on every resync; the owner-only Marketplace checkbox remains the boundary every later cycle ends on. The false critical finding in the sample generation was a real engine bug found by dogfooding the production path.

## Unresolved questions

Whether the Marketplace v2 will ever be published; why the extension listing was not rediscovered earlier; whether any external Action run ever occurred.
