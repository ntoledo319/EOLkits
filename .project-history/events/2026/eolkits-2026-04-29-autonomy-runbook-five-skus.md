---
id: eolkits-2026-04-29-autonomy-runbook-five-skus
title: "The autonomy runbook: five self-serve SKUs, a Stripe-and-Worker fulfilment loop, and CI trust signals"
kind: operating-model
scope: project-wide
components: [worker, web, github-app, github-action, vscode-extension, rules, ci]
paths: ["apps/worker/**", "apps/web/**", "apps/github-app/**", "apps/github-action/**", "apps/vscode-extension/**", "rules/**", "pricing.yml", ".github/workflows/**", "RULES.md"]
significance: foundational
occurred_at: 2026-04-29
decided_at: 2026-04-29
merged_at: 2026-04-29
released_at: 2026-05-02
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "A 688-line runbook rebased the business on five self-serve SKUs fulfilled by webhooks with no human in the loop, installed fourteen workflows as 'trust signals', and encoded the rule that every shipped deprecation rule cites a public source."
claim_ids: [CLM-E1-016, CLM-E1-017, CLM-E1-018, CLM-E1-019, CLM-E1-020, CLM-E1-021, CLM-E1-022, CLM-E1-023, CLM-E1-024, CLM-E1-025, CLM-E1-026, CLM-E1-027, CLM-E1-028, CLM-E1-029, CLM-E1-030, CLM-E1-031, CLM-E1-032, CLM-E1-055, CLM-E1-056, CLM-E1-057, CLM-E1-061, CLM-E1-064, CLM-E1-013, CLM-E1-014, CLM-E1-015]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-github-prs]
anchors: ["910795704f6829f054bf43cf2135c8e143bbbf99", "946537d67b0cc3d159059f6665b81572c64cc3cc", "14419470162497776ec8011f6363c1f4ea268a05"]
related: [eolkits-2026-04-28-rupture-mission-launch, eolkits-2026-05-02-v1-signed-release-and-marketplace]
amends: []
supersedes: []
superseded_by: [eolkits-2026-08-22-truthful-evidence-report-rebuild]
reversed_by: []
status: superseded
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

Day-one tiers sold human support ("Priority Slack", "live pairing"), which the new runbook judged incompatible with a solo operator who wanted no per-sale labour: the old ladder "violates the autonomy rule (offers human support)" (CLM-E1-018). PR #1, the first Claude Code contribution, had just fixed six real defects including tests that never exercised the rewriter (CLM-E1-013, CLM-E1-014).

## Intended beneficiaries

The same deadline-pressed engineering teams, now segmented by SKU: a free CLI for everyone, a $299 audit PDF (surging to $399/$599 near the deadline), a $1,499 "Migration Pack" (a bot-opened PR with a refund if CI fails), a $14,999/year organisation license, and a $19/month "Drift Watch" re-scan (CLM-E1-018).

## Goal, non-goal and definition of success

Three non-negotiables: $0 seed, fully autonomous fulfilment ("If a step needs a human, it does not exist"), strict platform-ToS compliance (CLM-E1-017). Success was a fifteen-item acceptance list (four live checkout flows, nightly benchmark, valid ICS calendar, determinism/property/mutation gates, signed release, an App-opened PR, a Marketplace Action, a VS Code extension, a green status page, a submitted Show HN) and a week-one forecast of $9k–$22k "realistic" (CLM-E1-019). Explicit cuts: cold email, unsolicited PRs, paid legal/SOC 2 tooling, a custom domain, paid LLM APIs, cash bounties, telemetry, storing buyer code, pre-staked HN comments (CLM-E1-020).

## Principles affirmed, introduced, weakened or challenged

Introduced: "If a rule cannot cite a public source, it does not ship" (P-03; CLM-E1-021); "every trust signal terminates in a verifiable hash" (P-05 v1); ToS absolutism (P-04); no telemetry (CLM-E1-064); opt-in-only PR bot with throttling and a `.no-rupture` opt-out (P-06; CLM-E1-025). Weakened on arrival: the same commit shipped a `deprecations.yml` whose Python and Node dates contradicted the kit READMEs, in the file declared the single source of truth for the ICS feed, SEO pages and surge pricing (CLM-E1-022, CLM-E1-061).

## Alternatives considered and rejected paths

The runbook's §5.F table records what was cut and why (CLM-E1-020). The "dry-launch mode" (pre-order capture without charges) was designed as the fallback if three blocking credentials — Stripe live key, Cloudflare token, GitHub App registration — were not supplied (CLM-E1-028).

## Decision and rationale

Adopt the runbook wholesale: 116 files, +12,328 lines, committed under the owner's identity with a Claude co-author trailer (CLM-E1-016). The rationale, in the runbook's words, is that a webhook business needs no human, so every SKU must fulfil itself. The historian notes this is an agent-drafted document; how much the owner authored versus approved is not recoverable.

## Implementation and evidence anchors

910795704f6829f054bf43cf2135c8e143bbbf99: a TypeScript Cloudflare Worker with Stripe checkout/webhooks, idempotency, rate limits, Resend email, a partner program and a Workers-AI "LLM-on-rails" support bot (CLM-E1-025, CLM-E1-026); a Python runner whose migration-PR path was still a stub (CLM-E1-027); a Jinja static-site generator; fourteen workflows including a five-minute status synth committing as `rupture-bot` (CLM-E1-029, CLM-E1-030); template legal documents (CLM-E1-055). 946537d67b0cc3d159059f6665b81572c64cc3cc (2026-04-30) provisioned live Stripe products and committed their identifiers into pricing.yml (CLM-E1-032; identifiers not reproduced here).

## Expected outcome

Fifteen acceptance items green and first revenue within the week.

## Observed outcome

The first status run recorded every probe failing (Pages 404, worker unreachable), replacing a hand-written all-green data file (CLM-E1-031). The release "reproducibility" job hashed literal strings; benchmark and determinism workflows tried to `pip install` a Node package (CLM-E1-024). Dependabot opened ten PRs within an hour; most were never merged (CLM-E1-015). The README described the Node kit as a Python package for three days (CLM-E1-023). No revenue followed.

## Tradeoffs, debt and follow-ups

The status synth alone produced 2,949 commits over four months, burying the human history under automation noise — a debt this history system inherits. Placeholder trust signals seeded a long series of "make CI honest" corrections. The five-SKU catalogue, sold before it could fulfil, is the promise the August 2026 rebuild finally withdrew.

## Unresolved questions

Whether the owner read the runbook's §5.F cuts before they were reversed within days (see eolkits-2026-05-02-v1-signed-release-and-marketplace); which AWS dates were authoritative on 2026-04-29.
