# Maintenance and roadmap completion

The September 10 local cleanup is implemented and verified on
`codex/project-cleanup-20260910`. Changes remain **local and uncommitted** under
AGENTS.md's blocked-cycle rule. Publication, hosted container checks and the
operator-controlled release gates remain unfinished.

## Completed locally

- Deleted the requested emergency document and retained its remaining work here.
- Implemented all ten original kit roadmap items; see the exact scopes below.
- Consolidated six active revenue ledgers from 5,540 lines into concise summaries.
  Every original byte, including then-uncommitted updates, is preserved in
  [the checksummed archive](../revenue/archive/2026-09-10/README.md).
- Corrected setup/contribution instructions, stale operating directions, fake
  fixed-green test badges, and unsupported package/default claims. Current docs
  link to executable commands and explicit release gates.
- Extracted four commerce templates and the main stylesheet from the web builder.
  The return URL now explicitly says it does not confirm payment.
- Isolated static builds for both deployment paths. GRACE preflight checks public
  permissions, links, origins, CSP, checkout gating, symlinks and sample hashes;
  internal Markdown is excluded from release artifacts.
- Added one [verification entry point](development.md), runtime-aware reusable
  environments, interruption-safe result status, dependency fingerprints and
  regression tests. CI includes the new maintenance and release checks.
- Integrated all twelve pending dependency targets locally, preserved supported
  editor bounds and fixed additional vulnerable development dependencies.
- Updated the living history; all 277 cited SHAs resolve, with no validation errors
  or warnings. Original snapshot ref deletions remain documented advisory drift.

## All ten roadmap items

| Kit / command | Implemented scope | Evidence boundary |
|---|---|---|
| Python `layers` | Bounded ZIP paths, CPython ABI/ELF architecture, saved or explicit live layer metadata | No extraction, imports or universal compatibility claim |
| Python `extensions` | Entrypoint permissions, shebang/interpreter and native architecture evidence | Dynamic launchers and independent extension runtimes need review |
| Python `powertools` | Exact release metadata matrix and resolved dependency pins | Unknown releases/ranges stay unresolved; supports supplied PyPI metadata |
| Python `boto3` | AST calls against explicit target/baseline botocore models | Dynamic bindings get review findings; model gaps do not prove AWS retirement |
| Python `action` | Packaged workflow preview and explicit file creation | Offline vendored kit; no AWS or deployment step |
| AL2023 `config-export` | Existing Config aggregator EC2 inventory and rule evaluations, fully paginated | Read-only live opt-in; missing recorder coverage is not compliance |
| AL2023 `terraform-state` | Raw v4/show JSON v1.x, modules, provider AMI attributes and catalog evidence | Unknown/missing image identity fails strict mode; unrelated state is omitted |
| AL2023 `eks-proposal` | Applicable parallel-node-group patch and operator-invoked draft-PR script | Direct standard `.tf.json` groups only; no Terraform apply |
| AL2023 `agent-shim` | Private Datadog/New Relic configuration bundles and guarded restore scripts | Prepared AL2023 destination required; no in-place OS migration |
| AL2023 `ci-template` | Offline state gate with explicit workflow generation | No implicit credentials, cloud writes or publication |

See [Python usage](../kits/python-pivot/docs/COMPATIBILITY.md) and
[AL2023 workflows](../kits/al2023-gate/docs/ROADMAP.md) for examples, limits and
primary sources. These are free capabilities, not reopened legacy paid offers.

## Verification

`python3 scripts/verify.py all` passed all **13 local groups**. The final relevant
rechecks also pass. Evidence receipts are retained in `tmp/verify/full-run.json`
and `tmp/verify/last-run.json`; review coordination is in `.unlazy/squeaky-clean/`.

- Python Pivot: **130 tests**; AL2023 Gate: **92 tests**.
- API: **95 tests**; report runner: **45 tests** and committed sample verification.
- Web: **79 tests**, deterministic isolated builds and actual Chromium workflows.
- Worker: **39 tests**, TypeScript build and Wrangler dry-run bundle.
- Node kit, editor compile/lint/scanner/lifecycle/VSIX, Action fixtures and
  acquisition-evidence checks passed.
- Python lint/format/type checks, **13** verification/deployment regression tests,
  **22** history tests and workflow syntax checks passed.
- All four Python lockfile audits and all three full Node graph audits passed;
  Node graphs report **zero vulnerabilities**, including development dependencies.
  All **30** Node runtime license records passed.
- Independent parent execution under actual **Python 3.14.7** passed the same
  API 95/runner 45 suites, sample check, native PDF imports/rendering and closed
  preflight. Sharp 0.35.4 passed native AVIF decoding and PNG resizing.
- Changed-file secret review has no unresolved finding; one existing literal
  synthetic Compose-test placeholder was classified explicitly.

Local interpreter tests do not establish an exact Docker image build, real cloud
migration, vendor telemetry delivery or paid fulfillment. The API test client
emits one upstream deprecation warning; its tests pass. Kit Python 3.9 syntax was
checked, but this pass did not execute a Python 3.9 test matrix.

## Remaining external work

| Work | Current evidence / next step |
|---|---|
| First-party analytics repair | Complete: 65 HTML files repaired with 67 backups; browser tracker script/event 200; [static guard](https://github.com/ntoledo319/EOLkits/actions/runs/34455421385) and [IndexNow](https://github.com/ntoledo319/EOLkits/actions/runs/34455467762) succeeded. |
| Focused maintenance publication | Existing local branch `codex/emergency-maintenance-20260910`, commit `190e6432`. Publication requires the execution-policy block below to be removed, then fresh CI and the authorized verified merge. |
| Dependency PRs | #59 merged; #32/#36/#37 closed for compatibility. #31/#33/#39/#40/#45/#46/#47/#48/#49/#60/#61/#62 remain open. Their targets are locally integrated; refresh CI before merging or superseding them publicly. Merge types before Wrangler and parser before plugin; serialize shared locks. |
| PR #63 verification | Last remote failures: history declaration and dependency audit. Description/local fixes exist, but refreshed remote CI is pending. Keep this broad PR open as previously directed. |
| Exact container images | Both Dockerfiles pin the reviewed Python 3.14.7 tag/digest. The exact native container build/smokes require hosted CI; local 3.14 evidence is separate. |
| Cleanup publication | Review the current branch's complete working-tree diff, then commit/publish when policy permits. No cleanup deployment or main merge is claimed. |
| Operational prerequisites | Private configuration, seller/account facts, closed rollout, real payment/email/refund/retention proof, Marketplace attestations and author-controlled DEV cleanup remain in the [owner queue](../revenue/HUMAN_QUEUE.md). Checkout is no longer closed: it opened live on 2026-09-20 with these prerequisites still outstanding. |

The exact rejected action was `git push -u origin codex/emergency-maintenance-20260910`.
Automatic approval review returned:
`approval required by policy, but AskForApproval is set to Never`.
The owner explicitly authorized push and verified merge; the subsequent rejection
persisted. Another verbal approval or alternate transport does not resolve that
control. Resume publication when the command policy permits it. No new cleanup
commit was created while this condition remained in force.

## Inventory disposition

The final source scan found no remaining implementation TODO/FIXME/TBD markers or
skipped/stubbed tests in active source. The two old roadmap lists are fully
implemented. Operator runbook checklists intentionally await their real execution;
archived launch/revenue plans preserve historical proposals and are not reopened
requirements. GitHub inspection found **zero open issues** and the thirteen open
PRs listed above. Retired Stripe credential rotation/revocation remains explicitly
excluded by the owner, not represented as completed.

Unlazy root acceptance: **6 of 7 gates met; publication/remote-CI gate blocked**.
The skill's outside-repository approval store conflicts with containment, so the
record uses inspected commands, fingerprints and independent parent checks; it
makes no stock certification claim.
