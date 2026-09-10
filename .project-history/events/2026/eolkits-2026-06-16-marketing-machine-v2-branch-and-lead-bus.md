---
id: eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus
title: "marketing-machine-v2: a long-lived branch that production deployed directly, and an API that became the studio's lead bus"
kind: operating-model
scope: project-wide
components: [web, grace-api, deploy, ci]
paths: ["apps/web/**", "apps/grace-api/**", "deploy/grace/**", "launch/distribution/**"]
significance: high
occurred_at: 2026-06-16
decided_at: 2026-06-16
merged_at: 2026-08-22
released_at: 2026-06-22
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "From 2026-06-16 all substantive work moved to a branch that a VPS cron pulled and deployed daily while main received only bot commits for nine weeks; the same fortnight the fulfilment API gained a generic lead endpoint serving six of the owner's other sites, so EOLkits' backend quietly became shared infrastructure."
claim_ids: [CLM-E2-033, CLM-E2-034, CLM-E2-038, CLM-E2-039, CLM-E2-040, CLM-E2-041, CLM-E2-042, CLM-E2-043, CLM-E2-044, CLM-E2-048, CLM-E2-050, CLM-E2-053, CLM-E2-057, CLM-EXT-018, CLM-E3-001, CLM-E3-014, CLM-E4A-024, CLM-E3-048, CLM-E3-055]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-tc-truth-register, SRC-marketing-arm]
anchors: ["11cecfb09c18546ed4727e92121a00e646d51c8c", "94b18b6f3a6bfed2ae5970142f8527c4566da73b", "ccf307b348ee706c74bf9535ce1c18ad30deac6c", "d840cdb2da615788848f6e6a0420b0689a4bc4ad", "465d3419ec0d7937cc8e3c233319c58046914318", "e3e65e0fbc4ac7e94bf72a9c4287455446006087", "f033a400d020149490368bb41468fe007640b972", "4e15de9adf6214b48c3c83663554505edbd5d80a", "805c9e5aa195fcdaa894b26cf889b8283f39657c", "85c9f43e330a668779e1de60c80ed5023a90129d"]
related: [eolkits-2026-05-31-deterministic-deprecation-seo, eolkits-2026-06-08-cloudflare-to-grace-runtime, eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-08-29-marketing-machine-v2-absorbed]
amends: []
supersedes: []
superseded_by: [eolkits-2026-08-29-marketing-machine-v2-absorbed]
reversed_by: []
status: superseded
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

Launch blocked by HN policy; no analytics; a FormSubmit lead form on the studio sites that "silently dropped every submission" (CLM-E2-038). The repository had no way to deploy to the VPS, so the practical route was a cron on the box that pulled a branch.

## Intended beneficiaries

Cold-reach visitors (free `/scan`, `/fix` pages) and, for the lead bus, every prospect of the owner's six studio microsites — beneficiaries outside this product entirely.

## Goal, non-goal and definition of success

Goal: "cold-reach surfaces + attribution" — a free client-side scanner, sourced error pages, badges, RSS, first-touch attribution, and durable lead capture where "the DB row is the guarantee; notify is best-effort" (CLM-E2-039). Non-goal: bulk cold outreach, "deliberately NOT revived" (CLM-E2-053). Success: a first `checkout_click` on `/status`, 50+ leads in the autopsy's plan.

## Principles affirmed, introduced, weakened or challenged

Affirmed P-18 (deterministic build enforced by `--check`, CLM-E2-044) and P-16 (durable-first capture; notify failures made loud on 2026-06-20/21, CLM-E2-042, CLM-E2-043). Introduced, without being stated as a principle, the practice of running production from a non-`main` branch — a revealed priority of shipping speed over review, which later cost hand-authored work (CLM-E4A-043).

## Alternatives considered and rejected paths

Deploying `main` was rejected in practice: the owner's marketing plan warned that the deployed API was "149 behind / 4 ahead" of `origin/main` and that deploying `main` would delete the lead endpoint (CLM-EXT-018). Keeping FormSubmit was rejected because it lost submissions. The autopsy weighed founder-visible trust against a faceless funnel and chose faceless (P-13).

## Decision and rationale

Work on `marketing-machine-v2`, let the box cron deploy it, and make the EOLkits API the capture point for the whole portfolio. The stated rationale is durability and speed; the historian notes the branch also let a nightly agent ship without review, which the July operating doc then formalised as its "ship channel" (CLM-E3-014).

## Implementation and evidence anchors

11cecfb09c18546ed4727e92121a00e646d51c8c (2026-06-16, "Marketing machine v2"); 94b18b6f3a6bfed2ae5970142f8527c4566da73b and ccf307b348ee706c74bf9535ce1c18ad30deac6c (2026-06-17, `POST /api/v1/lead`, "the studio lead bus"); VPS-side pins e3e65e0fbc4ac7e94bf72a9c4287455446006087 (author "Toledo Ops", 2026-06-17) and f033a400d020149490368bb41468fe007640b972 (a VPS host identity, 2026-06-21; branch `vps-live-state-20260621`, never merged, CLM-E2-041); d840cdb2da615788848f6e6a0420b0689a4bc4ad and 465d3419ec0d7937cc8e3c233319c58046914318 (notify hardening); 4e15de9adf6214b48c3c83663554505edbd5d80a (`ship-web.sh` and the daily cron, 2026-06-22); 805c9e5aa195fcdaa894b26cf889b8283f39657c (2026-06-28, the first commit authored "Claude" — the weekly cloud routine). The branch reached `main` only through 85c9f43e330a668779e1de60c80ed5023a90129d on 2026-08-22.

## Expected outcome

A measurable funnel and a lead pipeline for the studio, with the site updated daily without owner effort.

## Observed outcome

The branch was the deployed line for roughly nine weeks (CLM-E3-001). Owner records verified the lead bus live on 2026-06-22 with `unnotified_leads: 0` (CLM-EXT-018). The 2026-08-10 merge message reports 78 of the last 81 lead submissions were spam (CLM-E3-040). No lead or funnel count for EOLkits itself was ever written into a ledger.

## Tradeoffs, debt and follow-ups

`main` and production diverged; the CORS allow-list hard-coded six unrelated hostnames into this product's API; the autopsy itself observed the machine had "become another build project — 40% live, 60% stuck unmerged". The daily cron outlived its own disabling in the repository and kept deploying the branch through August (CLM-E4A-029).

## Unresolved questions

What the VPS ran after 2026-06-21; whether the marketing sink URL was ever configured (the code is a no-op without it); the actual lead and event counts in the SQLite tables on the host.
