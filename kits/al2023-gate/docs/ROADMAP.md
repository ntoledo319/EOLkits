# Organization inventory and migration proposals

These five additions complement the original six commands. They do not apply AWS
changes or migrate the machine running the CLI. New proposal/configuration bundles
require `--apply`; `AL2023_GATE_DRY_RUN=1` overrides it. Reports print JSON by default;
an explicit `--out` creates a new report and refuses to overwrite an existing one.

## AWS Config Rules export

```bash
al2023-gate config-export --fixture examples/config-export.json --ami-catalog examples/ami-catalog.json
al2023-gate config-export --live --aggregator existing-org --region us-east-1 --rule approved-amis --ami-catalog images.json --out organization-report.json --strict
```

`--live` is required for network access. Install the optional `[aws]` extra first.
The exporter queries **recorded EC2 instances** across the accounts and regions in
an existing aggregator. The CLI never creates AWS Config infrastructure. Config
recording must already be configured by its owner; enabling it can cost money and
is outside this command. An optional existing rule name adds its noncompliant
resource evaluations across all returned accounts/regions. It paginates inventory,
rule summaries and rule details; access errors or repeated tokens fail the export
instead of reporting an incomplete success.

Read permissions are `config:SelectAggregateResourceConfig`, plus
`config:DescribeAggregateComplianceByConfigRules` and
`config:GetAggregateComplianceDetailsByConfigRule` when `--rule` is supplied.
Credential access remains whatever the explicitly selected profile permits.

AMI identifiers alone cannot reveal the operating system. Supply a JSON catalog
of `{ "region": "us-east-1", "ami_id": "ami-12345678", "description": "Amazon Linux 2" }`
objects using descriptions you have independently verified. A `*` region is an
explicit opt-in to matching that image ID across regions. Unmatched IDs remain
`unknown`. Rule noncompliance is reported separately and never treated as OS proof.
Annotations and unrelated resource configuration are omitted from the report.

Offline fixtures use `{ "resources": [...], "evaluations": [...] }` (see the
example). Resource objects match decoded Config SELECT results; evaluations use
the normalized `rule`, `account_id`, `region`, `resource_id`, `resource_type`, and
`compliance` fields. `--strict` exits 1 on AL1/AL2, unknown AMIs or noncompliant rule
evaluations. A successful empty query says only that the aggregator returned no
recorded instances; it does not establish organization-wide compliance.

AWS documents [cross-account SELECT pagination](https://docs.aws.amazon.com/config/latest/APIReference/API_SelectAggregateResourceConfig.html),
[rule summaries](https://docs.aws.amazon.com/config/latest/APIReference/API_DescribeAggregateComplianceByConfigRules.html),
[rule evaluation details](https://docs.aws.amazon.com/config/latest/APIReference/API_GetAggregateComplianceDetailsByConfigRule.html),
and [the exclusion of unrecorded/deleted resources](https://docs.aws.amazon.com/config/latest/developerguide/querying-AWS-resources.html).

## Terraform state scanner

```bash
al2023-gate terraform-state examples/terraform.tfstate --region us-east-1 --ami-catalog examples/ami-catalog.json --strict
terraform show -json > inventory.json
al2023-gate terraform-state inventory.json --region us-east-1
```

Accepts Terraform raw state v4 and `terraform show -json` state format 1.x,
including child modules and indexed instances. Terraform plans and other formats
fail explicitly. It examines managed `aws_instance`, `aws_launch_template`,
`aws_launch_configuration`, and `aws_eks_node_group` resources. Findings include
resource addresses and JSON attribute paths for AMI IDs and EKS AMI types. Resolved
`aws_ami` data-source descriptions in the state can supply local evidence; otherwise
use the same optional AMI catalog. No network call is made.

Raw state commonly contains secrets. The scanner excludes outputs, user data and
unrelated attributes from reports, but input files must stay private. Zero AL2
findings with unknown images is not a clean migration result: `--strict` also fails
on unknowns and missing/unresolved provider image attributes. Only the provider's
direct AMI attribute is evidence; similarly named tags or nested metadata are
ignored. State-local AMI descriptions require an explicit source/default region.
Resource types outside the supported list are not examined.
[HashiCorp specifies the show JSON structure](https://developer.hashicorp.com/terraform/internals/json-format).

## EKS AMI proposal and draft PR

```bash
al2023-gate eks-proposal examples/eks.tf.json --resource workers --repo-path infrastructure/eks.tf.json
al2023-gate eks-proposal examples/eks.tf.json --resource workers --repo-path infrastructure/eks.tf.json --apply --out proposal
# After reviewing the private bundle, run from the clean destination repository:
bash /path/to/proposal/open-pr.sh --create-pr
```

For explicit standard `AL2_x86_64` and `AL2_ARM_64` node groups, the generator adds
a **parallel** group with the corresponding AL2023 standard AMI type and a distinct
name. It leaves the original group unchanged. The bundle includes an applicable
Git patch, complete proposed JSON, a PR body/checklist, and a working PR script.
Running that script without `--create-pr` only displays the patch. The explicit
option requires a clean worktree, checks patch applicability, creates a new branch,
commits, pushes to origin and opens a draft with `gh`; it never applies Terraform.
Keep the bundle outside the worktree or in an ignored directory. Failed GitHub
publication leaves the local branch/commit available for inspection and retry.

Supported scope is direct `aws_eks_node_group` blocks in **Terraform `.tf.json`**.
HCL, module abstractions, GPU/custom AMIs, launch templates, dynamic/count/for_each,
custom release versions and resource lifecycle/provisioner overrides are refused.
Node names must be explicit. This deliberate scope prevents an unsafe generic text
replacement. Inspect a fresh Terraform plan, validate architecture and cluster/CNI
compatibility, and budget parallel capacity before applying it. The tool does not
promise zero downtime or zero deployment cost. Drain and removal of old nodes are
separate operator-controlled steps after workload validation.

[AWS requires a blue/green path for these managed-node-group migrations](https://docs.aws.amazon.com/eks/latest/userguide/al2023.html)
and describes the changed `nodeadm` initialization behavior. Custom-AMI launch
template migrations are a different workflow and are not generated here.

## Datadog and New Relic configuration shims

Export the relevant configuration into a private directory first; `--config-root`
uses an `etc`-style layout. Datadog expects `datadog-agent/datadog.yaml` and preserves
that directory tree. New Relic expects `newrelic-infra.yml` and additionally
preserves `newrelic-infra/` when present.

```bash
al2023-gate agent-shim --agent datadog --config-root private-config
al2023-gate agent-shim --agent newrelic --config-root private-config --apply --out private-agent-bundle
# On a prepared destination or an offline mounted AL2023 image:
python3 private-agent-bundle/migrate.py --target-root mounted-al2023
python3 private-agent-bundle/migrate.py --target-root mounted-al2023 --apply
```

The generator requires a nonempty scalar `api_key` or `license_key` in the main
configuration, refuses symlinks and preserves config bytes, comments, proxies, tags
and integration files. It validates presence, not credential validity. Environment
credentials, unit overrides, custom binaries and files outside the selected tree
need separate review. The bundle contains the original credentials: directories
are private, config artifacts are mode 0600, values never appear in CLI summaries,
and **the bundle must never be committed or published**.

`migrate.py` checks the selected target's `os-release` for AL2023. Preview is the
default. Apply makes timestamped backups, preserves existing ownership/mode, and
restores copied contents if a copy fails. It does not install packages or contact a
vendor. A real-host restore requires the vendor RPM already installed. Service
restart requires both `--apply --restart` and `--target-root /`; do not use those
arguments on the original AL2 host. A restart may produce external effects that a
file rollback cannot reverse. Confirm reporting before removing the old host.

Datadog documents [the configuration tree and service commands](https://docs.datadoghq.com/agent/supported_platforms/linux/)
and [AL2023 Agent 7.40+ support on x86_64 and ARM64](https://docs.datadoghq.com/agent/supported_platforms/).
New Relic documents [its config file and environment precedence](https://docs.newrelic.com/docs/infrastructure/infrastructure-agent/configuration/configure-infrastructure-agent/)
and [architecture-specific AL2023 repositories with GPG verification](https://docs.newrelic.com/docs/infrastructure/infrastructure-agent/linux-installation/package-manager-install/).
Use a currently supported vendor release on a separately prepared AL2023 host;
these shims do not upgrade the operating system in place.

## GitHub Actions template

```bash
al2023-gate ci-template --state-path inventory/sanitized-state.json --region us-east-1 --ami-catalog inventory/images.json
al2023-gate ci-template --state-path inventory/sanitized-state.json --apply --out .github/workflows/al2023-gate-ci.yml
```

The generated workflow checks out code with read-only permissions, installs the
vendored kit (default `kits/al2023-gate`, configurable with `--kit-path`), and runs
the real offline state scanner with `--strict`. It needs a prepared sanitized
state-shaped inventory at the selected path. It requests no AWS credentials and
uploads no raw state. The kit must be present in the consuming repository; this is
not a pre-published remote action. The included example uses fictional inventory
only as a demonstration; replace that input with your own protected evidence.
Use `--region` when state lacks region attributes and the AMI catalog is scoped to
a specific region; split multi-region state when one default region is insufficient.

Primary references above were checked on 2026-09-10. Real cloud exports, host
migrations, Terraform apply and external PR publication were not executed while
implementing these commands; offline tests exercise their supported boundaries.

The existing Python 3.8 remap still chooses an optional Python 3.11 target; its
description now distinguishes that choice from
[AL2023's system Python 3.9](https://docs.aws.amazon.com/linux/al2023/ug/python.html).
The generated workflow follows GitHub's
[minimum token permissions guidance](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).
