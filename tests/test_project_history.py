"""Tests for scripts/project_history.py (stdlib unittest; also collectable by pytest)."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "project_history.py"

spec = importlib.util.spec_from_file_location("project_history", SCRIPT)
ph = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ph)


def _git(root: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()


EVENT_TEMPLATE = """---
id: {id}
title: {title}
kind: {kind}
scope: project-wide
paths: ["apps/**"]
significance: high
occurred_at: {occurred}
decided_at: null
merged_at: null
released_at: null
recorded_at: {recorded}
last_verified_at: null
summary: A test event.
claim_ids: [CLM-T-001]
source_ids: [SRC-git]
related: []
amends: []
supersedes: {supersedes}
status: {status}
confidence: plausible
secrets_reviewed: true
---

## Before-state and pressure
x
## Intended beneficiaries
x
## Goal, non-goal and definition of success
x
## Principles affirmed, introduced, weakened or challenged
x
## Alternatives considered and rejected paths
x
## Decision and rationale
x
## Implementation and evidence anchors
x
## Expected outcome
x
## Observed outcome
{outcome}
## Tradeoffs, debt and follow-ups
x
## Unresolved questions
x
"""

SECTIONS = [
    "Before-state and pressure",
    "Intended beneficiaries",
    "Goal, non-goal and definition of success",
    "Principles affirmed, introduced, weakened or challenged",
    "Alternatives considered and rejected paths",
    "Decision and rationale",
    "Implementation and evidence anchors",
    "Expected outcome",
    "Observed outcome",
    "Tradeoffs, debt and follow-ups",
    "Unresolved questions",
]


class Fixture:
    """A throwaway git repo with a minimal but valid history installation."""

    def __init__(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="ph-test-"))
        self.root = self.dir / "proj"
        self.root.mkdir()
        _git(self.root, "init", "-q", "-b", "main")
        (self.root / "apps").mkdir()
        (self.root / "apps" / "app.py").write_text("print('v1')\n")
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-q", "-m", "feat: first")
        self.sha1 = _git(self.root, "rev-parse", "HEAD")
        (self.root / "apps" / "app.py").write_text("print('v2')\n")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "status.json").write_text("{}\n")
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-q", "-m", "feat: second")
        self.sha2 = _git(self.root, "rev-parse", "HEAD")
        self.ph = self.root / ".project-history"
        (self.ph / "events" / "2026").mkdir(parents=True)
        (self.ph / "doctrine").mkdir()
        (self.ph / "schemas").mkdir()
        (self.ph / "templates").mkdir()
        self.docs = self.root / "docs" / "history"
        self.docs.mkdir()
        shutil.copy(REPO_ROOT / ".project-history" / "schemas" / "event.schema.json", self.ph / "schemas" / "event.schema.json")
        shutil.copy(REPO_ROOT / ".project-history" / "templates" / "event.md", self.ph / "templates" / "event.md")
        self.write_policy()
        self.write_ledgers()
        self.write_docs()
        self.write_event("eolkits-2026-01-01-first", "First decision", "origin", "2026-01-01", "2026-09-04", "implemented", "it shipped")
        self.write_event("eolkits-2026-09-04-bootstrap", "History system bootstrap", "bootstrap", "2026-09-04", "2026-09-04", "implemented", "installed")

    def write_policy(self) -> None:
        (self.ph / "policy.yml").write_text(
            "docs_dir: docs/history\n"
            "commands:\n"
            "  assess: python3 scripts/project_history.py assess\n"
            "  context: python3 scripts/project_history.py context\n"
            "  validate: python3 scripts/project_history.py validate\n"
            "  render: python3 scripts/project_history.py render\n"
            "  audit_full: python3 scripts/project_history.py audit --full\n"
            "  audit_incremental: python3 scripts/project_history.py audit --since HEAD~1\n"
            "  test: python3 -m unittest -q tests/test_project_history.py\n"
            "title: Test history\n"
            "reading_guide: Read carefully.\n"
            "reading_order: [ORIENTATION.md, NARRATIVE.md, IDEOLOGY.md, GOALS.md, DECISION_MAP.md, OPEN_QUESTIONS.md, TIMELINE.md, COVERAGE.md]\n"
            "event_sections:\n" + "".join(f"  - {s}\n" for s in SECTIONS) + "material_surfaces:\n"
            "  - name: app\n"
            '    globs: ["apps/**"]\n'
            "    why: the app\n"
            'noise_globs: ["docs/status.json"]\n'
            'noise_authors: ["bot"]\n'
        )

    def write_ledgers(self, anchor: str | None = None) -> None:
        anchor = anchor or self.sha1
        (self.ph / "sources.yml").write_text(
            "sources:\n"
            "  - id: SRC-git\n"
            "    kind: git-repository\n"
            f"    locator: {self.root}\n"
            "    evidence_class: direct\n"
            "    access: accessible\n"
            "    retrieved: 2026-09-04\n"
        )
        (self.ph / "claims.yml").write_text(
            "claims:\n"
            "  - claim_id: CLM-T-001\n"
            "    claim: The first commit created the app.\n"
            "    date: 2026-01-01\n"
            "    source_ids: [SRC-git]\n"
            f"    locator: {self.sha1}\n"
            "    evidence_type: direct\n"
            "    status: verified\n"
            "    confidence: confirmed\n"
            "    rationale: The commit exists.\n"
            "    caveats: none\n"
        )
        (self.ph / "contradictions.yml").write_text(
            "contradictions:\n"
            "  - id: CON-001\n"
            "    disputed_claim: Whether v2 was planned.\n"
            "    accounts:\n"
            "      - label: commit\n"
            "        account: says feat\n"
            "        source_ids: [SRC-git]\n"
            "      - label: memory\n"
            "        account: says fix\n"
            "        source_ids: [SRC-git]\n"
            "    disagreement_kind: interpretation\n"
            "    best_supported_reading: planned\n"
            "    confidence: plausible\n"
            "    resolving_evidence: a design note\n"
            "    status: open\n"
        )
        (self.ph / "state.yml").write_text(
            "repository: test/proj\n"
            "audit_date: 2026-09-04\n"
            f"full_audit_anchor: {anchor}\n"
            f"incremental_anchor: {anchor}\n"
            f"root_commit: {self.sha1}\n"
            "reachable_commit_count: 2\n"
            "refs_examined:\n"
            "  - name: refs/heads/main\n"
            f"    tip: {self.sha2}\n"
            "exclusion_counts:\n"
            "  bot: 0\n"
            "source_classes:\n"
            "  direct: 1\n"
            "inaccessible_sources: []\n"
            "evidence_gaps: []\n"
            "rewritten_history:\n"
            "  status: \"no\"\n"
            "  note: test\n"
        )
        (self.ph / "doctrine" / "principles.yml").write_text(
            "principles:\n"
            "  - id: P-01\n"
            "    version: 1\n"
            "    statement: Be truthful.\n"
            "    status: active\n"
            "    since: 2026-01-01\n"
            "    supersedes: null\n"
            "    claim_ids: [CLM-T-001]\n"
        )
        (self.ph / "doctrine" / "goals.yml").write_text(
            "goals:\n"
            "  - id: G-01\n"
            "    version: 1\n"
            "    statement: Ship.\n"
            "    status: active\n"
            "    proposed: 2026-01-01\n"
            "    review_by: 2026-12-01\n"
            "    supersedes: null\n"
            "    claim_ids: [CLM-T-001]\n"
            "    definition_of_success: it ships\n"
        )

    def write_docs(self) -> None:
        for name in ("ORIENTATION", "NARRATIVE", "IDEOLOGY", "GOALS", "OPEN_QUESTIONS"):
            body = f"# {name.title()}\n\nText with a [link](NARRATIVE.md) and a [ledger](../../.project-history/claims.yml).\n"
            if name == "ORIENTATION":
                body += "\n## Present tense\n\nThe project is in a test state.\n"
            (self.docs / f"{name}.md").write_text(body)
        (self.docs / "DECISION_MAP.md").write_text("# Decision map\n\n<!-- generated:decision-index -->\n<!-- /generated:decision-index -->\n")

    def write_event(self, eid, title, kind, occurred, recorded, status, outcome, supersedes="[]"):
        (self.ph / "events" / "2026" / f"{eid}.md").write_text(
            EVENT_TEMPLATE.format(id=eid, title=title, kind=kind, occurred=occurred, recorded=recorded, status=status, outcome=outcome, supersedes=supersedes)
        )

    def repo(self, use_git: bool = True):
        return ph.Repo(self.root, use_git=use_git)

    def render(self) -> None:
        ph.render(self.repo(), write=True)

    def cleanup(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


def run_cli(root: Path, *argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = ph.main(["--root", str(root), *argv])
    return code, buf.getvalue()


class YamlParserTests(unittest.TestCase):
    def test_mappings_sequences_and_scalars(self):
        data = ph.parse_yaml(
            "a: 1\nb: \"two\"\nc:\n  - x\n  - y: 2\n    z: [p, 'q']\nd: |\n  line1\n  line2\ne: null\nf: true\n# comment\ng: 'it''s'\n"
        )
        self.assertEqual(data["a"], 1)
        self.assertEqual(data["b"], "two")
        self.assertEqual(data["c"][0], "x")
        self.assertEqual(data["c"][1], {"y": 2, "z": ["p", "q"]})
        self.assertEqual(data["d"], "line1\nline2")
        self.assertIsNone(data["e"])
        self.assertTrue(data["f"])
        self.assertEqual(data["g"], "it's")

    def test_duplicate_key_rejected(self):
        with self.assertRaises(ph.YamlError):
            ph.parse_yaml("a: 1\na: 2\n")

    def test_sha_like_strings_stay_strings(self):
        data = ph.parse_yaml("sha: 05435fd26157dd1bd763e6e9fb1b4ecd39a7cecb\n")
        self.assertEqual(data["sha"], "05435fd26157dd1bd763e6e9fb1b4ecd39a7cecb")


class SecretScanTests(unittest.TestCase):
    def test_positive_control_and_clean_text(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            bad = tmp / "bad.md"
            # Synthetic, non-functional fixture shaped like a key (the AWS documentation example id).
            bad.write_text("token AKIAIOSFODNN7EXAMPLE here\n")
            good = tmp / "good.md"
            good.write_text("STRIPE_KEY is read from the environment; value never recorded.\n")
            hits = ph.scan_secrets([bad, good], tmp)
            self.assertEqual(len(hits), 1)
            self.assertTrue(hits[0].startswith("bad.md:1"))
        finally:
            shutil.rmtree(tmp)


class ValidateAndRenderTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.fx.render()

    def tearDown(self):
        self.fx.cleanup()

    def test_validate_passes_on_valid_fixture(self):
        rep = ph.validate(self.fx.repo())
        self.assertEqual(rep.errors, [], rep.errors)

    def test_render_is_byte_stable(self):
        before = {p: p.read_bytes() for p in self.fx.root.rglob("*.md")}
        changed = ph.render(self.fx.repo(), write=True)
        self.assertEqual(changed, [])
        after = {p: p.read_bytes() for p in self.fx.root.rglob("*.md")}
        self.assertEqual(before, after)
        self.assertEqual(ph.render(self.fx.repo(), write=False), [])

    def test_render_detects_drift_and_rewrites_links(self):
        (self.fx.docs / "TIMELINE.md").write_text("stale\n")
        self.assertIn("docs/history/TIMELINE.md", ph.render(self.fx.repo(), write=False))
        ph.render(self.fx.repo(), write=True)
        text = (self.fx.root / "PROJECT_HISTORY.md").read_text()
        self.assertIn("](docs/history/NARRATIVE.md)", text)
        self.assertIn("](.project-history/claims.yml)", text)
        self.assertIn("Appendix A", text)
        self.assertNotIn("../../.project-history", text)

    def test_duplicate_event_id_fails(self):
        self.fx.write_event("eolkits-2026-02-02-dup", "Dup", "product", "2026-02-02", "2026-09-04", "decided", "")
        text = (self.fx.ph / "events" / "2026" / "eolkits-2026-02-02-dup.md").read_text()
        (self.fx.ph / "events" / "2026" / "eolkits-2026-02-03-other.md").write_text(text)
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("duplicate id" in e or "filename must equal id" in e for e in rep.errors), rep.errors)

    def test_backfill_date_order_enforced(self):
        self.fx.write_event("eolkits-2026-03-03-late", "Late", "product", "2026-03-03", "2026-01-01", "decided", "")
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("recorded_at" in e and "earlier" in e for e in rep.errors), rep.errors)

    def test_broken_supersedes_link_fails(self):
        self.fx.write_event("eolkits-2026-04-04-sup", "Sup", "product", "2026-04-04", "2026-09-04", "decided", "", supersedes='["eolkits-2099-01-01-missing"]')
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("supersedes references unknown event" in e for e in rep.errors), rep.errors)

    def test_unknown_claim_and_source_fail(self):
        text = (self.fx.ph / "events" / "2026" / "eolkits-2026-01-01-first.md").read_text()
        text = text.replace("claim_ids: [CLM-T-001]", "claim_ids: [CLM-NOPE]")
        (self.fx.ph / "events" / "2026" / "eolkits-2026-01-01-first.md").write_text(text)
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("unknown claim_id CLM-NOPE" in e for e in rep.errors), rep.errors)

    def test_expired_deferral_fails_validation_and_audit(self):
        (self.fx.ph / "deferrals.yml").write_text(
            "deferrals:\n  - id: DEF-1\n    reason: hotfix\n    owner: owner\n    deadline: 2026-01-15\n    status: open\n"
        )
        rep = ph.validate(self.fx.repo(), as_of="2026-09-04")
        self.assertTrue(any("expired" in e for e in rep.errors), rep.errors)
        hard, _, _ = ph.audit(self.fx.repo(), None, True, "2026-09-04")
        self.assertTrue(any("expired" in h for h in hard))
        rep_ok = ph.validate(self.fx.repo(), as_of="2026-01-01")
        self.assertFalse(any("expired" in e for e in rep_ok.errors))

    def test_unreachable_anchor_detected(self):
        self.fx.write_ledgers(anchor="0" * 40)
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("not reachable" in e for e in rep.errors), rep.errors)
        hard, _, _ = ph.audit(self.fx.repo(), None, True, None)
        self.assertTrue(any("unreachable" in h for h in hard))

    def test_secret_fixture_in_artifact_fails(self):
        (self.fx.docs / "NARRATIVE.md").write_text("# N\n\nleak AKIAIOSFODNN7EXAMPLE\n")
        self.fx.render()
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("possible secret" in e for e in rep.errors), rep.errors)

    def test_missing_bootstrap_fails(self):
        (self.fx.ph / "events" / "2026" / "eolkits-2026-09-04-bootstrap.md").unlink()
        self.fx.render()
        rep = ph.validate(self.fx.repo())
        self.assertTrue(any("bootstrap" in e for e in rep.errors), rep.errors)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.fx.render()

    def tearDown(self):
        self.fx.cleanup()

    def test_assess_flags_material_surface_and_history_only(self):
        code, out = run_cli(self.fx.root, "assess")
        self.assertEqual(code, 0)
        self.assertIn("history impact: LIKELY", out)
        self.assertIn("app:", out)
        self.assertIn("history:recorded", out)
        (self.fx.root / "PROJECT_HISTORY.md").write_text((self.fx.root / "PROJECT_HISTORY.md").read_text() + "\n")
        _git(self.fx.root, "add", "PROJECT_HISTORY.md")
        _git(self.fx.root, "commit", "-q", "-m", "history: touch")
        code, out = run_cli(self.fx.root, "assess", "--range", "HEAD~1..HEAD")
        self.assertEqual(code, 0)
        self.assertIn("[history-only]", out)
        self.assertIn("history impact: UNLIKELY", out)

    def test_context_surfaces_events_for_paths(self):
        code, out = run_cli(self.fx.root, "context", "apps/app.py")
        self.assertEqual(code, 0)
        self.assertIn("eolkits-2026-01-01-first", out)
        self.assertIn("Active principles", out)
        self.assertIn("Present tense", out)
        code, out = run_cli(self.fx.root, "context")
        self.assertEqual(code, 0)

    def test_audit_modes(self):
        code, out = run_cli(self.fx.root, "audit", "--full")
        self.assertEqual(code, 0, out)
        self.assertIn("AUDIT OK", out)
        self.assertIn("cited by no claim", out)  # sha2 touches apps/ and is uncited
        code, out = run_cli(self.fx.root, "audit", "--since", "HEAD~1")
        self.assertEqual(code, 0, out)
        report = self.fx.root / "drift.md"
        code, out = run_cli(self.fx.root, "audit", "--full", "--report", str(report))
        self.assertEqual(code, 0)
        self.assertTrue(report.exists())
        self.assertIn("History drift report", report.read_text())

    def test_audit_detects_moved_ref(self):
        (self.fx.root / "apps" / "app.py").write_text("print('v3')\n")
        _git(self.fx.root, "commit", "-q", "-am", "feat: third")
        _, findings, _ = ph.audit(self.fx.repo(), None, True, None)
        self.assertTrue(any("advanced" in f for f in findings), findings)

    def test_validate_cli_and_render_check(self):
        code, out = run_cli(self.fx.root, "validate")
        self.assertEqual(code, 0, out)
        self.assertIn("VALIDATION PASSED", out)
        code, out = run_cli(self.fx.root, "render", "--check")
        self.assertEqual(code, 0, out)

    def test_schema_file_is_valid_json_with_required_fields(self):
        schema = json.loads((REPO_ROOT / ".project-history" / "schemas" / "event.schema.json").read_text())
        for key in ("id", "occurred_at", "recorded_at", "claim_ids", "secrets_reviewed"):
            self.assertIn(key, schema["required"])


@unittest.skipUnless((REPO_ROOT / ".project-history" / "state.yml").exists(), "real ledgers not installed")
class RealRepositoryTests(unittest.TestCase):
    def test_real_ledgers_validate_without_git(self):
        rep = ph.validate(ph.Repo(REPO_ROOT, use_git=False), check_git=False)
        self.assertEqual([e for e in rep.errors if "drift" not in e], [], rep.errors)


if __name__ == "__main__":
    sys.exit(unittest.main())
