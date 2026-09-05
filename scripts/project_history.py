#!/usr/bin/env python3
"""EOLkits living-history tool.

Deterministic, stdlib-only maintenance tool for the project's history ledgers under
``.project-history/`` and the curated chapters under ``docs/history/``.

Sub-commands (all runnable from the project root):

    assess   [--range A..B] [paths...]   inspect new work for potentially material surfaces
    context  [paths-or-component...]     smallest relevant history for an agent about to work
    validate [--no-git] [--as-of DATE]   validate ledgers, events, links, SHAs, secrets, drift
    render   [--check]                   deterministically rebuild generated views (byte-stable)
    audit    (--full | --since ANCHOR) [--report PATH] [--as-of DATE] [--strict]

The tool never writes historical interpretation. It only assembles, indexes and checks
human-curated prose and structured ledgers.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY_DIR_NAME = ".project-history"

SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

EVIDENCE_TYPES = {"direct", "contemporaneous", "retrospective", "behavioral", "inferred"}
CLAIM_STATUSES = {"verified", "reported", "inferred", "disputed", "unknown"}
CONFIDENCES = {"confirmed", "strongly_supported", "plausible", "speculative", "unknown"}
EVENT_STATUSES = {"open", "decided", "implemented", "observed", "closed", "reversed", "superseded"}
GOAL_STATES = {
    "proposed",
    "active",
    "measured",
    "narrowed",
    "expanded",
    "blocked",
    "achieved",
    "abandoned",
    "superseded",
}
PRINCIPLE_STATES = {"active", "weakened", "superseded", "retired"}
DISAGREEMENT_KINDS = {"fact", "chronology", "interpretation", "motive", "credit", "outcome"}
SOURCE_ACCESS = {"accessible", "inaccessible", "partial"}

# Secret patterns: mirrors the independent verifier plus a generic assignment check.
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ASIA[0-9A-Z]{16}"),
    re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[0-9A-Za-z]{16,}"),
    re.compile(r"\bwhsec_[0-9A-Za-z]{16,}"),
    re.compile(r"\bghp_[0-9A-Za-z]{30,}"),
    re.compile(r"\bgithub_pat_[0-9A-Za-z_]{20,}"),
    re.compile(r"\bgho_[0-9A-Za-z]{30,}"),
    re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bre_[A-Za-z0-9]{8}_[A-Za-z0-9]{20,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/]+:[^@\s/]{4,}@", re.I),
    re.compile(
        r"\b[A-Za-z_]*(?:SECRET|TOKEN|PASSWORD|API_KEY)[A-Za-z_]*\s*[=:]\s*[\"']?"
        r"(?!\$\{|\$[A-Z]|<|\[|\(|\{|null|none|redacted|changeme|xxx|your[-_])"
        r"[A-Za-z0-9+/=_\-]{24,}[\"']?"
    ),
]

GENERATED_START = "<!-- generated:{name} -->"
GENERATED_END = "<!-- /generated:{name} -->"


# --------------------------------------------------------------------------------------
# Minimal YAML subset parser (stdlib only). Supports block mappings, block sequences,
# sequences of mappings, inline lists, quoted scalars, literal (|) and folded (>) blocks,
# comments, null/bool/int scalars. This is the dialect the ledgers are written in.
# --------------------------------------------------------------------------------------


class YamlError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    out = []
    quote = None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(text: str):
    text = text.strip()
    if text == "" or text in ("null", "~"):
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        inner = text[1:-1]
        if text[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner
    if text.startswith("[") and text.endswith("]"):
        body = text[1:-1].strip()
        if not body:
            return []
        parts = []
        cur = []
        quote = None
        for ch in body:
            if quote:
                cur.append(ch)
                if ch == quote:
                    quote = None
            elif ch in ("'", '"'):
                quote = ch
                cur.append(ch)
            elif ch == ",":
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        parts.append("".join(cur))
        return [_scalar(p) for p in parts]
    if re.fullmatch(r"-?\d{1,12}", text):
        return int(text)
    return text


def parse_yaml(text: str):
    raw_lines = text.splitlines()
    lines = []  # (indent, content, raw)
    for raw in raw_lines:
        if raw.strip() == "---" and not lines:
            continue
        content = _strip_comment(raw)
        if not content.strip():
            lines.append((None, "", raw))
            continue
        indent = len(content) - len(content.lstrip(" "))
        lines.append((indent, content.strip(), raw))

    def block_scalar(start: int, base_indent: int, folded: bool):
        chunks = []
        i = start
        block_indent = None
        while i < len(lines):
            ind, cont, raw = lines[i]
            if ind is None:
                chunks.append("")
                i += 1
                continue
            if ind <= base_indent:
                break
            if block_indent is None:
                block_indent = ind
            chunks.append(raw[block_indent:] if len(raw) >= block_indent else raw.strip())
            i += 1
        while chunks and chunks[-1] == "":
            chunks.pop()
        if folded:
            return " ".join(c.strip() for c in chunks if c.strip()), i
        return "\n".join(chunks), i

    def parse_block(start: int, indent: int):
        i = start
        while i < len(lines) and lines[i][0] is None:
            i += 1
        if i >= len(lines):
            return None, i
        ind, cont, _ = lines[i]
        if ind != indent:
            if ind > indent:
                return parse_block(i, ind)
            return None, i
        if cont.startswith("- ") or cont == "-":
            return parse_seq(i, indent)
        return parse_map(i, indent)

    def parse_seq(start: int, indent: int):
        items = []
        i = start
        while i < len(lines):
            ind, cont, raw = lines[i]
            if ind is None:
                i += 1
                continue
            if ind < indent:
                break
            if ind > indent:
                raise YamlError(f"unexpected indent at line {i + 1}: {raw}")
            if not (cont.startswith("- ") or cont == "-"):
                break
            rest = cont[2:].strip() if cont != "-" else ""
            if rest == "":
                val, i = parse_block(i + 1, indent + 1)
                items.append(val)
                continue
            if re.match(r"^(?:\"[^\"]*\"|'[^']*'|[^\s\"'\[{-][^:]*?)\s*:(\s|$)", rest):
                # mapping item; rewrite this line as a mapping line at indent+2
                new_indent = ind + 2
                lines[i] = (new_indent, rest, " " * new_indent + rest)
                val, i = parse_map(i, new_indent)
                items.append(val)
                continue
            items.append(_scalar(rest))
            i += 1
        return items, i

    def parse_map(start: int, indent: int):
        result = {}
        i = start
        while i < len(lines):
            ind, cont, raw = lines[i]
            if ind is None:
                i += 1
                continue
            if ind < indent:
                break
            if ind > indent:
                raise YamlError(f"unexpected indent at line {i + 1}: {raw}")
            m = re.match(r"^(\"[^\"]*\"|'[^']*'|[^\s\"'\[{-][^:]*?)\s*:(?:\s+(.*))?$", cont)
            if not m:
                raise YamlError(f"expected 'key: value' at line {i + 1}: {raw}")
            key, val = m.group(1).strip(), m.group(2)
            if len(key) >= 2 and key[0] == key[-1] and key[0] in ("'", '"'):
                key = key[1:-1]
            if key in result:
                raise YamlError(f"duplicate key '{key}' at line {i + 1}")
            if val is None or val == "":
                # nested block or null
                j = i + 1
                while j < len(lines) and lines[j][0] is None:
                    j += 1
                if j < len(lines) and lines[j][0] > indent:
                    value, i = parse_block(j, lines[j][0])
                    result[key] = value
                    continue
                if j < len(lines) and lines[j][0] == indent and lines[j][1].startswith("- "):
                    value, i = parse_seq(j, indent)
                    result[key] = value
                    continue
                result[key] = None
                i = j
                continue
            if val in ("|", "|-", ">", ">-"):
                value, i = block_scalar(i + 1, indent, folded=val.startswith(">"))
                result[key] = value
                continue
            result[key] = _scalar(val)
            i += 1
        return result, i

    value, _ = parse_block(0, 0)
    return value


def load_yaml(path: Path):
    try:
        return parse_yaml(path.read_text(encoding="utf-8"))
    except YamlError as exc:
        raise YamlError(f"{path}: {exc}") from exc


# --------------------------------------------------------------------------------------
# Repository model
# --------------------------------------------------------------------------------------


class Repo:
    def __init__(self, root: Path, use_git: bool = True):
        self.root = Path(root)
        self.ph = self.root / HISTORY_DIR_NAME
        self.policy = load_yaml(self.ph / "policy.yml") or {}
        self.docs = self.root / self.policy.get("docs_dir", "docs/history")
        self.use_git = use_git and (self.root / ".git").exists()
        self._sha_cache: dict[str, bool] = {}
        self._related_repos: list[Path] | None = None

    # -- git helpers ------------------------------------------------------------------
    def git(self, *args: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout

    def commit_exists(self, sha: str, repo: Path | None = None) -> bool:
        target = repo or self.root
        proc = subprocess.run(
            ["git", "-C", str(target), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
        )
        return proc.returncode == 0

    def related_repos(self) -> list[Path]:
        if self._related_repos is not None:
            return self._related_repos
        repos: list[Path] = []
        sources = self.load_sources()
        for src in sources:
            for key in ("path", "locator"):
                value = src.get(key)
                if isinstance(value, str) and value.startswith("/"):
                    candidate = Path(value.split("#")[0].split(" ")[0].rstrip("/"))
                    while candidate != candidate.parent:
                        if (candidate / ".git").exists():
                            if candidate not in repos and candidate != self.root:
                                repos.append(candidate)
                            break
                        candidate = candidate.parent
        self._related_repos = repos
        return repos

    def sha_resolves(self, sha: str) -> bool:
        if sha in self._sha_cache:
            return self._sha_cache[sha]
        found = False
        if self.use_git:
            found = self.commit_exists(sha)
            if not found:
                for repo in self.related_repos():
                    if self.commit_exists(sha, repo):
                        found = True
                        break
        self._sha_cache[sha] = found
        return found

    # -- ledgers ------------------------------------------------------------------------
    def load_list(self, name: str, key: str) -> list[dict]:
        path = self.ph / name
        if not path.exists():
            return []
        data = load_yaml(path) or {}
        items = data.get(key) or []
        return [item for item in items if isinstance(item, dict)]

    def load_sources(self) -> list[dict]:
        return self.load_list("sources.yml", "sources")

    def load_claims(self) -> list[dict]:
        return self.load_list("claims.yml", "claims")

    def load_contradictions(self) -> list[dict]:
        return self.load_list("contradictions.yml", "contradictions")

    def load_principles(self) -> list[dict]:
        return self.load_list("doctrine/principles.yml", "principles")

    def load_goals(self) -> list[dict]:
        return self.load_list("doctrine/goals.yml", "goals")

    def load_deferrals(self) -> list[dict]:
        return self.load_list("deferrals.yml", "deferrals")

    def load_state(self) -> dict:
        path = self.ph / "state.yml"
        return (load_yaml(path) or {}) if path.exists() else {}

    def event_files(self) -> list[Path]:
        base = self.ph / "events"
        if not base.exists():
            return []
        return sorted(p for p in base.rglob("*.md") if p.is_file())

    def load_events(self) -> list[dict]:
        events = []
        for path in self.event_files():
            events.append(parse_event(path, self.ph))
        events.sort(key=lambda e: (e["meta"].get("occurred_at") or "9999", e["meta"].get("id") or ""))
        return events


def parse_event(path: Path, ph: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end == -1:
            raise YamlError(f"{path}: unterminated front matter")
        meta = parse_yaml(text[4:end]) or {}
        body = text[end + 5 :]
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return {
        "path": path,
        "rel": path.relative_to(ph.parent).as_posix(),
        "meta": meta,
        "sections": sections,
        "body": body,
    }


# --------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    def emit(self, out=sys.stdout) -> None:
        for msg in self.infos:
            out.write(f"ok: {msg}\n")
        for msg in self.warnings:
            out.write(f"WARN: {msg}\n")
        for msg in self.errors:
            out.write(f"FAIL: {msg}\n")

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_date(value) -> bool:
    return isinstance(value, str) and bool(DATE_RE.match(value))


def _is_date_or_range(value) -> bool:
    if _is_date(value):
        return True
    if isinstance(value, str):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*(?:\.\.|/|to)\s*(\d{4}-\d{2}-\d{2})$", value)
        return bool(m)
    return False


def validate_schema(instance, schema: dict, path: str, rep: Report) -> None:
    """Tiny JSON-schema subset validator: type, enum, pattern, required, properties, items."""
    stype = schema.get("type")
    if stype:
        types = stype if isinstance(stype, list) else [stype]
        ok = False
        for t in types:
            if t == "string" and isinstance(instance, str):
                ok = True
            elif t == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
                ok = True
            elif t == "boolean" and isinstance(instance, bool):
                ok = True
            elif t == "null" and instance is None:
                ok = True
            elif t == "array" and isinstance(instance, list):
                ok = True
            elif t == "object" and isinstance(instance, dict):
                ok = True
        if not ok:
            rep.error(f"{path}: expected type {stype}, got {type(instance).__name__}")
            return
    if "enum" in schema and instance not in schema["enum"]:
        rep.error(f"{path}: value {instance!r} not in {schema['enum']}")
    if "const" in schema and instance != schema["const"]:
        rep.error(f"{path}: value {instance!r} must equal {schema['const']!r}")
    if "pattern" in schema and isinstance(instance, str) and not re.search(schema["pattern"], instance):
        rep.error(f"{path}: value {instance!r} does not match /{schema['pattern']}/")
    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                rep.error(f"{path}: missing required field '{req}'")
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                validate_schema(instance[key], sub, f"{path}.{key}", rep)
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            rep.error(f"{path}: expected at least {schema['minItems']} items")
        items = schema.get("items")
        if items:
            for i, item in enumerate(instance):
                validate_schema(item, items, f"{path}[{i}]", rep)


def scan_secrets(paths: list[Path], root: Path) -> list[str]:
    hits = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat in SECRET_PATTERNS:
                if pat.search(line):
                    hits.append(f"{path.relative_to(root).as_posix()}:{lineno} (pattern {pat.pattern[:28]}...)")
                    break
    return hits


def history_artifact_files(repo: Repo) -> list[Path]:
    files = []
    ph_file = repo.root / "PROJECT_HISTORY.md"
    if ph_file.exists():
        files.append(ph_file)
    for base in (repo.docs, repo.ph):
        if base.exists():
            files.extend(sorted(p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts))
    return files


def markdown_links(text: str):
    for m in re.finditer(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", text):
        yield m.group(1)


def validate(repo: Repo, as_of: str | None = None, check_git: bool = True) -> Report:
    rep = Report()
    policy = repo.policy
    as_of = as_of or repo.load_state().get("audit_date") or "1970-01-01"

    # policy
    if not policy.get("docs_dir"):
        rep.error("policy.yml: docs_dir missing")
    commands = policy.get("commands") or {}
    for key in ("assess", "context", "validate", "render", "audit_full", "audit_incremental", "test"):
        if key not in commands:
            rep.error(f"policy.yml: commands.{key} missing")
    for name in (
        "ORIENTATION.md",
        "NARRATIVE.md",
        "IDEOLOGY.md",
        "GOALS.md",
        "DECISION_MAP.md",
        "TIMELINE.md",
        "OPEN_QUESTIONS.md",
    ):
        if not (repo.docs / name).exists():
            rep.error(f"{repo.docs.relative_to(repo.root)}/{name} missing")
    for name in (
        "sources.yml",
        "claims.yml",
        "contradictions.yml",
        "state.yml",
        "doctrine/principles.yml",
        "doctrine/goals.yml",
        "schemas/event.schema.json",
        "templates/event.md",
    ):
        if not (repo.ph / name).exists():
            rep.error(f"{HISTORY_DIR_NAME}/{name} missing")
    if rep.errors:
        return rep

    # sources
    sources = repo.load_sources()
    source_ids: set[str] = set()
    for i, src in enumerate(sources):
        sid = src.get("id")
        if not sid or not ID_RE.match(str(sid)):
            rep.error(f"sources[{i}]: invalid or missing id")
            continue
        if sid in source_ids:
            rep.error(f"sources: duplicate id {sid}")
        source_ids.add(sid)
        for field in ("kind", "locator", "access", "evidence_class"):
            if field not in src:
                rep.error(f"source {sid}: missing {field}")
        if src.get("access") not in SOURCE_ACCESS:
            rep.error(f"source {sid}: access must be one of {sorted(SOURCE_ACCESS)}")
        if src.get("retrieved") is not None and not _is_date(src.get("retrieved")):
            rep.error(f"source {sid}: retrieved must be YYYY-MM-DD or null")
    rep.info(f"{len(sources)} sources")

    # claims
    claims = repo.load_claims()
    claim_ids: set[str] = set()
    claim_by_id: dict[str, dict] = {}
    for i, claim in enumerate(claims):
        cid = claim.get("claim_id")
        if not cid or not ID_RE.match(str(cid)):
            rep.error(f"claims[{i}]: invalid or missing claim_id")
            continue
        if cid in claim_ids:
            rep.error(f"claims: duplicate claim_id {cid}")
        claim_ids.add(cid)
        claim_by_id[cid] = claim
        for field in ("claim", "source_ids", "locator", "evidence_type", "status", "confidence", "rationale", "caveats"):
            if field not in claim:
                rep.error(f"claim {cid}: missing {field}")
        date = claim.get("date") or claim.get("date_range")
        if not _is_date_or_range(date):
            rep.error(f"claim {cid}: date/date_range must be YYYY-MM-DD or a range")
        if claim.get("evidence_type") not in EVIDENCE_TYPES:
            rep.error(f"claim {cid}: evidence_type invalid")
        if claim.get("status") not in CLAIM_STATUSES:
            rep.error(f"claim {cid}: status invalid")
        if claim.get("confidence") not in CONFIDENCES:
            rep.error(f"claim {cid}: confidence invalid")
        for sid in claim.get("source_ids") or []:
            if sid not in source_ids:
                rep.error(f"claim {cid}: unknown source_id {sid}")
        if not claim.get("source_ids"):
            rep.error(f"claim {cid}: source_ids empty")
    rep.info(f"{len(claims)} claims")

    # contradictions
    contradictions = repo.load_contradictions()
    con_ids: set[str] = set()
    for i, con in enumerate(contradictions):
        cid = con.get("id")
        if not cid or not ID_RE.match(str(cid)):
            rep.error(f"contradictions[{i}]: invalid id")
            continue
        if cid in con_ids:
            rep.error(f"contradictions: duplicate id {cid}")
        con_ids.add(cid)
        for field in ("disputed_claim", "accounts", "disagreement_kind", "best_supported_reading", "confidence", "resolving_evidence"):
            if field not in con:
                rep.error(f"contradiction {cid}: missing {field}")
        accounts = con.get("accounts") or []
        if len(accounts) < 2:
            rep.error(f"contradiction {cid}: needs at least two accounts")
        if con.get("disagreement_kind") not in DISAGREEMENT_KINDS:
            rep.error(f"contradiction {cid}: disagreement_kind invalid")
        if con.get("confidence") not in CONFIDENCES:
            rep.error(f"contradiction {cid}: confidence invalid")
        for acc in accounts:
            if isinstance(acc, dict):
                for sid in acc.get("source_ids") or []:
                    if sid not in source_ids:
                        rep.error(f"contradiction {cid}: unknown source_id {sid}")
                for cl in acc.get("claim_ids") or []:
                    if cl not in claim_ids:
                        rep.error(f"contradiction {cid}: unknown claim_id {cl}")
    rep.info(f"{len(contradictions)} contradictions")

    # doctrine
    principles = repo.load_principles()
    p_ids: set[str] = set()
    for p in principles:
        pid = p.get("id")
        if not pid or not ID_RE.match(str(pid)):
            rep.error("principles: item with invalid id")
            continue
        if pid in p_ids:
            rep.error(f"principles: duplicate id {pid}")
        p_ids.add(pid)
    for p in principles:
        pid = p.get("id")
        for field in ("version", "statement", "status", "since", "supersedes", "claim_ids"):
            if field not in p:
                rep.error(f"principle {pid}: missing {field}")
        if p.get("status") not in PRINCIPLE_STATES:
            rep.error(f"principle {pid}: status invalid")
        if p.get("supersedes") is not None and p.get("supersedes") not in p_ids:
            rep.error(f"principle {pid}: supersedes unknown id {p.get('supersedes')}")
        if p.get("supersedes") == pid:
            rep.error(f"principle {pid}: supersedes itself")
        if not _is_date(p.get("since")):
            rep.error(f"principle {pid}: since must be a date")
        for cl in p.get("claim_ids") or []:
            if cl not in claim_ids:
                rep.error(f"principle {pid}: unknown claim_id {cl}")
    goals = repo.load_goals()
    g_ids: set[str] = set()
    for g in goals:
        gid = g.get("id")
        if not gid or not ID_RE.match(str(gid)):
            rep.error("goals: item with invalid id")
            continue
        if gid in g_ids:
            rep.error(f"goals: duplicate id {gid}")
        g_ids.add(gid)
    for g in goals:
        gid = g.get("id")
        for field in ("version", "statement", "status", "proposed", "supersedes", "claim_ids", "definition_of_success"):
            if field not in g:
                rep.error(f"goal {gid}: missing {field}")
        if g.get("status") not in GOAL_STATES:
            rep.error(f"goal {gid}: status invalid")
        if g.get("supersedes") is not None and g.get("supersedes") not in g_ids:
            rep.error(f"goal {gid}: supersedes unknown id {g.get('supersedes')}")
        if g.get("supersedes") == gid:
            rep.error(f"goal {gid}: supersedes itself")
        if not _is_date(g.get("proposed")):
            rep.error(f"goal {gid}: proposed must be a date")
        if g.get("review_by") is not None and not _is_date(g.get("review_by")):
            rep.error(f"goal {gid}: review_by must be a date or null")
        for cl in g.get("claim_ids") or []:
            if cl not in claim_ids:
                rep.error(f"goal {gid}: unknown claim_id {cl}")
    rep.info(f"{len(principles)} principles, {len(goals)} goals")

    # events
    schema = json.loads((repo.ph / "schemas" / "event.schema.json").read_text(encoding="utf-8"))
    required_sections = policy.get("event_sections") or []
    events = repo.load_events()
    e_ids: set[str] = set()
    for ev in events:
        meta = ev["meta"]
        eid = meta.get("id")
        if not eid:
            rep.error(f"{ev['rel']}: missing id")
            continue
        if eid in e_ids:
            rep.error(f"events: duplicate id {eid}")
        e_ids.add(eid)
        if ev["path"].stem != eid:
            rep.error(f"{ev['rel']}: filename must equal id ({eid})")
    bootstrap_seen = False
    for ev in events:
        meta = ev["meta"]
        eid = meta.get("id") or ev["rel"]
        validate_schema(meta, schema, f"event {eid}", rep)
        occurred = meta.get("occurred_at")
        recorded = meta.get("recorded_at")
        if _is_date(occurred) and _is_date(recorded) and recorded < occurred:
            rep.error(f"event {eid}: recorded_at {recorded} earlier than occurred_at {occurred}")
        for key in ("decided_at", "merged_at", "released_at", "last_verified_at"):
            value = meta.get(key)
            if value is not None and not _is_date(value):
                rep.error(f"event {eid}: {key} must be a date or null")
        for cl in meta.get("claim_ids") or []:
            if cl not in claim_ids:
                rep.error(f"event {eid}: unknown claim_id {cl}")
        for sid in meta.get("source_ids") or []:
            if sid not in source_ids:
                rep.error(f"event {eid}: unknown source_id {sid}")
        for key in ("related", "amends", "supersedes", "reversed_by", "superseded_by"):
            refs = meta.get(key) or []
            if isinstance(refs, str):
                refs = [refs]
            for ref in refs:
                if ref not in e_ids:
                    rep.error(f"event {eid}: {key} references unknown event {ref}")
                if ref == eid:
                    rep.error(f"event {eid}: {key} references itself")
        if meta.get("secrets_reviewed") is not True:
            rep.error(f"event {eid}: secrets_reviewed must be true")
        for section in required_sections:
            if section not in ev["sections"]:
                rep.error(f"event {eid}: missing section '## {section}'")
        if meta.get("kind") == "bootstrap":
            bootstrap_seen = True
        if meta.get("status") in ("implemented", "observed", "closed"):
            outcome = ev["sections"].get("Observed outcome", "")
            if not outcome.strip():
                rep.warn(f"event {eid}: status {meta.get('status')} but 'Observed outcome' is empty")
    if not bootstrap_seen:
        rep.error("events: no bootstrap event (kind: bootstrap) for the history system")
    rep.info(f"{len(events)} events")

    # deferrals
    for d in repo.load_deferrals():
        did = d.get("id", "?")
        for field in ("reason", "owner", "deadline", "status"):
            if field not in d:
                rep.error(f"deferral {did}: missing {field}")
        if d.get("status") == "open" and _is_date(d.get("deadline")) and d["deadline"] < as_of:
            rep.error(f"deferral {did}: expired on {d['deadline']} (as of {as_of})")

    # state
    state = repo.load_state()
    for key in (
        "repository",
        "audit_date",
        "full_audit_anchor",
        "incremental_anchor",
        "reachable_commit_count",
        "refs_examined",
        "exclusion_counts",
        "source_classes",
        "inaccessible_sources",
        "evidence_gaps",
        "rewritten_history",
    ):
        if key not in state:
            rep.error(f"state.yml: missing {key}")
    for key in ("full_audit_anchor", "incremental_anchor"):
        value = state.get(key)
        if not (isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value)):
            rep.error(f"state.yml: {key} must be a 40-hex SHA")
        elif check_git and repo.use_git and not repo.commit_exists(value):
            rep.error(f"state.yml: {key} {value} is not reachable (rewritten or missing history)")
    if check_git and repo.use_git and isinstance(state.get("reachable_commit_count"), int):
        actual = int(repo.git("rev-list", "--all", "--count").strip())
        if actual != state["reachable_commit_count"]:
            rep.warn(
                f"state.yml reachable_commit_count={state['reachable_commit_count']} but git reports {actual}; "
                "run audit and update state.yml"
            )

    # SHA resolution across all artifacts
    if check_git and repo.use_git:
        shas: set[str] = set()
        for path in history_artifact_files(repo):
            if path.suffix in (".md", ".yml", ".yaml", ".json"):
                shas.update(SHA_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
        unresolved = sorted(s for s in shas if not repo.sha_resolves(s))
        if unresolved:
            rep.error(f"{len(unresolved)} cited SHAs do not resolve: {', '.join(unresolved[:6])}")
        else:
            rep.info(f"{len(shas)} cited SHAs resolve")

    # secrets
    hits = scan_secrets(history_artifact_files(repo), repo.root)
    for hit in hits[:20]:
        rep.error(f"possible secret in {hit}")
    if not hits:
        rep.info("secret scan clean")

    # links
    bad = []
    for path in [repo.root / "PROJECT_HISTORY.md", *sorted(repo.docs.rglob("*.md"))]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for target in markdown_links(text):
            if re.match(r"^[a-z]+:", target, re.I):
                continue
            if not (path.parent / target).exists():
                bad.append(f"{path.relative_to(repo.root).as_posix()} -> {target}")
    for item in bad[:20]:
        rep.error(f"broken link {item}")
    if not bad:
        rep.info("internal links resolve")

    # render drift
    drift = render(repo, write=False)
    if drift:
        rep.error("rendered output has drifted; run render: " + ", ".join(drift))
    else:
        rep.info("rendered output up to date")
    return rep


# --------------------------------------------------------------------------------------
# Rendering (deterministic, no timestamps)
# --------------------------------------------------------------------------------------


def _short(text: str, n: int = 120) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _sort_key_date(value) -> str:
    if isinstance(value, str) and value:
        return value[:10]
    return "9999-99-99"


def render_timeline(repo: Repo, events: list[dict], claims: list[dict]) -> str:
    docs_rel = repo.docs.relative_to(repo.root).as_posix()
    lines = [
        "# Timeline",
        "",
        "Deterministic index generated by `scripts/project_history.py render` from the event",
        "capsules and the claim ledger. Do not edit by hand; edit the sources and re-render.",
        "Dates are the `occurred_at` of each event (author dates for commits unless a capsule",
        "says otherwise). `decided`, `merged`, and `released` columns are kept distinct on purpose.",
        "",
        "## Events",
        "",
        "| Occurred | Decided | Merged | Released | Event | Kind | Significance | Status | Confidence |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for ev in sorted(events, key=lambda e: (_sort_key_date(e["meta"].get("occurred_at")), e["meta"].get("id") or "")):
        m = ev["meta"]
        link = os.path.relpath(ev["path"], repo.docs).replace(os.sep, "/")
        lines.append(
            "| {o} | {d} | {mg} | {r} | [{t}]({l}) `{i}` | {k} | {s} | {st} | {c} |".format(
                o=m.get("occurred_at") or "—",
                d=m.get("decided_at") or "—",
                mg=m.get("merged_at") or "—",
                r=m.get("released_at") or "—",
                t=m.get("title", "").replace("|", "\\|"),
                l=link,
                i=m.get("id"),
                k=m.get("kind", ""),
                s=m.get("significance", ""),
                st=m.get("status", ""),
                c=m.get("confidence", ""),
            )
        )
    lines += ["", "## Claims by date", "", "| Date | Claim | Evidence | Status | Confidence |", "|---|---|---|---|---|"]
    for claim in sorted(claims, key=lambda c: (_sort_key_date(c.get("date") or c.get("date_range")), c.get("claim_id") or "")):
        lines.append(
            "| {d} | `{i}` {c} | {e} | {s} | {cf} |".format(
                d=claim.get("date") or claim.get("date_range") or "—",
                i=claim.get("claim_id"),
                c=_short(claim.get("claim", ""), 140).replace("|", "\\|"),
                e=claim.get("evidence_type", ""),
                s=claim.get("status", ""),
                cf=claim.get("confidence", ""),
            )
        )
    lines.append("")
    lines.append(f"Sources for every claim are listed in [`{HISTORY_DIR_NAME}/claims.yml`](../../{HISTORY_DIR_NAME}/claims.yml); the reading path is [`PROJECT_HISTORY.md`](../../PROJECT_HISTORY.md) (chapter directory: `{docs_rel}`).")
    lines.append("")
    return "\n".join(lines)


def render_decision_index(repo: Repo, events: list[dict]) -> str:
    lines = ["| Event | Kind | Related | Amends | Supersedes | Superseded by | Reversed by |", "|---|---|---|---|---|---|---|"]

    def fmt(refs) -> str:
        if not refs:
            return "—"
        if isinstance(refs, str):
            refs = [refs]
        return ", ".join(f"`{r}`" for r in refs)

    for ev in sorted(events, key=lambda e: (_sort_key_date(e["meta"].get("occurred_at")), e["meta"].get("id") or "")):
        m = ev["meta"]
        link = os.path.relpath(ev["path"], repo.docs).replace(os.sep, "/")
        lines.append(
            f"| [{m.get('title', '').replace('|', '/')}]({link}) `{m.get('id')}` | {m.get('kind', '')} | "
            f"{fmt(m.get('related'))} | {fmt(m.get('amends'))} | {fmt(m.get('supersedes'))} | "
            f"{fmt(m.get('superseded_by'))} | {fmt(m.get('reversed_by'))} |"
        )
    return "\n".join(lines)


def render_coverage(repo: Repo) -> str:
    state = repo.load_state()
    sources = repo.load_sources()
    lines = [
        "# Coverage and source inventory",
        "",
        "Generated from `.project-history/state.yml` and `.project-history/sources.yml` by",
        "`scripts/project_history.py render`. Edit those files, not this one.",
        "",
        "## Audit anchors",
        "",
        f"- Repository: `{state.get('repository', '')}`",
        f"- Audit date: {state.get('audit_date', '')}",
        f"- Full-audit anchor: `{state.get('full_audit_anchor', '')}`",
        f"- Incremental anchor: `{state.get('incremental_anchor', '')}`",
        f"- Reachable commits at audit (`git rev-list --all --count`): {state.get('reachable_commit_count', '')}",
        f"- Root commit: `{state.get('root_commit', '')}`",
        "",
        "## Refs examined",
        "",
    ]
    refs = state.get("refs_examined") or []
    if isinstance(refs, dict):
        for k, v in refs.items():
            lines.append(f"- {k}: {v}")
    else:
        for r in refs:
            if isinstance(r, dict):
                lines.append(f"- `{r.get('name')}` @ `{r.get('tip')}`" + (f" — {r.get('note')}" if r.get("note") else ""))
            else:
                lines.append(f"- {r}")
    lines += ["", "## Exclusion counts (classified, not deep-read)", ""]
    for k, v in (state.get("exclusion_counts") or {}).items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Deep-review coverage", ""]
    for k, v in (state.get("deep_review") or {}).items():
        lines.append(f"- {k}: {v}")
    matrix = state.get("coverage_matrix") or []
    if matrix:
        lines += ["", "## Coverage matrix (era × source class)", "", "| Era | Git | Docs in repo | GitHub metadata | Owner records | Depth |", "|---|---|---|---|---|---|"]
        for row in matrix:
            if isinstance(row, dict):
                lines.append(
                    f"| {row.get('era', '')} | {row.get('git', '')} | {row.get('repo_docs', '')} | {row.get('github', '')} | {row.get('owner_records', '')} | {row.get('depth', '')} |"
                )
    lines += ["", "## Source classes", ""]
    for k, v in (state.get("source_classes") or {}).items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Inaccessible sources", ""]
    for item in state.get("inaccessible_sources") or []:
        lines.append(f"- {item}")
    lines += ["", "## Evidence gaps", ""]
    for item in state.get("evidence_gaps") or []:
        lines.append(f"- {item}")
    rw = state.get("rewritten_history") or {}
    lines += ["", "## Rewritten history", ""]
    if isinstance(rw, dict):
        lines.append(f"- Status: {rw.get('status', '')}")
        if rw.get("note"):
            lines.append(f"- Note: {rw.get('note')}")
    else:
        lines.append(f"- {rw}")
    lines += ["", "## Source inventory", "", "| Id | Kind | Class | Access | Retrieved | Locator |", "|---|---|---|---|---|---|"]
    for src in sorted(sources, key=lambda s: s.get("id", "")):
        lines.append(
            f"| `{src.get('id')}` | {src.get('kind', '')} | {src.get('evidence_class', '')} | {src.get('access', '')} | "
            f"{src.get('retrieved') or '—'} | {_short(str(src.get('locator', '')), 110).replace('|', '\\|')} |"
        )
    lines.append("")
    lines.append("Completeness statement: all reachable Git objects were mechanically inventoried and the non-bot commits were semantically reviewed; that is not the same as all project history being known. See the evidence gaps above and `OPEN_QUESTIONS.md`.")
    lines.append("")
    return "\n".join(lines)


def _rewrite_links(text: str, chapter_dir_rel: str) -> str:
    def repl(m: re.Match) -> str:
        target = m.group(1)
        if re.match(r"^[a-z]+:", target, re.I) or target.startswith("#") or target.startswith("/"):
            return m.group(0)
        new = os.path.normpath(os.path.join(chapter_dir_rel, target)).replace(os.sep, "/")
        return m.group(0).replace(target, new, 1)

    return re.sub(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", repl, text)


def _replace_generated(text: str, name: str, body: str) -> str:
    start = GENERATED_START.format(name=name)
    end = GENERATED_END.format(name=name)
    if start not in text or end not in text:
        return text
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    return f"{pre}{start}\n{body}\n{end}{post}"


def render_project_history(repo: Repo, events: list[dict], claims: list[dict], contradictions: list[dict]) -> str:
    policy = repo.policy
    docs_rel = repo.docs.relative_to(repo.root).as_posix()
    title = policy.get("title") or "Project history"
    order = policy.get("reading_order") or [
        "ORIENTATION.md",
        "NARRATIVE.md",
        "eras/*.md",
        "IDEOLOGY.md",
        "GOALS.md",
        "DECISION_MAP.md",
        "OPEN_QUESTIONS.md",
        "TIMELINE.md",
        "COVERAGE.md",
    ]
    chapters: list[Path] = []
    for entry in order:
        if "*" in entry:
            chapters.extend(sorted(repo.docs.glob(entry)))
        else:
            p = repo.docs / entry
            if p.exists():
                chapters.append(p)
    out = [f"# {title}", ""]
    out.append(
        f"This is the canonical, unabridged reading path. It is assembled deterministically by "
        f"`scripts/project_history.py render` from the curated chapters in `{docs_rel}/` and the "
        f"structured ledgers in `{HISTORY_DIR_NAME}/`. Edit the chapters, not this file."
    )
    out.append("")
    out.append("## How to read this history")
    out.append("")
    out.append(policy.get("reading_guide") or "")
    out.append("")
    out.append("## Contents")
    out.append("")
    for p in chapters:
        first = next((line for line in p.read_text(encoding="utf-8").splitlines() if line.startswith("# ")), p.stem)
        anchor = re.sub(r"[^a-z0-9]+", "-", first[2:].lower()).strip("-")
        out.append(f"- [{first[2:]}](#{anchor}) — `{p.relative_to(repo.root).as_posix()}`")
    out.append("- [Appendix A — Event capsules](#appendix-a-event-capsules)")
    out.append("- [Appendix B — Contradiction register](#appendix-b-contradiction-register)")
    out.append("")
    for p in chapters:
        text = p.read_text(encoding="utf-8").rstrip("\n")
        chapter_dir_rel = p.parent.relative_to(repo.root).as_posix()
        text = _rewrite_links(text, chapter_dir_rel)
        out.append("---")
        out.append("")
        out.append(f"<!-- chapter: {p.relative_to(repo.root).as_posix()} -->")
        out.append(text)
        out.append("")
    out += ["---", "", "## Appendix A — Event capsules", ""]
    out.append("One capsule per material decision arc. Each carries distinct occurred/decided/merged/released/recorded dates, claim ids, and a secrets-reviewed marker.")
    out.append("")
    for ev in sorted(events, key=lambda e: (_sort_key_date(e["meta"].get("occurred_at")), e["meta"].get("id") or "")):
        m = ev["meta"]
        out.append(f"### {m.get('title')}")
        out.append("")
        out.append(
            f"`{m.get('id')}` · kind: {m.get('kind')} · scope: {m.get('scope')} · significance: {m.get('significance')} · "
            f"status: {m.get('status')} · confidence: {m.get('confidence')}  "
        )
        out.append(
            f"occurred {m.get('occurred_at') or 'unknown'} · decided {m.get('decided_at') or 'unknown'} · merged {m.get('merged_at') or 'unknown'} · "
            f"released {m.get('released_at') or 'unknown'} · recorded {m.get('recorded_at')} · last verified {m.get('last_verified_at') or 'unknown'}  "
        )
        out.append(f"claims: {', '.join(f'`{c}`' for c in (m.get('claim_ids') or [])) or '—'} · capsule: [`{ev['rel']}`]({ev['rel']})")
        out.append("")
        for section, body in ev["sections"].items():
            if not body.strip():
                continue
            out.append(f"**{section}.** {body.strip()}")
            out.append("")
    out += ["---", "", "## Appendix B — Contradiction register", ""]
    for con in sorted(contradictions, key=lambda c: c.get("id", "")):
        out.append(f"### {con.get('id')} — {_short(con.get('disputed_claim', ''), 160)}")
        out.append("")
        out.append(f"- Kind of disagreement: {con.get('disagreement_kind')}")
        for acc in con.get("accounts") or []:
            if isinstance(acc, dict):
                out.append(f"- Account ({acc.get('label', 'source')}): {acc.get('account')} — sources {', '.join(acc.get('source_ids') or [])}")
        out.append(f"- Best-supported reading ({con.get('confidence')}): {con.get('best_supported_reading')}")
        out.append(f"- Evidence that would resolve it: {con.get('resolving_evidence')}")
        out.append("")
    out.append(f"Full ledgers: [`{HISTORY_DIR_NAME}/claims.yml`]({HISTORY_DIR_NAME}/claims.yml), [`{HISTORY_DIR_NAME}/contradictions.yml`]({HISTORY_DIR_NAME}/contradictions.yml), [`{HISTORY_DIR_NAME}/sources.yml`]({HISTORY_DIR_NAME}/sources.yml), [`{HISTORY_DIR_NAME}/state.yml`]({HISTORY_DIR_NAME}/state.yml).")
    out.append("")
    return "\n".join(out)


def render(repo: Repo, write: bool = True) -> list[str]:
    """Render generated views. Returns the list of files whose content differs from disk."""
    events = repo.load_events()
    claims = repo.load_claims()
    contradictions = repo.load_contradictions()
    outputs: dict[Path, str] = {}
    outputs[repo.docs / "TIMELINE.md"] = render_timeline(repo, events, claims)
    outputs[repo.docs / "COVERAGE.md"] = render_coverage(repo)
    decision_map = repo.docs / "DECISION_MAP.md"
    if decision_map.exists():
        outputs[decision_map] = _replace_generated(
            decision_map.read_text(encoding="utf-8"), "decision-index", render_decision_index(repo, events)
        )
    changed = []
    for path, content in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(path.relative_to(repo.root).as_posix())
    if write:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                path.write_text(content, encoding="utf-8")
    # PROJECT_HISTORY.md is assembled from the chapters on disk. In check mode, a drifted
    # chapter implies the assembled document drifts too, so it is reported without rebuilding.
    ph_out = render_project_history(repo, events, claims, contradictions) if write or not changed else None
    if ph_out is None:
        changed.append("PROJECT_HISTORY.md")
    else:
        ph_path = repo.root / "PROJECT_HISTORY.md"
        if not ph_path.exists() or ph_path.read_text(encoding="utf-8") != ph_out:
            changed.append("PROJECT_HISTORY.md")
            if write:
                ph_path.write_text(ph_out, encoding="utf-8")
    return changed


# --------------------------------------------------------------------------------------
# Git-facing helpers for assess / audit
# --------------------------------------------------------------------------------------


def history_only_path(path: str, repo: Repo) -> bool:
    docs_rel = repo.docs.relative_to(repo.root).as_posix()
    return (
        path == "PROJECT_HISTORY.md"
        or path.startswith(docs_rel + "/")
        or path.startswith(HISTORY_DIR_NAME + "/")
        or re.match(r"^scripts/project_history\.[a-z]+$", path) is not None
        or re.match(r"^tests?/.*project_history.*$", path) is not None
    )


def match_surfaces(paths: list[str], repo: Repo) -> dict[str, list[str]]:
    surfaces = repo.policy.get("material_surfaces") or []
    noise = repo.policy.get("noise_globs") or []
    hits: dict[str, list[str]] = {}
    for path in paths:
        if any(fnmatch.fnmatch(path, g) for g in noise):
            continue
        for surface in surfaces:
            for glob in surface.get("globs") or []:
                if fnmatch.fnmatch(path, glob):
                    hits.setdefault(surface["name"], []).append(path)
                    break
    return hits


def commits_in_range(repo: Repo, rev_range: str) -> list[dict]:
    out = repo.git("log", "--format=%H%x00%an%x00%aI%x00%s", rev_range, check=False)
    commits = []
    for line in out.splitlines():
        parts = line.split("\x00")
        if len(parts) == 4:
            commits.append({"sha": parts[0], "author": parts[1], "date": parts[2], "subject": parts[3]})
    return commits


def commit_paths(repo: Repo, sha: str) -> list[str]:
    out = repo.git("show", "--format=", "--name-only", sha, check=False)
    return [p for p in out.splitlines() if p.strip()]


def default_range(repo: Repo) -> str:
    state = repo.load_state()
    anchor = state.get("incremental_anchor")
    head = repo.git("rev-parse", "HEAD").strip()
    if isinstance(anchor, str) and re.fullmatch(r"[0-9a-f]{40}", anchor) and repo.commit_exists(anchor) and anchor != head:
        proc = subprocess.run(["git", "-C", str(repo.root), "merge-base", "--is-ancestor", anchor, "HEAD"], capture_output=True)
        if proc.returncode == 0:
            return f"{anchor}..HEAD"
    parent = repo.git("rev-parse", "--verify", "--quiet", "HEAD~1", check=False).strip()
    return "HEAD~1..HEAD" if parent else head


def events_for_paths(events: list[dict], paths: list[str]) -> list[dict]:
    matched = []
    for ev in events:
        globs = ev["meta"].get("paths") or []
        if isinstance(globs, str):
            globs = [globs]
        if any(fnmatch.fnmatch(p, g) for p in paths for g in globs):
            matched.append(ev)
    return matched


def cmd_assess(repo: Repo, args: argparse.Namespace) -> int:
    print("EOLkits history-impact assessment (advisory; heuristics flag candidates, they do not decide meaning)")
    if not repo.use_git:
        print("git unavailable; nothing to assess")
        return 0
    rev_range = args.range or default_range(repo)
    noise_authors = set(repo.policy.get("noise_authors") or [])
    commits = commits_in_range(repo, rev_range) if ".." in rev_range else []
    print(f"range: {rev_range} ({len(commits)} commits)")
    changed: list[str] = []
    if ".." in rev_range:
        changed = [p for p in repo.git("diff", "--name-only", rev_range, check=False).splitlines() if p.strip()]
    if args.paths:
        changed = list(args.paths)
    wt = [line[3:].strip() for line in repo.git("status", "--porcelain", check=False).splitlines() if line.strip()]
    wt_paths = [p.split(" -> ")[-1].strip('"') for p in wt]
    substantive = [c for c in commits if c["author"] not in noise_authors]
    noise = len(commits) - len(substantive)
    history_only = [c for c in substantive if commit_paths(repo, c["sha"]) and all(history_only_path(p, repo) for p in commit_paths(repo, c["sha"]))]
    print(f"commits: {len(substantive)} substantive, {noise} by noise authors, {len(history_only)} history-only")
    for c in substantive[:40]:
        tag = " [history-only]" if c in history_only else ""
        print(f"  {c['sha']} {c['date'][:10]} {c['author']}: {_short(c['subject'], 90)}{tag}")
    hits = match_surfaces([p for p in changed if not history_only_path(p, repo)], repo)
    events = repo.load_events()
    print("")
    if hits:
        print("potentially material surfaces touched:")
        surfaces = {s["name"]: s for s in (repo.policy.get("material_surfaces") or [])}
        for name, paths in sorted(hits.items()):
            print(f"  - {name}: {len(paths)} path(s) — {surfaces[name].get('why', '')}")
            for p in paths[:8]:
                print(f"      {p}")
            related = events_for_paths(events, paths)
            if related:
                print("      existing events on these paths: " + ", ".join(f"`{e['meta'].get('id')}`" for e in related[:6]))
        verdict = "LIKELY"
    elif changed:
        verdict = "UNLIKELY"
        print("no material surface matched; changed paths look like noise or documentation-only work")
    else:
        verdict = "NONE"
        print("no committed changes in range")
    if wt_paths:
        print("")
        print("uncommitted working-tree changes (present-tense work, not history):")
        for p in wt_paths[:20]:
            print(f"  {p}")
    print("")
    print(f"history impact: {verdict}")
    print("Declare exactly one of: `history:recorded <event-id>` · `history:none — <reason>` · `history:defer — <tracking item, owner, deadline>`")
    print(f"See {repo.docs.relative_to(repo.root).as_posix()}/ORIENTATION.md for the materiality policy.")
    return 0


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def cmd_context(repo: Repo, args: argparse.Namespace) -> int:
    orientation = repo.docs / "ORIENTATION.md"
    events = repo.load_events()
    principles = repo.load_principles()
    goals = repo.load_goals()
    targets = list(args.paths or [])
    print("# History context" + (f" for {', '.join(targets)}" if targets else " (project-wide)"))
    print("")
    if orientation.exists():
        text = orientation.read_text(encoding="utf-8")
        present = _section(text, "Present tense") or _section(text, "Present-tense briefing")
        if present:
            print("## Present tense (from ORIENTATION.md)")
            print("")
            print(present)
            print("")
    active_p = [p for p in principles if p.get("status") == "active"]
    if active_p:
        print("## Active principles")
        print("")
        for p in active_p:
            print(f"- `{p['id']}` v{p.get('version')}: {p.get('statement')}")
        print("")
    active_g = [g for g in goals if g.get("status") in ("active", "measured", "blocked", "narrowed")]
    if active_g:
        print("## Goals in play")
        print("")
        for g in active_g:
            print(f"- `{g['id']}` ({g.get('status')}): {g.get('statement')} — success: {_short(g.get('definition_of_success', ''), 140)}")
        print("")
    if targets:
        matched = events_for_paths(events, targets)
        components = {t.lower() for t in targets}
        for ev in events:
            scope = str(ev["meta"].get("scope", "")).lower()
            comps = [str(c).lower() for c in (ev["meta"].get("components") or [])]
            if ev not in matched and (scope in components or any(c in components for c in comps)):
                matched.append(ev)
    else:
        order = {"foundational": 0, "high": 1, "medium": 2, "low": 3}
        matched = sorted(events, key=lambda e: (order.get(e["meta"].get("significance"), 9), e["meta"].get("occurred_at") or ""))[:8]
    print("## Relevant events" + ("" if targets else " (highest significance)"))
    print("")
    if not matched:
        print("- none recorded for these paths; check DECISION_MAP.md before assuming the area has no history")
    for ev in matched:
        m = ev["meta"]
        summary = m.get("summary") or _short(ev["sections"].get("Decision and rationale", ""), 200)
        print(f"- `{m.get('id')}` ({m.get('occurred_at')}, {m.get('status')}, {m.get('confidence')}): {m.get('title')} — {summary}")
        print(f"  capsule: {ev['rel']}")
    print("")
    oq = repo.docs / "OPEN_QUESTIONS.md"
    if oq.exists():
        print(f"Open questions and gaps: {oq.relative_to(repo.root).as_posix()}")
    print(f"Full reading path: PROJECT_HISTORY.md · declare history impact at task end (see {repo.docs.relative_to(repo.root).as_posix()}/ORIENTATION.md)")
    return 0


def cmd_validate(repo: Repo, args: argparse.Namespace) -> int:
    rep = validate(repo, as_of=args.as_of, check_git=not args.no_git)
    rep.emit()
    print(f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    print("VALIDATION " + ("PASSED" if rep.ok else "FAILED"))
    return 0 if rep.ok else 1


def cmd_render(repo: Repo, args: argparse.Namespace) -> int:
    if args.check:
        changed = render(repo, write=False)
        if changed:
            print("render drift: " + ", ".join(changed))
            return 1
        print("rendered output up to date")
        return 0
    changed = render(repo, write=True)
    if changed:
        print("rendered: " + ", ".join(changed))
    else:
        print("rendered output unchanged (byte-stable)")
    return 0


def audit(repo: Repo, rev_range: str | None, full: bool, as_of: str | None) -> tuple[list[str], list[str], list[str]]:
    """Returns (hard_failures, findings, notes)."""
    hard: list[str] = []
    findings: list[str] = []
    notes: list[str] = []
    state = repo.load_state()
    as_of = as_of or state.get("audit_date") or "1970-01-01"
    claims = repo.load_claims()
    events = repo.load_events()
    goals = repo.load_goals()
    if not repo.use_git:
        notes.append("git unavailable; only ledger-level checks were performed")
    else:
        head = repo.git("rev-parse", "HEAD").strip()
        notes.append(f"HEAD {head}")
        for key in ("full_audit_anchor", "incremental_anchor"):
            anchor = state.get(key)
            if isinstance(anchor, str) and re.fullmatch(r"[0-9a-f]{40}", anchor):
                if not repo.commit_exists(anchor):
                    hard.append(f"{key} {anchor} unreachable: ancestry rewritten or objects missing; re-audit the affected range")
            else:
                hard.append(f"{key} malformed")
        root_commit = state.get("root_commit")
        if isinstance(root_commit, str) and re.fullmatch(r"[0-9a-f]{40}", root_commit):
            roots = repo.git("rev-list", "--max-parents=0", "--all", check=False).split()
            if root_commit not in roots:
                hard.append(f"recorded root commit {root_commit} is no longer a root; history was rewritten or re-imported")
        # refs snapshot drift
        moved = []
        for ref in state.get("refs_examined") or []:
            if isinstance(ref, dict) and ref.get("name") and ref.get("tip"):
                current = repo.git("rev-parse", "--verify", "--quiet", ref["name"], check=False).strip()
                if not current:
                    moved.append(f"{ref['name']} (deleted)")
                elif current != ref["tip"]:
                    proc = subprocess.run(["git", "-C", str(repo.root), "merge-base", "--is-ancestor", ref["tip"], current], capture_output=True)
                    moved.append(f"{ref['name']} ({'advanced' if proc.returncode == 0 else 'REWRITTEN/force-moved'} {ref['tip'][:12]} -> {current[:12]})")
        if moved:
            findings.append("refs changed since the recorded snapshot: " + "; ".join(moved[:12]))
        actual = int(repo.git("rev-list", "--all", "--count").strip())
        if isinstance(state.get("reachable_commit_count"), int) and actual != state["reachable_commit_count"]:
            findings.append(f"reachable commits now {actual} (state.yml says {state['reachable_commit_count']})")
        # cited SHAs
        shas: set[str] = set()
        for claim in claims:
            shas.update(SHA_RE.findall(str(claim.get("locator", ""))))
            shas.update(SHA_RE.findall(str(claim.get("sha", ""))))
        for path in history_artifact_files(repo):
            if path.suffix in (".md", ".yml", ".yaml", ".json"):
                shas.update(SHA_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
        unresolved = sorted(s for s in shas if not repo.sha_resolves(s))
        if unresolved:
            hard.append(f"{len(unresolved)} cited SHAs no longer resolve (rewritten history?): {', '.join(unresolved[:5])}")
        notes.append(f"{len(shas)} cited SHAs checked")
        # unrecorded material commits
        if full:
            anchor = state.get("full_audit_anchor")
            rng = f"{anchor}..HEAD" if isinstance(anchor, str) and repo.commit_exists(anchor) else None
        else:
            rng = rev_range
        cited = set()
        for claim in claims:
            cited.update(SHA_RE.findall(str(claim.get("locator", ""))))
            cited.update(SHA_RE.findall(str(claim.get("sha", ""))))
        noise_authors = set(repo.policy.get("noise_authors") or [])
        if rng:
            commits = commits_in_range(repo, rng)
            notes.append(f"range {rng}: {len(commits)} commits")
            unrecorded = []
            for c in commits:
                if c["author"] in noise_authors or c["sha"] in cited:
                    continue
                paths = commit_paths(repo, c["sha"])
                if not paths or all(history_only_path(p, repo) for p in paths):
                    continue
                hits = match_surfaces(paths, repo)
                if hits:
                    unrecorded.append(f"{c['sha']} {c['date'][:10]} {c['author']}: {_short(c['subject'], 80)} -> {', '.join(sorted(hits))}")
            if unrecorded:
                findings.append(f"{len(unrecorded)} commit(s) touch material surfaces but are cited by no claim:")
                findings.extend("  " + u for u in unrecorded[:40])
        else:
            notes.append("no commit range could be derived for unrecorded-change detection")
    # deferrals
    for d in repo.load_deferrals():
        if d.get("status") == "open" and _is_date(d.get("deadline")) and d["deadline"] < as_of:
            hard.append(f"deferral {d.get('id')} expired {d['deadline']} (owner {d.get('owner')}): {d.get('reason')}")
        elif d.get("status") == "open":
            findings.append(f"open deferral {d.get('id')} due {d.get('deadline')} (owner {d.get('owner')})")
    # stale goals / missing outcomes / open contradictions
    for g in goals:
        if g.get("status") in ("active", "measured") and _is_date(g.get("review_by")) and g["review_by"] < as_of:
            findings.append(f"goal {g['id']} is past its review_by {g['review_by']} without a lifecycle update")
    for ev in events:
        m = ev["meta"]
        if m.get("status") in ("decided", "implemented") and not ev["sections"].get("Observed outcome", "").strip():
            findings.append(f"event {m.get('id')} has status {m.get('status')} but no observed outcome")
        if m.get("status") == "open":
            findings.append(f"event {m.get('id')} is still open (unresolved decision)")
    for con in repo.load_contradictions():
        if con.get("status", "open") == "open" and con.get("confidence") in ("speculative", "unknown"):
            findings.append(f"contradiction {con.get('id')} remains unresolved at {con.get('confidence')} confidence")
    return hard, findings, notes


def cmd_audit(repo: Repo, args: argparse.Namespace) -> int:
    if not args.full and not args.since:
        print("audit requires --full or --since <anchor>")
        return 2
    rev_range = None
    if args.since:
        rev_range = args.since if ".." in args.since else f"{args.since}..HEAD"
    hard, findings, notes = audit(repo, rev_range, args.full, args.as_of)
    lines = ["# History drift report", ""]
    lines.append(f"Mode: {'full' if args.full else 'incremental ' + (rev_range or '')}")
    if args.as_of:
        lines.append(f"As of: {args.as_of}")
    lines.append("")
    lines.append("## Notes")
    lines.extend(f"- {n}" for n in notes)
    lines.append("")
    lines.append("## Hard failures (invalid records, unreachable anchors, expired deferrals)")
    lines.extend(f"- {h}" for h in hard) if hard else lines.append("- none")
    lines.append("")
    lines.append("## Findings (advisory: likely unrecorded material work, stale goals, missing outcomes)")
    lines.extend(f"- {f}" for f in findings) if findings else lines.append("- none")
    lines.append("")
    lines.append("Findings are candidates for a human or agent to record as events; the tool never authors historical interpretation.")
    lines.append("")
    report = "\n".join(lines)
    if args.report:
        path = Path(args.report)
        if not path.is_absolute():
            path = repo.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"wrote {path.relative_to(repo.root).as_posix() if path.is_relative_to(repo.root) else path}")
    print(report)
    if hard:
        print("AUDIT FAILED")
        return 1
    if args.strict and findings:
        print("AUDIT FOUND GAPS (strict)")
        return 1
    print("AUDIT OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project_history.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None, help="project root (default: parent of scripts/)")
    parser.add_argument("--no-git", action="store_true", help="skip git-backed checks")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("assess", help="inspect new work for potentially material surfaces")
    p.add_argument("--range", default=None, help="git revision range A..B (default: incremental anchor..HEAD)")
    p.add_argument("paths", nargs="*", help="paths to assess instead of the git range")
    p.set_defaults(func=cmd_assess)
    p = sub.add_parser("context", help="smallest relevant history for the given paths or component")
    p.add_argument("paths", nargs="*")
    p.set_defaults(func=cmd_context)
    p = sub.add_parser("validate", help="validate ledgers, events, links, SHAs, secrets and render drift")
    p.add_argument("--as-of", default=None, help="date used for deferral expiry (default: state.audit_date)")
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser("render", help="rebuild generated views deterministically")
    p.add_argument("--check", action="store_true", help="exit 1 if rendering would change any file")
    p.set_defaults(func=cmd_render)
    p = sub.add_parser("audit", help="compare git and recorded evidence with history coverage")
    p.add_argument("--full", action="store_true")
    p.add_argument("--since", default=None, help="anchor commit or A..B range")
    p.add_argument("--report", default=None, help="write the drift report to this path")
    p.add_argument("--as-of", default=None)
    p.add_argument("--strict", action="store_true", help="exit 1 on advisory findings too")
    p.set_defaults(func=cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        repo = Repo(root, use_git=not args.no_git)
    except (YamlError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}")
        return 1
    try:
        return args.func(repo, args)
    except YamlError as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
