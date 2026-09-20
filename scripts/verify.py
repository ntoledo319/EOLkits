#!/usr/bin/env python3
"""Run the project's local verification matrix with isolated, reusable tools.

No deployment, account credentials, global installs, or shell command strings.
Dependencies, caches, reports and command evidence stay in this repository's tmp/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = (
    "python",
    "al2023",
    "node",
    "worker",
    "editor",
    "api",
    "runner",
    "web",
    "action",
    "lint",
    "history",
    "maintenance",
    "audit",
)


class VerificationError(RuntimeError):
    """A required check failed or its prerequisites were unavailable."""


def confined(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise VerificationError(f"Refusing path outside the repository: {path}")
    return resolved


class Verifier:
    def __init__(self, *, offline: bool = False) -> None:
        self.offline = offline
        self.tmp = confined(ROOT / "tmp" / "verify")
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.env = os.environ.copy()
        for key, name in (
            ("TMPDIR", "runtime"),
            ("PIP_CACHE_DIR", "pip-cache"),
            ("npm_config_cache", "npm-cache"),
            ("XDG_CACHE_HOME", "cache"),
            ("XDG_CONFIG_HOME", "config"),
            ("UV_CACHE_DIR", "uv-cache"),
        ):
            target = confined(self.tmp / name)
            target.mkdir(exist_ok=True)
            self.env[key] = str(target)
        self.env.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "WRANGLER_SEND_METRICS": "false",
                "EOLKITS_BASE_PATH": "/EOLkits",
                "EOLKITS_SITE_URL": "https://ntoledo319.github.io/EOLkits",
                "EOLKITS_API_URL": "https://eolkits.com",
            }
        )
        self.evidence: list[dict] = []
        self.ready: dict[str, Path] = {}

    def run(
        self,
        args: list[str | Path],
        *,
        cwd: Path = ROOT,
        env: dict | None = None,
        timeout: int = 600,
    ) -> str:
        cwd = confined(cwd)
        command = [str(arg) for arg in args]
        started = time.monotonic()
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env or self.env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VerificationError(f"Could not finish {command[0]}: {exc}") from exc
        output = result.stdout
        self.evidence.append(
            {
                "command": command,
                "cwd": str(cwd),
                "exit": result.returncode,
                "seconds": round(time.monotonic() - started, 3),
                "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "output_bytes": len(output.encode()),
            }
        )
        if result.returncode:
            print(output[-18000:], file=sys.stderr)
            raise VerificationError(f"Exit {result.returncode}: {' '.join(command)}")
        lines = output.rstrip().splitlines()
        if lines:
            print("  " + " | ".join(lines[-2:])[:700], flush=True)
        return output

    def python(self, name: str, installs: list[list[str]], inputs: list[str]) -> Path:
        if name in self.ready:
            return self.ready[name]
        folder = confined(self.tmp / ("venv-" + name))
        interpreter = folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        fingerprint = hashlib.sha256()
        fingerprint.update(sys.version.encode())
        fingerprint.update(json.dumps(installs).encode())
        for rel in inputs:
            fingerprint.update(confined(ROOT / rel).read_bytes())
        digest = fingerprint.hexdigest()
        marker = folder / ".verified-dependencies"
        current = marker.read_text() if marker.exists() else ""
        runtime_matches = (
            interpreter.exists()
            and self.run([interpreter, "-c", "import sys; print(sys.version)"]).strip()
            == sys.version
        )
        if not runtime_matches or current != digest:
            if self.offline:
                raise VerificationError(
                    f"{name} environment missing or stale; run without --offline"
                )
            if not runtime_matches:
                self.run([sys.executable, "-m", "venv", "--clear", folder])
            for install in installs:
                self.run([interpreter, "-m", "pip", "install", *install])
            self.run([interpreter, "-m", "pip", "check"])
            marker.write_text(digest)
        self.ready[name] = interpreter
        return interpreter

    def npm(self, rel: str) -> Path:
        folder = confined(ROOT / rel)
        digest = hashlib.sha256(
            (folder / "package.json").read_bytes() + (folder / "package-lock.json").read_bytes()
        ).hexdigest()
        marker = self.tmp / ("npm-" + rel.replace("/", "-") + ".sha256")
        if not self.offline:
            self.run(["npm", "ci", "--no-audit"], cwd=folder)
            marker.write_text(digest)
        elif (
            not (folder / "node_modules").is_dir()
            or not marker.exists()
            or marker.read_text() != digest
        ):
            raise VerificationError(f"Missing or stale {rel} dependencies; run without --offline")
        return folder

    def pytest(self, interpreter: Path, rel: str) -> None:
        self.run(
            [
                interpreter,
                "-m",
                "pytest",
                "-q",
                rel,
                "-o",
                f"cache_dir={self.tmp / 'pytest-cache' / rel.replace('/', '-')}",
            ]
        )

    def check(self, group: str) -> None:
        print(f"[{group}]", flush=True)
        if group in {"python", "al2023"}:
            kit = "python-pivot" if group == "python" else "al2023-gate"
            rel = "kits/" + kit
            interpreter = self.python(kit, [["-e", rel + "[dev]"]], [rel + "/pyproject.toml"])
            self.pytest(interpreter, rel + "/test")
        elif group in {"node", "worker", "editor"}:
            rel = {
                "node": "kits/lambda-lifeline",
                "worker": "apps/worker",
                "editor": "apps/vscode-extension",
            }[group]
            folder = self.npm(rel)
            if group == "worker":
                self.run(["npm", "run", "build"], cwd=folder)
            self.run(["npm", "test"], cwd=folder)
            if group == "editor":
                self.run(["npm", "run", "package"], cwd=folder)
            if group == "worker":
                self.run(
                    [
                        "npm",
                        "exec",
                        "--",
                        "wrangler",
                        "deploy",
                        "--dry-run",
                        "--outdir",
                        self.tmp / "worker-bundle",
                    ],
                    cwd=folder,
                )
        elif group == "api":
            files = [
                "apps/grace-api/requirements.lock",
                "apps/grace-api/requirements-dev.txt",
                "apps/grace-api/requirements.txt",
            ]
            interpreter = self.python(
                "api", [["--require-hashes", "-r", files[0]], ["-r", files[1]]], files
            )
            self.pytest(interpreter, "apps/grace-api")
        elif group == "runner":
            files = ["apps/runner/requirements.lock", "apps/runner/requirements-test.lock"]
            interpreter = self.python(
                "runner", [["--require-hashes", "-r", file] for file in files], files
            )
            self.pytest(interpreter, "apps/runner")
            self.run([interpreter, "apps/runner/build_sample_report.py", "--check"])
        elif group == "web":
            lock = "apps/web/requirements-dev.lock"
            interpreter = self.python("web", [["--require-hashes", "-r", lock]], [lock])
            self.run([interpreter, "apps/web/build.py"])
            self.pytest(interpreter, "apps/web")
            self.run(["node", "apps/web/test_browser.mjs"])
        elif group == "action":
            if self.offline:
                raise VerificationError(
                    "The real Action provisions its dependencies; omit --offline for action"
                )
            self.run([sys.executable, "scripts/verify_action.py"])
            self.run(["node", "--test", "scripts/vscode-gallery-evidence.test.mjs"])
        elif group == "lint":
            interpreter = self.python(
                "lint", [["-r", "requirements-lint.txt"]], ["requirements-lint.txt"]
            )
            paths = [
                "kits/",
                "apps/grace-api",
                "apps/runner",
                "apps/web",
                "scripts/verify.py",
                "scripts/verify_action.py",
                "scripts/verify_maintenance.py",
                "scripts/verify_static_release.py",
                "tests/test_verify.py",
                "tests/test_deploy_scripts.py",
            ]
            self.run([interpreter, "-m", "ruff", "check", *paths])
            self.run([interpreter, "-m", "black", "--check", *paths])
            self.run(
                [
                    interpreter,
                    "-m",
                    "mypy",
                    "kits/al2023-gate/src",
                    "kits/python-pivot/src",
                    "--ignore-missing-imports",
                    "--cache-dir",
                    self.tmp / "mypy-cache",
                ]
            )
            scripts = sorted((ROOT / "deploy/grace").glob("*.sh"))
            for script in scripts:
                self.run(["bash", "-n", confined(script)])
            if not shutil.which("shellcheck"):
                raise VerificationError("shellcheck is required for the deployment lint gate")
            self.run(["shellcheck", "--severity=warning", *scripts])
        elif group == "history":
            self.run([sys.executable, "-m", "unittest", "-q", "tests/test_project_history.py"])
            self.run([sys.executable, "scripts/project_history.py", "validate"])
        elif group == "maintenance":
            self.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "-q",
                    "tests/test_deploy_scripts.py",
                    "tests/test_verify.py",
                ]
            )
            self.run([sys.executable, "scripts/verify_maintenance.py", "--inventory"])
        elif group == "audit":
            interpreter = self.python("audit", [["pip-audit>=2.10,<3"]], [])
            for lock in [
                "apps/grace-api/requirements.lock",
                "apps/runner/requirements.lock",
                "apps/runner/requirements-test.lock",
                "apps/web/requirements-dev.lock",
            ]:
                self.run([interpreter, "-m", "pip_audit", "-r", lock, "--progress-spinner", "off"])
            self.run(
                [
                    "node",
                    "scripts/audit-node-locks.mjs",
                    "kits/lambda-lifeline/package-lock.json",
                    "apps/worker/package-lock.json",
                    "apps/vscode-extension/package-lock.json",
                ]
            )
            for rel in ["kits/lambda-lifeline", "apps/worker", "apps/vscode-extension"]:
                self.run(
                    ["npm", "audit", "--package-lock-only", "--audit-level=high"],
                    cwd=ROOT / rel,
                )

    def save(self, success: bool | None) -> None:
        target = confined(self.tmp / "last-run.json")
        target.write_text(
            json.dumps(
                {
                    "success": success,
                    "status": "running" if success is None else "passed" if success else "failed",
                    "checks": self.evidence,
                },
                indent=2,
            )
            + "\n"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "groups", nargs="*", metavar="GROUP", help="all or one or more of: " + ", ".join(GROUPS)
    )
    parser.add_argument(
        "--offline", action="store_true", help="Reuse prepared environments; install nothing"
    )
    parser.add_argument(
        "--list", action="store_true", help="List groups without running checks or installing tools"
    )
    args = parser.parse_args(argv)
    unknown = set(args.groups) - {"all", *GROUPS}
    if unknown:
        parser.error("Unknown verification group: " + ", ".join(sorted(unknown)))
    if args.list:
        print("\n".join(GROUPS))
        return 0
    if sys.version_info < (3, 12):
        parser.error(
            "Verification requires Python 3.12+; the distributed kits retain Python 3.9 support"
        )
    if not args.groups:
        args.groups = ["all"]
    groups = GROUPS if "all" in args.groups else tuple(dict.fromkeys(args.groups))
    verifier = Verifier(offline=args.offline)
    # A killed/interrupted new run must not leave a previous successful receipt
    # looking like evidence that the newly requested checks passed.
    verifier.save(None)
    try:
        if any(group in groups for group in ("node", "worker", "editor", "web", "action", "audit")):
            version = verifier.run(["node", "--version"]).strip()
            if int(version.lstrip("v").split(".")[0]) < 24:
                raise VerificationError(
                    "Node.js 24+ is required by the dependency and tooling matrix"
                )
        for group in groups:
            verifier.check(group)
    except (VerificationError, OSError) as exc:
        verifier.save(False)
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    verifier.save(True)
    print("verification passed: " + ", ".join(groups))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
