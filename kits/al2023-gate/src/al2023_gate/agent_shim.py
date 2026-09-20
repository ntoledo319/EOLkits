"""Preserve monitoring-agent configuration in private, reviewable migration bundles."""

from __future__ import annotations

import re
from pathlib import Path

from . import util
from .artifacts import emit_report, json_text, write_bundle

AGENTS = {
    "datadog": {
        "main": "datadog-agent/datadog.yaml",
        "tree": "datadog-agent",
        "key": "api_key",
        "service": "datadog-agent",
        "docs": "https://docs.datadoghq.com/agent/supported_platforms/linux/",
    },
    "newrelic": {
        "main": "newrelic-infra.yml",
        "tree": "newrelic-infra",
        "key": "license_key",
        "service": "newrelic-infra",
        "docs": "https://docs.newrelic.com/docs/infrastructure/infrastructure-agent/linux-installation/package-manager-install/",
    },
}

MIGRATE = '''#!/usr/bin/env python3
"""Restore preserved configuration on a prepared AL2023 host; preview by default."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--target-root', required=True, help='AL2023 filesystem root (use / only on the prepared destination host)')
parser.add_argument('--apply', action='store_true')
parser.add_argument('--restart', action='store_true', help='Explicitly restart the installed agent after copying; only valid for target-root /')
args = parser.parse_args()
bundle = Path(__file__).resolve().parent
manifest = json.loads((bundle / 'manifest.json').read_text())
root = Path(args.target_root).resolve()
if args.restart and (not args.apply or root != Path('/')):
    parser.error('--restart requires --apply and target-root /')
def safe_target(relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise SystemExit('Unsafe target path in manifest')
    path = root / relative
    current = path
    while current != root:
        if current.is_symlink():
            raise SystemExit('Refusing a symlink in target configuration path')
        current = current.parent
    if not path.resolve().is_relative_to(root):
        raise SystemExit('Target escapes selected root')
    return path
release = safe_target('etc/os-release').read_text()
properties = dict(line.split('=', 1) for line in release.splitlines() if '=' in line and not line.startswith('#'))
if properties.get('ID', '').strip('"') != 'amzn' or properties.get('VERSION_ID', '').strip('"') != '2023':
    raise SystemExit('Target must identify itself as Amazon Linux 2023')
for relative in manifest['files']:
    source = bundle / 'config' / relative
    if source.is_symlink() or not source.resolve().is_relative_to(bundle / 'config'):
        raise SystemExit('Refusing a symlink or escaped bundle file')
    target = safe_target('etc/' + relative)
    if target.exists() and not target.is_file():
        raise SystemExit('Target is not a regular file')
if not args.apply:
    print(json.dumps({'dry_run': True, 'agent': manifest['agent'], 'files': manifest['files'], 'restart': False}, sort_keys=True))
    raise SystemExit(0)
if root == Path('/'):
    # Require a vendor-installed package; no curl-pipe-shell or repository changes.
    subprocess.run(['rpm', '-q', manifest['service']], check=True, capture_output=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup = root / ('al2023-agent-backup-' + stamp)
backup.mkdir(mode=0o700)
applied = []
try:
    for relative in manifest['files']:
        target = safe_target('etc/' + relative)
        previous = backup / relative
        existed = target.exists()
        if existed:
            previous.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copy2(target, previous)
            previous.chmod(0o600)
        missing = []
        parent = target.parent
        while not parent.exists():
            missing.append(parent)
            parent = parent.parent
        target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        if root == Path('/') and manifest['agent'] == 'datadog':
            import grp
            for parent in missing:
                os.chown(parent, 0, grp.getgrnam('dd-agent').gr_gid)
                parent.chmod(0o750)
        data = (bundle / 'config' / relative).read_bytes()
        candidate = target.with_name(target.name + '.al2023-staged-' + stamp)
        with os.fdopen(os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as handle:
            handle.write(data)
        if existed:
            before = target.stat()
            os.chown(candidate, before.st_uid, before.st_gid)
            candidate.chmod(before.st_mode & 0o777)
        else:
            candidate.chmod(0o640)
            if root == Path('/') and manifest['agent'] == 'datadog':
                import grp
                os.chown(candidate, 0, grp.getgrnam('dd-agent').gr_gid)
        os.replace(candidate, target)
        applied.append((target, previous, existed))
    if args.restart:
        subprocess.run(['systemctl', 'restart', manifest['service']], check=True)
        subprocess.run(['systemctl', 'is-active', '--quiet', manifest['service']], check=True)
except BaseException:
    for target, previous, existed in reversed(applied):
        if existed:
            # Content rollback retains the destination's original ownership.
            mode = target.stat().st_mode & 0o777
            shutil.copyfile(previous, target)
            target.chmod(mode)
        else:
            target.unlink()
    raise
print(json.dumps({'applied': True, 'backup': str(backup), 'files': manifest['files'], 'restart': args.restart}, sort_keys=True))
'''


def build_bundle(config_root, agent):
    root = Path(config_root).resolve()
    spec = AGENTS[agent]
    main = root / spec["main"]
    if main.is_symlink() or not main.resolve().is_relative_to(root) or not main.is_file():
        raise ValueError(f"Missing regular {spec['main']} beneath --config-root")
    if main.stat().st_size > 1024 * 1024:
        raise ValueError("Main agent configuration exceeds 1 MiB")
    text = main.read_text(encoding="utf-8")
    matches = re.findall(r"^" + spec["key"] + r":[ \t]*([^\r\n]*)", text, re.M)
    if (
        len(matches) != 1
        or not matches[0].split(" #", 1)[0].strip(" \t\"'")
        or matches[0].lstrip().startswith(("#", "|", ">", "null", "~", "{", "[", "&", "*", "!"))
    ):
        raise ValueError(
            f"Configuration requires one nonempty scalar {spec['key']}; environment-only credentials require manual migration"
        )
    paths = [main]
    tree = root / spec["tree"]
    if tree.exists():
        if tree.is_symlink():
            raise ValueError("Symlinked configuration directories are unsupported")
        paths.extend(tree.rglob("*"))
    files = {}
    size = 0
    for path in sorted(set(paths)):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Symlinks in configuration require manual review")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Configuration contains a non-regular file")
        size += path.stat().st_size
        if size > 16 * 1024 * 1024 or len(files) >= 1024:
            raise ValueError("Configuration exceeds the 16 MiB / 1024-file bound")
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    manifest = {
        "schema_version": 1,
        "agent": agent,
        "service": spec["service"],
        "files": sorted(files),
        "preserves_values": True,
        "reference": spec["docs"],
    }
    guidance = f"""# {agent} configuration migration

This bundle contains sensitive configuration. Keep the entire bundle private and outside Git. Existing keys, tags, proxies, integration files and comments are copied byte for byte. Environment variables, service overrides, binaries, embedded Python packages and custom integrations outside the selected tree are not captured.

1. Provision a separate AL2023 host through your normal process; this is not an in-place AL2 OS upgrade.
2. Install the vendor agent following {spec["docs"]}. Datadog AL2023 supports Agent 7.40+; use a currently supported release. New Relic publishes distinct amazonlinux/2023 RPM repositories for x86_64 and aarch64. Select the destination architecture and retain GPG verification.
3. Copy this private bundle to the new host. Inspect manifest.json and configs without posting credentials. Run `python3 migrate.py --target-root /` to preview. For a mounted image use its explicit root path instead.
4. Run `python3 migrate.py --target-root / --apply` to copy configs with backups, then review the installed agent's configuration and service permissions. Restart is a separate explicit `--restart` option; it is never performed by default.
5. Verify metrics, logs, tags, proxies, integration dependencies and hostname identity in the vendor UI before draining the AL2 host. Automatic start after package installation may already be enabled by the vendor.

Each apply records a private backup directory at the selected filesystem root. Restore its files to their matching etc paths through your normal change process if validation fails; retain the old host until telemetry is verified. The script rolls back copied contents on failure, but cannot guarantee rollback of effects from a requested service restart.
"""
    return manifest, {
        **{"config/" + name: data for name, data in files.items()},
        "manifest.json": json_text(manifest),
        "migrate.py": MIGRATE,
        "README.md": guidance,
    }


def run(args):
    manifest, files = build_bundle(args.config_root, args.agent)
    manifest["written"] = not util.is_dry_run(args)
    if manifest["written"]:
        if not args.out:
            raise ValueError("--apply requires --out for a new private migration bundle")
        write_bundle(args.out, files)
    emit_report(manifest)
    return 0
