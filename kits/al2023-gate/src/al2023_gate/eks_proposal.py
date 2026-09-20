"""Generate a blue/green EKS Terraform JSON patch and an opt-in draft PR script."""

from __future__ import annotations

import copy
import difflib
import re
from pathlib import Path

from . import util
from .artifacts import emit_report, json_text, read_json, write_bundle

AMI_TYPES = {"AL2_x86_64": "AL2023_x86_64_STANDARD", "AL2_ARM_64": "AL2023_ARM_64_STANDARD"}
REFERENCE = "https://docs.aws.amazon.com/eks/latest/userguide/al2023.html"

OPEN_PR = """#!/usr/bin/env bash
set -euo pipefail
bundle=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ "${1:-}" != "--create-pr" || "$#" != 1 ]]; then
  printf '%s\n' 'Preview only. Review migration.patch and PR.md; run this script with --create-pr from a clean repository to publish a draft PR.'
  cat "$bundle/migration.patch"
  exit 0
fi
[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || { printf '%s\n' 'Refusing a dirty repository. Keep this bundle outside the worktree or ignored.' >&2; exit 2; }
[[ "$(pwd -P)" == "$(git rev-parse --show-toplevel)" ]] || { printf '%s\n' 'Run from the repository root.' >&2; exit 2; }
git remote get-url origin
gh auth status
git apply --check "$bundle/migration.patch"
base=$(git branch --show-current)
[[ -n "$base" ]] || { printf '%s\n' 'Detached HEAD is unsupported.' >&2; exit 2; }
branch="codex/eks-al2023-$(date -u +%Y%m%dT%H%M%SZ)"
git switch -c "$branch"
git apply --index "$bundle/migration.patch"
git diff --cached --check
git commit -m 'Propose parallel AL2023 EKS managed node group'
git push --set-upstream origin "$branch"
gh pr create --draft --base "$base" --head "$branch" --title 'Propose parallel AL2023 EKS node group' --body-file "$bundle/PR.md"
"""


def propose(document, resource, relative_path, source_text):
    relative = Path(relative_path)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not re.fullmatch(r"[A-Za-z0-9_./-]+\.tf\.json", relative_path)
    ):
        raise ValueError("Repository path must be a simple relative .tf.json path")
    groups = document.get("resource", {}).get("aws_eks_node_group", {})
    if resource not in groups or not isinstance(groups[resource], dict):
        raise ValueError("Selected aws_eks_node_group resource is absent")
    original = groups[resource]
    if original.get("ami_type") not in AMI_TYPES:
        raise ValueError(
            "Only explicit AL2_x86_64 and AL2_ARM_64 standard node groups are supported; GPU/custom AMIs need manual review"
        )
    unsupported = {
        "launch_template",
        "count",
        "for_each",
        "dynamic",
        "provisioner",
        "lifecycle",
        "release_version",
    }.intersection(original)
    if unsupported:
        raise ValueError(
            "Manual review required for node-group fields: " + ", ".join(sorted(unsupported))
        )
    name = original.get("node_group_name")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,55}", name):
        raise ValueError("An explicit node_group_name of at most 56 simple characters is required")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", resource):
        raise ValueError("Unsupported Terraform resource identifier")
    if any(
        key not in original
        for key in ("cluster_name", "node_role_arn", "subnet_ids", "scaling_config")
    ):
        raise ValueError("Node group lacks required cluster, role, subnet or scaling configuration")
    new_resource = resource + "_al2023"
    if new_resource in groups:
        raise ValueError("Target Terraform resource already exists; refusing a second proposal")
    if f"aws_eks_node_group.{resource}." in json_text(original):
        raise ValueError("Self-referencing node-group expressions require manual review")
    proposed = copy.deepcopy(document)
    replacement = copy.deepcopy(original)
    replacement["ami_type"] = AMI_TYPES[original["ami_type"]]
    replacement["node_group_name"] = name + "-al2023"
    if any(
        group.get("node_group_name") == replacement["node_group_name"]
        for group in groups.values()
        if isinstance(group, dict)
    ):
        raise ValueError("Target AWS node group name already exists in configuration")
    proposed["resource"]["aws_eks_node_group"][new_resource] = replacement
    candidate = json_text(proposed)
    diff = difflib.unified_diff(
        source_text.splitlines(keepends=True),
        candidate.splitlines(keepends=True),
        fromfile="a/" + relative_path,
        tofile="b/" + relative_path,
    )
    patch = "".join(
        line if line.endswith("\n") else line + "\n\\ No newline at end of file\n" for line in diff
    )
    body = f"""The existing `{resource}` AL2 node group is retained. This proposal adds `{new_resource}` with `{replacement["ami_type"]}` and a distinct AWS name for a blue/green migration.

Review before apply:
- Run Terraform format/validate and inspect a fresh plan: only the new node group should be added; no existing node group may be destroyed.
- Verify Kubernetes version, VPC CNI compatibility, instance architecture, AMI availability, IP capacity and additional node cost.
- Test workloads, storage, security controls and nodeadm behavior on the new group. This generator does not validate the cluster.
- Cordon/drain old nodes only after staging checks and PodDisruptionBudget review. Retain old capacity for rollback.
- Remove old capacity in a separate reviewed change after workload validation; reverting this proposal alone is not an operational rollback.

No infrastructure operation was executed. The PR script only prepares and publishes a draft; it never runs Terraform apply.
Source: {REFERENCE}
"""
    return {
        "schema_version": 1,
        "resource": resource,
        "new_resource": new_resource,
        "old_ami_type": original["ami_type"],
        "new_ami_type": replacement["ami_type"],
        "strategy": "parallel-node-group",
        "source_unchanged": True,
        "reference": REFERENCE,
    }, {
        "migration.patch": patch,
        "proposed.tf.json": candidate,
        "PR.md": body,
        "open-pr.sh": OPEN_PR,
    }


def run(args):
    path = Path(args.path)
    if not path.name.endswith(".tf.json"):
        raise ValueError(
            "EKS proposals support Terraform .tf.json only; HCL, modules and custom templates require manual review"
        )
    document = read_json(path)
    report, files = propose(
        document, args.resource, args.repo_path or path.name, path.read_text(encoding="utf-8")
    )
    report["artifacts"] = sorted(files)
    if not util.is_dry_run(args):
        if not args.out:
            raise ValueError("--apply requires --out for a new proposal bundle")
        write_bundle(args.out, files)
        report["written"] = True
    else:
        report["written"] = False
        report["patch"] = files["migration.patch"]
    emit_report(report)
    return 0
