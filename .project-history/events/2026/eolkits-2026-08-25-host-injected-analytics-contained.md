---
id: eolkits-2026-08-25-host-injected-analytics-contained
title: "Incident: the custom host injects a third-party analytics script into every page; contained by a content-security policy, never removed"
kind: incident
scope: web
components: [web, deploy, legal]
paths: ["apps/web/build.py", "apps/web/templates/**", "legal/privacy.md", ".github/workflows/verify-grace-static.yml"]
significance: medium
occurred_at: 2026-08-25
decided_at: 2026-08-25
merged_at: 2026-08-25
released_at: 2026-08-26
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "When the custom domain first served the truthful copy on 2026-08-25, every page carried a cross-origin analytics script injected by the shared host under another project's hostname, contradicting the privacy policy; a meta CSP blocked execution by 2026-08-26, the verifier was deliberately left red, and the raw injection was still present on 2026-09-04 pending an owner-side host change."
claim_ids: [CLM-E4A-038, CLM-E4A-047, CLM-E4B-065, CLM-E2-050, CLM-E4A-054]
source_ids: [SRC-repo-git]
anchors: ["fcb127336a80515bb8e4fce54eed520947ebf360", "b97befa7c4707c9e4c9a9c39e22871ec536fa5f9", "1918eb8f861bf5519353551cf40b95eca8d33468"]
related: [eolkits-2026-06-08-cloudflare-to-grace-runtime, eolkits-2026-08-22-free-surfaces-made-truthful, eolkits-2026-08-30-fail-closed-relaunch-recovery]
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

The privacy policy promised no third-party analytics and a first-party cookieless beacon (CLM-E2-050). The custom host is a shared VPS serving several of the owner's sites behind one Caddy; the daily cron deployed the static site there at 07:17 UTC (CLM-E4A-024).

## Intended beneficiaries

Visitors whose browsers would otherwise load a script the policy said did not exist.

## Goal, non-goal and definition of success

Prevent execution and exfiltration without host access; block search notification and checkout on the custom domain until the injection is gone. Non-goal: weakening the verifier to make the site look clean.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-06 (minimise what a stranger's browser is exposed to; the same commit removed a session id from the success URL) and P-07.3 (the verifier stays red because the raw HTML is still untrue to the policy). Challenged P-13's implied promise that the faceless site is entirely first-party.

## Alternatives considered and rejected paths

Treating the CSP as remediation (rejected, D39: containment only); pointing acquisition links back at the custom domain (rejected; Pages stays canonical).

## Decision and rationale

Ship a meta content-security policy from the build, guard IndexNow and checkout on the custom domain, and hand the host fix to the owner (HQ-3). The stated rationale: the agents had no host access and would not read machine credentials to get it (P-10).

## Implementation and evidence anchors

fcb127336a80515bb8e4fce54eed520947ebf360 (build.py CSP, session-id removal, link tests, privacy note; mirror b97befa7c4707c9e4c9a9c39e22871ec536fa5f9); verifier and IndexNow guards; 1918eb8f861bf5519353551cf40b95eca8d33468 (2026-08-26 confirmation that the CSP was live on both hosts, CLM-E4A-047).

## Expected outcome

Script blocked in browsers within a day; host fixed by the owner within the queue's minutes.

## Observed outcome

CSP live on both hosts by 2026-08-26; raw responses still contain the tag; through 2026-09-04 the ledgers describe the custom host as pre-v2 with the injection present (CLM-E4B-065); HQ-A at HEAD is the emergency Caddy block the owner has not yet installed.

## Tradeoffs, debt and follow-ups

Custom-domain IndexNow blocked; checkout blocked; the verifier red by design, which any future maintainer must understand before "fixing" it.

## Unresolved questions

What injects the script (a host-level Caddy rule shared with a sibling site is the ledger's guess) and whether it was ever removed.
