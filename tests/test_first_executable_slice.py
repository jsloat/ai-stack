import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path("/Users/jsloat/Dev/ai-stack")
CLI_PATH = REPO_ROOT / "bin" / "ai-stack"


class FirstExecutableSliceTests(unittest.TestCase):
    def run_cli(self, cwd: Path, skill: str):
        return subprocess.run(
            [sys.executable, str(CLI_PATH), "resolve-skill", skill],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_absent_local_config_and_index_are_clean_no_ops(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(Path(tmpdir), "pull-request")

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertFalse(trace["config"]["localConfigFound"])
        self.assertFalse(trace["skillIndex"]["found"])
        self.assertFalse(trace["resolution"]["matched"])
        self.assertEqual(trace["resolution"]["requestedSkill"], "pull-request")

    def test_skill_resolves_from_local_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes" / "local").mkdir(parents=True)
            (root / "skill-indexes" / "local" / "skill-index.example.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: skill-index
                    description: Test index
                    ---

                    # Local Skill Index

                    ## Skill Registry

                    | Skill | When to use | Source Repo | Skill Path |
                    |-------|-------------|-------------|------------|
                    | `pull-request` | Creating pull requests | `~/Dev/example-tools` | `.github/skills/pull-request/SKILL.md` |
                    """
                )
            )
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    defaultHarness: codex

                    models:
                      planner: sonnet
                      implementer: gpt-5.5
                      cheapVerifier: gpt-5.5-mini

                    telemetry:
                      enabled: false
                    """
                )
            )

            result = self.run_cli(root, "pull-request")

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["config"]["localConfigFound"])
        self.assertEqual(trace["config"]["effective"]["defaultHarness"], "codex")
        self.assertTrue(trace["skillIndex"]["found"])
        self.assertTrue(trace["skillIndex"]["parsed"])
        self.assertEqual(trace["skillIndex"]["rowCount"], 1)
        self.assertTrue(trace["resolution"]["matched"])
        self.assertEqual(trace["resolution"]["sourceRepo"], "~/Dev/example-tools")
        self.assertEqual(
            trace["resolution"]["skillPath"],
            ".github/skills/pull-request/SKILL.md",
        )

    def test_missing_skill_in_existing_index_returns_not_found_trace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes" / "local").mkdir(parents=True)
            (root / "skill-indexes" / "local" / "skill-index.example.md").write_text(
                textwrap.dedent(
                    """\
                    # Local Skill Index

                    ## Skill Registry

                    | Skill | When to use | Source Repo | Skill Path |
                    |-------|-------------|-------------|------------|
                    | `incident-review` | Reviewing incidents | `~/Dev/local-ops-skills` | `skills/incident-review/SKILL.md` |
                    """
                )
            )

            result = self.run_cli(root, "pull-request")

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["skillIndex"]["found"])
        self.assertTrue(trace["skillIndex"]["parsed"])
        self.assertFalse(trace["resolution"]["matched"])
        self.assertIsNone(trace["resolution"]["sourceRepo"])
        self.assertIsNone(trace["resolution"]["skillPath"])


if __name__ == "__main__":
    unittest.main()
