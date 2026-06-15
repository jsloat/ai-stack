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


REPO_ROOT = Path("/Users/jsloat/Dev/ai-stack")
CLI_PATH = REPO_ROOT / "bin" / "ai-stack"


class CliResolutionAndAdapterTests(unittest.TestCase):
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

    def run_skill_cli(self, cwd: Path, skill: str, prompt: str, extra_env=None, root: Optional[Path] = None):
        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)
        cmd = [sys.executable, str(CLI_PATH), "run-skill", skill, "--prompt", prompt]
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
        installed_skills_dir: Optional[Path] = None,
        backup_root: Optional[Path] = None,
    ):
        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)
        cmd = [sys.executable, str(CLI_PATH), "sync-skills", "--apply" if apply else "--dry-run"]
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

    def test_absent_local_config_and_index_are_clean_no_ops(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(Path(tmpdir), "pull-request", root=Path(tmpdir))

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

    def test_example_index_is_not_used_as_runtime_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes" / "local").mkdir(parents=True)
            (root / "skill-indexes" / "local" / "skill-index.example.yaml").write_text(
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
        self.assertEqual(trace["skillIndex"]["path"], "skill-indexes/local/skill-index.yaml")
        self.assertFalse(trace["skillIndex"]["found"])
        self.assertFalse(trace["resolution"]["matched"])

    def test_skill_resolves_from_local_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes" / "local").mkdir(parents=True)
            (root / "skill-indexes" / "local" / "skill-index.yaml").write_text(
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
            (root / "skill-indexes" / "local" / "skill-index.yaml").write_text(
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
        self.assertEqual(trace["adapter"]["selected"], "mystery")
        self.assertFalse(trace["adapter"]["found"])
        self.assertEqual(trace["adapter"]["status"], "unsupported")
        self.assertFalse(trace["adapter"]["attempted"])

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
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], str(path_dir / "rtk"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["command"], str(path_dir / "codex"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["model"], "gpt-5.5")
        self.assertIsNone(trace["adapter"]["details"]["harness"]["install"])
        self.assertTrue(trace["adapter"]["details"]["harness"]["yolo"])

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
        self.assertEqual(trace["adapter"]["details"]["rtk"]["command"], str(path_dir / "rtk"))
        self.assertEqual(trace["adapter"]["details"]["harness"]["id"], "codex")
        self.assertEqual(trace["adapter"]["details"]["harness"]["command"], "codex")
        self.assertIsNone(trace["adapter"]["details"]["harness"]["install"])

    def test_run_skill_executes_resolved_skill_with_live_adapter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skill-indexes" / "local").mkdir(parents=True)
            (root / "skills" / "pull-request").mkdir(parents=True)
            (root / "skills" / "pull-request" / "SKILL.md").write_text(
                "# Pull Request Skill\n\nSKILL SENTINEL\n"
            )
            (root / "skill-indexes" / "local" / "skill-index.yaml").write_text(
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
            fake_codex = path_dir / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import sys
                    print("RUN SKILL OK")
                    print("ARGS:" + " ".join(sys.argv[1:]))
                    """
                )
            )
            fake_codex.chmod(0o755)

            result = self.run_skill_cli(
                root,
                "pull-request",
                "Reply with OK",
                extra_env={
                    "PATH": f"{path_dir}:/usr/bin:/bin:/opt/homebrew/bin",
                },
                root=root,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertTrue(trace["resolution"]["matched"])
        self.assertEqual(trace["resolution"]["requestedSkill"], "pull-request")
        self.assertEqual(trace["adapter"]["selected"], "codex")
        self.assertEqual(trace["adapter"]["mode"], "live")
        self.assertEqual(trace["adapter"]["status"], "completed")
        self.assertEqual(trace["adapter"]["details"]["harness"]["model"], "gpt-5.5")
        self.assertIn("RUN SKILL OK", trace["adapter"]["resultText"])
        self.assertIn("-m gpt-5.5", trace["adapter"]["resultText"])
        self.assertIn("SKILL SENTINEL", trace["adapter"]["resultText"])
        self.assertIn("Reply with OK", trace["adapter"]["resultText"])
        self.assertEqual(trace["adapter"]["details"]["requestedSkill"], "pull-request")
        self.assertEqual(trace["adapter"]["details"]["sourceRepo"], ".")
        self.assertEqual(trace["adapter"]["details"]["skillPath"], "skills/pull-request/SKILL.md")
        self.assertEqual(
            trace["adapter"]["details"]["resolvedSkillFilePath"],
            str((root / "skills" / "pull-request" / "SKILL.md").resolve()),
        )

    def test_run_skill_returns_not_found_without_live_adapter_attempt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = self.run_skill_cli(root, "pull-request", "Reply with OK", root=root)

        self.assertEqual(result.returncode, 1, result.stderr)
        trace = json.loads(result.stdout)
        self.assertFalse(trace["resolution"]["matched"])
        self.assertEqual(trace["adapter"]["mode"], "dry-run")
        self.assertEqual(trace["adapter"]["status"], "skipped")
        self.assertFalse(trace["adapter"]["attempted"])

    def test_root_override_allows_repo_scoped_commands_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as other_tmpdir:
            root = Path(tmpdir)
            other_cwd = Path(other_tmpdir)
            (root / "skill-indexes" / "local").mkdir(parents=True)
            (root / "skill-indexes" / "local" / "skill-index.yaml").write_text(
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
        self.assertEqual(
            [action["skill"] for action in trace["actions"]],
            ["scriptable-handoff", "todoist-cli"],
        )
        self.assertEqual(
            [action["action"] for action in trace["actions"]],
            ["install", "install"],
        )
        self.assertEqual(trace["installed"]["unknown"][0]["name"], "legacy-skill")
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
        self.assertEqual(trace["installed"]["managed"][0]["name"], "todoist-cli")

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


if __name__ == "__main__":
    unittest.main()
