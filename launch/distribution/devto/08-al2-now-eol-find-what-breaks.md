---
title: "Amazon Linux 2 is now EOL. Here's how to find what it breaks in your AWS account — free"
published: false
tags: aws, devops, lambda, security
canonical_url: https://eolkits.com/blog/amazon-linux-2-eol-what-breaks
---

Amazon Linux 2 reached end-of-life on **June 30, 2026**. It's past now — which means it stopped being a calendar problem and started being a running one: no new AMIs, no security backports, and AWS's clock has moved on to the next set of deadlines. If you still have AL2 anywhere, you're carrying unpatched infrastructure right now.

The tricky part isn't knowing AL2 is EOL. It's that "AL2" is hiding in more places than the obvious EC2 fleet, and the *next* wave of deadlines is easy to misread. Here's how to find your actual exposure in about 30 seconds, for free, and what the fix really involves.

## Where AL2 is actually hiding

Most teams check their EC2 launch templates and call it done. The blast radius is wider:

- **EKS / ECS node groups** still pinned to AL2 AMIs
- **Elastic Beanstalk** platform branches built on AL2
- **Lambda** runtimes and container base images that sit on AL2 under the hood — Java 8/11/17, `python3.10`, `python3.11`, and `provided.al2`
- **Packer / Ansible** pipelines that bake `amazonlinux:2`
- **cloud-init / launch-template user-data** that assumes `yum`, `amazon-linux-extras`, `ntpd`, or `iptables` — all of which change or disappear on AL2023

Any one of those keeps you on a dead OS while everything looks green in the console.

## The next cliff people misread

There's a widely-repeated claim that Lambda `nodejs20.x` gets blocked in **Sep 30, 2026**. It's stale. Per [AWS's own runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), the real dates are later — and they land as one big simultaneous wave:

| Runtime | Block **create** | Block **update** |
|---|---|---|
| `nodejs16.x` / `nodejs18.x` / `nodejs20.x` | **Feb 1, 2027** | **Mar 3, 2027** |
| `python3.9` / `python3.10` | **Feb 1, 2027** | **Mar 3, 2027** |

On **Feb 1, 2027**, AWS stops letting you *create* new functions on five legacy runtimes at once; on **Mar 3, 2027**, it stops letting you *update* existing ones. After block-update, a function on those runtimes is frozen — you can't ship a change to it at all. The only way out is a full redeploy on a supported runtime. Better to find those functions now than the week you need to hotfix one.

## Find your exposure in 30 seconds (free, nothing uploaded)

I've been building a set of open-source (MIT) kits for exactly these deadlines. The fastest way to see where you stand is the browser scanner — paste a config, it classifies everything client-side, nothing leaves your machine:

**→ https://eolkits.com/scan**

If you'd rather run it against a real account from your terminal, the CLIs are free and on GitHub:

```bash
git clone https://github.com/ntoledo319/EOLkits.git
cd EOLkits/kits/al2023-gate
pip install -e .

# Scan an inventory offline first (no AWS creds needed)
al2023-gate scan --fixture test/fixtures/inventory.json --format table

# Or point it at your account (read-only) via boto3
al2023-gate scan --format table
```

There are three kits, one per deadline:

- `al2023-gate` — Amazon Linux 2 → AL2023
- `python-pivot` — Lambda Python 3.9/3.10 → 3.12
- `lambda-lifeline` — Lambda Node 16/18/20 → 22

Every finding is cited to an AWS primary source, so you can check the reasoning rather than trust a score.

## Why the fix is rarely one line

The reason these migrations get deferred until they're on fire is that the diff is almost never "bump the version." Real AL2 → AL2023 work runs into:

- `yum` → `dnf`, and `amazon-linux-extras` simply doesn't exist anymore
- packages that were retired or renamed between the two OSes
- `iptables` rules that need to move to `nftables`
- OpenSSL 1.0 → 3.x, which changes hash behavior your code may have depended on
- `ntpd` → `chrony`, cloud-init schema changes, IMDSv1 calls that are now blocked

So each kit does more than detect: it runs mechanical codemods (dry-run by default — nothing writes without `--apply`), patches IaC across SAM / CDK / Terraform / Serverless / Packer / Ansible, generates a staged canary plan, and writes a rollback script. You can evaluate the whole thing offline against fixtures before it ever touches AWS.

## If you'd rather not do it yourself

The CLIs and the scanner are free and MIT — genuinely, clone them and go. If you want the work done *for* you, there's a paid tier: a $299 audit report that scores every finding by severity × blast-radius with a roll-forward plan, or a $1,499 done-for-you migration PR opened straight on your repo. But you don't need either to find out what's exposed — start with the free scan and see how bad it is first.

The deadline that already passed is the one worth checking today.

*Dates in this post are from AWS's [Lambda runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) and the [Amazon Linux 2 FAQ](https://aws.amazon.com/amazon-linux-2/faqs/), verified 2026-07-22.*
