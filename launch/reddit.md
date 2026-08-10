# Reddit pack — r/aws + r/devops (the missing Arm A variant)

**Built 2026-07-22 by Eve. Dates verified against AWS's live runtime doc.**
Reddit punishes self-promo harder than HN. Rules baked in: **disclose authorship in the body**,
lead with the deadline (the news), make the post useful even if nobody clicks the repo, and
**do not drop the same post in five subs the same hour** (crossposting spam = shadowban). Space
them ≥1 day apart, read each sub's self-promo rule first, and reply to comments like a person.

Verified dates (AWS `lambda-runtimes`, 2026-07-22):
- **Amazon Linux 2 (OS):** EOL **Jun 30, 2026 — passed.**
- **`nodejs20.x`:** deprecated Apr 30, 2026 → **block-create Feb 1, 2027 → block-update Mar 3, 2027.**
- **`nodejs16/18.x`, `python3.9`:** also **block-create Feb 1, 2027 / block-update Mar 3, 2027.**
- **`python3.10`:** deprecates **Oct 31, 2026** → block-create Feb 1, 2027.

---

## 1) r/aws — the flagship Reddit post

> r/aws allows "I built this" posts if they're substantive and disclosed. Use flair **"article"** or
> **"general"** (not "self-promotion" unless the rules force it — check the sidebar the day you post).
> Best window: Tue–Thu, ~9–11am ET.

**Title:**
```
Amazon Linux 2 is EOL and a big Lambda runtime wall lands Feb 1, 2027 — how I find what breaks
```

**Body:**
```
Two AWS deadlines worth a calendar entry if you run Lambda or EC2/ECS/EKS:

1. Amazon Linux 2 hit end-of-life on June 30, 2026. If you still have AL2 in a launch
   template, an EKS/ECS node group, a Beanstalk platform, or a Lambda base image, you're
   on unpatched infra now — no new AMIs, no security backports.

2. On Feb 1, 2027 AWS blocks *creating* new functions on nodejs16/18/20.x and python3.9/3.10
   at the same time; Mar 3, 2027 blocks *updating* them. After update-blocking lands you can't
   change those functions at all — the only path is a redeploy on a supported runtime. (Dates
   straight from AWS's runtime doc, which I'd double-check yourself before trusting a rando.)

The annoying part is never "which runtime" — the AWS Health email tells you that. It's *which*
of your functions across N accounts/regions are affected, and which upgrades actually break:
native wheels that don't exist on the new runtime, OpenSSL 3 hash changes, aws-sdk v2 being
unbundled, an IMDSv1 call that's now blocked. That's the part that eats a sprint.

Full disclosure: I got tired of doing this by hand and built an open-source thing for it
(MIT, links in a comment so this isn't just an ad). But even if you never touch it, the
approach that's worked for me:
- Grep your IaC for `runtime = "nodejs20.x"` / `python3.9` / `FROM amazonlinux:2` — it hides in
  SAM, CDK, Terraform, Serverless, Packer, and Ansible, so check all of them, not just one.
- Inventory live functions with `aws lambda list-functions` + a `--runtime` filter across regions.
- Do the upgrade behind a canary + alias so you can roll back on a CloudWatch alarm, because the
  breakage usually shows up at runtime, not at deploy.

Anyone already through the AL2 → AL2023 or Node 20 → 22 jump — what bit you that a checklist
wouldn't have caught? Trying to make sure the codemod rules cover the real-world failures.
```

**First comment (post it yourself, right after):**
```
The tool I mentioned: https://github.com/ntoledo319/EOLkits — three CLIs (one per deadline),
plus a no-signup browser scanner at https://eolkits.com/scan that classifies pasted IaC locally
(nothing uploaded). All MIT. There are paid tiers but the CLIs + scanner are free — clone and run.
Happy to answer anything about the codemod rules.
```

---

## 2) r/devops — softer, problem-first

> r/devops is stricter on promo. Lead almost entirely with the problem; keep the tool to one line
> at the end. Flair per sidebar.

**Title:**
```
PSA: AL2 is EOL and 5 Lambda runtimes hit block-create on the same day (Feb 1, 2027)
```

**Body:**
```
Batching two easy-to-miss AWS deadlines because they're going to generate a wave of "why did my
deploy start failing" tickets:

- Amazon Linux 2: EOL June 30, 2026 (passed). Unpatched from here on anything still pinned to it.
- Feb 1, 2027: AWS blocks new-function creation on nodejs16/18/20.x + python3.9/3.10 together.
  Mar 3, 2027: blocks updates to existing ones. python3.10 also formally deprecates Oct 31, 2026.

If you own a Lambda fleet, the work isn't the runtime bump — it's finding every function across
accounts/regions and catching the migrations that break at runtime (native modules, OpenSSL 3,
unbundled aws-sdk v2). Worth an audit now while it's a planned change instead of a Feb-2027 fire.

How are you all tracking runtime EOLs across a big fleet — tagging, a scheduled Config rule,
something homegrown? Curious what's actually holding up in prod.

(I maintain an open-source scanner/codemod set for exactly these if it's useful — link in comments,
not pasting it inline.)
```

**First comment:**
```
Link, since I kept it out of the post: https://github.com/ntoledo319/EOLkits (MIT). Browser
scanner (no signup): https://eolkits.com/scan. Genuinely more interested in how people track
this at scale — the tool's the easy part.
```

---

## Comment posture (both subs)
- Reply within the first 2–3 hours; Reddit ranking rewards early engagement.
- Answer the question first; link a doc only if asked. Never argue — "fair, I'll fix that" > defense.
- If a mod removes it as promo, don't repost — message the mod, ask what framing is allowed.
- Do NOT upvote-ring or ask friends to upvote. One honest post per sub, spaced out.

## Fire order (fits the LAUNCH-NOW sequence)
re:Post answers (today) → dev.to writeup → **Show HN (Tue–Thu AM)** → same day: X/LinkedIn →
**next day: r/aws** → day after: r/devops. Never same-hour crossposts.
