# 🚀 LAUNCH NOW — fire-ready pack (re-anchored post-AL2-EOL)

**Supersedes** `show-hn-final.md` (written for a June 12 window that passed; AL2 was "18 days away" — it's now 3+ weeks PAST).
**Built:** 2026-07-22 by Eve. **All dates verified against AWS's live runtime doc today.**

> ⚠️ **Credibility fix baked in:** the old assets said Lambda Node 20 blocks Aug 31 / Sep 30, 2026.
> AWS's current doc says `nodejs20.x` **block-create Feb 1, 2027 / block-update Mar 3, 2027.**
> The stale dates are ALSO live-wrong in `README.md` and on the site — fix before/with launch (see PRE-FIRE).

---

## ✅ Verified deadline table (AWS `lambda-runtimes` doc, fetched 2026-07-22)

| Thing | Deprecation | Block **create** | Block **update** |
|---|---|---|---|
| **Amazon Linux 2 (OS)** | **EOL Jun 30, 2026 — PASSED** | — | — |
| `nodejs16.x` | Jun 12, 2024 | **Feb 1, 2027** | **Mar 3, 2027** |
| `nodejs18.x` | Sep 1, 2025 | **Feb 1, 2027** | **Mar 3, 2027** |
| `nodejs20.x` | Apr 30, 2026 | **Feb 1, 2027** | **Mar 3, 2027** |
| `python3.9` | Dec 15, 2025 | **Feb 1, 2027** | **Mar 3, 2027** |
| `python3.10` | **Oct 31, 2026** | **Feb 1, 2027** | **Mar 3, 2027** |
| `python3.11` | Jun 30, 2027 | Jul 31, 2027 | Aug 31, 2027 |

**The story:** AL2 is already dead. Then on **Feb 1, 2027**, AWS blocks new-function creation on five legacy runtimes *at once* (Node 16/18/20, Python 3.9/3.10); Mar 3 blocks updates. Python 3.10 formally deprecates Oct 31, 2026. That's a wall coming for a huge share of real Lambda fleets.

---

## ✅ PRE-FIRE checklist — VERIFIED 2026-07-22 by Eve (all green; one deploy dependency noted)
HN/Reddit fact-check hard. Every claim below must resolve or get cut. Honesty rule: don't post what we can't back.
- [x] **Node 20 date fixed** → Feb 1 / Mar 3, 2027 across README, published blog (regenerated), `build.py`, both `lambda-lifeline` docs, and the re:Post answer bank. Verified against AWS's live runtime doc today. **Zero stale dates remain in any live-facing file.** ⚠️ *The fix is staged in the repo but the live site still shows old dates until deploy (owner's call).*
- [x] **Links verified** — all funnel pages 200 (`/scan /audit /pack /migrate /fix /verify /blog/… deprecations.ics`), repo 200, and `ntoledo319/EOLkits@v1` resolves on the remote (tag `c00f505`). ⚠️ The GitHub *Marketplace* listing URL 404s — the post correctly uses the `@v1` ref, so **don't link to a marketplace URL**.
- [x] **Receipts real AND clickable** — latest release (`v1.1.0`) carries Sigstore `.sig` signatures + CycloneDX SBOMs for all three kits; determinism CI runs each kit twice + `diff`s; audit SHA-256 verify page is live (200); codemods are property-tested (92 Python property/unit tests pass). Public benchmark (`BENCHMARK.md`) is real but modest (12 repos). Mutation/nightly workflows exist but aren't linked → leave those two out of the post.
- [x] **Scanner works + is date-correct** — `eolkits.com/scan` is 200 and live-shows `2027-02-01` (the tool was already corrected; only the marketing copy was wrong).
- [x] **Tests badge fixed** → real count is **168** (al2023-gate 48, python-pivot 44, grace-api 36, runner 8, lambda-lifeline 24, worker 8), re-run on Linux today. Badge + breakdown updated from stale 172.

---

## 1) SHOW HN — the flagship (never actually fired yet)

**Title** (≤80 chars):
```
Show HN: EOLkits – CLIs for AWS runtime deprecations (Amazon Linux 2 now EOL)
```
**Submission URL:**
```
https://github.com/ntoledo319/EOLkits
```
**Body:**
```
Amazon Linux 2 reached end-of-life on June 30, 2026 — about three weeks ago. If you
still have AL2 in a launch template, an EKS/ECS node group, a Beanstalk platform, or a
Lambda base image, you're now running unpatched: no new AMIs, no security backports.

And the next Lambda cliff is a big one. On Feb 1, 2027 AWS blocks *new-function creation*
on nodejs16/18/20.x and python3.9/3.10 simultaneously; Mar 3, 2027 blocks *updates*. Once
update-blocking lands you can't change those functions at all — the only path is a full
redeploy on a supported runtime, or the code is frozen. (Dates from AWS's own runtime doc.)

I built EOLkits: one CLI per deadline.

  al2023-gate      Amazon Linux 2 -> AL2023          (OS EOL Jun 30, 2026, passed)
  python-pivot     Lambda Python 3.9/3.10 -> 3.12    (block-create Feb 1, 2027)
  lambda-lifeline  Lambda Node 16/18/20 -> 22        (block-create Feb 1, 2027)

Each kit does the same five things: scan the account for affected resources, run
mechanical codemods (dry-run by default; --apply writes), patch IaC across
SAM / CDK / Terraform / Serverless / Packer / Ansible, generate a staged canary plan
with auto-rollback hooks, and produce a tested rollback script. Everything runs offline
against fixtures so you can evaluate before pointing it at a real account.

The parts I cared about getting right:
- Deterministic output — CI runs each kit twice on the same inputs and fails on any diff.
- Audit reports embed a SHA-256 of the inputs + the rule-pack version, with a verify URL.
- Codemods are property-tested.
- Releases are Sigstore-signed with a CycloneDX SBOM attached (github.com/ntoledo319/EOLkits/releases).
- Everything is dry-run by default; nothing writes without --apply, and every change has
  a generated rollback path.

The free GitHub Action runs the dry-run pass on PRs and comments findings. There's also a
zero-signup browser scanner (eolkits.com/scan) that classifies your config locally. Paid
tiers exist (a $299 cited audit PDF, a $1,499 done-for-you migration PR) but the CLIs and
scanner are MIT and free — clone and run them yourself.

Why I built it: every few months AWS emails "your runtime is deprecated," and the fix is
rarely one line — native wheels that don't exist for the new runtime, OpenSSL 3 hash
changes, an iptables rule that breaks on nftables, an IMDSv1 call that's now blocked.
CloudQuery gives inventory; Migration Hub is lift-and-shift; aws-samples gives snippets.
I couldn't find one tool that did scan + codemod + IaC patch + canary + rollback for a
single specific deprecation, end to end. So each kit is scoped tight: one runtime, one
deadline, one job.

Repo:      https://github.com/ntoledo319/EOLkits
Action:    ntoledo319/EOLkits@v1
Scanner:   https://eolkits.com/scan   (no signup, nothing uploaded)

Open to feedback on the codemod rules especially — if you've done one of these migrations
and a kit missed something, that's the most useful thing you can tell me.
```
> Note: I trimmed the Sigstore/SBOM/nightly-benchmark/mutation-testing bullets from the old
> draft into one honest "parts I got right" block. Re-add specific receipts **only** after
> PRE-FIRE confirms each is real — with a link. Unbacked receipts are how HN launches die.

**Timing:** Tue–Thu, **8:15–9:15 a.m. ET**. Submit, then stay in-thread the first ~6 hours.
**Comment posture:** one reply per top-level comment, lead with the answer, link a doc only
on second mention. Don't seed, don't pre-stake, don't argue. "Good catch, fixing" > defense.

---

## 2) CONTENT INVENTORY (as of 2026-07-22 — most already built)
- ✅ **Reddit r/aws + r/devops** — `launch/reddit.md` (built today; disclosed-authorship, correct dates).
- ✅ **dev.to** — 7 posts in `launch/distribution/devto/` (AL2, Node20, Py3.12/3.13, SDK-v2, OpenSSL3, real-deadline).
- ✅ **X thread** — `launch/distribution/x/threads.md`; **LinkedIn** — `launch/social.md`.
- ✅ **AWS re:Post** — answer banks `launch/distribution/repost-answers*.md` + `ledger/internal/thread-answers.md` (dates fixed).
- ✅ **Arm B** — fix-first lead list `launch/distribution/email/targets.md` (refreshed today; honest verdict: low-volume side bet).
- ⚠️ All the above now carry corrected Node-20 dates. The only genuinely *new* build needed was Reddit — done.

---
*Fire order, once PRE-FIRE is green: re:Post answers (today) → dev.to writeup → Show HN (Tue–Thu AM) → Reddit + X/LinkedIn same day to amplify. Arm B outreach runs in parallel, independent of all social accounts.*
