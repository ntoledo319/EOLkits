---
id: eolkits-YYYY-MM-DD-short-slug
title: One-line title of the decision arc
kind: product            # see schemas/event.schema.json for the enum
scope: project-wide      # or a component: kits, grace-api, worker, web, vscode-extension, github-action, runner, revenue, launch, ci
components: []
paths: []                # fnmatch globs, e.g. ["apps/grace-api/**", "pricing.yml"]
significance: medium     # foundational | high | medium | low
occurred_at: YYYY-MM-DD  # when the underlying project event happened (null if unknown)
decided_at: null         # when the decision was taken, if distinct
merged_at: null          # when it reached main
released_at: null        # release / deployment / publication date
recorded_at: YYYY-MM-DD  # when this capsule was written; MUST be >= occurred_at for backfills
last_verified_at: null
summary: One sentence an agent can read in `context` output.
claim_ids: [CLM-XX-000]
source_ids: [SRC-repo-git]
anchors: []              # full SHAs, "PR #n", tags, archived URLs
related: []
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: decided          # open | decided | implemented | observed | closed | reversed | superseded
confidence: plausible    # confirmed | strongly_supported | plausible | speculative | unknown
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

What the situation was and what forced the question. Keep said/did/outcome/inferred distinct.

## Intended beneficiaries

Who this was for.

## Goal, non-goal and definition of success

What success meant at the time, and what was explicitly out of scope.

## Principles affirmed, introduced, weakened or challenged

Reference doctrine ids (P-xx) where applicable.

## Alternatives considered and rejected paths

Cite evidence or state "none found in evidence".

## Decision and rationale

Mark uncertainty explicitly ("the commit message says…", "inferred from…").

## Implementation and evidence anchors

Full SHAs, paths at revision, PR numbers, release tags.

## Expected outcome

What participants said would happen.

## Observed outcome

What the evidence shows actually happened (leave empty if unknown and keep status at `decided`).

## Tradeoffs, debt and follow-ups

What this cost, what it deferred, what it obligated.

## Unresolved questions

Questions whose answers would change this record.
