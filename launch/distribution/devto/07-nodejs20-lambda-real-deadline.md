---
title: The AWS Lambda Node.js 20 deadline everyone gets wrong (it's not September 2026)
canonical_url: https://eolkits.com/migrate/lambda-node.js-20-phase-1/
description: Half the internet says AWS blocks nodejs20.x in August/September 2026. AWS delayed it. The real block dates are Feb 1 and Mar 3, 2027 — here's the authoritative timeline and why the confusion exists.
tags: aws, lambda, node, serverless
---

If you searched "nodejs20.x Lambda deadline" recently, you probably read that AWS blocks new function creation on **Aug 31, 2026** and updates on **Sep 30, 2026**. A lot of blog posts say exactly that.

Those dates are wrong now. AWS moved them.

## The actual AWS schedule

Straight from the [AWS Lambda runtimes table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html):

| Phase | nodejs20.x date |
|---|---|
| Deprecation (security patches stop) | **Apr 30, 2026** — already passed |
| Block function **create** | **Feb 1, 2027** |
| Block function **update** | **Mar 3, 2027** |

So the hard cliffs are in **Q1 2027**, not late 2026.

## Why so many posts say September 2026

AWS's *default* deprecation policy is mechanical: block **create** at least 30 days after deprecation, block **update** at least 60 days after. Apply that to the Apr 30, 2026 deprecation and you get roughly end-of-August and end-of-September 2026 — which is exactly what a wave of posts computed and published.

But AWS added a note to that same policy page:

> "For some runtimes, AWS is delaying the block-function-create and block-function-update dates beyond the usual 30 and 60 days after deprecation… in response to customer feedback to give you more time to upgrade your functions."

`nodejs20.x` is one of those runtimes. AWS pushed its blocks into a **synchronized Q1-2027 cluster**. The posts that predate that change never got corrected.

## Don't relax — "deprecated" already bit you

The block dates being in 2027 does **not** mean you're fine until 2027. `nodejs20.x` was **deprecated on Apr 30, 2026**, which already means:

- **No more security patches** to the runtime. New CVEs in the runtime or its OS won't be fixed.
- **No technical support** for functions on it.
- Deprecated runtimes are provided "as-is" and can degrade — including things like **certificate expiry** that silently break a function that was running fine.

You keep the ability to invoke and (until the block dates) update — but you're running unpatched. That's the real reason to move now, not the block date.

## The bigger trap: everything blocks on the same two days

The Q1-2027 cluster isn't just Node 20. These all hit **block-create Feb 1, 2027** and **block-update Mar 3, 2027**:

`nodejs16.x` · `nodejs18.x` · `nodejs20.x` · `python3.8` · `python3.9` · `python3.10` · `ruby3.2` · `dotnet6`

If your account has a mix of these — most do — a single date freezes a large slice of your fleet at once. That's a capacity-planning problem you want to find in July, not in February.

## What to actually do

1. **Inventory now.** Find every function on a runtime in that cluster, across regions.
2. **Upgrade off, don't wait for the block.** `nodejs20.x` → `nodejs22.x` (LTS, maintained into 2027). The mechanical breakage is well-known: `aws-sdk` v2 no longer bundled, import `assert` → `with`, native-addon ABI rebuilds, OpenSSL 3, `crypto.createCipher` removed.
3. **Stage it.** Canary a few functions with a CloudWatch alarm and a rollback path before you touch the rest.

I maintain a free, open-source CLI (`lambda-lifeline`) that scans every account/region for at-risk runtimes with the **correct** dates, codemods the mechanical breakage, patches your IaC, and stages a canary with rollback. There's also a **free browser scanner** that flags at-risk config in ~30 seconds — nothing uploaded: **[eolkits.com/scan](https://eolkits.com/scan)**.

Authoritative per-runtime timeline (kept in sync with the AWS table): **[eolkits.com/migrate/lambda-node.js-20-phase-1](https://eolkits.com/migrate/lambda-node.js-20-phase-1/)**.
