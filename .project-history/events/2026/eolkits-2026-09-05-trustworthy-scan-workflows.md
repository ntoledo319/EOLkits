---
id: eolkits-2026-09-05-trustworthy-scan-workflows
title: "Make scan coverage, recovery and local migration edits trustworthy across the product"
kind: product
scope: project-wide
components: [web, vscode-extension, kits, grace-api, runner, ci]
paths: ["apps/web/**", "docs/scan/**", "apps/vscode-extension/**", "kits/lambda-lifeline/**", "kits/python-pivot/**", "apps/grace-api/**", "apps/runner/**", ".github/workflows/test.yml", "README.md", "revenue/**"]
significance: high
occurred_at: 2026-09-05
decided_at: 2026-09-05
merged_at: null
released_at: null
recorded_at: 2026-09-05
last_verified_at: 2026-09-05
summary: "Local product improvements make browser and editor coverage visible, correct supported CLI manifest processing and unsafe runtime rewrites, and reject malformed paid-report input before checkout; deployment and commercial gates remain separate."
claim_ids: [CLM-E5-001, CLM-E5-002, CLM-E5-003, CLM-E5-004]
source_ids: [SRC-product-improvement-20260905]
anchors: ["24c2debcce3782667c17c567742b45216881766a"]
related: [eolkits-2026-08-22-free-surfaces-made-truthful, eolkits-2026-08-22-truthful-evidence-report-rebuild, eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: implemented
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The owner requested a whole-product improvement grounded in running the existing software. The agent reconstructed EOLkits as free AWS migration scanners plus a bounded optional evidence PDF. Reproductions found a browser read failure that could end in a no-findings state, disconnected editor scan state, Python manifests missed by quote-based extraction, unrelated runtime settings eligible for rewriting, an automatic rollback fallback that could select a newer version, and malformed package JSON accepted by paid preflight. Existing regression suites had passed despite these gaps.

## Intended beneficiaries

Developers checking a repository before an AWS runtime migration, especially those deciding which findings to review, whether a scan covered their input, and whether a local rewrite is safe to apply. Paid-report users also need rejected input to be recoverable before checkout.

## Goal, non-goal and definition of success

The selected goal was coherent, truthful local scanning and recovery across the browser, editor, CLI and report intake. Acceptance required meaningful negative and positive controls, actual browser interaction and downloads, synchronized editor views, scoped and idempotent CLI edits, and independently rerun worker checks. The task did not authorize publishing, spending, opening checkout, contacting people, changing lifecycle dates, or replacing the existing stack. This is a local implementation record, not a release or demand measurement.

## Principles affirmed, introduced, weakened or challenged

P-06 was strengthened by narrower local rewrites, staged batch validation and safer rollback selection. P-16.2 was affirmed by rejecting malformed input before checkout while preserving the deployment gate. P-17 was affirmed by making coverage, recovery and local findings export available in the free browser and editor surfaces. Their lifecycle statuses remain active.

## Alternatives considered and rejected paths

The agent considered visual polish alone, adding commercial features, and replacing the scanner stack. It chose to fix observed breaks in the existing workflows: presentation depends on accurate coverage, editor views need one state owner, and template edits need source spans and resource scope. A general YAML/HCL engine and dependency resolver would exceed the selected change; bounded parsing and explicit manual-review limits were retained. No new runtime dependency was introduced.

## Decision and rationale

The agent selected trustworthy scan outcomes as the shared improvement across layers. Rejected or incomplete input must remain visible; results must refer to the selected source; local changes must stay within identified Lambda configuration. Three specialist workers owned the editor, paid path review/intake repair, and CLI corrections while the root implemented the browser and independently verified the returned work. These are recorded engineering decisions, not an inference about customer demand.

## Implementation and evidence anchors

The anchor above is the existing history-system commit, **not** an implementation commit. Changes were made in its working tree on `codex/whole-product-improvement-20260905`. Reproducible evidence is in `apps/web/test_scan.py`, `apps/web/test_browser.mjs`, `apps/vscode-extension/test/lifecycle.test.cjs`, the two changed kits' test suites, `apps/grace-api/test/test_app.py`, and `apps/runner/test/test_audit_pdf.py`. Local command captures, source hashes, screenshots and the provider-fixture PDF flow are under ignored `tmp/product-improvement/`; acceptance and independent-review records are under ignored `.unlazy/product-improvement/`.

CI now runs the rendered scanner smoke. Existing deployment-URL checks exclude `docs/history/`, whose intentional historical citations were reproduced as false failures; all other generated public artifacts remain checked. The history renderer uses explicit HTML line breaks for event metadata so new generated capsules pass `git diff --check` without trailing whitespace.

## Expected outcome

Users should distinguish findings from missing coverage, recover from input or read failures, inspect and export useful local evidence, see current editor state, and preview template edits without modifying unrelated settings. Invalid report input should be corrected through a new immutable upload before payment. No conversion, speed or revenue improvement was forecast as a measured result.

## Observed outcome

The web suite passed 66 tests. Chromium exercised keyboard input, real file selection and JSON download, filtering, malformed and unreadable input, cancellation, stale-result protection and bounded batches; desktop and 390/320-pixel layouts were inspected. The extension compiled and passed lint, rule and activation-level lifecycle tests. Paid-path verification passed 95 API tests and 45 runner tests, plus a local signed-upload/webhook-to-real-PDF/download/retention flow with providers mocked. CLI verification exercised actual commands for manifest parsing, dry-run/apply/idempotency, unrelated settings and whole-batch refusal, plus rollback fixtures. Final verification details are recorded in `revenue/METRICS.md`; none are evidence of a deployed purchase.

## Tradeoffs, debt and follow-ups

Browser analysis remains bounded pattern matching, with 100 files, 1 MiB per file and 10 MiB per batch; a complete batch is not proof of migration safety. Browser TOML support is narrower than the Python CLI's real TOML parser. YAML/HCL editors deliberately support a subset, and CDK remains source-pattern based. Python 3.9/3.10 TOML audits need the optional existing `tomli` package or a flat requirements file. Editor lifecycle tests use a mock VS Code host, not an Electron extension host. Live AWS, Stripe, Resend and deployed retention remain unverified. No version bump or publishing occurred.

## Unresolved questions

Will these changes improve real developer adoption or paid-report demand after release? That requires external observation. G-09 and G-12 still require their real deployment and purchase evidence; local tests do not satisfy them.
