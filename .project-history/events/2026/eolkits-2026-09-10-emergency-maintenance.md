---
id: eolkits-2026-09-10-emergency-maintenance
title: "Emergency maintenance: restore first-party analytics and verify dependency compatibility"
kind: incident
scope: project-wide
components: [web, grace-api, runner, worker, vscode-extension, kits, ci, revenue]
paths: [".github/**", "apps/*/requirements*", "apps/*/Dockerfile", "apps/worker/package*", "apps/vscode-extension/package*", "kits/lambda-lifeline/package*", "ATTRIBUTIONS.md", "THIRD_PARTY_LICENSES*.md", "deploy/grace/**", "revenue/**"]
significance: high
occurred_at: 2026-09-10
decided_at: 2026-09-10
merged_at: null
released_at: null
recorded_at: 2026-09-10
last_verified_at: 2026-09-10
summary: "Emergency follow-up repairs the host's first-party analytics and passes both static guards, fixes the remaining API dependency exposure, and adds runtime-specific dependency gates; remaining PR outcomes are pending at this recording."
claim_ids: [CLM-E5-006]
source_ids: [SRC-emergency-maintenance-20260910, SRC-github-api, SRC-repo-git]
anchors: ["3f6e9f5b9f56eda162867137262037213b43e078", "e20b67297dec4bb4b5d945c5e7d38d609ba0b490", "5fb6350352a29ac736aec8823e1ba53d16ec9700", "PR #63", "PR #59"]
related: [eolkits-2026-09-05-trustworthy-scan-workflows, eolkits-2026-08-25-host-injected-analytics-contained, eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: implemented
confidence: strongly_supported
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The owner requested completion of `EMERGENCYDDOTHISNOW.md`. That handoff identified host-injected cross-origin analytics breaking two daily static-site guards, sixteen dependency PRs, and unverified PR #63 checks. Fresh GitHub inspection found PR #63 still failing: the API lock retained WeasyPrint 69.0 despite the runner's 70.0 fix, and the PR body lacked its required history declaration. Missing cited objects were no longer the observed history failure.

## Intended beneficiaries

Visitors to the existing free website, maintainers relying on its operational guards, and developers using the supported scanner and extension versions.

## Goal, non-goal and definition of success

Complete the documented maintenance with verified production guards and current dependency checks, preserving the closed paid checkout and shared host services. The owner explicitly granted a one-time exception to the repository jail for reading and running `/home/nick/fix-eolkits-stats.sh` and the SSH access needed for that documented VPS repair. This exception does not authorize unrelated local access or future host work. The handoff requests confirming PR #63 green; it does not request merging its broad product changes. Maintenance code is to reach main through a separate focused PR, whose identifier remains pending at this recording. No paid-product launch or customer contact is part of this task.

## Principles affirmed, introduced, weakened or challenged

P-06, P-08 and P-16.2 remain active: preserve supported user environments, make production changes reversible, and keep payment gates closed. P-10 remains the default containment rule with one explicit, task-limited owner exception. P-14 and P-15 require an evidence-linked record and preservation of cited history; the `history/cited-objects` and `archive/*` tags remain protected. No goal or principle lifecycle status changed.

## Alternatives considered and rejected paths

Loosening the generated CSP would discard existing cross-origin script protections. The selected repair instead serves the tracker through `/_stats/` on the same origin. Dependency review rejects #32's VS Code types 1.134 because packaging requires compatibility with the declared VS Code 1.85 minimum; targeted policy excludes types >=1.86. It defers #37's TypeScript 7 because typescript-eslint 8.69 still requires TypeScript <6.1; policy excludes >=6.1. It declines #36's Node 26 types because the worker needs no new Node API surface; existing Node 20 types remain supported and policy excludes >=21. These are compatibility decisions, not unexamined major-version refusals.

## Decision and rationale

Merge independent compatible dependencies only after refreshed checks, and sequence shared lockfile or peer-dependency changes. Retain Python 3.12 coverage while testing 3.14 before accepting the image upgrades. Exercise the actual container's native PDF libraries and fail-closed API preflight. Move worker CI from Node 20 to Node 24 to satisfy Wrangler's existing Node >=22 engine requirement; this toolchain change does not require widening its declared Node API types. The worker remains retired and its deployment check is a dry run.

## Implementation and evidence anchors

PR #63 at `3f6e9f5b9f56eda162867137262037213b43e078` contains the earlier scanner improvements and runner-only security update. Actions run `34450366804`, job `102784483509`, identifies WeasyPrint 69.0 / CVE-2026-55073 in the first audited API graph. Local commit `e20b67297dec4bb4b5d945c5e7d38d609ba0b490` raises the API lock and both input minimums to WeasyPrint 70.0 and synchronizes license records. `.github/workflows/test.yml` adds Python 3.12/3.14 API and runner matrices, runtime dependency checks, network-disabled container PDF/preflight smokes, and a metrics-disabled Wrangler bundle dry run. `.github/dependabot.yml` records the supported compatibility bounds. The focused maintenance branch contains corresponding local commits `f9bdc9041e6e02048c698eef62ecd7b567a5acb8` and `190e6432dcc12b392c4742ef3365cc5a78cd449c`; these are not publication evidence. PR #59 merged at `5fb6350352a29ac736aec8823e1ba53d16ec9700`; remaining compatible dependency updates are still in progress at this recording.

## Expected outcome

The static guards should accept a first-party tracker while the CSP remains strict. Fresh CI should establish compatibility of the selected dependency updates with their actual runtimes and keep unsupported combinations out of the recurring queue.

## Observed outcome

The root operator reported repairing all 65 deployed HTML files, retaining 67 timestamped backups, and observing no further changes on rerun. Recorded probes show five EOLkits paths returning HTTP 200 with a first-party tracker, CSP present and no external scripts; `/_stats/script.js` returns HTTP 200. Both other shared-host homepages remain HTTP 200. GitHub confirms successful post-repair runs [Verify GRACE static release](https://github.com/ntoledo319/EOLkits/actions/runs/34455421385) and [Submit changed site URLs to IndexNow](https://github.com/ntoledo319/EOLkits/actions/runs/34455467762).

GitHub confirmed PR #59 merged and #32, #37 and #36 closed on September 10. Local parsing confirmed valid workflow YAML, shell blocks and embedded Python; these checks do not substitute for execution of the new CI jobs. The root operator reported automatic approval review rejecting the push while the tool policy disallowed approval escalation; explicit publication authorization was requested. The code fixes remain local, refreshed CI is pending, and no maintenance publication is claimed. PR #63 and the overall emergency list are not yet declared complete, and PR #63 is to remain open after its checks pass.

## Tradeoffs, debt and follow-ups

The repair retains timestamped backups and requires Caddy validation before graceful reload. The root operator must amend this capsule with refreshed PR CI results and final dependency dispositions. A successful analytics route is not evidence of visits or revenue. The disabled revenue loop remains disabled; history archive tags must not be removed.

## Unresolved questions

Will the refreshed Python 3.14 and dependency graphs pass their runtime tests, and which dependency PRs will land in main? Those outcomes remain pending rather than inferred from the old green builds.
