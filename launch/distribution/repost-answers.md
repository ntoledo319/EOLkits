# Batches 1–2 below: ARCHIVED — DO NOT POST

Targets and answers in Batches 1 and 2 are stale (drafted 2026-07 to 2026-08-22) and require fresh manual
policy and fact review before use. **Batch 3, appended 2026-08-23 at the bottom of this file, is fresh and
ready to post** — it was drafted from questions found via live search on drafting day, with URLs and dates
verified against this cycle's established facts. Re-verify each URL still resolves and still lacks a
better answer before pasting, since time may have passed since drafting.

# Historical answer research

Each item below is a **real person asking about this exact EOL right now**. Posting a genuinely useful answer
(with the tool mentioned once, disclosed) is the closest-to-a-buyer, $0, TOS-clean move that exists — and it's a
**one-time ~10–15 min** effort, not ongoing. The agent drafted these (it may not post as you); **you paste them.**

**Keep it clean & on-brand (so it helps, doesn't get flagged):**
- Answer the question **substantively first**; mention the free tool **once**, as a resource, and **disclose** you maintain it.
- **Do not paste the same text twice** — re:Post / Stack Overflow flag duplicate self-promotion. Each answer below is already unique.
- Use the AWS-official dates in these drafts (many blogs are stale — that's part of the value you're adding).
- **Links:** `/scan/` and `/amazon-linux-2-eol-checklist/` and `/fix/` are **live now**; `/eol-checker/` goes live on the next deploy (tonight) — if you post before then, drop that one link.

---

## 1 — AWS re:Post: "Amazon Linux 2 End of Life Migration"
**Post at:** https://repost.aws/questions/QUjhyVpUEPShyFSWrWT3mICw/amazon-linux-2-end-of-life-migration

> Amazon Linux 2 reached end of **standard support on June 30, 2026** — it no longer receives security patches, so the priority is getting off it (AWS's paid Extended Support is only a stopgap). The target is **Amazon Linux 2023**, and the things that actually break in practice are:
>
> - **Package manager:** `yum` → `dnf`. `amazon-linux-extras` is gone — packages are now default, version-namespaced (`dnf install python3.11`, `nginx1.24`), or in **SPAL** (which replaces EPEL).
> - **Time sync:** `ntpd` → `chronyd`.
> - **Firewall:** the `iptables-services` unit isn't installed by default — AL2023 uses **nftables**.
> - **Python 2** isn't available at all.
> - **cloud-init / user-data** written for AL2 often fails on first boot for the reasons above.
>
> A safe path: (1) snapshot/AMI first; (2) rebuild your base AMI on AL2023 (Packer helps); (3) port user-data + Ansible/config; (4) canary a small % behind a health check before the whole fleet; (5) keep a rollback AMI.
>
> To find your exposure quickly, I maintain a **free, open-source** scanner + browser tool (no signup, nothing uploaded) that flags AL2 AMIs/user-data and the specific breakages, plus a step-by-step AL2→AL2023 checklist: https://eolkits.com/scan/ and https://eolkits.com/amazon-linux-2-eol-checklist/ . *(Disclosure: I built these; the CLIs are MIT on GitHub.)* If you hit a specific error there are per-error fix pages (e.g. `dnf: Unable to find a match`).

---

## 2 — AWS re:Post: "AWS Lambda Python runtime 3.9 EoL"
**Post at:** https://repost.aws/questions/QUwvZZcO78S2iFe9UF6rK4nw/aws-lambda-python-runtime-3-9-eol

> Worth clearing up the dates first, because they've moved and most blog posts are stale: `python3.9` was **deprecated on 2025-12-15** (no more security patches). AWS originally set the create/update block dates for early 2026, then **delayed them** — per the current [AWS Lambda runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) the block-create date is **2027-02-01** and block-update is **2027-03-03**. Since AWS has moved these before, treat that table as the source of truth — but either way it's already unpatched, so migrate now.
>
> Target is **python3.12** (3.13 is available). The breakages that actually bite on 3.9 → 3.12:
> - `distutils` and `imp` are **removed** (`ModuleNotFoundError`) — use `setuptools` / `importlib`.
> - `collections.Mapping` etc. moved to `collections.abc`.
> - **Native wheels:** anything with C extensions needs a `cp312` wheel built for Amazon Linux 2023 (glibc), or you get an import error at cold start.
> - `datetime.utcnow()` is deprecated.
>
> Find every function on 3.9 across regions (Trusted Advisor's "Lambda Functions Using Deprecated Runtimes" check, or `aws lambda list-functions --query "Functions[?Runtime=='python3.9']"`), fix the code, then update the runtime with a canary + a CloudWatch alarm to auto-rollback.
>
> I maintain a **free, open-source** CLI + browser checker that scans for exactly these and codemods the mechanical parts: https://eolkits.com/scan/ . *(Disclosure: I built it — MIT.)* There are also fix pages for the specific errors (e.g. `No module named 'distutils'`).

---

## 3 — AWS re:Post: "Amazon Linux 2 motd says EOL is 2025-06-30"
**Post at:** https://repost.aws/questions/QU8_7ivy19Q7Wq3CKUE5b7Jw/amazon-linux-2-motd-says-eol-is-2025-06-30

> That motd is stale — AWS **extended** Amazon Linux 2's end of life. The old date was **2025-06-30** (what your motd shows); the final date was **June 30, 2026**, and it has now passed, so AL2 is out of standard support and no longer getting patches. AWS's announcement: https://aws.amazon.com/blogs/aws/update-on-amazon-linux-2-end-of-life/ .
>
> Practically: if you're still on AL2 you're now unpatched. Options are AWS's **paid Extended Support** (a bridge, not a fix) or migrating to **Amazon Linux 2023** (the real move) — the main gotchas are `yum`→`dnf`, `amazon-linux-extras` gone (use dnf/SPAL), `ntpd`→`chronyd`, and nftables instead of the iptables service. A **free** browser tool to check your specific exposure (nothing uploaded): https://eolkits.com/scan/ . *(Disclosure: I maintain it.)*

---

## Optional next targets (search these, answer only if genuinely helpful)
- Stack Overflow: `[amazon-linux] end of life`, `nodejs20.x lambda deprecated`, `No module named 'distutils' lambda`
- AWS re:Post tag: https://repost.aws/tags/questions/TAl4y_oRX1RjmpJJGVndhKtA (Amazon Linux)
- Each answer must be **unique** and **help-first**. One good answer > ten copy-pasted ones.

---

# Batch 3 — drafted 2026-08-23, fresh and ready to post

Found via search this cycle; not duplicates of batch 1/2 (different threads, different questions). Same
rules apply: post from your own account, lead with the fix, one disclosed link, never cross-post the same
text. Dates below match the current AWS Lambda runtimes table
(https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) as of this drafting date — AWS has
revised block-create/block-update dates for this cluster more than once, so re-check the live table before
posting if it's been more than a few days.

Links point to `https://ntoledo319.github.io/EOLkits/...` (the verified GitHub Pages build), not
`eolkits.com` — this drafting cycle had no way to independently confirm the custom domain is serving the
repaired, truthful site (network egress to eolkits.com was unavailable), while Pages is confirmed repaired
per `revenue/DECISIONS.md` D19/D20. If `eolkits.com` is confirmed fully repaired and stable by the time you
post, swapping the domain in is fine — the paths are identical.

## 1 — [Action Required] AWS Lambda end of support for Node.js 18 - referenced functions no longer exist

Post at: https://repost.aws/questions/QUz3FDy7jfQliBFrh_hKZoaQ/action-required-aws-lambda-end-of-support-for-node-js-18-referenced-functions-no-longer-exist

> If the Health Dashboard event is listing ARNs for functions you're sure you already deleted, the most
> common cause is **Lambda@Edge replicas**. When a Lambda@Edge function is associated with a CloudFront
> distribution, AWS replicates it to regions/edge locations near your viewers. Deleting the "parent" function
> in its home region — or deleting the CloudFormation stack that created it — does **not** delete those
> replicas by itself. AWS only allows replica deletion after every CloudFront association is removed and
> propagation finishes, which can take hours; if a distribution was deleted while still referencing the
> function, or the stack teardown raced the CloudFront propagation, the replica (and the deprecation notice
> tied to it) can outlive what you see in your own account/region view.
>
> To confirm and clear it:
> 1. Check the exact ARN in the Health event — a Lambda@Edge replica ARN includes a version suffix and
>    typically shows up in `us-east-1` regardless of where you deployed it.
>    `aws lambda get-function --region us-east-1 --function-name <name>:<version>` will tell you if it still
>    exists and which CloudFront distributions (if any) still reference it.
> 2. If a distribution still lists the association, remove it (or delete the distribution) and wait — AWS's
>    own guidance is the replica becomes deletable a few hours after the last association is removed:
>    https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-delete-replicas.html
> 3. If the function is confirmed gone from every region/account you control and the notice still won't
>    clear, that's a Health Dashboard sync lag, not something in your account — AWS Support can force-refresh
>    it.
> 4. Separately, to see every *real*, still-existing function on a deprecated runtime (not just what the
>    Health event lists), AWS has an official CLI/console method:
>    https://docs.aws.amazon.com/lambda/latest/dg/runtimes-list-deprecated.html
>
> On the runtime itself: `nodejs18.x` stopped receiving security patches on 2025-09-01. Per the current AWS
> runtimes table, block-create and block-update for this cluster (nodejs16.x/18.x/20.x plus python3.8/3.9)
> now land 2027-02-01 and 2027-03-03 — but AWS has pushed these dates back more than once already, so treat
> the live table as the source of truth, not this comment.
>
> If it's useful for auditing every function across regions in one pass (not just what Health Dashboard
> surfaces), I maintain a free, open-source scanner — nothing uploaded, MIT licensed (disclosure: I built it):
> https://ntoledo319.github.io/EOLkits/scan/

## 2 — How can I use Amazon Linux 2023 for AWS CodeBuild Runner Projects? Still getting AL2

Post at: https://repost.aws/questions/QUqvfJVhQ4ReeApG8shtcu1A/how-can-i-use-amazon-linux-2023-for-aws-codebuild-runner-projects-still-getting-al2

> This is almost always a `runs-on` labeling issue, not a project-level default. AWS's CodeBuild-hosted
> GitHub Actions runner picks the compute image from **labels in the workflow YAML itself**, and if you don't
> specify an image label it falls back to the AL2-based default rather than AL2023.
>
> To pin AL2023 explicitly, add an `image:` label alongside your runner label in `runs-on:`:
>
> ```yaml
> jobs:
>   build:
>     runs-on:
>       - codebuild-<your-fleet-name>-${{ github.run_id }}-${{ github.run_attempt }}
>       - image:linux-5.0
> ```
>
> `linux-5.0` maps to `aws/codebuild/amazonlinux-x86_64-standard:5.0`, which is the AL2023-based standard
> image; `linux-4.0` is the AL2-based one that's likely what you're getting by default. AWS's reference list
> of valid image labels for the hosted runner is here (worth bookmarking, since new standard-image versions
> get added over time):
> https://docs.aws.amazon.com/codebuild/latest/userguide/sample-github-action-runners-update-yaml.images.html
>
> Two things that trip people up after switching:
> - If you're using the EC2-fleet variant (not the Lambda-fleet one), the base AMI reference is different —
>   `aws/codebuild/ami/amazonlinux-x86_64-base:latest` — and that's a separate setting in the fleet, not the
>   workflow YAML.
> - AL2023 uses `dnf`, not `yum`, and doesn't have `amazon-linux-extras`; any `yum install`/`amazon-linux-extras
>   install` steps in your build image bootstrap need to change to `dnf install <package>` (packages are
>   default-versioned or version-namespaced, e.g. `python3.12`).
>
> The full AL2023 walkthrough for the general (non-runner) case, if useful:
> https://docs.aws.amazon.com/codebuild/latest/userguide/action-runner.html
>
> If it helps, I maintain a free open-source scanner that flags exactly this kind of stale-AL2/yum drift in
> Dockerfiles, buildspecs, and IaC before it causes a surprise like this (disclosure: mine, MIT, nothing
> uploaded): https://ntoledo319.github.io/EOLkits/scan/ — and a step-by-step AL2→AL2023 checklist:
> https://ntoledo319.github.io/EOLkits/amazon-linux-2-eol-checklist/
