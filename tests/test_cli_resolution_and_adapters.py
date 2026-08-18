import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Optional

from ai_stack.resolve_skill import infer_repo_root


REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "bin" / "ai-stack"


class CliResolutionAndAdapterTests(unittest.TestCase):
    def assert_telemetry(self, trace, *, command: str, outcome: str, capture_enabled: bool):
        self.assertIn("telemetry", trace)
        telemetry = trace["telemetry"]
        self.assertEqual(telemetry["command"], command)
        self.assertEqual(telemetry["outcome"], outcome)
        self.assertEqual(telemetry["captureEnabled"], capture_enabled)
        self.assertIsInstance(telemetry["startedAt"], str)
        self.assertIsInstance(telemetry["finishedAt"], str)
        self.assertIsInstance(telemetry["durationMs"], int)
        self.assertGreaterEqual(telemetry["durationMs"], 0)
        self.assertIsInstance(telemetry["route"], dict)

    def test_infer_repo_root_matches_expected_checkout_root(self):
        inferred_root = infer_repo_root()

        self.assertEqual(inferred_root, REPO_ROOT)
        self.assertTrue((inferred_root / "ai_stack" / "resolve_skill.py").exists())
        self.assertTrue((inferred_root / "bin" / "ai-stack").exists())
        self.assertTrue((inferred_root / "README.md").exists())

    def run_cli(self, cwd: Path, skill: str, root: Optional[Path] = None):
        cmd = [sys.executable, str(CLI_PATH), "resolve-skill", skill]
        if root is not None:
            cmd.extend(["--root", str(root)])
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    def run_adapter_cli(self, cwd: Path, harness: str, prompt: str, extra_env=None, root: Optional[Path] = None):
        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)
        cmd = [sys.executable, str(CLI_PATH), "adapter", harness, "--prompt", prompt]
        if root is not None:
            cmd.extend(["--root", str(root)])
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def run_sync_cli(
        self,
        cwd: Path,
        extra_env=None,
        root: Optional[Path] = None,
        apply: bool = False,
        harness: str = "codex",
        installed_skills_dir: Optional[Path] = None,
        backup_root: Optional[Path] = None,
    ):
        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)
        cmd = [sys.executable, str(CLI_PATH), "sync-skills", "--apply" if apply else "--dry-run", "--harness", harness]
        if root is not None:
            cmd.extend(["--root", str(root)])
        if installed_skills_dir is not None:
            cmd.extend(["--installed-skills-dir", str(installed_skills_dir)])
        if backup_root is not None:
            cmd.extend(["--backup-root", str(backup_root)])
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def run_sync_global_instructions_cli(
        self,
        cwd: Path,
        *,
        extra_env=None,
        root: Optional[Path] = None,
        apply: bool = False,
        harness: str = "all",
        codex_target_file: Optional[Path] = None,
        copilot_target_file: Optional[Path] = None,
        backup_root: Optional[Path] = None,
    ):
        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)
        cmd = [
            sys.executable,
            str(CLI_PATH),
            "sync-global-instructions",
            "--apply" if apply else "--dry-run",
            "--harness",
            harness,
        ]
        if root is not None:
            cmd.extend(["--root", str(root)])
        if codex_target_file is not None:
            cmd.extend(["--codex-target-file", str(codex_target_file)])
        if copilot_target_file is not None:
            cmd.extend(["--copilot-target-file", str(copilot_target_file)])
        if backup_root is not None:
            cmd.extend(["--backup-root", str(backup_root)])
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_absent_local_config_and_index_are_clean_no_ops(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(Path(tmpdir), "pull-request", root=Path(tmpdir))

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertFalse(trace["config"]["localConfigFound"])
        self.assertTrue(trace["config"]["valid"])
        self.assertFalse(trace["skillIndex"]["found"])
        self.assertFalse(trace["resolution"]["matched"])
        self.assertEqual(trace["resolution"]["requestedSkill"], "pull-request")
        self.assertEqual(trace["adapter"]["selected"], "copilot")
        self.assertTrue(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["mode"], "dry-run")
        self.assertEqual(trace["adapter"]["status"], "skipped")
        self.assertFalse(trace["adapter"]["attempted"])
        self.assert_telemetry(trace, command="resolve-skill", outcome="not-matched", capture_enabled=True)
        self.assertEqual(trace["telemetry"]["route"]["requestedSkill"], "pull-request")
        self.assertEqual(trace["telemetry"]["route"]["selectedHarness"], "copilot")

    def test_example_index_is_not_used_as_runtime_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes").mkdir(parents=True)
            (root / "skill-indexes" / "skill-index.example.yaml").write_text(
                textwrap.dedent(
                    """\
                    skills:
                      - id: pull-request
                        when: Example fallback index
                        repo: .
                        path: skills/example/SKILL.md
                    """
                )
            )

            result = self.run_cli(root, "pull-request", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["skillIndex"]["path"], "skill-indexes/skill-index.yaml")
        self.assertFalse(trace["skillIndex"]["found"])
        self.assertFalse(trace["resolution"]["matched"])

    def test_invalid_config_unknown_key_blocks_resolution_with_structured_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    defaultHarness: codex
                    unsupportedFlag: true
                    """
                )
            )

            result = self.run_cli(root, "pull-request", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["config"]["localConfigFound"])
        self.assertTrue(trace["config"]["parsed"])
        self.assertFalse(trace["config"]["valid"])
        self.assertEqual(trace["config"]["errors"], ["Unknown top-level config key: unsupportedFlag"])
        self.assertEqual(trace["adapter"]["status"], "blocked")
        self.assertEqual(trace["adapter"]["details"]["reason"], "invalid-config")
        self.assertFalse(trace["skillIndex"]["found"])
        self.assertFalse(trace["resolution"]["matched"])
        self.assert_telemetry(trace, command="resolve-skill", outcome="blocked", capture_enabled=False)

    def test_invalid_config_yaml_blocks_adapter_command_with_structured_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    defaultHarness:
                      - codex
                    """
                )
            )

            result = self.run_adapter_cli(root, "codex", "Reply with OK", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["config"]["localConfigFound"])
        self.assertTrue(trace["config"]["parsed"])
        self.assertFalse(trace["config"]["valid"])
        self.assertEqual(trace["config"]["errors"], ["defaultHarness must be a string"])
        self.assertEqual(trace["adapter"]["status"], "blocked")
        self.assertEqual(trace["adapter"]["details"]["reason"], "invalid-config")
        self.assertFalse(trace["adapter"]["attempted"])
        self.assert_telemetry(trace, command="adapter", outcome="blocked", capture_enabled=False)
        self.assertEqual(trace["telemetry"]["route"]["selectedHarness"], "codex")

    def test_invalid_config_nonexistent_ai_stack_repo_blocks_resolution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    repos:
                      aiStack: ./missing-ai-stack
                    """
                )
            )

            result = self.run_cli(root, "pull-request", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertFalse(trace["config"]["valid"])
        self.assertEqual(trace["config"]["errors"], ["repos.aiStack must point to an existing path"])
        self.assertEqual(trace["adapter"]["status"], "blocked")
        self.assertEqual(trace["adapter"]["details"]["reason"], "invalid-config")
        self.assert_telemetry(trace, command="resolve-skill", outcome="blocked", capture_enabled=False)

    def test_valid_config_ai_stack_repo_path_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ai_stack_checkout = root / "worktrees" / "ai-stack"
            ai_stack_checkout.mkdir(parents=True)
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    repos:
                      aiStack: ./worktrees/ai-stack
                    """
                )
            )

            result = self.run_cli(root, "pull-request", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["config"]["valid"])
        self.assertEqual(trace["config"]["effective"]["repos"]["aiStack"], "./worktrees/ai-stack")
        self.assertEqual(trace["adapter"]["status"], "skipped")
        self.assert_telemetry(trace, command="resolve-skill", outcome="not-matched", capture_enabled=True)

    def test_skill_resolves_from_skill_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes").mkdir(parents=True)
            (root / "skill-indexes" / "skill-index.yaml").write_text(
                textwrap.dedent(
                    """\
                    name: skill-index
                    description: Test index
                    skills:
                      - id: pull-request
                        when: Creating pull requests
                        repo: ~/Dev/example-tools
                        path: .github/skills/pull-request/SKILL.md
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

            result = self.run_cli(root, "pull-request", root=root)

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["config"]["localConfigFound"])
        self.assertTrue(trace["config"]["parsed"])
        self.assertTrue(trace["config"]["valid"])
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
        self.assert_telemetry(trace, command="resolve-skill", outcome="matched", capture_enabled=False)
        self.assertEqual(trace["telemetry"]["route"]["requestedSkill"], "pull-request")
        self.assertEqual(trace["telemetry"]["route"]["selectedHarness"], "codex")

    def test_missing_skill_in_existing_index_returns_not_found_trace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes").mkdir(parents=True)
            (root / "skill-indexes" / "skill-index.yaml").write_text(
                textwrap.dedent(
                    """\
                    skills:
                      - id: incident-review
                        when: Reviewing incidents
                        repo: ~/Dev/local-ops-skills
                        path: skills/incident-review/SKILL.md
                    """
                )
            )

            result = self.run_cli(root, "pull-request", root=root)

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
        self.assert_telemetry(trace, command="resolve-skill", outcome="not-matched", capture_enabled=True)

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

            result = self.run_cli(root, "pull-request", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["config"]["valid"])
        self.assertEqual(trace["adapter"]["selected"], "mystery")
        self.assertFalse(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["status"], "unsupported")
        self.assertFalse(trace["adapter"]["attempted"])
        self.assert_telemetry(trace, command="resolve-skill", outcome="not-matched", capture_enabled=True)

    def test_copilot_live_adapter_reports_rtk_exemption_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = self.run_adapter_cli(root, "copilot", "Reply with OK", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["adapter"]["selected"], "copilot")
        self.assertEqual(trace["adapter"]["mode"], "live")
        self.assertEqual(trace["adapter"]["status"], "unsupported")
        self.assertFalse(trace["adapter"]["attempted"])
        self.assertEqual(trace["adapter"]["details"]["reason"], "live-execution-not-supported")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["status"], "exempt")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["mediation"], "exempt")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["reason"], "harness-exempt-from-rtk")
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "copilot")
        self.assertEqual(trace["adapter"]["details"]["harness"]["executionSupport"], "dry-run-only")
        self.assertEqual(trace["adapter"]["details"]["harness"]["rtkSupport"], "exempt")
        self.assertEqual(trace["adapter"]["details"]["harness"]["toolSurface"], "native-cli")
        self.assert_telemetry(trace, command="adapter", outcome="unsupported", capture_enabled=True)

    def test_codex_live_adapter_reports_success_with_fake_executable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config.local.yaml").write_text(
                textwrap.dedent(
                    """\
                    defaultHarness: codex
                    yolo: true

                    models:
                      planner: sonnet
                      implementer: gpt-5.5
                      cheapVerifier: gpt-5.5-mini

                    telemetry:
                      enabled: false
                    """
                )
            )
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
                root=root,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["adapter"]["selected"], "codex")
        self.assertEqual(trace["adapter"]["mode"], "live")
        self.assertEqual(trace["adapter"]["status"], "completed")
        self.assertTrue(trace["adapter"]["attempted"])
        self.assertEqual(trace["adapter"]["exitCode"], 0)
        self.assertEqual(
            trace["adapter"]["resultText"],
            "OK FROM FAKE CODEX\nARGS:exec -m gpt-5.5 --sandbox danger-full-access --skip-git-repo-check Reply with OK",
        )
        self.assertEqual(
            trace["adapter"]["debug"]["stdout"],
            "OK FROM FAKE CODEX\nARGS:exec -m gpt-5.5 --sandbox danger-full-access --skip-git-repo-check Reply with OK\n",
        )
        self.assertEqual(trace["adapter"]["debug"]["stderr"], "")
        self.assertEqual(
            trace["adapter"]["details"]["command"],
            [
                str(path_dir / "rtk"),
                "proxy",
                str(path_dir / "codex"),
                "exec",
                "-m",
                "gpt-5.5",
                "--sandbox",
                "danger-full-access",
                "--skip-git-repo-check",
                "Reply with OK",
            ],
        )
        self.assertEqual(trace["adapter"]["details"]["rtk"]["status"], "active")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["mediation"], "required")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], str(path_dir / "rtk"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["command"], str(path_dir / "codex"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["executionSupport"], "live")
        self.assertEqual(trace["adapter"]["details"]["harness"]["rtkSupport"], "required")
        self.assertEqual(trace["adapter"]["details"]["harness"]["toolSurface"], "native-cli")
        self.assertEqual(trace["adapter"]["details"]["harness"]["model"], "gpt-5.5")
        self.assertIsNone(trace["adapter"]["details"]["harness"]["install"])
        self.assertTrue(trace["adapter"]["details"]["harness"]["yolo"])
        self.assert_telemetry(trace, command="adapter", outcome="completed", capture_enabled=False)
        self.assertEqual(trace["telemetry"]["route"]["selectedHarness"], "codex")
        self.assertEqual(trace["telemetry"]["route"]["adapterMode"], "live")

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
                    "PATH": f"{path_dir}:/usr/bin:/bin",
                },
                root=root,
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
        self.assertEqual(trace["adapter"]["details"]["rtk"]["mediation"], "required")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["reason"], "binary-not-found")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], "rtk")
        self.assertIn(
            "curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh",
            trace["adapter"]["details"]["rtk"]["install"]["installCommands"],
        )
        self.assertIn(
            'export PATH="$HOME/.local/bin:$PATH"',
            trace["adapter"]["details"]["rtk"]["install"]["pathSuggestion"],
        )
        self.assert_telemetry(trace, command="adapter", outcome="failed", capture_enabled=True)

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
                root=root,
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
        self.assertEqual(trace["adapter"]["details"]["rtk"]["mediation"], "required")
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], str(path_dir / "rtk"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["command"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["executionSupport"], "live")
        self.assertEqual(trace["adapter"]["details"]["harness"]["rtkSupport"], "required")
        self.assertEqual(trace["adapter"]["details"]["harness"]["toolSurface"], "native-cli")
        self.assertIsNone(trace["adapter"]["details"]["harness"]["install"])
        self.assert_telemetry(trace, command="adapter", outcome="failed", capture_enabled=True)

    def test_run_skill_command_is_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "run-skill",
                    "pull-request",
                    "--prompt",
                    "Reply with OK",
                ],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)
        self.assertIn("run-skill", result.stderr)

    def test_root_override_allows_repo_scoped_commands_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as other_tmpdir:
            root = Path(tmpdir)
            other_cwd = Path(other_tmpdir)
            (root / "skill-indexes").mkdir(parents=True)
            (root / "skill-indexes" / "skill-index.yaml").write_text(
                textwrap.dedent(
                    """\
                    skills:
                      - id: pull-request
                        when: Creating pull requests
                        repo: .
                        path: skills/pull-request/SKILL.md
                    """
                )
            )

            result = self.run_cli(other_cwd, "pull-request", root=root)

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["skillIndex"]["found"])
        self.assertTrue(trace["resolution"]["matched"])

    def test_sync_skills_dry_run_reports_installs_and_unknown_installed(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "local" / "todoist-cli").mkdir(parents=True)
            (root / "skills" / "local" / "todoist-cli" / "SKILL.md").write_text("# Todoist\n")
            (root / "skills" / "local" / "scriptable-handoff").mkdir(parents=True)
            (root / "skills" / "local" / "scriptable-handoff" / "SKILL.md").write_text("# Scriptable\n")
            (home / ".codex" / "skills" / "legacy-skill").mkdir(parents=True)
            (home / ".codex" / "skills" / "legacy-skill" / "SKILL.md").write_text("# Legacy\n")

            result = self.run_sync_cli(
                root,
                root=root,
                installed_skills_dir=home / ".codex" / "skills",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(any(root_entry["exists"] for root_entry in trace["source"]["roots"]))
        self.assertEqual(trace["summary"]["sourceSkills"], 2)
        self.assertEqual(trace["summary"]["install"], 2)
        self.assertEqual(trace["summary"]["unknownInstalled"], 1)
        self.assertEqual(trace["summary"]["unknownCollision"], 0)
        self.assert_telemetry(trace, command="sync-skills", outcome="planned", capture_enabled=True)
        self.assertEqual(trace["telemetry"]["route"]["syncMode"], "dry-run")
        self.assertEqual(
            [action["skill"] for action in trace["actions"]],
            ["scriptable-handoff", "todoist-cli"],
        )
        self.assertEqual(
            [action["action"] for action in trace["actions"]],
            ["install", "install"],
        )
        self.assertEqual(trace["targets"][0]["unknown"][0]["name"], "legacy-skill")
        self.assertEqual(
            [skill["scope"] for skill in trace["source"]["skills"]],
            ["local", "local"],
        )

    def test_sync_skills_dry_run_blocks_unknown_collision(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "local" / "todoist-cli").mkdir(parents=True)
            (root / "skills" / "local" / "todoist-cli" / "SKILL.md").write_text("# Repo Todoist\n")
            (home / ".codex" / "skills" / "todoist-cli").mkdir(parents=True)
            (home / ".codex" / "skills" / "todoist-cli" / "SKILL.md").write_text("# Installed Todoist\n")

            result = self.run_sync_cli(
                root,
                root=root,
                installed_skills_dir=home / ".codex" / "skills",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["sourceSkills"], 1)
        self.assertEqual(trace["summary"]["unknownCollision"], 1)
        self.assertEqual(trace["actions"][0]["skill"], "todoist-cli")
        self.assertEqual(trace["actions"][0]["action"], "unknown-collision")
        self.assert_telemetry(trace, command="sync-skills", outcome="planned", capture_enabled=True)

    def test_sync_skills_dry_run_skips_unchanged_managed_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "skills" / "local" / "todoist-cli"
            source_dir.mkdir(parents=True)
            source_skill = source_dir / "SKILL.md"
            source_skill.write_text("# Todoist\n")

            installed_dir = home / ".codex" / "skills" / "todoist-cli"
            installed_dir.mkdir(parents=True)
            (installed_dir / "SKILL.md").write_text("# Todoist\n")
            (installed_dir / ".ai-stack-skill.json").write_text(
                json.dumps(
                    {
                        "managedBy": "ai-stack",
                        "sourcePath": "skills/local/todoist-cli",
                        "syncedAt": "2026-06-12T00:00:00Z",
                    }
                )
            )

            result = self.run_sync_cli(
                root,
                root=root,
                installed_skills_dir=home / ".codex" / "skills",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["skip"], 1)
        self.assertEqual(trace["summary"]["update"], 0)
        self.assertEqual(trace["actions"][0]["action"], "skip")
        self.assertEqual(trace["targets"][0]["managed"][0]["name"], "todoist-cli")
        self.assert_telemetry(trace, command="sync-skills", outcome="planned", capture_enabled=True)

    def test_sync_skills_dry_run_reports_remove_for_managed_skill_missing_from_source(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            installed_dir = home / ".codex" / "skills" / "todoist-cli"
            installed_dir.mkdir(parents=True)
            (installed_dir / "SKILL.md").write_text("# Todoist\n")
            (installed_dir / ".ai-stack-skill.json").write_text(
                json.dumps(
                    {
                        "managedBy": "ai-stack",
                        "sourcePath": "skills/local/todoist-cli",
                        "syncedAt": "2026-06-12T00:00:00Z",
                    }
                )
            )

            result = self.run_sync_cli(
                root,
                root=root,
                installed_skills_dir=home / ".codex" / "skills",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["remove"], 1)
        self.assertEqual(trace["actions"][0]["action"], "remove")
        self.assertEqual(trace["actions"][0]["skill"], "todoist-cli")
        self.assert_telemetry(trace, command="sync-skills", outcome="planned", capture_enabled=True)

    def test_sync_skills_apply_installs_local_skills_and_writes_marker(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "skills" / "local" / "todoist-cli"
            source_dir.mkdir(parents=True)
            (source_dir / "SKILL.md").write_text("# Todoist\n")

            result = self.run_sync_cli(
                root,
                root=root,
                apply=True,
                installed_skills_dir=home / ".codex" / "skills",
                backup_root=home / ".codex" / "skills-sync-backups",
            )

            installed_dir = home / ".codex" / "skills" / "todoist-cli"
            marker = json.loads((installed_dir / ".ai-stack-skill.json").read_text())
            installed_skill_exists = (installed_dir / "SKILL.md").exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["mode"], "apply")
        self.assertEqual(trace["summary"]["applied"], 1)
        self.assertTrue(installed_skill_exists)
        self.assertEqual(marker["managedBy"], "ai-stack")
        self.assertEqual(marker["sourcePath"], "skills/local/todoist-cli")
        self.assert_telemetry(trace, command="sync-skills", outcome="applied", capture_enabled=True)

    def test_sync_skills_apply_removes_managed_skill_with_backup_when_missing_from_source(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            installed_dir = home / ".codex" / "skills" / "todoist-cli"
            installed_dir.mkdir(parents=True)
            (installed_dir / "SKILL.md").write_text("# Todoist\n")
            (installed_dir / ".ai-stack-skill.json").write_text(
                json.dumps(
                    {
                        "managedBy": "ai-stack",
                        "sourcePath": "skills/local/todoist-cli",
                        "syncedAt": "2026-06-12T00:00:00Z",
                    }
                )
            )

            result = self.run_sync_cli(
                root,
                root=root,
                apply=True,
                installed_skills_dir=home / ".codex" / "skills",
                backup_root=home / ".codex" / "skills-sync-backups",
            )

            backup_root = home / ".codex" / "skills-sync-backups"
            backup_skill_files = list(backup_root.glob("*/todoist-cli/SKILL.md"))

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["remove"], 1)
        self.assertEqual(trace["summary"]["applied"], 1)
        self.assertFalse(installed_dir.exists())
        self.assertEqual(len(backup_skill_files), 1)
        self.assert_telemetry(trace, command="sync-skills", outcome="applied", capture_enabled=True)

    def test_sync_skills_apply_installs_shared_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "skills" / "shared" / "skill-creator"
            source_dir.mkdir(parents=True)
            (source_dir / "SKILL.md").write_text("# Skill Creator\n")

            result = self.run_sync_cli(
                root,
                root=root,
                apply=True,
                installed_skills_dir=home / ".codex" / "skills",
                backup_root=home / ".codex" / "skills-sync-backups",
            )

            installed_dir = home / ".codex" / "skills" / "skill-creator"
            marker = json.loads((installed_dir / ".ai-stack-skill.json").read_text())
            installed_skill_exists = (installed_dir / "SKILL.md").exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["applied"], 1)
        self.assertTrue(installed_skill_exists)
        self.assertEqual(marker["managedBy"], "ai-stack")
        self.assertEqual(marker["sourcePath"], "skills/shared/skill-creator")
        self.assert_telemetry(trace, command="sync-skills", outcome="applied", capture_enabled=True)

    def test_sync_skills_router_is_not_installed_without_index_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "skills" / "shared" / "skill-index-router"
            source_dir.mkdir(parents=True)
            (source_dir / "SKILL.md").write_text("# Router\n")

            result = self.run_sync_cli(
                root,
                root=root,
                installed_skills_dir=home / ".codex" / "skills",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["sourceSkills"], 0)
        self.assertEqual(trace["actions"], [])
        self.assert_telemetry(trace, command="sync-skills", outcome="planned", capture_enabled=True)

    def test_sync_skills_router_installs_with_generated_index_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "skills" / "shared" / "skill-index-router"
            source_dir.mkdir(parents=True)
            (source_dir / "SKILL.md").write_text("# Router\n")
            (root / "skill-indexes").mkdir(parents=True)
            index_text = textwrap.dedent(
                """\
                skills:
                  - id: pull-request
                    when: Creating pull requests
                    repo: ~/Dev/example-tools
                    path: .github/skills/pull-request/SKILL.md
                """
            )
            (root / "skill-indexes" / "skill-index.yaml").write_text(index_text)

            result = self.run_sync_cli(
                root,
                root=root,
                apply=True,
                installed_skills_dir=home / ".codex" / "skills",
                backup_root=home / ".codex" / "skills-sync-backups",
            )

            installed_dir = home / ".codex" / "skills" / "skill-index-router"
            generated_index = (installed_dir / "references" / "skill-index.yaml").read_text()

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["applied"], 1)
        self.assertEqual(trace["results"][0]["skill"], "skill-index-router")
        self.assertEqual(generated_index, index_text)
        self.assert_telemetry(trace, command="sync-skills", outcome="applied", capture_enabled=True)

    def test_sync_global_instructions_dry_run_plans_install_for_all_harnesses(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "global-agent-instructions"
            source_dir.mkdir(parents=True)
            (source_dir / "shared.md").write_text("# Shared\n\n- Never commit without confirmation.\n")
            (source_dir / "local.example.md").write_text("# Local Overlay\n")

            result = self.run_sync_global_instructions_cli(
                root,
                root=root,
                codex_target_file=home / ".codex" / "AGENTS.md",
                copilot_target_file=home / ".copilot" / "copilot-instructions.md",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["install"], 2)
        self.assertEqual(trace["summary"]["unknownCollision"], 0)
        self.assertEqual(trace["source"]["shared"]["path"], "global-agent-instructions/shared.md")
        self.assertFalse(trace["source"]["local"]["found"])
        self.assertEqual(
            [action["harness"] for action in trace["actions"]],
            ["codex", "copilot"],
        )
        self.assertEqual(
            [action["action"] for action in trace["actions"]],
            ["install", "install"],
        )
        self.assert_telemetry(trace, command="sync-global-instructions", outcome="planned", capture_enabled=True)
        self.assertEqual(trace["telemetry"]["route"]["targetHarness"], "all")

    def test_sync_global_instructions_apply_installs_shared_and_local_overlay_for_codex(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "global-agent-instructions"
            source_dir.mkdir(parents=True)
            (source_dir / "shared.md").write_text(
                "# Shared\n\n"
                "- Never push without confirmation.\n"
                "- When the user asks to create, update, refine, or restructure a skill and does not name a different target repo, treat that as work in the configured `repos.aiStack` checkout.\n"
            )
            (source_dir / "local.md").write_text("# Local\n\n- Use machine-local overlays.\n")
            (source_dir / "local.example.md").write_text("# Local Overlay\n")

            target_file = home / ".codex" / "AGENTS.md"
            result = self.run_sync_global_instructions_cli(
                root,
                root=root,
                apply=True,
                harness="codex",
                codex_target_file=target_file,
                backup_root=home / ".ai-stack" / "agent-sync-backups",
            )

            installed_text = target_file.read_text()
            marker = json.loads((target_file.parent / ".ai-stack-global-instructions.json").read_text())

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["applied"], 1)
        self.assertIn("Never push without confirmation.", installed_text)
        self.assertIn("configured `repos.aiStack` checkout", installed_text)
        self.assertIn("Use machine-local overlays.", installed_text)
        self.assertEqual(marker["managedBy"], "ai-stack")
        self.assertEqual(marker["harness"], "codex")
        self.assertEqual(marker["sourceDirectory"], "global-agent-instructions")
        self.assert_telemetry(trace, command="sync-global-instructions", outcome="applied", capture_enabled=True)

    def test_sync_global_instructions_dry_run_blocks_unmanaged_collision(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "global-agent-instructions"
            source_dir.mkdir(parents=True)
            (source_dir / "shared.md").write_text("# Shared\n\n- Never commit without confirmation.\n")
            (source_dir / "local.example.md").write_text("# Local Overlay\n")
            target_file = home / ".copilot" / "copilot-instructions.md"
            target_file.parent.mkdir(parents=True)
            target_file.write_text("# Existing\n")

            result = self.run_sync_global_instructions_cli(
                root,
                root=root,
                harness="copilot",
                copilot_target_file=target_file,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["unknownCollision"], 1)
        self.assertEqual(trace["actions"][0]["action"], "unknown-collision")
        self.assertEqual(trace["actions"][0]["harness"], "copilot")
        self.assert_telemetry(trace, command="sync-global-instructions", outcome="planned", capture_enabled=True)

    def test_sync_global_instructions_dry_run_adopts_empty_unmanaged_target(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            source_dir = root / "global-agent-instructions"
            source_dir.mkdir(parents=True)
            (source_dir / "shared.md").write_text("# Shared\n\n- Never commit without confirmation.\n")
            (source_dir / "local.example.md").write_text("# Local Overlay\n")
            target_file = home / ".codex" / "AGENTS.md"
            target_file.parent.mkdir(parents=True)
            target_file.write_text("")

            result = self.run_sync_global_instructions_cli(
                root,
                root=root,
                harness="codex",
                codex_target_file=target_file,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["install"], 1)
        self.assertEqual(trace["summary"]["unknownCollision"], 0)
        self.assertEqual(trace["actions"][0]["action"], "install")
        self.assertEqual(trace["actions"][0]["harness"], "codex")

    # ------------------------------------------------------------------
    # Multi-harness / Copilot sync tests
    # ------------------------------------------------------------------

    def test_sync_skills_copilot_dry_run_reports_installs(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "shared" / "skill-creator").mkdir(parents=True)
            (root / "skills" / "shared" / "skill-creator" / "SKILL.md").write_text("# Skill Creator\n")
            copilot_skills = home / ".copilot" / "skills"
            copilot_skills.mkdir(parents=True)

            result = self.run_sync_cli(
                root,
                root=root,
                harness="copilot",
                installed_skills_dir=copilot_skills,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["harness"], "copilot")
        self.assertEqual(len(trace["targets"]), 1)
        self.assertEqual(trace["targets"][0]["harness"], "copilot")
        self.assertEqual(trace["summary"]["install"], 1)
        self.assertEqual(trace["actions"][0]["harness"], "copilot")
        self.assertEqual(trace["actions"][0]["skill"], "skill-creator")
        self.assertEqual(trace["actions"][0]["action"], "install")
        self.assert_telemetry(trace, command="sync-skills", outcome="planned", capture_enabled=True)
        self.assertEqual(trace["telemetry"]["route"]["targetHarness"], "copilot")

    def test_sync_skills_copilot_apply_installs_and_writes_marker(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "local" / "my-skill").mkdir(parents=True)
            (root / "skills" / "local" / "my-skill" / "SKILL.md").write_text("# My Skill\n")
            copilot_skills = home / ".copilot" / "skills"
            copilot_skills.mkdir(parents=True)

            result = self.run_sync_cli(
                root,
                root=root,
                harness="copilot",
                apply=True,
                installed_skills_dir=copilot_skills,
                backup_root=home / ".ai-stack" / "skills-sync-backups" / "copilot",
            )

            installed_dir = copilot_skills / "my-skill"
            skill_md_exists = (installed_dir / "SKILL.md").exists()
            marker = json.loads((installed_dir / ".ai-stack-skill.json").read_text())

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["mode"], "apply")
        self.assertEqual(trace["harness"], "copilot")
        self.assertEqual(trace["summary"]["applied"], 1)
        self.assertTrue(skill_md_exists)
        self.assertEqual(marker["managedBy"], "ai-stack")
        self.assertEqual(marker["sourcePath"], "skills/local/my-skill")
        self.assert_telemetry(trace, command="sync-skills", outcome="applied", capture_enabled=True)

    def test_sync_skills_all_harnesses_dry_run_shows_actions_for_each(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "shared" / "skill-creator").mkdir(parents=True)
            (root / "skills" / "shared" / "skill-creator" / "SKILL.md").write_text("# Skill Creator\n")
            (home / ".codex" / "skills").mkdir(parents=True)
            (home / ".copilot" / "skills").mkdir(parents=True)

            # Run with harness=all using CLI directly (no installed_skills_dir override)
            result = subprocess.run(
                [
                    sys.executable, str(CLI_PATH), "sync-skills", "--dry-run",
                    "--harness", "all",
                    "--root", str(root),
                ],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "HOME": str(home)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["harness"], "all")
        self.assertEqual(len(trace["targets"]), 2)
        harnesses = [t["harness"] for t in trace["targets"]]
        self.assertIn("codex", harnesses)
        self.assertIn("copilot", harnesses)
        action_harnesses = [a["harness"] for a in trace["actions"]]
        self.assertIn("codex", action_harnesses)
        self.assertIn("copilot", action_harnesses)
        self.assertEqual(trace["summary"]["install"], 2)  # one per harness

    def test_sync_skills_apply_skips_absent_harness_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "shared" / "skill-creator").mkdir(parents=True)
            (root / "skills" / "shared" / "skill-creator" / "SKILL.md").write_text("# Skill Creator\n")
            # Only create .copilot, not .codex — simulate Codex not installed
            (home / ".copilot" / "skills").mkdir(parents=True)

            result = subprocess.run(
                [
                    sys.executable, str(CLI_PATH), "sync-skills", "--apply",
                    "--harness", "all",
                    "--root", str(root),
                ],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "HOME": str(home)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        codex_results = [r for r in trace["results"] if r["harness"] == "codex"]
        copilot_results = [r for r in trace["results"] if r["harness"] == "copilot"]
        self.assertTrue(all(r["status"] == "skipped-harness-absent" for r in codex_results))
        self.assertTrue(all(r["status"] == "applied" for r in copilot_results))
        self.assertFalse((home / ".codex").exists())
        self.assertEqual(trace["summary"]["skippedHarnessAbsent"], len(codex_results))

    def test_sync_skills_copilot_blocks_unmanaged_collision(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "shared" / "skill-creator").mkdir(parents=True)
            (root / "skills" / "shared" / "skill-creator" / "SKILL.md").write_text("# New Skill Creator\n")
            copilot_skills = home / ".copilot" / "skills"
            (copilot_skills / "skill-creator").mkdir(parents=True)
            (copilot_skills / "skill-creator" / "SKILL.md").write_text("# Old unmanaged version\n")

            result = self.run_sync_cli(
                root,
                root=root,
                harness="copilot",
                installed_skills_dir=copilot_skills,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["unknownCollision"], 1)
        self.assertEqual(trace["actions"][0]["action"], "unknown-collision")
        self.assertEqual(trace["actions"][0]["harness"], "copilot")

    def test_sync_skills_copilot_skips_up_to_date_managed_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (root / "skills" / "local" / "my-skill").mkdir(parents=True)
            (root / "skills" / "local" / "my-skill" / "SKILL.md").write_text("# My Skill\n")
            copilot_skills = home / ".copilot" / "skills"
            installed = copilot_skills / "my-skill"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text("# My Skill\n")
            (installed / ".ai-stack-skill.json").write_text(
                json.dumps({"managedBy": "ai-stack", "sourcePath": "skills/local/my-skill", "syncedAt": "20260818T000000Z"})
            )

            result = self.run_sync_cli(
                root,
                root=root,
                harness="copilot",
                installed_skills_dir=copilot_skills,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["summary"]["skip"], 1)
        self.assertEqual(trace["actions"][0]["action"], "skip")
        self.assertEqual(trace["actions"][0]["harness"], "copilot")

    def test_sync_skills_harness_flag_included_in_telemetry_route(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as homedir:
            root = Path(tmpdir)
            home = Path(homedir)
            (home / ".copilot" / "skills").mkdir(parents=True)

            result = self.run_sync_cli(
                root,
                root=root,
                harness="copilot",
                installed_skills_dir=home / ".copilot" / "skills",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["telemetry"]["route"]["targetHarness"], "copilot")


if __name__ == "__main__":
    unittest.main()
