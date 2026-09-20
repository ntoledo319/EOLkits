"""Verification tooling must not hide failed checks or accept stale dependencies."""

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify = load("verify")
maintenance = load("verify_maintenance")


class VerificationTests(unittest.TestCase):
    def test_help_and_list_need_no_dependency_install(self):
        for flag in ("--help", "--list"):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/verify.py"), flag],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("history", result.stdout)

    def test_failed_process_cannot_claim_success(self):
        runner = verify.Verifier(offline=True)
        result = subprocess.CompletedProcess(["irrelevant"], 1, "verification passed")
        with patch.object(verify.subprocess, "run", return_value=result):
            with (
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(verify.VerificationError),
            ):
                runner.run(["irrelevant"])
        self.assertEqual(runner.evidence[-1]["exit"], 1)

    def test_outside_cwd_refused_before_process_execution(self):
        runner = verify.Verifier(offline=True)
        with patch.object(verify.subprocess, "run") as run:
            with self.assertRaises(verify.VerificationError):
                runner.run(["irrelevant"], cwd=ROOT.parent)
            run.assert_not_called()

    def test_marker_detection_has_positive_and_negative_controls(self):
        self.assertTrue(maintenance.unresolved_markers("# TODO: implement a real result"))
        self.assertFalse(maintenance.unresolved_markers("# completed implementation"))

    def test_starting_a_new_run_replaces_previous_success(self):
        runner = verify.Verifier(offline=True)
        with tempfile.TemporaryDirectory(dir=runner.tmp) as temporary:
            runner.tmp = Path(temporary)
            runner.save(True)
            runner.save(None)
            receipt = json.loads((runner.tmp / "last-run.json").read_text())
            self.assertIsNone(receipt["success"])
            self.assertEqual(receipt["status"], "running")

    def test_offline_environment_rejects_an_old_interpreter(self):
        runner = verify.Verifier(offline=True)
        with tempfile.TemporaryDirectory(dir=runner.tmp) as temporary:
            runner.tmp = Path(temporary)
            interpreter = runner.tmp / "venv-example/bin/python"
            interpreter.parent.mkdir(parents=True)
            interpreter.write_text("fake interpreter for the mocked version probe")
            with patch.object(runner, "run", return_value="3.9.0 old-runtime") as run:
                with self.assertRaisesRegex(verify.VerificationError, "missing or stale"):
                    runner.python("example", [], [])
                self.assertEqual(run.call_count, 1)
                self.assertFalse((runner.tmp / "venv-example/.verified-dependencies").exists())

    def test_online_environment_replaces_an_old_interpreter_before_installing(self):
        runner = verify.Verifier(offline=False)
        with tempfile.TemporaryDirectory(dir=runner.tmp) as temporary:
            runner.tmp = Path(temporary)
            interpreter = runner.tmp / "venv-example/bin/python"
            interpreter.parent.mkdir(parents=True)
            interpreter.write_text("fake interpreter for the mocked version probe")
            with patch.object(runner, "run", return_value="3.9.0 old-runtime") as run:
                runner.python("example", [["example-package"]], [])
                commands = [call.args[0] for call in run.call_args_list]
                self.assertIn("--clear", commands[1])
                self.assertEqual(commands[2][1:4], ["-m", "pip", "install"])

    def test_offline_npm_refuses_changed_manifest_without_installing(self):
        runner = verify.Verifier(offline=True)
        with tempfile.TemporaryDirectory(dir=runner.tmp) as temporary:
            folder = Path(temporary)
            (folder / "package.json").write_text('{"name":"changed-input"}')
            (folder / "package-lock.json").write_text("{}")
            (folder / "node_modules").mkdir()
            relative = folder.relative_to(ROOT).as_posix()
            marker = runner.tmp / ("npm-" + relative.replace("/", "-") + ".sha256")
            marker.write_text("stale")
            try:
                with patch.object(runner, "run") as run:
                    with self.assertRaisesRegex(verify.VerificationError, "stale"):
                        runner.npm(relative)
                    run.assert_not_called()
            finally:
                marker.unlink()

    def test_document_link_check_detects_missing_target(self):
        folder = ROOT / "tmp/verify/tests"
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temporary:
            directory = Path(temporary)
            doc = directory / "index.md"
            doc.write_text("[broken](missing.md)\n")
            self.assertEqual(len(maintenance.check_links(doc)), 1)
            (directory / "missing.md").write_text("Present\n")
            self.assertEqual(maintenance.check_links(doc), [])


if __name__ == "__main__":
    unittest.main()
