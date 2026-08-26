# Batches 1–2 below: ARCHIVED — DO NOT POST

Targets and answers in Batches 1 and 2 are stale (drafted 2026-07 to 2026-08-22) and require fresh manual
policy and fact review before use. **Batches 3–6, appended 2026-08-23 through 2026-08-26 at the bottom of
this file, are fresh and ready to post** — each was drafted from questions found via live search on its
drafting day, with URLs and dates verified against this cycle's established facts. Re-verify each URL still
resolves and still lacks a better answer before pasting, since time may have passed since drafting.

**Recovery note (2026-08-26):** Batches 3–5 (211 lines, three cycles of verified work) were silently dropped
from this file by an earlier two-parent merge (`a5510969`) that took its tree from a diverged branch
(`b97befa7`, the GRACE-privacy work) instead of combining both sides' changes. Both branches touched
unrelated files, so the loss was a merge-tooling gap, not a deliberate archival decision. This cycle restored
Batches 3–5 verbatim from commit `7da75425` (the pre-merge tip) and appended Batch 6. If a future cycle
performs a similar two-parent "tree-matches-one-side" merge across branches that both touch this file, diff
the dropped side's changes to this file specifically before advancing, or the backlog will silently regress
again.

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

---

# Batch 4 — drafted 2026-08-24, fresh and ready to post

Found via search this cycle; not a duplicate of Batches 1–3 (different thread, different question). Same
rules apply: post from your own account, lead with the fix, one disclosed link, never cross-post the same
text. WebFetch (direct page fetch) was unavailable again this cycle (`EGRESS_BLOCKED`), so this was
cross-checked via multiple independent search results rather than a byte-for-byte page fetch — re-verify
the thread still lacks a better answer before pasting, since time may have passed since drafting. The
runtime-management-controls mechanism and its rollback path below are AWS's own documented feature
(https://docs.aws.amazon.com/lambda/latest/dg/runtime-management.html and
.../runtime-management-rollback.html), not inferred from the thread. Link points to
`https://ntoledo319.github.io/EOLkits/...` (the verified GitHub Pages build) for the same reason Batch 3
does — network egress to `eolkits.com` was unavailable this cycle to independently confirm it is still
serving the repaired site.

## 1 — python 3.9 runtime update gives Runtime.Unknown in INIT phase

Post at: https://repost.aws/questions/QUowJJh-50R3KbxGrZ2YNsCA/python-3-9-runtime-update-gives-runtime-unknown-in-init-phase

> This is almost always a **native-extension / glibc mismatch introduced by an automatic minor-version
> bump of the runtime's execution environment**, not a change in your own code. By default Lambda's
> "runtime management controls" are set to **Auto**, which means AWS can silently roll your function onto a
> newer internal build of `python3.9` (for example bumping from build `v96` to `v101`) even though you
> never touched the function. If any dependency ships a compiled/native component — `psycopg2`, `numpy`,
> `pandas`, `lxml`, `grpcio`, `cryptography` — and it was built against the glibc/OpenSSL of the *older*
> internal build, it can fail to load in the new one. That failure often surfaces as a bare
> `Runtime.Unknown` during INIT instead of a clear `ImportModuleError`, because the crash happens before
> the Python interpreter finishes initializing enough to report a normal traceback.
>
> To confirm and fix:
> 1. Compare the runtime version ARN of a failing invocation against a known-good one:
>    `aws lambda get-function --function-name <name> --query 'Configuration.RuntimeVersionConfig'`. If it
>    changed without a deployment on your end, that confirms an automatic runtime update, not a code
>    regression.
> 2. For an immediate rollback while you investigate, Lambda explicitly supports pinning to the last known
>    working runtime version ARN via the console's "Runtime version" tab or
>    `PutRuntimeManagementConfig` with `UpdateRuntimeOn=Manual`. This is a documented, supported mitigation
>    for exactly this scenario:
>    https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html
> 3. The durable fix is to rebuild any native dependency inside the *exact* target runtime's build image
>    (e.g. AWS SAM's `public.ecr.aws/sam/build-python3.9` container, or the equivalent Lambda base image)
>    rather than shipping a locally-built wheel, or switch that dependency to a maintained Lambda Layer.
>    Full runtime-management-controls background:
>    https://docs.aws.amazon.com/lambda/latest/dg/runtime-management.html
>
> Worth noting separately: `python3.9` itself is already past Lambda's own deprecation timeline (deprecated
> 2025-12-15; per the current runtimes table, block-create is 2027-02-01 and block-update is 2027-03-03 for
> this runtime cluster — AWS has revised these dates before, so treat the live table as the source of
> truth, not this comment: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html). Since any
> native dependency will need the same rebuild-for-target-glibc treatment on 3.11/3.12/3.13 anyway, it's
> usually less total work to do that rebuild once as part of moving off 3.9 rather than chasing another
> silent minor-version drift later.
>
> If useful, I've written up this exact glibc/native-extension failure mode in more depth, and I maintain a
> free, open-source scanner that flags stale-runtime and native-dependency drift in source/IaC before it
> causes this kind of surprise (disclosure: mine, MIT, nothing uploaded):
> https://ntoledo319.github.io/EOLkits/fix/lambda-glibc-version-not-found/

# Batch 5 — drafted 2026-08-25, fresh and ready to post

Found via search this cycle; not a duplicate of Batches 1–4 (different thread, different question). Same rules
apply: post from your own account, lead with the fix, one disclosed link, never cross-post the same text.
WebFetch (direct page fetch) was unavailable again this cycle (`EGRESS_BLOCKED` on a neutral control,
`example.com`); WebSearch worked and was used, cross-checked against multiple independent search-result
snippets per claim before drafting — re-verify the thread still lacks a better answer before pasting, since
time may have passed since drafting. The exact current block-create/block-update dates cited below
(2027-02-01 / 2027-03-03 for the nodejs16.x/nodejs18.x/nodejs20.x/python3.8/python3.9 cluster) are AWS's own
published runtimes table (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), already
cross-verified in this repo's own prior cycles — **do not** use the various superseded 2026 dates (e.g.
"August 31, 2026" / "September 30, 2026" / "June 1, 2026" / "July 1, 2026") that several blogs and even some
other re:Post threads still repeat; AWS pushed those blocks back and the live table is the only source of
truth. Link points to `https://ntoledo319.github.io/EOLkits/...` (the verified GitHub Pages build) for the
same reason Batches 3–4 do — network egress to `eolkits.com` was unavailable this cycle to independently
confirm it is still serving the repaired site.

## 1 — API GATEWAY DEV PORTAL - Update Lambda Functions to nodejs20

Post at: https://repost.aws/questions/QURnP8vskJREG40Ilrwx_RLQ/api-gateway-dev-portal-update-lambda-functions-to-nodejs20

> Two separate things are colliding here, and it's worth untangling both before you pick a target runtime.
>
> **1. The login/auth failures after bumping the SAM-generated functions from `nodejs16.x` to `nodejs20.x` are
> almost certainly an AWS SDK v2 → v3 breaking change, not a Node syntax issue.** The `nodejs16.x` runtime
> bundles AWS SDK for JavaScript **v2**; starting at `nodejs18.x`, Lambda's managed runtime bundles SDK **v3**
> instead, and v2's `require('aws-sdk')` API surface (client construction, callback-vs-promise style, error
> shapes) is not a drop-in match for v3's modular `@aws-sdk/client-*` packages. If the portal's generated
> Lambda code (or a dependency it pulls in, e.g. for Cognito login) still does `require('aws-sdk')` and
> expects v2 behavior, that's the most common cause of exactly this kind of silent breakage right after a
> runtime bump. Two ways to confirm/fix:
>   - Grep the generated function code and its `node_modules` for `require('aws-sdk')` or `from 'aws-sdk'`.
>     If found, either migrate that code to the modular v3 clients (`@aws-sdk/client-cognito-identity-provider`,
>     etc. — Lambda includes v3 by default so no explicit dependency is needed), or, as a stopgap, bundle SDK
>     v2 explicitly as a *regular* (not dev) dependency so your own pinned copy ships instead of relying on
>     what the runtime provides.
>   - Check CloudWatch Logs for the specific function around the failed login attempt — an SDK v2/v3 mismatch
>     usually throws a clear `TypeError` or "is not a function" on a client method the moment it's called,
>     which confirms this diagnosis quickly.
>
> **2. Don't stop at `nodejs20.x`.** As of AWS's current runtimes table, `nodejs20.x` is now in the *same*
> deprecation cluster as `nodejs16.x`/`nodejs18.x` (along with `python3.8`/`python3.9`): Lambda blocks
> **creating** new functions on it starting **2027-02-01** and blocks **updating** existing functions on it
> starting **2027-03-03**. (AWS has revised these dates before — the live table is the source of truth, not
> this comment, and definitely not the various 2026 dates still floating around some blog posts and even
> older re:Post threads: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html.) Since you're
> already touching this code to fix the login break, it's usually less total rework to go straight to
> `nodejs22.x` (current LTS, SDK v3 bundled) or `nodejs24.x` rather than doing this same migration exercise
> twice within the next year.
>
> If it helps, I maintain a free, open-source scanner that flags exactly this kind of stale-runtime and
> `require('aws-sdk')`-v2-on-v3-runtime drift in source and IaC before it causes a surprise like this
> (disclosure: mine, MIT, nothing uploaded): https://ntoledo319.github.io/EOLkits/scan/

---

# Batch 6 — drafted 2026-08-26, fresh and ready to post

Found via search this cycle; not a duplicate of Batches 1–5 (different thread, different runtime, different
root cause). WebFetch (direct page fetch) was unavailable again this cycle — `EGRESS_BLOCKED` on every tested
host, including the neutral control `example.com`, confirmed via both the WebFetch tool and a direct `curl`
through the configured proxy (`gateway answered 403 to CONNECT`) — so, as in Batches 4–5, this was
cross-checked via multiple independent search-result snippets (AWS's own blog post on the nodejs14.x/16.x CDK
end-of-support, a GitHub issue on the identical error against `aws-amplify/amplify-cli`, and a dev.to writeup
of the same error string) rather than a page fetch. Re-verify the thread still lacks a better answer before
pasting, since time may have passed since drafting, and re-verify the runtime table before citing dates from
here — this comment is not the source of truth.

## 1 — The runtime parameter of nodejs14.x is no longer supported for creating or updating AWS Lambda functions. We recommend you use the new runtime (nodejs20.x)

Post at: https://repost.aws/questions/QUVhoUXEhDSBGXtsiU8xCpIA/the-runtime-parameter-of-nodejs14-x-is-no-longer-supported-for-creating-or-updating-aws-lambda-functions-we-recommend-you-use-the-new-runtime-nodejs20-x

> If this is coming from an **Amplify-generated** stack (it usually is when the error targets a function you
> never wrote yourself, e.g. `UserPoolClientLambda`, `S3TriggerFunction`, or another `*Lambda` resource an
> `amplify push` created), the blocker isn't your code — it's that the CloudFormation template Amplify
> generated hardcodes `Runtime: nodejs14.x`, and there's no runtime field exposed in `amplify configure`/CLI
> flags to bump it directly. Editing the generated template by hand doesn't stick either, since the next
> `amplify push` regenerates it.
>
> The supported fix is Amplify's **CloudFormation override** mechanism, which lets you patch specific
> resource properties in the generated template without touching the generated file itself:
> 1. `amplify override auth` (for the `UserPoolClientLambda`/trigger functions) or `amplify override function`
>    for a standalone function — this scaffolds an `overrides.ts` your project keeps.
> 2. In `overrides.ts`, target the specific resource and set its runtime, e.g. for a Cognito trigger:
>    `resources.userPoolClientLambda.runtime = 'nodejs20.x'` (the exact resource key differs by category/
>    trigger type — `amplify override` prints the available keys when scaffolded).
> 3. `amplify push` again; the override applies on top of the generated template every time, so it survives
>    future pushes.
>
> **Don't stop at `nodejs20.x` just because that's what AWS's error message suggests.** Per the current AWS
> Lambda runtimes table, `nodejs20.x` is already in the same 2027 deprecation cluster as `nodejs16.x`/
> `nodejs18.x` (plus `python3.8`/`python3.9`): block-create **2027-02-01**, block-update **2027-03-03** (AWS
> has revised these dates before, so the live table is the source of truth, not this comment or AWS's own
> error-message default — check it: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html). Since
> you're already doing the override work to get off `nodejs14.x`, it's less total rework to target
> `nodejs22.x` (current LTS) directly rather than redoing this same override exercise again in ~18 months.
>
> One thing worth testing after the bump regardless of target version: Node 18+ Lambda runtimes ship **AWS
> SDK v3 only** (no bundled `aws-sdk` v2), so if the Amplify-generated function or a layer it depends on does
> `require('aws-sdk')`, it'll throw `Cannot find module 'aws-sdk'` at cold start until you either migrate to
> the modular `@aws-sdk/client-*` packages or bundle v2 explicitly as your own dependency.
>
> If it's useful for finding every function still on a blocked/soon-to-block runtime across a project or
> account in one pass, I maintain a free, open-source scanner — nothing uploaded, MIT licensed (disclosure: I
> built it): https://ntoledo319.github.io/EOLkits/scan/
