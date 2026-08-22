---
title: "Why did my AWS deploy break with zero code changes?"
canonical_url: https://eolkits.com/eol-checker/
description: A CI run that was green last week is red today and nobody touched main. Most of the time this is a calendar cutoff, not a bug — here's how to tell which one hit you and where the non-calendar causes hide.
tags: aws, lambda, devops, serverless
---

> [!CAUTION]
> Archived launch copy — do not publish or reuse. This draft predates the current
> bounded browser scanner, telemetry disclosure, lifecycle-date corrections, and
> readiness-gated paid scope; claims and `eolkits.com` links below may be false or stale.
> Use the [current README](../../../README.md) and
> [verified public site](https://ntoledo319.github.io/EOLkits/) instead.

Every other class of "it broke" starts with a diff. This one doesn't. `git log` shows nothing since last week, CI was green then, it's red now, and the error doesn't look like anything your team wrote.

That's the tell. A deploy that breaks with zero code changes is almost always one of two things: a fixed AWS calendar cutoff you crossed passively, or a dependency/base-image that moved out from under you without a corresponding commit in your repo. Neither shows up in `git blame`. Here's how to tell them apart.

## First: is it a fixed AWS date?

Two calendar cutoffs cover almost every "nothing changed but it broke" report on Lambda and EC2/ECS/EKS right now.

**Lambda runtime blocks.** AWS enforces these on the account, not on your deploy history — the API call itself gets rejected once the date passes, independent of when you last touched the function. As of today, `nodejs16.x`, `nodejs18.x`, `nodejs20.x`, `python3.8`, `python3.9`, and `python3.10` all share the same two dates:

- **Block function *create*: Feb 1, 2027** — `CreateFunction` (or a Terraform/CDK/SAM deploy that provisions a *new* function or alias) on one of these runtimes is rejected outright after this date.
- **Block function *update*: Mar 3, 2027** — after this, `UpdateFunctionCode`/`UpdateFunctionConfiguration` on an *existing* function using one of these runtimes is rejected too. The function keeps running and keeps invoking; you just can't ship a change to it anymore.

(`python3.11` is on a later cluster: block-create Jul 31 2027, block-update Aug 31 2027 — don't assume every runtime lines up with the Q1-2027 dates above.)

If your error is coming back from the Lambda control plane itself — not from inside your code, not from a cold start — rather than a runtime crash, this is almost certainly it. Check the runtime string on the function the deploy touched.

**Amazon Linux 2 end of life.** AL2 reached end of standard support **June 30, 2026** — already past. This one doesn't reject an API call the way the Lambda blocks do; instead, AL2 stops getting security patches, and separately, any user-data or AMI-bake step that calls `yum`/`amazon-linux-extras` starts failing as AL2's package repos and Extras Library shift under it. If the failure is at *instance boot* or *AMI bake* time rather than at application runtime, check the base AMI before anything else.

Cross-check either of these in 10 seconds against the same table AWS enforces — paste your runtimes or click the ones you use in the free **[EOL checker](https://eolkits.com/eol-checker/)** (client-side, nothing uploaded); it flags exactly which cutoff applies and how many days you have left.

## If it's not a fixed date: three things that move without a commit

Not every silent break is calendar-driven. These three change underneath you with no corresponding line in your diff:

1. **An unpinned or `:latest`-tagged base image moved forward.** A Docker base image reference that isn't pinned to a digest can resolve to a newer patch build on a fresh pull — bringing a newer OS or language patch version than what last built successfully, with nothing in your Dockerfile diff to show for it.
2. **A transitive dependency resolved differently.** A fresh `npm ci` or `pip install` in CI re-resolves anything not exactly pinned. A transitive package (not your direct requirement) picking up a new minor version can drop or rename an API your code calls indirectly — again, invisible in your own diff.
3. **An IaC provider bumped its own defaults.** A routine `terraform init -upgrade` or CDK library bump can change what a resource defaults to when you didn't explicitly set it — including, on Lambda resources, which runtime a construct assumes if a version pin was left implicit.

None of these are bugs in the classic sense — they're all "something you depend on changed, and your repo correctly recorded that you didn't ask it to stay still."

## Narrowing it down

1. **Read where the error actually comes from.** A rejection with no invocation ever happening, straight from the deploy/API call, points at a Lambda block date. A failure during instance boot or AMI bake points at AL2. A runtime crash after a successful cold start points at a stdlib/dependency change — see the [runtime-upgrade error map](https://eolkits.com/fix/) for the exact error text against the specific fix.
2. **Check what's actually pinned.** `git diff` won't show you a moving base image tag or an unpinned transitive dependency — `docker inspect` on the built image, or a fresh `npm ls`/`pip freeze` diffed against your last known-good build, will.
3. **If you're not sure which functions or AMIs are even exposed**, the free **[scanner](https://eolkits.com/scan)** checks a whole account in about 30 seconds and flags both the calendar-cutoff risk and known dependency landmines before the next deploy trips one — nothing uploaded. I maintain it, disclosing that plainly since it's the one link here that isn't a diagnostic tool or a fix page.
