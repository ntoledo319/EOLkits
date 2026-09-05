---
id: eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening
title: "September 4: a five-sample evidence gate, v1.3.0, the reversal of daily date churn, admin authority found after all, and a closed deployment hardened for an owner who has not deployed it"
kind: release
scope: project-wide
components: [vscode-extension, github-action, kits, grace-api, runner, deploy, ci, legal, web]
paths: ["scripts/vscode-gallery-evidence.mjs", ".github/workflows/**", "apps/vscode-extension/**", "kits/lambda-lifeline/**", "apps/web/build.py", "apps/grace-api/**", "apps/runner/**", "deploy/grace/**", "legal/**", "tests/test_runtime_parity.py"]
significance: high
occurred_at: 2026-09-04
decided_at: 2026-09-04
merged_at: 2026-09-04
released_at: 2026-09-04
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "In one morning the Codex line 'falsified' the prior conclusion that nothing autonomous remained: it added a conservative five-sample Gallery evidence gate, shipped VS Code v1.3.0 with Node 16 / Python 3.8 rules and a cross-implementation lifecycle parity test, reverted the Claude line's daily BUILD_DATE bumps as false publication churn, repaired CI after npm retired an endpoint mid-PR, set the branch ruleset and Pages source with owner-scope authority it had believed absent, and hardened the closed API deployment with a guarded script — none of which opened checkout or produced a dollar."
claim_ids: [CLM-E4B-019, CLM-E4B-029, CLM-E4B-030, CLM-E4B-031, CLM-E4B-032, CLM-E4B-033, CLM-E4B-034, CLM-E4B-035, CLM-E4B-036, CLM-E4B-037, CLM-E4B-038, CLM-E4B-039, CLM-E4B-040, CLM-E4B-041, CLM-E4B-042, CLM-E4B-043, CLM-E4B-044, CLM-E4B-045, CLM-E4B-046, CLM-E4B-047, CLM-E4B-048, CLM-E4B-062, CLM-E4B-063, CLM-E4B-067, CLM-E4B-068, CLM-E4B-069, CLM-E4B-070]
source_ids: [SRC-repo-git, SRC-github-prs, SRC-github-api]
anchors: ["15861960c058e98e949a0391a00af55057814f07", "82da25ddce03ceba925e5dc8e2676846d2675076", "5106d80859c4072a240b43de8a15ebcf1628fcd1", "44e0425f3b94b085835c85a2e0dbf28642914973", "5c6acf6eae77d097f72f509ac33117ef42ba45ba", "b72c58e2ab14dc2c23e87aa752062e34bbde7bce", "c9727fae1730f6bf601971685e4831c6d9cf659e", "4f51c770ebe7d9b8b6d8fbd3429727f7a5e83271", "250ad3df46c1594324750f7be7208e2aea73fe31", "5bbf5a949148cd9f359d07aad03f649358c37e8c", "18f8b608a33032f4604cfe375271c82a54c307eb", "182a8474a93b1abc4b63ee451dde614bde08862e"]
related: [eolkits-2026-08-30-fail-closed-relaunch-recovery, eolkits-2026-08-31-vscode-reposition-and-authorized-ops, eolkits-2026-07-13-node20-date-truth-sweeps, eolkits-2026-05-31-deterministic-deprecation-seo, eolkits-2026-09-04-jail-violations-and-env-recovery-scan]
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

The Claude line's plan of Sep 2/4 said "nothing left but owner work" (CON-023). The Gallery install counter flickered between 103 and 104 on near-simultaneous reads, so a single read could pass or fail the gate at random (CLM-E4B-033). The VS rules lacked Node 16 and Python 3.8; lambda-lifeline had already needed python3.8 (2026-08-31) and python3.11 (2026-09-01) rows to stop reporting real functions healthy (CLM-E4B-019). The Claude cycles had bumped `BUILD_DATE` four times, rewriting every sitemap lastmod. The audit-page tracker was not loading. The runner accepted local paths over HTTP.

## Intended beneficiaries

Users of the free scanners, who get fewer false negatives; the owner, whose queue shrank to a handful of minutes with scripts behind each; the record itself, which gets a conservative lower-bound evidence method.

## Goal, non-goal and definition of success

Conservative evidence (five samples, lowest value), a correctness release that does not reset the reposition gate, the publisher used exactly once and closed, CI green with real container builds, "fix those defects before money". Non-goals: resetting the baseline (rejected, D64); a GHCR registry pipeline ("registry theater", D67); keyword-only releases, sponsor-link advertising, a duplicate hosted site (D74).

## Principles affirmed, introduced, weakened or challenged

Affirmed P-05.2 (evidence gates), P-03.2 (two-source bar; parity test across YAML, Node and Python, CLM-E4B-034), P-18 (dates describe content, not build activity — `PAGE_LASTMOD_OVERRIDES`, CLM-E4B-035), P-06 (runner rejects client-supplied upload paths; digest-pinned, non-root, read-only containers; secrets ≥ 32 bytes, CLM-E4B-042) and P-16.2 (`deploy-api-closed.sh` requires a 40-hex SHA, a non-root user, a clean checkout and a 0600 env file, and never opens checkout or edits Caddy, CLM-E4B-043). Challenged: the Aug 31 authority conclusion (D54) — D70 found owner-scope `gh` authority and spent it on the ruleset and Pages (CLM-E4B-040, CLM-E4B-041; CON-021).

## Alternatives considered and rejected paths

Waiting on evidence defects before fixing scanner bugs (rejected, D60); resetting the gate for v1.3.0 (rejected, D64); a registry (rejected, D67); leaving the admin settings to the owner (rejected once authority was found: "spend authenticated repository-admin authority, not owner minutes").

## Decision and rationale

Ship the free-surface correctness release, harden the closed deployment, and take the admin actions. The stated rationale is the plan's falsification of "nothing left". The historian notes that the two lines were applying the same evidence hierarchy and disagreeing about whether free-surface work is progress; under "dollars first", the stricter reading is the Claude line's (CON-023).

## Implementation and evidence anchors

15861960c058e98e949a0391a00af55057814f07 and 82da25ddce03ceba925e5dc8e2676846d2675076 (scanner rows, Claude line); PR #41 5106d80859c4072a240b43de8a15ebcf1628fcd1 → 44e0425f3b94b085835c85a2e0dbf28642914973 (09:56Z: `scripts/vscode-gallery-evidence.mjs`, v1.3.0, `runtimeLifecycle`, parity test, BUILD_DATE reversal, CLM-E4B-031); PR #42 5c6acf6eae77d097f72f509ac33117ef42ba45ba → b72c58e2ab14dc2c23e87aa752062e34bbde7bce (10:37Z: one-use trigger accepting only `before == 44e0425f…`; CI repaired after npm's quick-audit endpoint returned 400 then 503, CLM-E4B-037); PR #43 c9727fae1730f6bf601971685e4831c6d9cf659e → squash 4f51c770ebe7d9b8b6d8fbd3429727f7a5e83271 (11:00Z: trigger removed; its remote head is not present locally, CLM-E4B-030); ruleset 22266277 and Pages `build_type=workflow` at 11:15Z (verified via the API); PR #44 250ad3df46c1594324750f7be7208e2aea73fe31 → 5bbf5a949148cd9f359d07aad03f649358c37e8c (12:00Z: deployment hardening, Connecticut governing law and a registry-sourced business address, CLM-E4B-044); PR #50 18f8b608a33032f4604cfe375271c82a54c307eb (dependabot ecosystem fix, CLM-E4B-046); PR #55 182a8474a93b1abc4b63ee451dde614bde08862e (ledger-only handoff evidence, CLM-E4B-048). From PR #44 the local and remote commits are the same objects — the publishing transport switched to direct push (CLM-E4B-029).

## Expected outcome

A +1 install signal at best; a queue the owner can clear in about forty minutes; v1.3.0 live.

## Observed outcome

Reported: five consistent samples at 104 installs / 226 downloads, gate `passed` on +1 against a counter that flickers by 1 (CLM-E4B-039; CON-024); 20 PR contexts green including container builds; the owner queue 42 → 38 minutes. Not verified by this audit: Marketplace state. Not changed: purchases 0, checkout closed, GRACE undeployed, the Day-14 gate not yet due (CLM-E4B-063). Sixteen dependabot PRs sit open (CLM-E4B-047); a workflow registered on GitHub exists in no local ref (CLM-E4B-068).

## Tradeoffs, debt and follow-ups

`--no-audit` sprinkled across installs with a single dedicated audit job as the only vulnerability gate; a Claude line whose next cycle will conflict with the BUILD_DATE policy unless its (untracked) instructions change; the legal address now public; the reposition gate's next reading on 2026-09-05.

## Unresolved questions

How owner-scope `gh` authority reached the jailed workspace (no commit records it); whether the Marketplace shows 1.3.0; what the 2026-09-05 gate emits.
