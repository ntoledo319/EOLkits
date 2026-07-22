# 🔥 FIRE BATCH — the one-sitting launch runbook

**For:** Nick · **By:** Eve · **2026-07-22**
**What this is:** every post, in order, ready to paste. No file digging. ~15 min of your time, spread over ~5 days.
**Why this order:** it leads with the channels that DON'T gate on cold-account karma (re:Post, dev.to) and
holds the Show HN until your HN account is warm (it's karma-1 right now → a cold Show HN gets auto-buried).

**Money rail is confirmed green:** Stripe ✅ · PDF generation ✅ · email delivery ✅. Every post points at the
free scanner (`eolkits.com/scan`) or the repo. Free usage → funnel → $299 audits. That rail works *today.*

---

## DAY 1 — the two no-gate channels (do both today, ~8 min)

### ① AWS re:Post — highest-intent buyers (you have an AWS account; zero friction)
People asking these questions have the pain *right now* and are actively searching. You've posted here before.
1. Go to https://repost.aws and search: **"Amazon Linux 2 end of life"**, then **"Lambda nodejs20 deprecation"**, then **"python3.9 lambda runtime"**.
2. Find 2–3 *unanswered or thinly-answered* questions from the last few weeks.
3. Paste the matching answer from **`launch/distribution/repost-answers.md`** (+ `-batch2.md`) — they're written help-first, dates already correct. Tweak the first line to match their specific question.
4. Only link the free tool if it genuinely answers them. Answer the question first.

### ② dev.to — publish the anchor article (free account, no karma gate)
The evergreen SEO asset every other post links back to.
1. If you don't have a dev.to account, make one (free, 2 min, GitHub login).
2. New post → paste the body of **`launch/distribution/devto/08-al2-now-eol-find-what-breaks.md`** (title + tags are in the frontmatter). Flip `published: false` → publish.
3. Grab the published URL — you'll drop it into the Reddit/X posts below.

---

## DAY 2 — r/aws (Tue–Thu, ~9–11am ET)
r/aws allows disclosed "I built this" posts. Flair: **article** or **general**.

**Title:**
```
Amazon Linux 2 is EOL and a big Lambda runtime wall lands Feb 1, 2027 — how I find what breaks
```
**Body:** paste the r/aws body from **`launch/reddit.md` §1** (it's ready; discloses authorship, keeps the repo link out of the post).
**Immediately after posting, add the first comment** (also in `reddit.md §1`) with the repo + scanner links.
Reply to comments within 2–3 hrs, answer-first, never argue.

---

## DAY 3 — r/devops (softer, problem-first)
Stricter on promo — the post is 95% problem, tool is one line at the end.

**Title:**
```
PSA: AL2 is EOL and 5 Lambda runtimes hit block-create on the same day (Feb 1, 2027)
```
**Body + first comment:** paste from **`launch/reddit.md` §2**.

> Never crosspost the same hour. r/aws and r/devops are ≥1 day apart on purpose.

---

## ALONGSIDE (any day) — your own feeds, low effort
- **LinkedIn** (where the $1,499-pack buyer reads): paste the single post from **`launch/social.md` § LinkedIn**.
- **X**: post the 2-post thread from **`launch/social.md` § X** (skip old "Post 3" — that was the HN URL reply).

---

## THE HN PLAN (deferred, on purpose)
Your HN account `toledonick` is **karma 1**. A Show HN from it today ≈ auto-`[dead]`. So we warm it first:
- Over the next several days, drop **2–3 genuinely useful comments** on active r/aws-style HN threads (AWS, Lambda,
  DevOps topics). I'll hand you the comment drafts. Goal: get to a few dozen karma + some account age.
- Once it's not radioactive, we fire the Show HN from **`launch/LAUNCH-NOW-2026-07-22.md`** into a Tue–Thu 8:15–9:15am ET window — for a *real* shot, not a wasted one.

---

## RULES (baked in, don't skip)
- **No upvote rings, no asking friends to upvote, no same-hour crossposts.** One honest post per place. (TOS-clean = compounding; a shadowban = zero.)
- Disclose authorship everywhere. Lead with the deadline (the news), not the product.
- Answer questions first; link second. "Fair, I'll fix that" beats defending.

---

## AFTER YOU FIRE — watch this
`eolkits.com/status` → first `checkout_click` = a buyer is close; first `audits_delivered > 0` = **first dollar.**
Ping me the moment anything ticks and I'll help you work it (thread replies, follow-ups, converting interest).

*The content is done and verified. This is purely your 15 minutes of clicking "post." That's the whole gap now.*
