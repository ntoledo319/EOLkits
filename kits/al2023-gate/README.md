# al2023-gate
### Amazon Linux 2 → AL2023 migration kit — scan, remap, patch, ship, rollback

> **Amazon Linux 2 passed its published 2026-06-30 support milestone.** AWS has published AL2 material after that date, so do not infer the patch state of an instance from the date alone. Check the current AWS notice and the packages installed on the host, then plan the AL2023 migration.

`al2023-gate` is a dependency-light Python tool that checks supported AL2 resource patterns in selected AWS regions or fixtures, generates Packer scaffolding, previews Ansible and cloud-init changes, and produces resource-type-specific migration runbooks.

Works offline (fixture mode) for demos, audits, or air-gapped reviews. Works live against AWS with standard boto3 credentials.

[![Tests](https://img.shields.io/badge/tests-CI%20verified-green)](test/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![AL2 EOL](https://img.shields.io/badge/AL2%20EOL-2026--06--30-red)](https://aws.amazon.com/amazon-linux-2/faqs/)

---

## The deadline

The published 2026-06-30 milestone has passed. AWS can revise support behavior and publish exceptional updates, so the linked AWS notice is authoritative. The CLI identifies migration candidates; it does not determine whether a particular host is patched.

Primary source: <https://aws.amazon.com/amazon-linux-2/faqs/>

---

## Install

```bash
git clone https://github.com/ntoledo319/EOLkits.git
cd EOLkits/kits/al2023-gate
python3 -m venv .venv
.venv/bin/pip install -e .
. .venv/bin/activate
```

No external runtime deps. `boto3` is optional — only required for `scan` against live AWS. All other commands work offline.

---

## The 6 commands

```
al2023-gate scan        # classify visible EC2, launch-template, EKS, and EB patterns
al2023-gate remap       # translate yum packages → dnf equivalents (curated table of ~50)
al2023-gate packer      # generate ready-to-build Packer HCL for your AL2023 AMI
al2023-gate cloudinit   # diff user-data / cloud-init scripts for known AL2023 breakage
al2023-gate ansible     # rewrite ansible playbooks (yum→dnf, python2→3, extras removal)
al2023-gate runbook     # emit a resource-specific migration playbook (ASG / EKS / ECS / EB)
```

Each one does exactly one thing, can be piped, and has a `--format json` mode for CI use.

---

## 5-minute demo

### 1. Scan

```bash
$ al2023-gate scan --fixture test/fixtures/inventory.json

▸ Scanning fixture test/fixtures/inventory.json
ℹ Scanned 6 resource(s). 4 AL2, 0 AL1

Type                    Id                                    Region      Platform  Severity
--------------------------------------------------------------------------------------------
ec2_instance            i-0a1b2c3d4e5f60718                   us-east-1   al2       critical-eol
launch_template         lt-0f1e2d3c4b5a60978                  us-east-1   al2       critical-eol
eks_nodegroup           prod-cluster/ng-web-2a                us-east-2   al2       critical-eol
ecs_task_definition     payment-worker:47                     us-east-1   other     ok
beanstalk_environment   analytics-prod-env                    eu-west-1   al2       critical-eol
ec2_instance            i-0ffffeeeeddddccbb                   us-east-1   al2023    ok

⚠ AL2 EOL: 53 day(s) ago. Next: `al2023-gate packer` to scaffold an AL2023 AMI build.
```

Add `--strict` for CI (exits 1 if any AL2 resources are found). Add `--format json|csv|md` for machine output. Live AWS: drop `--fixture` and add `--regions us-east-1,eu-west-1`.

### 2. Remap your `yum` package list

```bash
$ al2023-gate remap docker nginx1 python3.8 php7.4 ntp yum-utils

AL2 PACKAGE  AL2023 EQUIVALENT  CATEGORY       NOTE
---------------------------------------------------
docker       docker             extras_to_dnf ! AL2 used `amazon-linux-extras install docker`. AL2023: `dnf install docker`.
nginx1       nginx              renamed         AL2 extras `nginx1` → AL2023 `nginx` (mainline).
python3.8    python3.11         replaced_by   ! AL2023 default python is 3.11. 3.8 not available.
php7.4       php8.2             replaced_by   ! PHP 7.4 is upstream EOL. AL2023 has php8.2 only.
ntp          chrony             replaced_by   ! ntpd is removed. AL2023 uses chrony for time sync.
yum-utils    dnf-utils          renamed         DNF replaces YUM. `yum-config-manager` is now `dnf config-manager`.
```

A `!` marks packages that require action — the rest are drop-in. Feed a file with `--file packages.txt`.

### 3. Generate a Packer template

```bash
$ al2023-gate packer --packages packages.txt --out ./build

▸ Packer template generator · ./build
ℹ Input packages: 23
✓ wrote build/al2023.pkr.hcl
✓ wrote build/migration-report.md
ℹ Next: `cd build && packer init . && packer build al2023.pkr.hcl`
```

Produces:
- `al2023.pkr.hcl` — a fully-parameterized Packer template (AWS amazon-ebs builder, AL2023 source AMI filter, pre-baked provisioners for `dnf update`, chrony enable, SSH hardening, cloud-init clean)
- `migration-report.md` — per-package action items grouped by category (removed, replaced, renamed) with AWS doc links

### 4. Diff your cloud-init / user-data

```bash
$ al2023-gate cloudinit user-data.sh

test/fixtures/user-data.sh
  [medium]   line 5  yum-to-dnf           yum update -y
  [critical] line 6  amazon-linux-extras  amazon-linux-extras install nginx1 -y
  [critical] line 15 python2-shebang      #!/usr/bin/python
  [high]     line 10 ntp-service          systemctl enable ntpd
  [high]     line 21 iptables-service     systemctl enable iptables
```

11 rules built in. Cloud-init is not auto-rewritten — too sensitive. You get precise line numbers + suggested edits instead.

### 5. Patch Ansible playbooks

```bash
$ al2023-gate ansible roles/ --apply

▸ Ansible patcher · roles/ · APPLY
ℹ [rewrite] roles/web/tasks/main.yml · yum module → dnf module · 3 hit(s)
ℹ [rewrite] roles/web/tasks/main.yml · yum task → dnf task (top-level) · 1 hit(s)
ℹ [lint]    roles/web/tasks/main.yml:42 · ntpd is not on AL2023 by default. Use chrony.
ℹ [lint]    roles/security/tasks/selinux.yml:3 · SELinux default changed; verify policy.

✓ 4 file(s), 11 edit(s) applied.
```

Safe, narrow rewrites only. Anything ambiguous is flagged for human review, not auto-changed. Default is dry-run.

### 6. Get a resource-specific runbook

```bash
$ al2023-gate runbook --kind asg --name prod-api-asg --region us-east-1 --out RUNBOOK.md
✓ wrote RUNBOOK.md
```

Produces a checklist with:
- Pre-flight: AMI tagged, staging soak ≥24h, alarms in place
- Execute: exact `aws` CLI commands for `create-launch-template-version` + `instance-refresh` with canary warm-up
- Rollback: previous Launch Template version swap + terminate-replacement

Same command supports `--kind eks|ecs|beanstalk` — each with resource-appropriate steps.

---

## What's in the box

| Component | Purpose |
|---|---|
| **Scanner** | Selected-region discovery for running/stopped EC2 instances, default/latest launch-template versions, EKS managed node groups, and Elastic Beanstalk platform descriptors. It classifies only patterns visible to the selected credential profile. |
| **Remap table** | ~50 curated AL2→AL2023 package entries (docker, nginx, php, postgresql, python, openssl ABI, curl→curl-minimal, ntp→chrony, yum→dnf, …). Handles `extras_to_dnf`, `renamed`, `replaced_by`, `removed`. |
| **Packer generator** | Full AWS amazon-ebs builder template with chrony, SSH hardening, cloud-init reset, dnf update, and your curated package list. |
| **cloud-init differ** | 11 rules for the highest-frequency AL2 user-data patterns that break on AL2023. |
| **Ansible patcher** | yum→dnf (module & top-level), `amazon-linux-extras` task removal, python2→3 path rewrites, SELinux/ntp/iptables lint. |
| **Runbook generator** | ASG (instance refresh + rollback), EKS (blue/green node group), ECS (task def base image swap), Beanstalk (CNAME swap). |
| **49-case test suite** | Offline behavioral coverage across commands, formats, and exit-code paths. |

---

## Safety

- Every write operation defaults to **dry-run**. `--apply` is required to touch a file.
- `scan` is strictly read-only (boto3 `Describe*` / `List*` only).
- Runbook templates include rollback steps; validate them against your own release process.
- No telemetry. No network calls outside AWS. No LLM.

---

## Free and hosted options

The CLI is free and MIT-licensed. The only paid product currently offered is a
server-gated [$299 repository evidence report](https://eolkits.com/audit): static
source/IaC findings with exact observed file/line locations, limitations, and cited
sources. It does not inspect an AWS account. Migration Pack and the previously
described hosted products are not for sale.

---

## Roadmap

- [ ] Live AWS Config Rules export (find AL2 at org-scale)
- [ ] Terraform state scanner (detect `ami-xxx` references without an API call)
- [ ] EKS AMI type auto-swap PR generator
- [ ] Datadog / New Relic agent migration shims
- [ ] GitHub Action template (`.github/workflows/al2023-gate-ci.yml`)

---

## License

MIT. See [LICENSE](LICENSE).

---

## Primary sources

- [AWS Amazon Linux 2 FAQ — EOL dates](https://aws.amazon.com/amazon-linux-2/faqs/)
- [AL2023 Comparison — packages, features, defaults](https://docs.aws.amazon.com/linux/al2023/ug/compare-with-al2.html)
- [EKS AMI types & release lifecycle](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html)
- [Elastic Beanstalk platform deprecation schedule](https://docs.aws.amazon.com/elasticbeanstalk/latest/platforms/platforms-supported.html)

*Built by [EOLkits Kits](https://github.com/ntoledo319/EOLkits). Tracked AWS deprecations deserve tested migration paths.*
