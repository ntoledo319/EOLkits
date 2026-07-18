# The AWS Runtime & OS End-of-Life Migration Playbook

*A single, opinionated guide to every active AWS EOL deadline that hits Lambda and EC2/EKS/ECS/Beanstalk workloads,
paired with three free command-line tools that do the mechanical parts of the migration for you.*

Maintained by [EOLkits](https://eolkits.com). Dates below are pulled directly from the AWS Lambda runtime
deprecation table (`docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html`) and the Amazon Linux 2 FAQ
(`aws.amazon.com/amazon-linux-2/faqs/`) — the same data that drives the live deadline calendar at
[eolkits.com/status](https://eolkits.com/status). If AWS revises a date, the calendar updates; this document is a
snapshot as of **2026-07-18**.

---

## 1. The one thing to understand: the Q1-2027 block cluster

In 2026 AWS **delayed** the runtime blocks it originally scheduled for late 2026, consolidating most of them into a
single synchronized window:

| Milestone | Date | What actually happens |
|---|---|---|
| **Block new function/layer creation** | **2027-02-01** | `CreateFunction` / `CreateLayerVersion` on a deprecated runtime starts failing |
| **Block updates to existing functions** | **2027-03-03** | `UpdateFunctionConfiguration` / `UpdateFunctionCode` on a deprecated runtime starts failing |

Runtimes in this cluster: **Node.js 18, Node.js 20, Python 3.8, Python 3.9, Python 3.10.** Existing functions keep
*running* after these dates — they just become permanently frozen: no config changes, no code deploys, no rollback
if something else breaks. A lot of blog posts and even some internal wikis still cite AWS's *original* 2026 dates,
which AWS superseded — always check the live AWS table, not a cached blog post, before you plan around a date.

Two additional deadlines that are **not** part of that cluster and already active:

| Deprecation | Deadline | Status |
|---|---|---|
| **Amazon Linux 2 standard support** | **2026-06-30** | **Already passed.** AL2 is unpatched today — no CVE backports, no new AMI publishes. |
| **Python 3.11 Lambda block** | Create 2027-07-31 / Update 2027-08-31 | Deprecated 2027-06-30, on its own later schedule |

---

## 2. Amazon Linux 2 → AL2023 (`al2023-gate`)

**Why now:** AL2's standard support ended 2026-06-30. Every day since, AL2 instances have been accumulating
unpatched CVEs. There is no more countdown — this is current exposure, not a future deadline.

**What breaks on the move to AL2023:**
- `yum` → `dnf` (yum is gone)
- `amazon-linux-extras` is not available
- `ntpd` → `chronyd`
- `iptables` → `nftables`
- Python 2 is not available

**Migration steps:**
```bash
al2023-gate scan       # inventories every AL2 resource: EC2, launch templates, EKS, ECS, Beanstalk
al2023-gate remap      # translates your yum package list to dnf equivalents (~50-entry curated table)
al2023-gate packer     # emits a ready-to-build Packer HCL template for a fresh AL2023 AMI
al2023-gate cloudinit  # diffs your cloud-init/user-data scripts for known AL2023 breakage
al2023-gate ansible    # rewrites Ansible playbooks: yum→dnf, python2→3, extras removal
al2023-gate runbook    # emits a resource-type-specific runbook (ASG / EKS / ECS / Beanstalk)
```
Run `scan` first against live AWS (needs `boto3` + standard credentials) or in fixture mode for an offline dry run.
The `runbook` output is written for whichever resource type dominates your account, so you get one relevant plan
instead of a generic wall of text.

---

## 3. Python Lambda → 3.12 (`python-pivot`)

**Who this hits:** any account running `python3.8`, `python3.9`, or `python3.10` Lambda functions. All three share
the same Q1-2027 block window (create 2027-02-01 / update 2027-03-03); 3.8 and 3.9 are already fully deprecated
(no patches since 2024-10-14 and 2025-12-15 respectively).

**What breaks on the move to 3.12:**
- `distutils` and `imp` are removed
- `collections.Mapping`-style imports (must use `collections.abc`)
- Native-wheel ABI changes — a dependency built for `cp39`/`cp310` may not have a `cp312` wheel yet

**Migration steps:**
```bash
python-pivot scan      # finds every Python Lambda function + its declared runtime, across regions
python-pivot codemod   # rewrites the known 3.8→3.12 breakages in your source
python-pivot audit     # checks 30+ common native-wheel dependencies for cp312 availability
python-pivot iac       # patches the runtime string in SAM / CDK / Terraform / Serverless Framework configs
python-pivot deploy     # staged canary deploy — refuses to run without a CloudWatch alarm ARN
python-pivot rollback   # automatic rollback if the canary's alarm fires
```
The safety net is the point: `deploy` will not proceed without an alarm ARN, so a bad runtime upgrade can't silently
eat your error budget at 3 a.m. — it rolls back on its own.

---

## 4. Node.js Lambda → 22 (`lambda-lifeline`)

**Who this hits:** any account running `nodejs18.x` or `nodejs20.x` — both in the Q1-2027 block cluster. `nodejs18.x`
in particular is still one of the most common runtimes in production Lambda fleets.

**What breaks on the move to Node 22:**
- `aws-sdk` v2 is not bundled — you need `@aws-sdk/*` v3 modular clients
- Native addons (`sharp`, `bcrypt`, `better-sqlite3`, etc.) must be rebuilt for the Node 22 ABI
- OpenSSL 3 behavior changes (hash/digest defaults, `DECODER` routine errors)
- CA-certificate handling changes in some HTTPS client code

**Migration steps:**
```bash
lambda-lifeline scan       # inventories Lambda functions on deprecated Node runtimes
lambda-lifeline codemod    # rewrites aws-sdk v2 → v3 modular imports
lambda-lifeline audit      # checks native-binary dependencies for Node-22 ABI compatibility
lambda-lifeline iac        # patches IaC runtime declarations
lambda-lifeline canary     # staged deploy gated on a CloudWatch alarm
lambda-lifeline rollback   # rollback on alarm trip
```
See `docs/ROLLBACK.md` in the kit for the exact rollback mechanics if you want to understand what the canary gate
does before you point it at production.

---

## 5. A general order of operations (all three kits)

1. **Scan first, everywhere.** Run the relevant `scan` command in every region you use — deprecated resources hide
   in regions nobody remembers enabling.
2. **Audit dependencies before you touch code.** The `audit` commands catch the native-wheel/ABI problem *before*
   you've rewritten anything, which is the failure mode that actually causes outages (a working codemod deployed on
   top of a binary that silently doesn't exist for the new runtime).
3. **Generate the IaC patch, review it like a PR, then apply it.** Don't hand-edit Terraform/CDK/SAM/Serverless
   configs to match — let the tool produce the diff so it's consistent across every resource.
4. **Never skip the canary + alarm.** The single most common bad outcome in a runtime upgrade is "the code was fine,
   the deploy wasn't." All three kits gate their deploy commands on an alarm ARN for exactly this reason.
5. **Re-run `scan` after you think you're done.** It's the same command either way, and confirming zero hits is the
   only way to close the loop with confidence.

---

## 6. If you'd rather not do this yourself

The three CLIs in this bundle do the mechanical work. If you want the scan + audit + runbook output already run
against your account, hash-anchored into a report, and delivered as a PDF — that's the **$299 Audit** at
[eolkits.com/audit](https://eolkits.com/audit). If you want an actual PR opened on your repo with the codemods and
IaC patches applied, gated on your CI passing, refunded automatically if it doesn't — that's the **$1,499 Migration
Pack** at [eolkits.com/pack](https://eolkits.com/pack). Neither is required to use this bundle; the CLIs are yours,
MIT-licensed, forever.

---

*Provenance: this playbook and the accompanying tooling were built with AI assistance (Claude) under human
direction and review. See `ATTRIBUTIONS.md` for the full dependency and license disclosure.*
