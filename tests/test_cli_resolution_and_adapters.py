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


class CliResolutionAndAdapterTests(unittest.TestCase):
    def run_cli(self, cwd: Path, skill: str):
        return subprocess.run(
            [sys.executable, str(CLI_PATH), "resolve-skill", skill],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    def run_adapter_cli(self, cwd: Path, harness: str, prompt: str, extra_env=None):
        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(CLI_PATH), "adapter", harness, "--prompt", prompt],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env=env,
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
        self.assertEqual(trace["adapter"]["selected"], "copilot")
        self.assertTrue(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["mode"], "dry-run")
        self.assertEqual(trace["adapter"]["status"], "skipped")
        self.assertFalse(trace["adapter"]["attempted"])

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
        self.assertEqual(trace["adapter"]["selected"], "codex")
        self.assertTrue(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["mode"], "dry-run")
        self.assertEqual(trace["adapter"]["status"], "ready")
        self.assertTrue(trace["adapter"]["attempted"])
        self.assertEqual(trace["adapter"]["details"]["skillPath"], ".github/skills/pull-request/SKILL.md")

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
        self.assertEqual(trace["adapter"]["selected"], "copilot")
        self.assertTrue(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["status"], "skipped")
        self.assertFalse(trace["adapter"]["attempted"])

    def test_unknown_adapter_is_reported_deterministically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    defaultHarness: mystery

                    models:
                      planner: sonnet
                      implementer: gpt-5.5
                      cheapVerifier: gpt-5.5-mini

                    telemetry:
                      enabled: true
                    """
                )
            )

            result = self.run_cli(root, "pull-request")

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["adapter"]["selected"], "mystery")
        self.assertFalse(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["status"], "unsupported")
        self.assertFalse(trace["adapter"]["attempted"])

    def test_codex_live_adapter_reports_success_with_fake_executable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_rtk = root / "fake-rtk.py"
            fake_codex = root / "fake-codex.py"
            fake_rtk.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import subprocess
                    import sys

                    args = sys.argv[1:]
                    if not args or args[0] != "proxy":
                        print("unexpected rtk args:" + " ".join(args), file=sys.stderr)
                        sys.exit(9)

                    proc = subprocess.run(args[1:], capture_output=True, text=True, check=False)
                    sys.stdout.write(proc.stdout)
                    sys.stderr.write(proc.stderr)
                    sys.exit(proc.returncode)
                    """
                )
            )
            fake_rtk.chmod(0o755)
            path_dir = root / "bin"
            path_dir.mkdir()
            (path_dir / "rtk").write_text(fake_rtk.read_text())
            (path_dir / "rtk").chmod(0o755)
            fake_codex.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import sys
                    print("OK FROM FAKE CODEX")
                    print("ARGS:" + " ".join(sys.argv[1:]))
                    """
                )
            )
            fake_codex.chmod(0o755)
            (path_dir / "codex").write_text(fake_codex.read_text())
            (path_dir / "codex").chmod(0o755)

            result = self.run_adapter_cli(
                root,
                "codex",
                "Reply with OK",
                extra_env={
                    "PATH": f"{path_dir}:{os.environ.get('PATH', '')}",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["adapter"]["selected"], "codex")
        self.assertEqual(trace["adapter"]["mode"], "live")
        self.assertEqual(trace["adapter"]["status"], "completed")
        self.assertTrue(trace["adapter"]["attempted"])
        self.assertEqual(trace["adapter"]["exitCode"], 0)
        self.assertEqual(trace["adapter"]["resultText"], "OK FROM FAKE CODEX\nARGS:exec Reply with OK")
        self.assertEqual(trace["adapter"]["debug"]["stdout"], "OK FROM FAKE CODEX\nARGS:exec Reply with OK\n")
        self.assertEqual(trace["adapter"]["debug"]["stderr"], "")
        self.assertEqual(
            trace["adapter"]["details"]["command"],
            [str(path_dir / "rtk"), "proxy", str(path_dir / "codex"), "exec", "Reply with OK"],
        )
        self.assertEqual(trace["adapter"]["details"]["rtk"]["status"], "active")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], str(path_dir / "rtk"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["command"], str(path_dir / "codex"))
        self.assertIsNone(trace["adapter"]["details"]["harness"]["install"])

    def test_codex_live_adapter_reports_missing_rtk_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path_dir = root / "bin"
            path_dir.mkdir()
            result = self.run_adapter_cli(
                root,
                "codex",
                "Reply with OK",
                extra_env={
                    "PATH": f"{path_dir}:/usr/bin:/bin:/opt/homebrew/bin",
                },
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["adapter"]["selected"], "codex")
        self.assertEqual(trace["adapter"]["mode"], "live")
        self.assertEqual(trace["adapter"]["status"], "failed")
        self.assertTrue(trace["adapter"]["attempted"])
        self.assertIsNone(trace["adapter"]["exitCode"])
        self.assertEqual(trace["adapter"]["resultText"], "")
        self.assertIn("No such file or directory", trace["adapter"]["debug"]["stderr"])
        self.assertEqual(trace["adapter"]["details"]["reason"], "rtk-missing")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["status"], "missing")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], "rtk")
        self.assertIn(
            "curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh",
            trace["adapter"]["details"]["rtk"]["install"]["installCommands"],
        )
        self.assertIn(
            'export PATH="$HOME/.local/bin:$PATH"',
            trace["adapter"]["details"]["rtk"]["install"]["pathSuggestion"],
        )

    def test_codex_live_adapter_reports_missing_codex_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path_dir = root / "bin"
            path_dir.mkdir()
            fake_rtk = path_dir / "rtk"
            fake_rtk.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import subprocess
                    import sys

                    proc = subprocess.run(sys.argv[2:], capture_output=True, text=True, check=False)
                    sys.stdout.write(proc.stdout)
                    sys.stderr.write(proc.stderr)
                    sys.exit(proc.returncode)
                    """
                )
            )
            fake_rtk.chmod(0o755)

            result = self.run_adapter_cli(
                root,
                "codex",
                "Reply with OK",
                extra_env={
                    "PATH": f"{path_dir}:/usr/bin:/bin:/opt/homebrew/bin",
                },
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["adapter"]["selected"], "codex")
        self.assertEqual(trace["adapter"]["mode"], "live")
        self.assertEqual(trace["adapter"]["status"], "failed")
        self.assertTrue(trace["adapter"]["attempted"])
        self.assertNotEqual(trace["adapter"]["exitCode"], 0)
        self.assertEqual(trace["adapter"]["resultText"], "")
        self.assertIn("No such file or directory", trace["adapter"]["debug"]["stderr"])
        self.assertEqual(trace["adapter"]["details"]["reason"], "codex-missing")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["status"], "active")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], str(path_dir / "rtk"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["command"], "codex")
        self.assertIsNone(trace["adapter"]["details"]["harness"]["install"])


if __name__ == "__main__":
    unittest.main()
