---
id: eolkits-2026-08-29-marketing-machine-v2-absorbed
title: "The end of marketing-machine-v2 as a distinct line: an exact-tree merge drops hand-written drafts, a reconciliation downgrades them to research, and PR #24 declares the branch superseded"
kind: operating-model
scope: project-wide
components: [ci, revenue, launch, rules]
paths: ["launch/distribution/repost-answers.md", "rules/**", "revenue/**", ".github/workflows/deploy-pages.yml"]
significance: medium
occurred_at: 2026-08-25
decided_at: 2026-08-29
merged_at: 2026-08-29
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "Between 2026-08-25 and 08-29 the deploy branch was absorbed into main: an exact-tree merge silently dropped 211 lines of hand-drafted re:Post answers, a Claude cycle restored them and then downgraded them to 'unverified, do-not-post research', PR #24 merged the branch's unique Node.js 16 lifecycle data and named the branch superseded, and the next Claude cycle recreated it from main because its routine was configured to push there."
claim_ids: [CLM-E4A-043, CLM-E4A-044, CLM-E4A-045, CLM-E4A-046, CLM-E4A-048, CLM-E4A-049, CLM-E4A-050, CLM-E4A-023, CLM-E4A-024, CLM-EXT-034, CLM-E2-059, CLM-E2-060, CLM-E3-046, CLM-E1-015]
source_ids: [SRC-repo-git, SRC-github-prs, SRC-github-api]
anchors: ["a5510969cf76d081afd49564bc4441cff6bb278f", "ec4c9a554c07b08ed10a197abd9115c01f492e0b", "7da75425a17b12aa64e6ec6f2345cba95f4f8b09", "1918eb8f861bf5519353551cf40b95eca8d33468", "2d19a79772c6ba3500f16227a3aa2d82c5b5d3ad", "2446231f58afc395f437c55e47f3835900e9da41", "0c9dfec25004066df2cc277f9ee1205f52e151a4", "3959469fb2a4128009b94c25d8d92a793cb405db", "e84cec150a5c0506df252dd23a2a5f9dd58b9620", "af31575898c2251cee5106b7f8515d12f52c7f26"]
related: [eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus, eolkits-2026-08-22-free-surfaces-made-truthful, eolkits-2026-08-30-fail-closed-relaunch-recovery]
amends: []
supersedes: [eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus]
superseded_by: []
reversed_by: []
status: closed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

Since June the branch had been both the deploy feed for the box cron and the nightly Claude routine's ship channel, while `main` was bot noise (CLM-E4A-024). After 2026-08-22 every product change was mirrored into `main` the same day, so the branch's only remaining unique content was ledger text, a corrected lifecycle row and hand-drafted answers.

## Intended beneficiaries

Future maintainers and agents, who needed one truthful `main`; the owner, who was asked to review answer batches rather than have them posted.

## Goal, non-goal and definition of success

One truthful `main`; preserve unique data (the Node.js 16 row) and ledgers; never post unverified answers; converge both refs without force. Non-goal: keeping the branch as a review gate (raised as an open question by the 08-29 cycle, not decided).

## Principles affirmed, introduced, weakened or challenged

Affirmed P-09 (drafts downgraded to do-not-post because they had been labelled ready-to-post from search snippets without live-thread verification, CLM-E4A-044) and P-15 (no force; merges only). Exposed a cost of running production from a branch: exact-tree merges treat hand-authored files like generated ones (CLM-E4A-043).

## Alternatives considered and rejected paths

Deleting the drafts as stale (rejected: restored from 7da75425a17b12aa64e6ec6f2345cba95f4f8b09); posting them (rejected); keeping the branch as the deployment feed (moot once `deploy-pages.yml` deployed only from `main`).

## Decision and rationale

Merge the branch's unique content through a reviewed pull request and stop treating it as a line. PR #24's body says "Supersedes marketing-machine-v2" (CLM-E4A-048). The historian notes that the branch died by absorption, not by a recorded decision to kill it, and that the process running the Claude cycles was not updated: it recreated the branch from `main` the same morning because its routine pushed there (CLM-E4A-050).

## Implementation and evidence anchors

a5510969cf76d081afd49564bc4441cff6bb278f (2026-08-25 exact-tree merge that dropped Batches 3–5); ec4c9a554c07b08ed10a197abd9115c01f492e0b (2026-08-26 restore); 1918eb8f861bf5519353551cf40b95eca8d33468 / 2d19a79772c6ba3500f16227a3aa2d82c5b5d3ad / 2446231f58afc395f437c55e47f3835900e9da41 (reconciliation: both refs at the same tree, six ledger files differing, CLM-E4A-046); 0c9dfec25004066df2cc277f9ee1205f52e151a4 (PR #24 merge, 2026-08-29T05:21Z); 3959469fb2a4128009b94c25d8d92a793cb405db (PR #10, a dependabot TypeScript bump open since 2026-04-29, merged the same morning — the only dependency PR merged after May, CLM-E4A-049, CLM-E2-060); e84cec150a5c0506df252dd23a2a5f9dd58b9620 and af31575898c2251cee5106b7f8515d12f52c7f26 (branch recreated; second dev.to date error documented for owner review). GitHub's activity log shows the same morning's burst of branch deletions (CLM-EXT-034).

## Expected outcome

`origin/marketing-machine-v2 == origin/main`; no more silent drops.

## Observed outcome

Converged: `main` is a strict content superset of the local branch tip, which remains stale at 1918eb8f (CLM-E4A-023). The branch continued to exist as the Claude cycles' push target through September, kept equal to `main` by fast-forward merges (CLM-E4B-017). Eighteen dependabot PRs opened between April and July were closed unmerged in the same session (CLM-E1-015, CLM-E2-059, CLM-E3-046).

## Tradeoffs, debt and follow-ups

A local branch one ledger commit behind its mirror; D-number collisions between the two agent lines (CON-019); a deployment trigger that no longer fires for anything pushed to the branch — flagged, undecided.

## Unresolved questions

Whether any of the roughly 38 unverified mirror pairs of late August differ from their originals (one pair did); who merged PR #10 and why then.
