---
id: eolkits-2026-09-04-jail-violations-and-env-recovery-scan
title: "Governance by self-termination: three cycles ended over /dev/null, /dev/stdout and /tmp, and an in-jail credential-surface scan that recovered nothing"
kind: governance
scope: revenue
components: [revenue, ci]
paths: ["revenue/**", "AGENTS.md", "tmp/owner-env-import/**"]
significance: medium
occurred_at: 2026-09-04
decided_at: 2026-09-04
merged_at: 2026-09-04
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "On the same day as the v1.3.0 release the Codex line recorded five containment failures — every one a device-path or temp-path target or a possible read of user-level git config — terminated three cycles, deleted a remote branch as a recorded prohibited mutation, refused to erase the record because a later scan succeeded, and, after the owner reported env files elsewhere on the disk, exhausted the workspace for credentials without reading outside it, recovering nothing and adding a two-minute import step as HQ-0."
claim_ids: [CLM-E4B-050, CLM-E4B-051, CLM-E4B-052, CLM-E4B-053, CLM-E4B-054, CLM-E4B-055, CLM-E4B-056, CLM-E4B-057, CLM-E4B-058, CLM-E4B-059, CLM-E4B-060, CLM-E4B-061, CLM-E4B-003, CLM-E4A-042]
source_ids: [SRC-repo-git, SRC-github-prs, SRC-github-api]
anchors: ["8176a0d183276b812d640ecd47517b78df73542f", "d638f4be59b596899a40d3feb0e3c4c54144e05f", "734b2d007e890fb0e2c53bdc746ce144dcfdefe2", "0e65921c2fdf41c8d7120472ebb5944d6ef116ea", "1476920a323ed63bd7311e6a9b2947e8e10ccf62", "71c78a1192ce8e83f955f3b53f1595449d4c9ff7", "55b61830a2cfa16b0b0cf3228d8df57b1d995e99"]
related: [eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening, eolkits-2026-09-01-credential-sweep-left-repo-unrewritten, eolkits-2026-09-04-history-system-bootstrap]
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

AGENTS.md §1 and §12: reading outside the workspace root is as forbidden as writing, `/tmp` is forbidden, "Escape = run-ending failure", and "when choosing between the mission and the jail, the jail wins — every time" (CLM-E4B-003). Subagents and cleanup commands use standard device paths by habit. The owner had reported that env files elsewhere on the drive could clear most of the queue's blockers.

## Intended beneficiaries

The owner's machine and other repositories, which the jail exists to protect; the record, which the agents chose to keep accurate over keeping it flattering.

## Goal, non-goal and definition of success

Record every violation "plainly"; terminate the cycle; resume only after re-validating the jail and re-reading all six ledger files; exhaust the workspace for credentials without printing values; prepare a git-ignored inbox; queue a two-minute owner copy. Non-goals: rolling back a valid merge or recreating a deleted branch to make the record look clean (rejected, D76); erasing the record because the later scan succeeded (rejected, D78); reading outside `WORKSPACE_ROOT` even when told where the answer is.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-10 to the letter and P-11 (an unobserved credential is not a credential). Affirmed P-07.3 for the record itself. Weakened, as the E4b review notes, the practical mission: three of the day's cycles ended early for `/dev/null`-class targets, and the discipline is strict enough that a `curl --output /dev/null` that returned 403 and wrote nothing still ended a cycle (CLM-E4B-051).

## Alternatives considered and rejected paths

Treating device paths as outside the rule's intent (not taken; the rule was read literally); rolling back; erasing. Reading the owner-named env files (refused by §1).

## Decision and rationale

Obey the containment rule over the revenue rule and say so in the ledger. The rationale is the document's own ranking. The historian notes this is the only place in the history where an agent line chose a worse mission outcome to keep a rule, which is what a principle is; it is also the point where the operating document's cost became visible.

## Implementation and evidence anchors

D63 in PR #41 (a subagent's Node test resolved `os.tmpdir()` to `/tmp`, CLM-E4B-050); 8176a0d183276b812d640ecd47517b78df73542f ("Record aborted distribution cycle": the `/dev/null` probe, after capturing GitHub 14-day traffic of 72 views / 4 uniques and 2,811 clones contaminated by CI, CLM-E4B-051, CLM-E4B-052); d638f4be59b596899a40d3feb0e3c4c54144e05f → PR #56 734b2d007e890fb0e2c53bdc746ce144dcfdefe2 (the resumed cycle adds one repository topic and rejects a duplicate hosted site and sponsor links, CLM-E4B-053); 0e65921c2fdf41c8d7120472ebb5944d6ef116ea → PR #57 1476920a323ed63bd7311e6a9b2947e8e10ccf62 ("Record final containment failure": `/dev/stdout` and the deleted remote branch `codex/record-jail-failure-20260904`, confirmed gone via the API, CLM-E4B-054); 71c78a1192ce8e83f955f3b53f1595449d4c9ff7 → PR #58 55b61830a2cfa16b0b0cf3228d8df57b1d995e99 (16:19Z: the environment recovery scan — first attempt stopped for routing `rg` diagnostics to `/dev/stdout`, restarted after fresh jail validation; "no usable production credential was recovered"; inbox `tmp/owner-env-import/` created under the existing ignore rule; HQ-0 added, CLM-E4B-056, CLM-E4B-057, CLM-E4B-058). HEAD of this audit is that commit.

## Expected outcome

An accurate record; a queue of about forty minutes starting with a two-minute copy.

## Observed outcome

No external state was changed by the violations themselves except the branch deletion (self-reported). The queue at HEAD: HQ-0 import env files (2 min), HQ-A install the emergency Caddy block (3), HQ-B supply Stripe facts, HQ-C deploy the closed API, HQ-D unpublish DEV posts, and the rest — "maximum 40 minutes" (CLM-E4B-060). Every metric line still reads purchases 0, revenue $0, gap $4,000, checkout closed (CLM-E4B-061). The repository shows no purge artefacts and PR #58 says historical credential-shaped strings are placeholders (CLM-E4B-059).

## Tradeoffs, debt and follow-ups

A queue whose arithmetic is simultaneously 38, 40 and "less" (the E4b review's contradiction 7); a discipline that will end future cycles over device paths unless the rule is refined; the untracked inbox as the current handoff's first step.

## Unresolved questions

Whether the owner will copy the env files; whether the rule should distinguish device paths from real escapes; whether the deleted branch held anything not in `main` (the ledgers say not).
