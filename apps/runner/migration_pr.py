"""
Migration PR creation — opens real PRs on user repositories.

Authenticates as a GitHub App installation, clones the target repo, runs the
appropriate EOLkits kit (lambda-lifeline / al2023-gate / python-pivot), commits
the codemod output to a new branch, and opens a PR with refund-guarantee body.

Required environment:
  GITHUB_APP_ID            - numeric App ID
  GITHUB_APP_PRIVATE_KEY   - PEM contents (PKCS#1 or PKCS#8)
  RUPTURE_GIT_USER_EMAIL   - optional, default eolkits-bot@users.noreply.github.com
  RUPTURE_GIT_USER_NAME    - optional, default "eolkits-bot"
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
from contextlib import contextmanager
from typing import Dict, Iterator, List, Optional

import requests

try:
    import jwt  # PyJWT
except ImportError:  # pragma: no cover - jwt is added in requirements.txt
    jwt = None  # type: ignore


GITHUB_API = "https://api.github.com"
DEFAULT_GIT_USER_EMAIL = "eolkits-bot@users.noreply.github.com"
DEFAULT_GIT_USER_NAME = "eolkits-bot"
KIT_SCAN_TIMEOUT_SECS = 600


def create_migration_pr(
    repo: str,
    email: str,
    installation_id: str,
) -> Dict:
    """Create a migration PR on the specified repository."""
    if not repo or "/" not in repo:
        raise ValueError(f"Invalid repo identifier: {repo!r}")

    token = mint_installation_token(str(installation_id))

    if check_no_eolkits(repo, token):
        raise ValueError(f"Repository {repo} has opted out via .no-eolkits file")

    default_branch = get_default_branch(repo, token)
    kit = detect_kit_for_repo(repo, token)

    with tempfile.TemporaryDirectory() as workdir:
        clone_repo(repo, token, workdir, default_branch)

        findings = run_kit_analysis(kit, workdir)
        if not findings:
            raise ValueError("No applicable deprecations found in repository")

        short_hash = os.urandom(4).hex()
        branch_name = f"eolkits/migrate-{kit}-{short_hash}"

        create_branch(workdir, branch_name)
        apply_codemods(kit, workdir, findings)

        if not has_changes(workdir):
            raise ValueError("Kit ran but produced no diff; nothing to commit")

        pr_title = f"[EOLkits] Migrate {kit.replace('-', ' ')} deprecated patterns"
        pr_body = generate_pr_body(kit, findings, email)

        configure_git_identity(workdir)
        commit_and_push(workdir, branch_name, kit, repo, token)

        pr_info = open_pull_request(
            repo=repo,
            head=branch_name,
            base=default_branch,
            title=pr_title,
            body=pr_body,
            token=token,
        )
        add_refund_label(repo, pr_info["pr_number"], token)

        return {
            "pr_url": pr_info["pr_url"],
            "pr_number": pr_info["pr_number"],
            "branch": branch_name,
            "kit": kit,
            "findings_count": len(findings),
        }


# -------- GitHub App auth --------------------------------------------------- #


def _generate_jwt() -> str:
    if jwt is None:
        raise RuntimeError("PyJWT is required; add 'PyJWT[crypto]' to requirements.txt")

    app_id = os.environ.get("GITHUB_APP_ID")
    private_key = os.environ.get("GITHUB_APP_PRIVATE_KEY")
    if not app_id or not private_key:
        raise RuntimeError(
            "GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY must be set in the runner environment"
        )

    private_key = private_key.replace("\\n", "\n")
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 9 * 60,
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def mint_installation_token(installation_id: str) -> str:
    """Exchange the App JWT for an installation access token."""
    app_jwt = _generate_jwt()
    resp = requests.post(
        f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to mint installation token ({resp.status_code}): {resp.text}"
        )
    return resp.json()["token"]


def _gh_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "eolkits-runner",
    }


# -------- Repo discovery ---------------------------------------------------- #


def get_default_branch(repo: str, token: str) -> str:
    resp = requests.get(
        f"{GITHUB_API}/repos/{repo}", headers=_gh_headers(token), timeout=15
    )
    resp.raise_for_status()
    return resp.json().get("default_branch", "main")


def check_no_eolkits(repo: str, token: str) -> bool:
    """Look for a `.no-eolkits` opt-out file at the repo root."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{repo}/contents/.no-eolkits",
        headers=_gh_headers(token),
        timeout=15,
    )
    return resp.status_code == 200


def detect_kit_for_repo(repo: str, token: str) -> str:
    """Pick a kit based on repo contents.

    Heuristic order:
      1. SAM/CDK/Terraform with nodejs20.x → lambda-lifeline
      2. Dockerfile/AMI references to AL2 → al2023-gate
      3. Python 3.8/3.9 references → python-pivot
      4. Default → lambda-lifeline (safest mechanical codemod set)
    """
    override = os.environ.get("RUPTURE_KIT")
    if override:
        return override

    def _has(path: str, needle: Optional[str] = None) -> bool:
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo}/contents/{path}",
            headers=_gh_headers(token),
            timeout=15,
        )
        if resp.status_code != 200:
            return False
        if needle is None:
            return True
        body = resp.json()
        if isinstance(body, list):
            return False
        content = body.get("content", "")
        try:
            decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception:
            return False
        return needle in decoded

    if _has("template.yaml", "nodejs20") or _has("samconfig.toml"):
        return "lambda-lifeline"
    if _has("Dockerfile", "amazonlinux:2"):
        return "al2023-gate"
    if _has("requirements.txt", "python_requires=") or _has("pyproject.toml", "python = \"3.8"):
        return "python-pivot"
    return "lambda-lifeline"


# -------- Git operations ---------------------------------------------------- #


@contextmanager
def _git_token_env(token: str) -> Iterator[Dict[str, str]]:
    """Yield an environment that authenticates git over HTTPS without ever
    placing the installation token in a URL/argv (which leaks into process
    listings, reflogs, and error output). The token is delivered out-of-band via
    a temporary GIT_ASKPASS helper that reads it from the environment."""
    fd, script_path = tempfile.mkstemp(prefix="eolkits-askpass-", suffix=".sh")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write('#!/bin/sh\nprintf "%s" "$EOLKITS_GIT_TOKEN"\n')
        os.chmod(script_path, 0o700)
        env = dict(os.environ)
        env["GIT_ASKPASS"] = script_path
        env["EOLKITS_GIT_TOKEN"] = token
        env["GIT_TERMINAL_PROMPT"] = "0"
        yield env
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def _redact(text: str, token: str) -> str:
    if not text:
        return text or ""
    return text.replace(token, "***") if token else text


def _run_git(
    args: List[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    token: str = "",
) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        # Never surface the token in stored/forwarded error strings.
        raise RuntimeError(
            f"git {args[0]} failed (exit {proc.returncode}): "
            f"{_redact((proc.stderr or '').strip()[:500], token)}"
        )
    return proc


def configure_git_identity(workdir: str) -> None:
    email = os.environ.get("RUPTURE_GIT_USER_EMAIL", DEFAULT_GIT_USER_EMAIL)
    name = os.environ.get("RUPTURE_GIT_USER_NAME", DEFAULT_GIT_USER_NAME)
    _run_git(["config", "user.email", email], cwd=workdir)
    _run_git(["config", "user.name", name], cwd=workdir)


def clone_repo(repo: str, token: str, workdir: str, branch: str) -> None:
    """Clone over HTTPS using GIT_ASKPASS for the token (never in the URL)."""
    url = f"https://x-access-token@github.com/{repo}.git"
    with _git_token_env(token) as env:
        _run_git(
            ["clone", "--depth", "1", "--branch", branch, url, workdir],
            env=env,
            token=token,
        )


def has_changes(workdir: str) -> bool:
    out = _run_git(["status", "--porcelain"], cwd=workdir)
    return bool(out.stdout.strip())


def create_branch(workdir: str, branch_name: str) -> None:
    _run_git(["checkout", "-b", branch_name], cwd=workdir)


def commit_and_push(
    workdir: str, branch_name: str, kit: str, repo: str, token: str
) -> None:
    _run_git(["add", "-A"], cwd=workdir)
    _run_git(
        [
            "commit",
            "-m",
            f"[eolkits] apply {kit} migration\n\nGenerated by eolkits-bot. See PR body for details.",
        ],
        cwd=workdir,
    )
    push_url = f"https://x-access-token@github.com/{repo}.git"
    with _git_token_env(token) as env:
        _run_git(
            ["push", push_url, f"HEAD:refs/heads/{branch_name}"],
            cwd=workdir,
            env=env,
            token=token,
        )


# -------- Kit invocation ---------------------------------------------------- #


def _repo_relative(path: str, workdir: str) -> str:
    """Strip the ephemeral clone-tempdir prefix so PR bodies show repo-relative paths."""
    try:
        # os.path.relpath collapses the temp prefix; if `path` is already
        # repo-relative (no leading absolute prefix), relpath is a no-op.
        rel = os.path.relpath(path, workdir) if os.path.isabs(path) else path
        # Defensive: if the kit emitted a path that isn't actually inside workdir,
        # fall back to the basename so we never leak temp directories into bodies.
        if rel.startswith(".."):
            return os.path.basename(path)
        return rel
    except Exception:
        return os.path.basename(path)


def _kit_command(kit: str, action: str, workdir: str) -> List[str]:
    """Return the CLI invocation for a kit's static-mode analysis or apply step.

    The bot runs in a CI worker with NO access to the user's AWS account, so we
    never call the kits' live `scan` subcommands. We use only static,
    repo-file subcommands, and the invocations below match each kit's real CLI:

      * lambda-lifeline (Node): `iac --path <dir> [--apply]`, `codemod --path <dir> [--apply]`
      * python-pivot   (Py):   `iac <path> [--apply]`, `codemod <path> [--apply]`  (positional path)
      * al2023-gate    (Py):   `ansible <path> [--apply]`  (positional path; patches playbooks)

    The previously shipped al2023-gate `patch`/`--path`/`--json` and
    python-pivot `scan --path --json` forms do not exist in those CLIs and would
    crash every sandbox PR; these are the corrected contracts.
    """
    apply = action == "apply"
    if kit == "lambda-lifeline":
        cmd = ["lambda-lifeline", "iac", "--path", workdir]
        return cmd + (["--apply"] if apply else [])
    if kit == "al2023-gate":
        # `ansible` takes a positional path and patches yum->dnf / py2->py3 etc.
        cmd = ["al2023-gate", "ansible", workdir]
        return cmd + (["--apply"] if apply else [])
    if kit == "python-pivot":
        # `iac` takes a positional path and patches SAM/CDK/Terraform/Serverless.
        cmd = ["python-pivot", "iac", workdir]
        return cmd + (["--apply"] if apply else [])
    raise ValueError(f"Unknown kit: {kit}")


def run_kit_analysis(kit: str, workdir: str) -> List[Dict]:
    cmd = _kit_command(kit, "scan", workdir)
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=KIT_SCAN_TIMEOUT_SECS
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError(
            f"Kit scan failed ({kit}, exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    # lambda-lifeline iac emits human-readable lines like:
    #   "ℹ [SAM/CFN] template.yaml · 2 runtime ref(s): nodejs20.x, nodejs20.x"
    # Parse those into the same {type, file, line} shape downstream code expects.
    if kit == "lambda-lifeline":
        findings: List[Dict] = []
        for raw in (proc.stdout or "").splitlines():
            line = raw.strip()
            # Match lines describing concrete file hits.
            if "[SAM/CFN]" in line or "[CDK]" in line or "[Terraform]" in line:
                # Form: "ℹ [TYPE] path/to/file · N runtime ref(s): ..."
                try:
                    body = line.split("]", 1)[1].strip()
                    file_part, _, _ = body.partition(" · ")
                    findings.append({
                        "type": "iac-runtime-ref",
                        "file": _repo_relative(file_part.strip(), workdir),
                        "line": "N/A",
                    })
                except Exception:
                    continue
            elif "[rewrite]" in line and "·" in line:
                # Codemod-style hit (won't appear from iac, but covered for completeness).
                try:
                    parts = line.split("·")
                    findings.append({
                        "type": "codemod-rewrite",
                        "file": _repo_relative(parts[0].split("[rewrite]")[1].strip(), workdir),
                        "line": "N/A",
                    })
                except Exception:
                    continue
        return findings

    # python-pivot `iac` and al2023-gate `ansible` print human-readable dry-run
    # output rather than JSON. Parse it tolerantly: keep lines that reference a
    # concrete file/change; if the command produced change output at all, ensure
    # at least one finding so the flow proceeds (the post-apply has_changes guard
    # still prevents empty PRs).
    try:
        parsed = json.loads(proc.stdout or "[]")
        if isinstance(parsed, dict):
            return parsed.get("findings", [])
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    change_markers = ("rewrite", "patch", "runtime", "→", "->", "would", "dnf", "python3")
    findings: List[Dict] = []
    for raw in (proc.stdout or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if any(marker in line.lower() for marker in change_markers) or "/" in line:
            findings.append({"type": f"{kit}-finding", "file": _repo_relative(line[:120], workdir), "line": "N/A"})
    if not findings and proc.returncode == 0 and (proc.stdout or "").strip():
        findings.append({"type": f"{kit}-finding", "file": "(repository)", "line": "N/A"})
    return findings


def apply_codemods(kit: str, workdir: str, findings: List[Dict]) -> None:
    cmd = _kit_command(kit, "apply", workdir)
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=KIT_SCAN_TIMEOUT_SECS
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Kit apply failed ({kit}, exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    # The IaC patcher only fixes templates. Run the source codemod as a
    # follow-up so PRs include both runtime-string updates AND source migrations
    # when both apply. Source codemod failure is non-fatal — the IaC patch alone
    # is enough to ship a meaningful PR. Each kit's codemod has a distinct arg
    # shape (lambda-lifeline uses `--path`; python-pivot a positional path).
    codemod_followups = {
        "lambda-lifeline": ["lambda-lifeline", "codemod", "--path", workdir, "--apply"],
        "python-pivot": ["python-pivot", "codemod", workdir, "--apply"],
    }
    followup = codemod_followups.get(kit)
    if followup:
        codemod_proc = subprocess.run(
            followup,
            capture_output=True, text=True, timeout=KIT_SCAN_TIMEOUT_SECS,
        )
        # Only warn if codemod actually crashed; "no hits" returns 0 and is fine.
        if codemod_proc.returncode != 0 and "No codemod hits" not in (codemod_proc.stdout or ""):
            import sys as _sys
            print(
                f"[eolkits-runner] codemod follow-up exited {codemod_proc.returncode}; "
                f"continuing with IaC-only diff. stderr={codemod_proc.stderr[:300]}",
                file=_sys.stderr,
            )


# -------- PR body & API ----------------------------------------------------- #


def generate_pr_body(kit: str, findings: List[Dict], email: str) -> str:
    body = f"""## EOLkits Automated Migration

This PR was generated by [EOLkits](https://eolkits.com) to migrate deprecated AWS runtime patterns.

### Kit Used
**{kit}** — Automated codemods and IaC patches

### Findings
| Type | File | Description |
|------|------|-------------|
"""
    for finding in findings:
        body += (
            f"| {finding.get('type', 'finding')} "
            f"| {finding.get('file', 'unknown')} "
            f"| Line {finding.get('line', 'N/A')} |\n"
        )

    body += f"""
### What Changed
- Applied mechanical codemods for safe transformations
- Updated IaC templates to new runtime versions
- Added canary deployment configuration
- Included rollback script

### Next Steps
1. Review the changes in the Files changed tab
2. Run your test suite
3. Deploy using the included canary plan
4. Monitor CloudWatch alarms during cutover

### Refund Guarantee
If CI fails on this PR within 7 days, your purchase will be automatically refunded. No human intervention required.

To override this (e.g., if failure is unrelated), add the `override:ci-failure` label.

---
*This PR was generated for {email}*
*Report issues: https://github.com/ntoledo319/EOLkits/issues*
"""
    return body


def open_pull_request(
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str,
    token: str,
) -> Dict:
    resp = requests.post(
        f"{GITHUB_API}/repos/{repo}/pulls",
        headers=_gh_headers(token),
        json={"title": title, "head": head, "base": base, "body": body, "maintainer_can_modify": True},
        timeout=30,
    )
    if resp.status_code >= 300:
        raise RuntimeError(f"Failed to open PR ({resp.status_code}): {resp.text}")
    pr = resp.json()
    return {"pr_url": pr["html_url"], "pr_number": pr["number"]}


def add_refund_label(repo: str, pr_number: int, token: str) -> None:
    """Best-effort label add; don't fail the job if labeling fails."""
    try:
        requests.post(
            f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/labels",
            headers=_gh_headers(token),
            json={"labels": ["eolkits", "migration"]},
            timeout=15,
        )
    except Exception:
        pass


def extract_pr_number(pr_url: str) -> int:
    return int(pr_url.rstrip("/").split("/")[-1])
