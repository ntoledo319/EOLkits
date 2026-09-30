---
id: eolkits-2026-09-01-credential-sweep-left-repo-unrewritten
title: "The September 2026 credential purge: eighteen repositories rewritten, this one inventoried, scanned and left untouched"
kind: external-constraint
scope: project-wide
components: [ci, worker, revenue]
paths: ["apps/worker/wrangler.toml", "revenue/**", "HANDOFF.md", "apps/runner/**", "deploy/grace/**"]
significance: high
occurred_at: 2026-09-01
decided_at: 2026-09-01
merged_at: null
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "A portfolio-wide secret sweep on 2026-09-01/02 rewrote eighteen of the owner's repositories; for EOLkits it found two gitleaks candidates and 72 exact-pattern events across 33 commits and 24 paths, classified every one as public configuration, placeholder or planted demo material with zero validated live credentials, and performed no rewrite, force-push, redaction or quarantine — so this repository's ancestry is intact and every anchor in this history still resolves."
claim_ids: [CLM-EXT-029, CLM-EXT-030, CLM-EXT-031, CLM-EXT-032, CLM-EXT-033, CLM-EXT-034, CLM-EXT-035, CLM-EXT-036, CLM-E4B-027, CLM-E4B-059, CLM-E1-032, CLM-E1-033]
source_ids: [SRC-purge-report, SRC-purge-ledgers, SRC-purge-memory, SRC-github-api, SRC-repo-git, SRC-bizops-root, SRC-aider-untracked]
anchors: ["a297ea4a18c535a27b6bcad1c4a40d4ed08b974e", "47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8", "d772637a8df2fca900550a3de650a4a9af702b5d", "172161d8164940ac62940a75a27ac741db3ba86f", "50d81348dadfe84145cfca46401145daec2b7d79"]
related: [eolkits-2026-08-22-legacy-commerce-retirement, eolkits-2026-09-04-jail-violations-and-env-recovery-scan, eolkits-2026-09-04-history-system-bootstrap]
amends: []
supersedes: []
superseded_by: []
reversed_by: []
status: closed
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

The repository had committed Stripe identifiers into `pricing.yml` since 2026-04-30 (identifiers, not keys; not reproduced here, CLM-E1-032), carried a Cloudflare `wrangler.toml` with account references, and had untracked tool logs from April containing a credential-shaped value (CLM-E1-033). A June ops note had already recorded that a Stripe-live-key-shaped string in Rupture "was a dummy" (CLM-EXT-036). The pressure was portfolio-wide: a credential exposure across the owner's estate led to a sweep of every repository.

## Intended beneficiaries

The owner's security posture; future readers of this history, who need to know whether the commit graph they are reading is the original one.

## Goal, non-goal and definition of success

The sweep's rule: rewrite only histories with confirmed live credentials; "no rewrite is authorized from this class alone" for unvalidated pattern matches. Success for this repository: an explicit classification and a decision not to rewrite.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-15 (preserve history) from outside the project. Confirmed the state.yml `rewritten_history: no` assertion on which every SHA citation in this history depends.

## Alternatives considered and rejected paths

Rewriting on pattern matches (explicitly refused by the plan's interpretation rule); quarantining the clone (no entry in the quarantine ledger).

## Decision and rationale

Classify as `EXACT_SOURCE_MATCH_UNCONFIRMED`, plan `NO_REWRITE_YET` with reason "exact text match is to an unvalidated canonical, high-confidence, credential-file, or detector-pattern source"; final pattern classification: five rows "public configuration, identifier, endpoint, environment reference, or placeholder with no embedded credential" and one row "repeated planted/demo private-key material … not live credential material" (CLM-EXT-030). Not on any rewritten, published, quarantined or security-commit list (CLM-EXT-029). The historian notes that the scan's type labels (`gemini_credential`, `codevault_credential`) name the source of the pattern, not the content of the match, and are easy to misread (CON-026).

## Implementation and evidence anchors

Owner-side ledgers only (SECURITY_CLEANUP_REPORT.md; `.unlazy/credential-cleanup/verification/history-remediation.json` histories[33]; `history-pattern-final-classification.json` rows 235, 243, 254, 256, 268, 270; `discovery/history.md`; `discovery/repositories.md`; the remote lease snapshot of 2026-09-02T00:03Z). Corroboration in this repository and on GitHub: `main` at a297ea4a18c535a27b6bcad1c4a40d4ed08b974e before and after; tags v1, v1.0.0, v1.1.0 at the same objects on 2026-09-04; `v2` at 47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8; no `refs/original`, no filter-repo marker, no reflog entries for 2026-09-01..03, plain push URL; in GitHub's 3,585-event activity log the only twelve force pushes are dependabot rebases of its own branches in April–May (CLM-EXT-033). Three of the 33 flagged commits: d772637a8df2fca900550a3de650a4a9af702b5d, 172161d8164940ac62940a75a27ac741db3ba86f, 50d81348dadfe84145cfca46401145daec2b7d79 — all still resolve.

## Expected outcome

No change to this repository.

## Observed outcome

No change. The repository's expected secret names (STRIPE_KEY, STRIPE_WEBHOOK_SECRET, RESEND_API_KEY, RUNNER_TOKEN, EOLKITS_ADMIN_TOKEN, EOLKITS_INTERNAL_URL_SECRET, GITHUB_TOKEN) were inventoried and a project env file plus a GitHub-App key file exist in the canonical vault by name (CLM-EXT-032). Whether any of those runtime secrets was rotated is not stated anywhere read (CLM-EXT-035). PR #58 on 2026-09-04 independently reports no purge and placeholder-only credential-shaped history (CLM-E4B-059).

## Tradeoffs, debt and follow-ups

The per-repository status ledger omits EOLkits rather than marking it clean; the untracked April tool logs still exist in the working tree; rotation of the project's own secrets is an open owner item shared with the agents' HQ-B/HQ-2 lineage. Should a rewrite ever happen, `audit --full` will report the unreachable anchors and this event must be amended, not edited.

## Unresolved questions

Whether STRIPE_KEY, RESEND_API_KEY and the GitHub App key were rotated after the sweep; whether the two gitleaks candidates ("deployment-path review") were reviewed to closure.
