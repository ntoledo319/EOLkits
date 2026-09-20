"""python-pivot CLI."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__, action_template, extensions, layers, powertools, sdk_audit, util
from . import audit as audit_mod
from . import codemod as codemod_mod
from . import deploy as deploy_mod
from . import iac as iac_mod
from . import rollback as rollback_mod
from . import scan as scan_mod

BANNER = r"""
  ____            _                  ____  _            _
 |  _ \ _   _    | | _____  _ __    |  _ \(_)_   _____ | |_
 | |_) | | | |   | |/ _ \ \/ /  \   | |_) | \ \ / / _ \| __|
 |  __/| |_| |   |   |  __/>  <|  \ |  __/| |\ V / (_) | |_
 |_|    \__, |   |_|\___/_/\_\   \ |_|   |_| \_/ \___/ \__|
        |___/

        PYTHON-PIVOT  •  Lambda Python 3.9/3.10/3.11 → 3.12 migration kit
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python-pivot",
        description="AWS Lambda Python runtime migration kit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"python-pivot {__version__}")
    p.add_argument("--no-banner", action="store_true", help="Suppress banner")

    sub = p.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    # scan
    s = sub.add_parser("scan", help="Find Python Lambda functions needing migration")
    s.add_argument("--profile", help="AWS profile")
    s.add_argument("--regions", help="Comma-separated regions (default us-east-1)")
    s.add_argument("--fixture", help="JSON fixture for offline mode")
    s.add_argument("--format", choices=["table", "json", "csv", "md", "markdown"], default="table")
    s.add_argument("--out", help="Write output to file")
    s.add_argument("--strict", action="store_true", help="Exit 1 if any EOL runtime found")
    s.set_defaults(func=scan_mod.run)

    # codemod
    c = sub.add_parser("codemod", help="Rewrite Python source for 3.12 compatibility")
    c.add_argument("path", help="File or directory")
    c.add_argument("--apply", action="store_true", help="Write changes (default dry-run)")
    c.add_argument("--strict", action="store_true", help="Exit 1 if any edits / lints")
    c.set_defaults(func=codemod_mod.run)

    # audit
    a = sub.add_parser(
        "audit", help="Compare declared dependencies with curated Python 3.12 baselines"
    )
    a.add_argument("path", help="requirements.txt, Pipfile, or pyproject.toml")
    a.add_argument("--format", choices=["table", "json"], default="table")
    a.add_argument("--strict", action="store_true", help="Exit 1 if any findings")
    a.set_defaults(func=audit_mod.run)

    # Read-only migration compatibility evidence. AWS access is never implicit.
    layer = sub.add_parser("layers", help="Check layer ZIP content or declared compatibility")
    layer_input = layer.add_mutually_exclusive_group(required=True)
    layer_input.add_argument("--archive", help="Local layer ZIP; never extracted or executed")
    layer_input.add_argument("--fixture", help="JSON object containing a layers array")
    layer_input.add_argument(
        "--live", action="store_true", help="Explicit read-only Lambda metadata lookup"
    )
    layer.add_argument("--function", help="Function for --live")
    layer.add_argument("--region", help="AWS region for --live")
    layer.add_argument("--profile", help="AWS profile for --live")
    layer.set_defaults(func=layers.run)

    extension = sub.add_parser(
        "extensions", help="Check extension ZIP launchers and Python interpreter evidence"
    )
    extension.add_argument("--archive", required=True, help="Local extension layer ZIP")
    extension.set_defaults(func=extensions.run)

    for command in (layer, extension):
        command.add_argument("--runtime", default="python3.12", help="Target Python runtime")
        command.add_argument("--architecture", choices=["x86_64", "arm64"], default="x86_64")

    power = sub.add_parser("powertools", help="Check exact Powertools release Python metadata")
    power.add_argument("path", nargs="?", help="Supported dependency file (exact pin required)")
    power.add_argument(
        "--matrix", action="store_true", help="Show the exact-release snapshot matrix"
    )
    power.add_argument("--package-version", help="Resolved Powertools version")
    power.add_argument("--metadata", help="Locally saved PyPI JSON for another exact release")
    power.add_argument("--runtime", default="python3.12")
    power.set_defaults(func=powertools.run)

    sdk = sub.add_parser(
        "boto3", help="Compare static SDK calls with local botocore service models"
    )
    sdk.add_argument("path", help="Python source file or directory")
    sdk_models = sdk.add_mutually_exclusive_group(required=True)
    sdk_models.add_argument("--models", help="Target botocore data directory")
    sdk_models.add_argument(
        "--installed-models",
        action="store_true",
        help="Use installed botocore models; no AWS client or requests",
    )
    sdk.add_argument("--baseline-models", help="Previous model set, required to prove removals")
    sdk.set_defaults(func=sdk_audit.run)
    for command in (layer, extension, power, sdk):
        command.add_argument("--format", choices=["table", "json"], default="table")
        command.add_argument(
            "--strict",
            action="store_true",
            help="Exit 1 for incompatibility or manual-review findings",
        )

    action = sub.add_parser("action", help="Preview a GitHub Actions workflow for a vendored kit")
    action.add_argument("--out", help="New workflow path (parent directory must exist)")
    action.add_argument(
        "--apply", action="store_true", help="Create the file; default prints preview only"
    )
    action.set_defaults(func=action_template.run)

    # iac
    i = sub.add_parser("iac", help="Patch Python runtime in SAM / CDK / Terraform / Serverless")
    i.add_argument("path", help="File or directory")
    i.add_argument("--apply", action="store_true", help="Write changes (default dry-run)")
    i.add_argument("--strict", action="store_true", help="Exit 1 if any rewrites needed")
    i.set_defaults(func=iac_mod.run)

    # deploy
    d = sub.add_parser("deploy", help="Staged canary deploy to python3.12 with auto-rollback")
    d.add_argument("--function", required=True, help="Lambda function name")
    d.add_argument("--alias", default="live", help="Lambda alias for canary routing")
    d.add_argument("--runtime", default="python3.12", help="Target runtime")
    d.add_argument("--stages", default="5,25,50,100", help="Canary weights, comma-separated")
    d.add_argument("--dwell", default="60", help="Seconds between stage checks")
    d.add_argument(
        "--alarm",
        help="CloudWatch alarm ARN/name for rollback trigger (REQUIRED with --apply)",
    )
    d.add_argument("--profile", help="AWS profile")
    d.add_argument("--region", help="AWS region")
    d.add_argument("--plan-only", action="store_true", help="Print plan only, no execution")
    d.add_argument("--apply", action="store_true", help="Execute deployment (default dry-run)")
    d.set_defaults(func=deploy_mod.run)

    # rollback
    rb = sub.add_parser("rollback", help="Revert alias to previous version")
    rb.add_argument("--function", required=True, help="Lambda function name")
    rb.add_argument("--alias", default="live", help="Alias name")
    rb.add_argument("--target-version", help="Specific version to roll back to")
    rb.add_argument("--profile", help="AWS profile")
    rb.add_argument("--region", help="AWS region")
    rb.add_argument("--apply", action="store_true", help="Execute rollback (default dry-run)")
    rb.set_defaults(func=rollback_mod.run)

    return p


def _is_machine_output(args: argparse.Namespace) -> bool:
    fmt = getattr(args, "format", None)
    if fmt in ("json", "csv", "md", "markdown"):
        return True
    return False


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "no_banner", False) and not _is_machine_output(args):
        sys.stderr.write(BANNER + "\n")

    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        util.err("interrupted")
        return 130
    except FileNotFoundError as e:
        util.err(str(e))
        return 2
    except Exception as e:  # noqa: BLE001
        util.err(f"fatal: {e}")
        if os.environ.get("PYTHON_PIVOT_DEBUG"):
            import traceback

            traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
