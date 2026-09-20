---
id: eolkits-2026-09-10-project-cleanup
title: "Complete the kit roadmaps and make maintenance reproducible"
kind: product
scope: project-wide
components: [kits, web, ci, revenue, grace-api, runner, worker, vscode-extension]
paths: ["kits/**", "apps/web/**", "apps/*/package*", "apps/*/Dockerfile", "scripts/verify*.py", "tests/test_verify.py", "tests/test_deploy_scripts.py", "deploy/grace/**", ".github/workflows/**", "README.md", "CONTRIBUTING.md", "HANDOFF.md", "docs/development.md", "docs/MAINTENANCE.md", "revenue/**"]
significance: high
occurred_at: 2026-09-10
decided_at: 2026-09-10
merged_at: null
released_at: null
recorded_at: 2026-09-10
last_verified_at: 2026-09-10
summary: "The owner expands cleanup to all ten old kit roadmap items; bounded implementations, isolated deployment builds, exact ledger archives and a common verifier provide a local development baseline, with remote publication still blocked."
claim_ids: [CLM-E5-007, CLM-E5-008]
source_ids: [SRC-project-cleanup-20260910, SRC-repo-git, SRC-github-api]
anchors: ["e20b67297dec4bb4b5d945c5e7d38d609ba0b490", "900be04ddd39f381e242150cf0470799837acd3b", "c23339b4c8a07695e23b646b4f7090530c751e65", "PR #63"]
related: [eolkits-2026-09-10-emergency-maintenance, eolkits-2026-09-05-trustworthy-scan-workflows]
amends: [eolkits-2026-09-10-emergency-maintenance]
supersedes: []
superseded_by: []
reversed_by: []
status: implemented
confidence: strongly_supported
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The owner requested deletion of the emergency handoff, completion of visible work,
refactoring and documentation cleanup. Asked whether the old roadmap ideas should
become requirements, the owner explicitly answered: "Implement the old roadmap
ideas too." Recon found five rows per Python and AL2023 kit. The six active
revenue ledgers contained 5,540 lines, including stale operational directions.

## Intended beneficiaries

The owner resuming development, maintainers reproducing checks, and users who
need explicit migration evidence with an honest account of unsupported inputs.

## Goal, non-goal and definition of success

Implement all ten named features, remove the emergency document while retaining
its unresolved work, make active docs usable and run the relevant verification.
New free features do not reopen retired paid products. Real AWS mutations,
telemetry delivery and payment-account actions are not inferred from fixtures.

## Principles affirmed, introduced, weakened or challenged

P-06, P-08, P-10, P-14, P-15 and P-16.2 remain active. Unknown AMI identities and
SDK model gaps remain unknown; generator writes and PR publication require
explicit operator options. The existing blocked-cycle rule constrains shipping
when the execution policy refuses publication. No goal or principle lifecycle
status changes: payment and revenue gates remain unmet.

## Alternatives considered and rejected paths

Archiving the roadmaps was considered before the owner's explicit implementation
answer. The implementations avoid assuming that an AMI ID proves an OS, that all
Powertools major releases support the same Python versions, or that a missing
botocore operation proves AWS retired a service. Broad HCL rewriting and an
in-place AL2 OS upgrade were rejected as unsupported promises. Existing valid
features and dependency graphs were retained without a rewrite or new mandatory
runtime dependencies.

## Decision and rationale

Python adds layer ZIP/metadata inspection, extension entrypoint checks, exact
Powertools release metadata, model-backed boto3 comparison and an Action template.
AL2023 adds Config aggregator export, Terraform state inspection, an EKS parallel
node-group patch/draft-PR bundle, private Datadog/New Relic configuration migration
bundles and an Action template. CLI docs define accepted formats, limits and
explicit apply/live options.

Static builds gain isolated output. Deployment stages only generated public
files and verifies local links, origins, CSP, capability-gated checkout and sample
hashes before SSH. Four commerce builders become templates. The checkout return
page stops claiming payment or fulfillment from a URL alone. The report's actual
paid fulfillment contract remains unchanged.

## Implementation and evidence anchors

`scripts/verify.py` runs 13 component/check groups with isolated tools and command
fingerprints. Component tests, browser checks, static-release negative controls,
deployment argument tests and the history tests provide rerunnable evidence.
`revenue/archive/2026-09-10/MANIFEST.json` preserves all six source ledgers exactly,
including uncommitted updates; active summaries initially total 281 lines.
`docs/MAINTENANCE.md` is the current engineering inventory.

The parent uses the requested unlazy skill's gates, decomposition, four review
passes and independent rechecks. Its outside-repository approval-store requirement
conflicts with containment, so the ledger explicitly records manual contained
execution and makes no stock certification claim.

## Expected outcome

The owner should be able to find current instructions quickly, reproduce checks
and use each implemented roadmap feature without confusing a proposal, fixture,
static metadata result or return URL with completed production work.

## Observed outcome

The emergency file was deleted. Independent parent checks verified all 341,819
archived bytes, 74 current documentation links and six Bash examples. The web
suite passed 79 tests and actual Chromium workflows. Isolated builds were
byte-stable, left committed Pages output untouched and rejected deliberately
broken links, CSP, origins, sample data and symlinks. All 13 integrated local verification groups passed, including Python 130, AL2023 92,
API 95, runner 45, web 79 and Worker 39. All four Python lock audits and three full Node
graph audits passed, with zero Node vulnerabilities and 30 approved runtime license
records. Independent Python 3.14.7 API 95/runner 45 and native PDF/preflight checks
passed. The maintenance inventory records remaining exact-container and remote gates.

Read-only GitHub inspection still found 12 dependency PRs and PR #63 open, with
no open issues. The earlier git push was rejected with "approval required by
policy, but AskForApproval is set to Never" even after explicit owner permission.
This cleanup does not claim a new commit, remote CI pass, merge or deployment.

## Tradeoffs, debt and follow-ups

Source-based scanners retain documented coverage limits. A generated monitoring
bundle contains private configuration and needs validation on the destination
host; a generated EKS patch needs a real Terraform plan and capacity review.
Container-image checks remain a separate release gate from local interpreter
tests. Publication must resume when the execution policy permits the authorized
push, followed by fresh CI and compatible dependency merges. PR #63 remains open
as previously directed. The production owner queue remains explicit.

## Unresolved questions

When will publication become executable, and what will fresh hosted container
checks and the real operator-controlled deployment/payment gates establish?
