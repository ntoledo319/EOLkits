# Show HN — final

This is the version to paste at submission time. Replaces the earlier draft.

## Voice notes (for self / future self)

- Audience: HN. They smell marketing language in two seconds. Reward: technical specificity and dry receipts. Punish: warmth, hedging, "we believe."
- Register: Mode 9 (analytical) primary with a single Mode 4 (vulnerable) graf for the why-I-built-this. No swearing — wrong audience for it.
- Em dashes are doing the heavy lifting on pivots. Don't smooth them out.
- The opening sentence is the deadline, not me. The deadline is the news.

---

## Title

```
Show HN: Rupture – three CLIs for AWS runtime deprecations (Lambda 20, AL2, Python)
```

## Submission URL

```
https://github.com/ntoledo319/Rupture
```

## Body

```
AWS Lambda Node.js 20 hits Phase 1 EOL on Apr 30, 2026. Amazon Linux 2 on Jun 30. Lambda Python 3.9/3.10/3.11 in waves after that. When Phase 3 lands you can't update functions on those runtimes anymore — the only path forward is a full deploy with a new runtime, or your code is frozen.

I built Rupture: three CLIs, one per deadline.

  lambda-lifeline   nodejs16/18/20 → 22       (Apr 30, 2026)
  al2023-gate       Amazon Linux 2 → AL2023   (Jun 30, 2026)
  python-pivot      Lambda Python 3.9-3.11 → 3.12

Each kit does the same five things: scan the account, run mechanical codemods (dry-run is the default; --apply writes), patch IaC across SAM / CDK / Terraform / Serverless / Packer / Ansible, generate a staged canary plan with auto-rollback hooks, and produce a tested rollback script. All offline-able through fixtures so you can evaluate before pointing it at AWS.

The pieces I cared about getting right:

- Deterministic builds. Same inputs → byte-identical outputs, CI-gated.
- Hash-anchored audit PDFs. Every report embeds SHA-256 of inputs and the rule-pack version, with a public verify URL.
- Property + mutation tested codemods. Mutation score is gated at 80%+ in CI.
- Sigstore-signed releases with CycloneDX SBOMs.
- Public nightly benchmark across a curated corpus of real public IaC repos — so you can see what the kits actually catch on real code, not synthetic fixtures.

The free GitHub Action runs the dry-run pass on PRs and comments findings. Paid tiers (audit PDF, migration pack, org license, drift watch) self-serve via webhook. No humans in the loop and no sales calls.

Why I built this: every six months AWS sends the same "your runtime is deprecated" email, and there's no integrated tool for any of it. CloudQuery gives you inventory. Migration Hub is for lift-and-shift. aws-samples gives you snippets. Nothing did scan + codemod + IaC patch + canary + rollback for one specific deprecation, end to end. So I scoped each kit tight: one runtime, one deadline, one job.

Repo:           https://github.com/ntoledo319/Rupture
Action:         ntoledo319/Rupture@v1
Benchmark:      https://ntoledo319.github.io/Rupture/status/
Sample PDF:     https://ntoledo319.github.io/Rupture/audit/
Calendar (.ics): https://ntoledo319.github.io/Rupture/deprecations.ics

Open to feedback on any of it — codemod rules especially. If you've already done one of these migrations and the kit missed something, tell me. That's the most useful thing anyone can do for me right now.
```

## Submission timing

Window: Tue or Wed, **6:00–9:00 a.m. PT**. (5/5 lands in this window.)

After submitting, paste the HN URL into `launched.txt`:

```
2026-05-05T15:30:00Z submitted by ntoledo319 link=https://news.ycombinator.com/item?id=...
```

## Comment posture

Stay in the thread the first 6 hours. Reply once per top-level comment, lead with the answer, link a doc on second mention only. Stop after one reply per thread unless someone asks. Do not pre-stake comments. Do not seed.
