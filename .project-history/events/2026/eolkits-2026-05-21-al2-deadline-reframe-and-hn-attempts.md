---
id: eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts
title: "The launch re-aimed at the Amazon Linux 2 deadline, and the Show HN that HN would not accept"
kind: goal
scope: launch
components: [launch, web, docs]
paths: ["launch/**", "README.md", "HANDOFF.md", "docs/index.html"]
significance: high
occurred_at: 2026-05-21
decided_at: 2026-05-21
merged_at: 2026-05-21
released_at: null
recorded_at: 2026-09-04
last_verified_at: 2026-09-04
summary: "After the May Show HN window was missed, the launch was rebuilt around the 2026-06-30 Amazon Linux 2 end-of-support date; the Show HN slipped six times, was submitted twice in June and rejected twice by HN's new-account policy, and the deadline thesis itself was disowned on 2026-06-21."
claim_ids: [CLM-E2-001, CLM-E2-002, CLM-E2-031, CLM-E2-032, CLM-E2-036, CLM-E2-062, CLM-E2-063, CLM-E1-051, CLM-E1-052, CLM-EXT-011, CLM-EXT-037, CLM-E2-037]
source_ids: [SRC-repo-git, SRC-repo-deleted-docs, SRC-tc-master-portfolio, SRC-bizops-root]
anchors: ["ba5edd33e06b689b0253eebdd97883e324054487", "b477d2b2c3ef0cd6ce3955f5679ed199c4ed0bdd", "cb5d832b41bc7b0868de8f692287f9193ae4b7bb", "18c0c1b5693d292b2c30573e3c7ae3051d0a9212", "0d20243042bf6257f2134ad16bb3ad0502877405", "52ddba1407450988a70ec72675284165c29215b0"]
related: [eolkits-2026-05-02-v1-signed-release-and-marketplace, eolkits-2026-06-21-autopsy-never-reached-market]
amends: []
supersedes: []
superseded_by: [eolkits-2026-06-21-autopsy-never-reached-market]
reversed_by: []
status: superseded
confidence: confirmed
secrets_reviewed: true
revision_notes: []
---

## Before-state and pressure

Eleven days of silence followed the signed v1.0.0 release: no non-bot commit between 2026-05-04 and 2026-05-15, `launched.txt` still "not yet submitted" (CLM-E1-051, CLM-E1-052). The launch copy led with the Lambda Node.js 20 date, which had already passed. The commit that reopened work on 2026-05-21 says the May 5/6 Show HN window was missed "when work was backburnered" and that the copy should "honestly own the missed window" (CLM-E2-001). The owner's own notes from 2026-05-05 had listed Rupture first among short-term revenue items, so the pressure was still revenue, now with a new clock: Amazon Linux 2 end of support on 2026-06-30.

## Intended beneficiaries

Teams still running Amazon Linux 2 with weeks to go; the same "panic buyer" of the founding thesis, now tied to a date the copy could count down to.

## Goal, non-goal and definition of success

Post a Show HN on Tuesday 2 June or Wednesday 3 June to capture "27–28 days of live AL2023 urgency"; Marketplace tile returning 200; sandbox PR; 126 tests green (CLM-E2-002). Non-goals inherited from the runbook: no paid channels, no cold spam. The definition of success was, literally, a Hacker News URL written into `launch/launched.txt`.

## Principles affirmed, introduced, weakened or challenged

Affirmed: honesty about the missed window (P-07); ToS absolutism — when HN rejected the post, no workaround was attempted (P-04). Affirmed and then exposed: the deadline-tiered pricing rule (P-12): surge tiers keyed to days-to-deadline, copy counting days, an ICS feed and a README hard-coded to "EOL in 19 days" (CLM-E2-062). Challenged: the founding premise that a deadline is a market.

## Alternatives considered and rejected paths

June 9/10 was the conservative window, rejected for June 2/3; Friday 22 May was avoided as a dead HN day and 26 May for Memorial Day (CLM-E2-002). After the first rejection the ledger records a moderator appeal queued through the owner's outreach cockpit and an automatic retry scheduled — submission was being driven partly by owner-side automation (CLM-E2-032). Reddit was later ruled "policy-dead" and cold email a domain-reputation risk (CLM-E2-052).

## Decision and rationale

Re-aim rather than rethink: the commit messages treat the missed window as a scheduling failure, not a thesis failure. The rationale is explicit in the copy — the deadline "is the news, not the product" — and the surge ladder made the price rise as the date approached. This is what the documents said; whether the owner or an agent chose the dates is not recoverable, though the commits are owner-authored with Claude co-author trailers (CLM-E2-058).

## Implementation and evidence anchors

ba5edd33e06b689b0253eebdd97883e324054487 and b477d2b2c3ef0cd6ce3955f5679ed199c4ed0bdd (2026-05-21: README hero, launch kit, HANDOFF rewritten around AL2). Show HN ledger entries cb5d832b41bc7b0868de8f692287f9193ae4b7bb, 18c0c1b5693d292b2c30573e3c7ae3051d0a9212 (2026-06-12 attempt and rejection) and 0d20243042bf6257f2134ad16bb3ad0502877405 (2026-06-17 second rejection). 52ddba1407450988a70ec72675284165c29215b0 (2026-06-22) removed the stale hard-coded day counts.

## Expected outcome

A front-page Show HN in the first week of June driving audits at the $399/$599 surge tiers before 30 June.

## Observed outcome

The window slipped at least six times (CLM-E2-036). Two submissions were made and both were rejected by HN's restriction on new accounts posting Show HN — "a policy gate, not a flag" (CLM-E2-031). The owner's portfolio recorded the launch as rejected and never resubmitted; that account is an artefact of branch divergence (CON-009), but no submission ever succeeded. On 2026-06-21 the autopsy declared that "a business whose demand arrives in 9-day spikes separated by multi-month deserts is not a business" (CLM-E2-063). The deadline passed with $0 collected; the copy was reframed to "past EOL, now unpatched" in stages that ended only on 2026-08-12 (CLM-E3-009).

## Tradeoffs, debt and follow-ups

Hard-coded countdowns went stale and became a class of truth bug that the July routine spent a month sweeping. Routing the entire distribution plan through one channel is the autopsy's first finding. The Show HN drafts were finally archived on 2026-08-22 as "launch copy predates Audit v2 and is not approved for publication" (CLM-E4A-058).

## Unresolved questions

Whether the 2026-06-22 "final retry" was attempted; why the HN account was new enough to be gated when the project had planned a Show HN since April; whether any AL2-deadline traffic reached the site at all (no analytics existed until 2026-06-22).
