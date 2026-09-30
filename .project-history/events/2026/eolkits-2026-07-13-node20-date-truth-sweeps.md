---
id: eolkits-2026-07-13-node20-date-truth-sweeps
title: "One wrong date, twenty places: the superseded Node.js 20 block dates and the month it took to sweep them out"
kind: data
scope: rules
components: [rules, kits, web, launch]
paths: ["rules/**", "kits/**", "apps/web/content/**", "launch/**", "README.md"]
significance: high
occurred_at: 2026-07-13
decided_at: 2026-07-13
merged_at: 2026-08-22
released_at: 2026-07-22
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "Cycle 0 verified at the AWS source that the Lambda Node.js 20 block dates had been delayed to 2027-02-01 and 2027-03-03; the superseded Aug/Sep 2026 dates, traced to blog schedules and the day-one research memo, were then found one layer deeper for five cycles running, in more than twenty files, until 2026-08-12 — and further date and version fabrications surfaced in August."
claim_ids: [CLM-E3-006, CLM-E3-007, CLM-E3-009, CLM-E3-021, CLM-E3-050, CLM-E3-051, CLM-E3-052, CLM-E1-022, CLM-E1-061, CLM-E2-061, CLM-E4A-003, CLM-E4A-051, CLM-E4B-019, CLM-EXT-037]
source_ids: [SRC-repo-git, SRC-openclaw-launch]
anchors: ["08ddf1793df9dd5b713d4c7f7a0f0aa3ede603c0", "ac8c49730932d8b9c2021a16e1dad02786bfcbbf", "8f1a94aa143ae385165cce77159721d8683465ca", "ab660bca218987ebfa9331a12a289bb59ed7b7c1", "668f505a697f839dfabcf63c4aebe9247ac2fa3b", "acd67d010d2b8267e1a14407c6f050e9b4756190", "8307102349f8c8333119553c0a16bbc8004e7fcc", "8aad5bd6b35ab4a350bfa01caf9ead198a4472fd", "0aeda1a1c05a1b5bc3af5be4b6716b1baa83e2fe", "915ebb14b55ac3ba244f18b94288c54db7b73870"]
related: [eolkits-2026-05-31-deterministic-deprecation-seo, eolkits-2026-07-13-revenue-loop-v2-operating-doc, eolkits-2026-08-22-truthful-evidence-report-rebuild]
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

The product's factual core is a table of AWS dates, and the first table shipped on 2026-04-29 was already inconsistent with the kit READMEs beside it (CLM-E1-022). Surge pricing, the ICS calendar and every SEO page derived from that table (CLM-E1-061, CLM-E2-061), so a wrong date was a wrong price and a wrong calendar entry. Launch copy had taken Node 20's block dates from blog posts reproducing AWS's original 30/60-day schedule; AWS had since delayed them (CLM-E3-007). Kit READMEs still advertised Solo/Team/Enterprise tiers, a Slack channel and a domain that did not exist (CLM-E3-021).

## Intended beneficiaries

Every reader of a public page or a scan result — the people the "truth only" rule was written for.

## Goal, non-goal and definition of success

"Verify dates at the AWS source, never from blogs — this is the #1 landmine" (HANDOFF-2026-07-15 §2.3). Success: no superseded date on any public surface. Non-goal: shipping any content the routine could not verify — it explicitly declined a codemod claim it could not check.

## Principles affirmed, introduced, weakened or challenged

Introduced P-03.2 (AWS source only; two-source bar later). Enforced P-07.2 as a stream of "truth fixes". Weakened P-18's promise in one respect: for 31 cycles the routine could not fetch any external source, so it verified only against the repository's own rules file — data it was simultaneously finding wrong elsewhere (CON-013's sibling tension in the E3 review).

## Alternatives considered and rejected paths

Search-engine-only verification was rejected because it "returned the exact superseded 2026 dates … unsafe"; the routine asked the owner to change the environment's egress policy, which never happened (CLM-E3-016). Leaving the committed `docs/` tree stale was tolerated until 2026-08-04 because the VPS cron rebuilt it daily without pushing back (CLM-E3-052).

## Decision and rationale

Treat the date class as a bug class: fix at the source, then sweep every consumer. The rationale is the operating document's truth rule; the historian notes that the sweeps also reveal how far copy had outrun verification since April.

## Implementation and evidence anchors

08ddf1793df9dd5b713d4c7f7a0f0aa3ede603c0 (Cycle 0 correction of lambda-lifeline and the VS Code extension); 915ebb14b55ac3ba244f18b94288c54db7b73870 (2026-07-15 fabricated README tiers removed); ac8c49730932d8b9c2021a16e1dad02786bfcbbf, 8f1a94aa143ae385165cce77159721d8683465ca and ab660bca218987ebfa9331a12a289bb59ed7b7c1 (2026-07-14/22 AL2 past-EOL reframes and Node date fixes on both lineages); 668f505a697f839dfabcf63c4aebe9247ac2fa3b, acd67d010d2b8267e1a14407c6f050e9b4756190, 8307102349f8c8333119553c0a16bbc8004e7fcc (2026-08-01..08-03: fixes.yml cause text, READMEs, thirteen instances in eight launch and ledger files, and the profit projection's "fabricated standalone Sep 30 2026 catalyst"); 8aad5bd6b35ab4a350bfa01caf9ead198a4472fd (2026-08-04 stale docs tree); 0aeda1a1c05a1b5bc3af5be4b6716b1baa83e2fe (2026-08-12 homepage badge, the last instance).

## Expected outcome

A one-time correction.

## Observed outcome

The same bug was found "one layer deeper" five cycles in a row (CLM-E3-051). In August the loop found three fabricated npm version floors and a stale PyPI claim being served by the free scan page (CLM-E4A-003), a wrong python3.10 date in a dev.to article (CLM-E4A-051), and — after the rebuild — that lambda-lifeline lacked python3.8 and python3.11 rows, so live scans would have reported those functions healthy (CLM-E4B-019). The owner's external content had pivoted to the 2027 dates by 2026-07-23 (CLM-EXT-037).

## Tradeoffs, debt and follow-ups

The date corpus remains a live risk, not a settled fact (CON-003). The September parity test across YAML, Node and Python (CLM-E4B-034) is the structural answer the July sweeps lacked. The repository still carries the day-one research memo with the superseded schedule as history.

## Unresolved questions

Whether any scan result delivered to a stranger before 2026-07-13 carried a wrong date; whether the dev.to articles published with superseded dates were ever corrected on dev.to.
