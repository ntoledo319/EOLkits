"""IaC patcher: rewrite Python Lambda runtimes in SAM / CDK / Terraform / Serverless."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from . import util
from .manifests import patch_manifest
from .terraform import patch_terraform

TARGET_RUNTIME = "python3.12"


@dataclass
class RewriteRule:
    name: str
    pattern: re.Pattern
    replacement: str


RULES: List[RewriteRule] = [
    # CDK (TypeScript and Python): Runtime.PYTHON_3_9, lambda.Runtime.PYTHON_3_9, _lambda.Runtime.PYTHON_3_9
    RewriteRule(
        name="cdk-runtime-enum",
        pattern=re.compile(r"(Runtime\.PYTHON_3_)(7|8|9|10|11)\b"),
        replacement=r"\g<1>12",
    ),
]


def _walk_iac_files(root: Path) -> List[Path]:
    if root.is_file():
        return [root]
    exts = {".yaml", ".yml", ".ts", ".js", ".tf", ".py", ".json"}
    out = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        if any(
            part
            in {
                ".venv",
                "venv",
                "__pycache__",
                "node_modules",
                ".git",
                "cdk.out",
                ".terraform",
            }
            for part in p.parts
        ):
            continue
        out.append(p)
    return out


def patch_text(text: str, filename: str = "template.yaml") -> Tuple[str, List[dict]]:
    path = Path(filename)
    if path.suffix == ".tf":
        changed, count = patch_terraform(
            text, {f"python3.{v}" for v in range(7, 12)}, TARGET_RUNTIME
        )
        return changed, [{"rule": "terraform-runtime", "count": count}] if count else []
    if path.suffix in {".json", ".yaml", ".yml"}:
        terraform = path.name.endswith(".tf.json")
        serverless = path.stem == "serverless"
        is_template = bool(
            re.search(
                r"AWS::(?:Lambda::Function|Serverless)|^\s*['\"]?Resources['\"]?\s*:",
                text,
                re.MULTILINE,
            )
        )
        if path.suffix == ".json" or text.lstrip().startswith("{"):
            try:
                data = json.loads(text)
                is_template = isinstance(data, dict) and (
                    "Resources" in data or ("Globals" in data and "Transform" in data)
                )
            except ValueError:
                is_template = (
                    is_template
                    or bool(re.search(r'"Resources"\s*:', text))
                    or path.name == "template.json"
                )
        if not (terraform or serverless or is_template):
            return text, []
        changed, count = patch_manifest(
            text,
            json_format=path.suffix == ".json",
            terraform=terraform,
            serverless=serverless,
            source_runtimes={f"python3.{v}" for v in range(7, 12)},
            target_runtime=TARGET_RUNTIME,
        )
        rule = (
            "terraform-runtime"
            if terraform
            else "serverless-runtime" if serverless else "sam-cfn-runtime"
        )
        return changed, [{"rule": rule, "count": count}] if count else []
    edits: List[dict] = []
    new = text
    for r in RULES:
        if r.name == "cdk-runtime-enum" and path.suffix not in {".ts", ".js", ".mjs", ".py"}:
            continue
        new, n = r.pattern.subn(r.replacement, new)
        if n > 0:
            edits.append({"rule": r.name, "count": n})
    return new, edits


def run(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not root.exists():
        util.err(f"path not found: {root}")
        return 2

    apply_mode = bool(args.apply)
    util.hdr(
        f"IaC patcher · {root} · {util.color.red('APPLY') if apply_mode else util.color.yellow('DRY-RUN')}"
    )
    util.dry_run_banner(apply_mode)

    files = _walk_iac_files(root)
    util.dim(f"  {len(files)} IaC candidate file(s) scanned")

    total_edits = 0
    files_changed = 0
    pending = []
    failures = 0
    for f in files:
        try:
            text = f.read_bytes().decode("utf-8")
            new_text, edits = patch_text(text, f.name)
        except (OSError, UnicodeError, ValueError) as exc:
            util.err(f"Cannot inspect {f}: {exc}")
            failures += 1
            continue
        if not edits:
            continue
        files_changed += 1
        for edit in edits:
            total_edits += edit["count"]
            util.info(
                f"{util.color.green('[rewrite]')} {f} · {edit['rule']} · {edit['count']} hit(s)"
            )
        pending.append((f, new_text))

    if failures:
        util.err(
            f"{failures} file(s) could not be inspected; no changes written. Resolve the errors and retry."
        )
        return 2
    if apply_mode:
        for f, new_text in pending:
            f.write_bytes(new_text.encode("utf-8"))

    print()
    if files_changed == 0:
        util.ok("No IaC files required runtime rewrites.")
    else:
        util.ok(f"{total_edits} rewrite(s) across {files_changed} file(s).")
        if not apply_mode:
            util.info("Re-run with --apply to write changes.")

    if args.strict and total_edits > 0 and not apply_mode:
        return 1
    return 0
