# EOLkits — Send-Ready Distribution Kit

_Updated 2026-06-22 for the new conversion site (free `/scan`, `/audit` with guarantee + sample,
`/fix` corpus) and the **Amazon Linux 2 EOL on Jun 30 — 8 days out**. This supersedes the stale
`show-hn-final.md` / `social.md` / `outreach.md` drafts._

> **Division of labor.** Claude built/updated every asset below and can find outreach targets via
> GitHub code search. **Posting and emailing is the access-gated step — it runs from your accounts.**
> Each block is copy-paste ready. Lead with value, never blast.

> **Prerequisite:** ship the site first (`deploy/grace/ship-web.sh --apply`) so every link below is
> live (the new `/scan`, `/audit/sample`, and `/fix/*` pages are currently only on the branch).

---

## Sequencing (the next 8 days — AL2 deadline is the catalyst)

| Day | Action | Channel |
|---|---|---|
| Deploy day | Ship the site; smoke-test `/scan`, `/audit`, `/audit/sample` | — |
| +0 | Post the free scanner to **r/aws** + **r/devops** (value-first, below) | Reddit |
| +1 | **Show HN** (morning ET window) | HN |
| +1 | X thread + LinkedIn (same morning) | Social |
| +1–7 | 5–10 personalized outreach touches/day to repos still on AL2 | Email/GH |
| +1–7 | Answer real SO / r/aws / re:Post questions matching the `/fix` corpus | Communities |
| Jun 30 | Deadline-day push; then flip copy to "still on AL2? you're now unpatched" | All |

---

## 1. Show HN

**Title**
```
Show HN: EOLkits – free scanner + CLIs for AWS runtime EOLs (Amazon Linux 2 ends Jun 30)
```
**URL:** `https://github.com/ntoledo319/EOLkits` (HN prefers source). If Show HN is still
karma-gated on the account, post as a normal submission with the same body, or lead with Reddit
first to build standing.

**Body**
```
Amazon Linux 2 hits end-of-life on Jun 30, 2026 — after that, no patches and no new AMIs, and
anything still pinned to AL2 in a launch template or EKS node group is on borrowed time. Lambda
Python 3.9–3.11 and Node 18/20 are in their own EOL waves with Q1-2027 update-blocking cliffs.

You can check your own stack in ~30 seconds without installing anything or signing up:

  https://eolkits.com/scan

Drop your SAM/CDK/Terraform/Serverless or package.json/requirements.txt onto the page — it runs
entirely in your browser (open the Network tab, it makes zero requests) and flags deprecated
runtimes, native-addon ABI breaks, and Python 3.12 wheel issues. It's the same detection logic as
the CLIs.

The CLIs are MIT and do the full job, one per deadline:

  al2023-gate       Amazon Linux 2 → AL2023   (Jun 30, 2026)
  python-pivot      Lambda Python 3.9–3.11 → 3.12
  lambda-lifeline   nodejs16/18/20 → 22

Each does scan → mechanical codemods (dry-run default) → IaC patch (SAM/CDK/Terraform/Serverless/
Packer/Ansible) → staged canary with auto-rollback → tested rollback script. Offline-able via
fixtures so you can evaluate before pointing it at AWS.

What I cared about getting right:
- Deterministic output — CI runs each kit twice on the same inputs and fails on any diff.
- Hash-anchored audit reports — every report embeds SHA-256 of inputs + rule-pack version, public verify URL.
- Property-tested codemods + weekly mutation testing on the Python kits.
- Sigstore-signed releases with CycloneDX SBOMs.
- Public nightly benchmark across real public IaC repos (BENCHMARK.md) — what it catches on real code.

The paid tiers are optional and exist so you don't have to do it by hand: a $299 hash-anchored
audit report (sample: https://eolkits.com/audit/sample/), or a done-for-you migration PR with an
auto-refund if your CI fails. Free GitHub Action runs the dry-run pass on PRs and comments findings.

Why: every six months AWS sends the same "your runtime is deprecated" email and there's no
integrated tool for it — CloudQuery gives inventory, Migration Hub is lift-and-shift, aws-samples
gives snippets. Nothing did scan + codemod + IaC + canary + rollback for one specific deprecation,
end to end. So each kit is scoped tight: one runtime, one deadline, one job.

Feedback on the codemod rules especially welcome — if you've done one of these migrations and the
kit would've missed something, that's the most useful thing you can tell me.
```
**Comment posture:** stay in-thread the first ~6h, lead with the answer, link a doc only on second
mention, one reply per thread. Don't seed or pre-stake. After posting, append to `launched.txt`:
`2026-06-__T__:__Z submitted by ntoledo319 link=https://news.ycombinator.com/item?id=...`

---

## 2. Reddit (value-first — the free scanner is the hook, not the paid tiers)

**r/aws** — title: `Amazon Linux 2 is EOL Jun 30 — free browser tool to see what in your stack breaks`
```
AL2 reaches end-of-life Jun 30 (no more patches/AMIs). I got tired of grepping for AL2 AMIs and
deprecated Lambda runtimes by hand, so I built a scanner that runs entirely in your browser — drop
your Terraform/SAM/CDK/serverless or package.json/requirements.txt and it flags what breaks, with
the AWS source for each finding. Nothing is uploaded (Network tab stays empty).

https://eolkits.com/scan

It's the free part of a set of MIT CLIs (al2023-gate / python-pivot / lambda-lifeline) that also do
the codemods + IaC patches if you want them. Curious what it catches/misses on your real configs —
feedback welcome.
```
**r/devops** — same tool, lead with the Node/Python angle (nodejs18.x aws-sdk v2 break, python3.12
distutils). Link `/fix/` for the specific errors. Follow each sub's self-promo rules; if unsure,
post the tool as a comment on an existing AL2/EOL thread instead of a new post.

---

## 3. X / Twitter thread
```
1/ Amazon Linux 2 is EOL June 30. After that: no patches, no new AMIs, EKS node groups and launch
templates pinned to AL2 start rotting.

Free 30-second check on your own stack (runs in your browser, nothing uploaded):
https://eolkits.com/scan

2/ It reads your Terraform/SAM/CDK/serverless + package.json/requirements.txt and flags:
- AL2 AMIs
- deprecated Lambda runtimes (python3.9, nodejs18.x…)
- native-addon ABI breaks + Python 3.12 wheel issues
every finding cited to the AWS doc.

3/ If you want it fixed, not just found: MIT CLIs do the codemods + IaC patches + canary + rollback,
or a $299 audit / done-for-you PR (auto-refund if your CI fails). Sample report:
https://eolkits.com/audit/sample/

What does it catch on your configs? Tell me what it misses.
```
**LinkedIn:** the same, one paragraph, professional register, link `/scan`.

---

## 4. Cold outreach — precision, not blast

Claude can run these **GitHub code searches** to find *public* repos still exposed, then draft one
true, specific message per maintainer (one touch each, no follow-up if no reply):

```
# AL2 AMIs / extras in IaC
"amazon-linux-extras" path:*.sh
"amzn2-ami-hvm" path:*.tf
ImageId amzn2 path:*.yaml
# nodejs18.x (aws-sdk v2 break)
"nodejs18.x" path:serverless.yml
"runtime = \"nodejs18.x\"" path:*.tf
# python3.9
"Runtime: python3.9" path:template.yaml
"runtime = \"python3.9\"" path:*.tf
```
**Template (fill the bracket with something true and specific):**
```
Subject: [repo] still targets [nodejs18.x / AL2] — heads-up before the AWS cutoff

Hi [name] — noticed [repo]'s [serverless.yml / launch template] still uses [nodejs18.x], which AWS
blocks updates on at the Q1-2027 cliff (AL2 itself is EOL Jun 30). I ran a free scanner over the
public config and it flagged [N] spots: [eolkits.com/scan]. The MIT CLI will codemod most of it if
useful. No ask — just didn't want it to bite you in prod. Happy to share the full finding list.
```

---

## 5. Communities (evergreen, year-round)
Answer real questions on **StackOverflow / AWS re:Post / GitHub issues** that match the `/fix`
corpus (e.g. "No module named 'distutils'", "Cannot find module 'aws-sdk'", "amazon-linux-extras:
command not found"). Post the genuine fix; link the matching `/fix/<slug>` page only as a "more
detail" second reference. Max ~3/day. Value first, every time.

---

## Post-deadline pivot (Jul 1+)
The moment Jun 30 passes, swap the AL2 framing from "beat the deadline" to **"still on AL2? you're
now running unpatched in prod — here's the cleanup path."** Pain *increases* after the deadline;
the demand doesn't vanish, it changes shape. `/migrate/amazon-linux-2-eol/` and the deadline-reminder
capture keep working.
