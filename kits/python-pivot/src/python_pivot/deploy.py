"""Staged canary deploy + rollback for Lambda Python runtime migrations.

Strategy:
  1. Verify an existing stable alias and an OK CloudWatch alarm
  2. Publish a new Lambda version with python3.12 runtime
  3. Update the alias through stages: 5% → 25% → 50% → 100%
  4. At each stage, wait the dwell time and check the alarm
  5. If the alarm trips or monitoring fails, roll back to the stable version

This is a SAFE default — it REQUIRES `--apply` and `--alarm <ARN>` to actually deploy.
`plan` is always available and prints the strategy without touching AWS.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import List, Optional

from . import util

DEFAULT_STAGES = [5, 25, 50, 100]
DEFAULT_DWELL_SECONDS = 60


@dataclass
class Stage:
    weight: int
    dwell_seconds: int


def build_plan(
    function_name: str,
    alias: str,
    stages: List[int],
    dwell: int,
    alarm: Optional[str],
    target_runtime: str,
) -> str:
    lines = [
        f"# Canary deployment plan for {function_name}",
        "",
        f"Target runtime   : {target_runtime}",
        f"Alias            : {alias}",
        f"Alarm ARN        : {alarm or '(none — deploy will REFUSE without one)'}",
        f"Stages           : {stages}",
        f"Dwell per stage  : {dwell}s",
        "",
        "## Steps",
    ]
    lines.append(f"1. Verify `{alias}` points to one stable version and the alarm is OK")
    lines.append(f"2. Update `{function_name}` to `{target_runtime}` and publish a new version")
    for i, w in enumerate(stages, start=1):
        lines.append(
            f"{i+2}. Update alias `{alias}` → route {w}% to the new version, wait {dwell}s, then check alarm state"
        )
    lines.append(
        f"{len(stages)+3}. If any alarm trips at any stage, auto-rollback alias to LATEST_STABLE and halt"
    )
    lines.append(
        f"{len(stages)+4}. On success, new version becomes 100%. Previous version retained for manual rollback."
    )
    return "\n".join(lines)


def _validate_stages(stages: List[int], dwell: int) -> str | None:
    if not stages:
        return "at least one canary stage is required"
    if any(weight <= 0 or weight > 100 for weight in stages):
        return "canary stages must be integers from 1 through 100"
    if stages != sorted(set(stages)):
        return "canary stages must be unique and strictly increasing"
    if stages[-1] != 100:
        return "the final canary stage must be 100"
    if dwell <= 0:
        return "dwell must be a positive number of seconds"
    return None


def _restore_alias(lam, function_name: str, alias: str, stable_version: str) -> None:
    lam.update_alias(
        FunctionName=function_name,
        Name=alias,
        FunctionVersion=stable_version,
        RoutingConfig={"AdditionalVersionWeights": {}},
    )


def _get_lambda_client(profile: Optional[str], region: str):
    try:
        import boto3
    except ImportError:
        util.err("boto3 not installed. Run: pip install 'python-pivot[aws]'")
        raise SystemExit(2)
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("lambda", region_name=region)


def _get_cw_client(profile: Optional[str], region: str):
    import boto3

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("cloudwatch", region_name=region)


def _alarm_state(cw, alarm_arn: str) -> str:
    # Accept either ARN or alarm name
    name = alarm_arn.split(":")[-1] if alarm_arn.startswith("arn:") else alarm_arn
    resp = cw.describe_alarms(AlarmNames=[name])
    alarms = resp.get("MetricAlarms", []) + resp.get("CompositeAlarms", [])
    if not alarms:
        raise RuntimeError(f"Alarm not found: {name}")
    return alarms[0]["StateValue"]  # OK | ALARM | INSUFFICIENT_DATA


def run(args: argparse.Namespace) -> int:
    fn = args.function
    alias = args.alias or "live"
    target_runtime = args.runtime or "python3.12"
    try:
        stages = [int(s) for s in (args.stages or ",".join(map(str, DEFAULT_STAGES))).split(",")]
        dwell = int(args.dwell or DEFAULT_DWELL_SECONDS)
    except ValueError:
        util.err("stages and dwell must contain integers")
        return 2
    validation_error = _validate_stages(stages, dwell)
    if validation_error:
        util.err(validation_error)
        return 2

    # Always print the plan first
    plan = build_plan(fn, alias, stages, dwell, args.alarm, target_runtime)

    if args.plan_only or not args.apply:
        print(plan)
        if not args.apply:
            util.warn(
                "DRY-RUN — pass --apply to execute. Requires --alarm <ARN>.",
                to_stderr=True,
            )
        return 0

    if not args.alarm:
        util.err("--apply requires --alarm <CloudWatch alarm ARN or name> as the rollback trigger.")
        return 2

    # Print plan then execute
    print(plan)
    print()

    region = args.region or "us-east-1"
    lam = _get_lambda_client(args.profile, region)
    cw = _get_cw_client(args.profile, region)

    # Prove the rollback target and alarm are usable before touching $LATEST.
    try:
        current_alias = lam.get_alias(FunctionName=fn, Name=alias)
    except lam.exceptions.ResourceNotFoundException:
        util.err(
            f"Alias {alias} not found on {fn}. Create a published-version alias before deploying."
        )
        return 2
    stable_version = str(current_alias.get("FunctionVersion") or "")
    weights = (current_alias.get("RoutingConfig") or {}).get("AdditionalVersionWeights") or {}
    if not stable_version or stable_version == "$LATEST" or weights:
        util.err(
            f"Alias {alias} must point to one published stable version with no existing canary weights."
        )
        return 2
    try:
        initial_alarm_state = _alarm_state(cw, args.alarm)
    except Exception as exc:
        util.err(f"Alarm preflight failed ({exc}); refusing to mutate the function.")
        return 2
    if initial_alarm_state != "OK":
        util.err(f"Alarm {args.alarm} is {initial_alarm_state}; refusing to mutate the function.")
        return 2
    util.info(f"Verified rollback target: {alias} → {stable_version}; alarm state: OK")

    # 1. Update function to new runtime (will produce new $LATEST).
    util.hdr(f"Updating runtime of {fn} → {target_runtime}")
    lam.update_function_configuration(FunctionName=fn, Runtime=target_runtime)

    # Wait for update to complete
    util.info("Waiting for update to settle…")
    waiter = lam.get_waiter("function_updated_v2")
    waiter.wait(FunctionName=fn)

    # 2. Publish version
    util.hdr("Publishing new version")
    v = lam.publish_version(
        FunctionName=fn, Description=f"python-pivot migration to {target_runtime}"
    )
    new_version = v["Version"]
    util.ok(f"Published version {new_version}")

    util.info(f"Previous stable version: {stable_version}")

    # 4. Canary loop
    for w in stages:
        util.hdr(f"Canary {w}% → {new_version} (stable {stable_version})")
        try:
            if w >= 100:
                # Full cut-over
                lam.update_alias(
                    FunctionName=fn,
                    Name=alias,
                    FunctionVersion=new_version,
                    RoutingConfig={"AdditionalVersionWeights": {}},
                )
            else:
                lam.update_alias(
                    FunctionName=fn,
                    Name=alias,
                    FunctionVersion=stable_version,
                    RoutingConfig={"AdditionalVersionWeights": {new_version: w / 100.0}},
                )
            util.info(f"  dwelling {dwell}s…")
            time.sleep(dwell)
            state = _alarm_state(cw, args.alarm)
            if state != "OK":
                raise RuntimeError(f"alarm state is {state}")
        except Exception as exc:
            util.err(f"Canary monitoring failed ({exc}) — rolling back.")
            try:
                _restore_alias(lam, fn, alias, stable_version)
            except Exception as rollback_exc:
                raise RuntimeError(
                    f"canary monitoring failed and alias rollback also failed: {rollback_exc}"
                ) from rollback_exc
            util.ok(f"Alias {alias} reverted to {stable_version}")
            return 1
        util.ok(f"  alarm state: {state}")

    util.hdr("Migration complete")
    util.ok(f"{fn} alias {alias} is now 100% on version {new_version} ({target_runtime})")
    util.info(
        f"Previous version {stable_version} retained. Manual rollback: `python-pivot rollback --function {fn} --alias {alias}`"
    )
    return 0
