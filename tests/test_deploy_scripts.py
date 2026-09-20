"""Deployment must refuse an unsafe target before installing tools or using SSH."""

import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StaticDeploymentArguments(unittest.TestCase):
    def call(self, *args, **updates):
        env = os.environ.copy()
        env.pop("GRACE_HOST", None)
        env.pop("GRACE_WEBROOT", None)
        env.update(updates)
        return subprocess.run(
            ["bash", "deploy/grace/ship-web.sh", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_does_not_require_credentials(self):
        result = self.call("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rsync dry run", result.stdout)

    def test_unknown_and_extra_arguments_fail_before_environment_access(self):
        for args in (("--aply",), ("--apply", "extra"), ("--help", "extra")):
            with self.subTest(args=args):
                result = self.call(*args)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Set GRACE_HOST", result.stderr)

    def test_host_injection_is_rejected_before_dependencies_or_ssh(self):
        for host in ("-oProxyCommand=anything", "user@host;anything", "user@host\nanything"):
            with self.subTest(host=host):
                result = self.call(
                    GRACE_HOST=host, GRACE_WEBROOT="/home/ubuntu/sites/eolkits-webroot"
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("unsupported characters", result.stderr)

    def test_only_exact_static_target_is_allowed(self):
        for target in (
            "/",
            "/home/ubuntu/sites/neighbor",
            "/home/ubuntu/sites/../sites/eolkits-webroot",
        ):
            with self.subTest(target=target):
                result = self.call(GRACE_HOST="example.invalid", GRACE_WEBROOT=target)
                self.assertEqual(result.returncode, 2)
                self.assertIn("GRACE_WEBROOT", result.stderr)


if __name__ == "__main__":
    unittest.main()
