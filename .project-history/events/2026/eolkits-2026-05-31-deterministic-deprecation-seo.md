---
id: eolkits-2026-05-31-deterministic-deprecation-seo
title: "Deterministic, zero-LLM deprecation pages: the rules file becomes the only source of public facts"
kind: architecture
scope: web
components: [web, rules, docs]
paths: ["apps/web/**", "rules/**", "docs/migrate/**", "docs/fix/**", "docs/sitemap.xml", "docs/feed.xml"]
significance: high
occurred_at: 2026-05-31
decided_at: 2026-05-31
merged_at: 2026-06-08
released_at: 2026-06-22
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "A renderer that generates every migration and error-fix page from rules/public/deprecations.yml and a hand-verified fixes corpus, with no LLM output and byte-identical rebuilds, became the project's acquisition surface and its most consistently defended principle."
claim_ids: [CLM-E2-004, CLM-E2-012, CLM-E2-034, CLM-E2-035, CLM-E2-044, CLM-E2-049, CLM-E2-050, CLM-E2-061, CLM-E4B-035, CLM-E3-028, CLM-E2-065]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs]
anchors: ["6741fd3e494a9662f8debed0a99811d916fedc86", "11cecfb09c18546ed4727e92121a00e646d51c8c", "e6bf3498b9fedb5a79328103c80fcb0c902989cb", "dfe9fa58eea1119886fceacaf84f0a5af29cd453", "d1b1bb47566d4a0e90d21b077d83828b2f827cfc", "4dd11edbde43f7e1d35eff5f3f25091db7c09e1a"]
related: [eolkits-2026-04-29-autonomy-runbook-five-skus, eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus, eolkits-2026-07-13-node20-date-truth-sweeps]
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

The April runbook had promised "programmatic SEO" and shipped a nightly `seo-pages` workflow that regenerated `/vs/` comparison pages as `rupture-bot`; the pages were thin and the site build still targeted GitHub Pages paths even after the custom domain existed (CLM-E2-020). With the Show HN blocked, organic search was the only channel the project was permitted to use, and the site had "zero analytics instrumentation".

## Intended beneficiaries

Engineers searching for a specific AWS error string or a specific deprecation date; secondarily, AI search engines, which the `llms.txt` and JSON-LD were written for.

## Goal, non-goal and definition of success

Goal: pages that rank because they are correct, each fact traceable to a `source_url` in the rules file; a `/migrate/` hub, `/fix/<error>/` pages, deadline badges and an RSS feed. Explicit non-goals: no LLM-generated text anywhere in the public corpus (the 2026-05-31 message says so), no fabricated error strings — "Fabricating error strings to rank would be scaled-content-abuse" (CLM-E2-035). Success was measured in indexed URLs (sitemap 22/23) and, from 2026-06-22, first-party pageview beacons.

## Principles affirmed, introduced, weakened or challenged

Introduced P-18 (deterministic, sourced public content). Reinforced P-03 (rules cite public sources) by making the rules file the single upstream for pages, ICS feed and surge pricing (CLM-E2-061) — which also meant a wrong date propagated everywhere at once. Introduced the determinism guarantee as a product promise: "byte-for-byte identical across any two rebuilds on the same UTC day — the determinism guarantee EOLkits sells" (CLM-E2-044).

## Alternatives considered and rejected paths

LLM-written pages were rejected in the 05-31 message. One candidate `/fix` page was dropped on 2026-06-22 because the claimed error was not real (CLM-E2-049) — the corpus rule enforced against its own author. Daily `BUILD_DATE` bumps, adopted by the later Claude routine, were reversed on 2026-09-04 as "false publication churn" (CLM-E4B-035): dates describe content, not build activity.

## Decision and rationale

Generate, never write: every public fact is data in `rules/public/deprecations.yml` or `apps/web/content/fixes.yml`, rendered by `apps/web/build.py`. The stated rationale is trust and platform safety — sourced facts rank and cannot be called scaled-content abuse. The historian notes that this was also the only content strategy compatible with a solo operator who could not review prose at volume.

## Implementation and evidence anchors

6741fd3e494a9662f8debed0a99811d916fedc86 (2026-05-31, renderer, `/migrate/` hub, JSON-LD, llms.txt); 11cecfb09c18546ed4727e92121a00e646d51c8c (2026-06-16, free `/scan`, first eight `/fix` pages, badges, RSS); e6bf3498b9fedb5a79328103c80fcb0c902989cb (2026-06-21, byte-deterministic build with `--check`); corpus growth 8→23 pages on 2026-06-22 (dfe9fa58eea1119886fceacaf84f0a5af29cd453 and siblings); head-term pages and the cookieless beacon d1b1bb47566d4a0e90d21b077d83828b2f827cfc; the `/eol-checker/` tool 4dd11edbde43f7e1d35eff5f3f25091db7c09e1a (2026-07-15).

## Expected outcome

Evergreen search demand replacing the deadline spikes; backlinks from dev.to canonicals; a measurable funnel from `/fix` and `/scan` to the paid audit.

## Observed outcome

The corpus reached 27 `/fix` pages by 2026-07-15 and survived every later regime: the 08-22 rebuild kept the renderer and deleted the bots around it. No traffic figure from the beacon was ever recorded in a ledger; the only measured traffic in the whole history is GitHub's 72 views over 14 days in September (CLM-E4B-052). The pages did what the principle required; whether anyone read them is unknown.

## Tradeoffs, debt and follow-ups

Making the rules file the single source of truth turned date errors into pricing and calendar errors (CLM-E1-061) and made the July truth sweeps necessary. The committed `docs/` tree became a build artefact that drifted from the deployed site (CLM-E3-052). The determinism promise was honoured in the build but contradicted by the daily `BUILD_DATE` routine until September.

## Unresolved questions

Whether any `/fix` page ever ranked or converted; whether the IndexNow submissions were crawled; where the "§2.1/§2.2 plan" referenced by the 2026-06-08 profit-levers commit lived.
