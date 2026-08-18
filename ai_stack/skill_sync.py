from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_stack.skill_index import INDEX_PATH, load_skill_index

SUPPORTED_HARNESSES = ("codex", "copilot")
SKILL_SOURCE_ROOTS = (
    ("local", Path("skills/local")),
    ("shared", Path("skills/shared")),
)
AI_STACK_MARKER = ".ai-stack-skill.json"
BACKUP_ROOT = Path.home() / ".ai-stack" / "skills-sync-backups"
ROUTER_SKILL_NAME = "skill-index-router"
ROUTER_INDEX_RELATIVE_PATH = Path("references/skill-index.yaml")


@dataclass(frozen=True)
class RepoSkill:
    name: str
    scope: str
    source_root: Path
    directory: Path
    skill_file: Path

    def to_dict(self, root: Path) -> Dict[str, str]:
        return {
            "name": self.name,
            "scope": self.scope,
            "sourceRoot": str(self.source_root),
            "directory": str(self.directory.relative_to(root)),
            "skillFile": str(self.skill_file.relative_to(root)),
        }


@dataclass(frozen=True)
class InstalledSkill:
    name: str
    directory: Path
    managed: bool
    marker: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "directory": str(self.directory),
            "managed": self.managed,
            "marker": self.marker,
        }


def user_skills_dir(harness: str) -> Path:
    if harness == "codex":
        return Path.home() / ".codex" / "skills"
    if harness == "copilot":
        return Path.home() / ".copilot" / "skills"
    raise ValueError(f"Unsupported harness: {harness}")


def backup_root_for_harness(harness: str) -> Path:
    return BACKUP_ROOT / harness


def discover_repo_skills(root: Path) -> List[RepoSkill]:
    skills: List[RepoSkill] = []
    skill_index = load_skill_index(root)
    router_enabled = skill_index["rowCount"] > 0
    for scope, source_root in SKILL_SOURCE_ROOTS:
        skills_root = root / source_root
        if not skills_root.exists():
            continue
        for child in sorted(skills_root.iterdir()):
            if not child.is_dir():
                continue
            if child.name == ROUTER_SKILL_NAME and not router_enabled:
                continue
            skill_file = child / "SKILL.md"
            if not skill_file.exists():
                continue
            skills.append(
                RepoSkill(
                    name=child.name,
                    scope=scope,
                    source_root=source_root,
                    directory=child,
                    skill_file=skill_file,
                )
            )
    return skills


def discover_installed_skills(harness: str, skills_dir: Optional[Path] = None) -> List[InstalledSkill]:
    skills_root = skills_dir or user_skills_dir(harness)
    if not skills_root.exists():
        return []

    installed: List[InstalledSkill] = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        marker_path = child / AI_STACK_MARKER
        marker = None
        managed = False
        if marker_path.exists():
            try:
                marker = json.loads(marker_path.read_text())
            except json.JSONDecodeError:
                marker = {"invalid": True}
            managed = isinstance(marker, dict) and marker.get("managedBy") == "ai-stack"
        installed.append(
            InstalledSkill(
                name=child.name,
                directory=child,
                managed=managed,
                marker=marker,
            )
        )
    return installed


def _build_harness_actions(
    root: Path,
    harness: str,
    repo_skills: List[RepoSkill],
    installed_skills_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    installed_root = installed_skills_dir or user_skills_dir(harness)
    installed = discover_installed_skills(harness, skills_dir=installed_skills_dir)
    installed_by_name = {skill.name: skill for skill in installed}
    repo_skill_names = {skill.name for skill in repo_skills}
    actions: List[Dict[str, Any]] = []

    for repo_skill in repo_skills:
        installed_skill = installed_by_name.get(repo_skill.name)
        if installed_skill is None:
            actions.append({
                "harness": harness,
                "skill": repo_skill.name,
                "action": "install",
                "sourceDirectory": str(repo_skill.directory.relative_to(root)),
                "targetDirectory": str(installed_root / repo_skill.name),
            })
            continue

        if not installed_skill.managed:
            actions.append({
                "harness": harness,
                "skill": repo_skill.name,
                "action": "unknown-collision",
                "sourceDirectory": str(repo_skill.directory.relative_to(root)),
                "targetDirectory": str(installed_skill.directory),
            })
            continue

        action = "skip" if _skills_match(root, repo_skill, installed_skill) else "update"
        actions.append({
            "harness": harness,
            "skill": repo_skill.name,
            "action": action,
            "sourceDirectory": str(repo_skill.directory.relative_to(root)),
            "targetDirectory": str(installed_skill.directory),
        })

    for installed_skill in installed:
        if installed_skill.managed and installed_skill.name not in repo_skill_names:
            actions.append({
                "harness": harness,
                "skill": installed_skill.name,
                "action": "remove",
                "sourceDirectory": None,
                "targetDirectory": str(installed_skill.directory),
            })

    unknown_installed = [
        skill.to_dict()
        for skill in installed
        if not skill.managed and skill.name not in repo_skill_names
    ]
    managed_installed = [skill.to_dict() for skill in installed if skill.managed]

    return {
        "harness": harness,
        "root": str(installed_root.resolve()),
        "managed": managed_installed,
        "unknown": unknown_installed,
        "actions": actions,
    }


def build_sync_plan(
    root: Path,
    harness: str = "all",
    installed_skills_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    selected = list(SUPPORTED_HARNESSES) if harness == "all" else [harness]
    repo_skills = discover_repo_skills(root)
    all_actions: List[Dict[str, Any]] = []
    targets: List[Dict[str, Any]] = []

    for h in selected:
        # installed_skills_dir override only applies when targeting a single harness
        override = installed_skills_dir if len(selected) == 1 else None
        result = _build_harness_actions(root, h, repo_skills, installed_skills_dir=override)
        all_actions.extend(result["actions"])
        targets.append({
            "harness": result["harness"],
            "root": result["root"],
            "managed": result["managed"],
            "unknown": result["unknown"],
        })

    return {
        "mode": "dry-run",
        "harness": harness,
        "source": {
            "roots": [
                {
                    "scope": scope,
                    "path": str((root / source_root).resolve()),
                    "exists": (root / source_root).exists(),
                }
                for scope, source_root in SKILL_SOURCE_ROOTS
            ],
            "skills": [skill.to_dict(root) for skill in repo_skills],
        },
        "targets": targets,
        "actions": all_actions,
        "summary": _summarize_actions(all_actions, targets),
    }


def apply_sync_plan(
    root: Path,
    harness: str = "all",
    installed_skills_dir: Optional[Path] = None,
    backup_root: Optional[Path] = None,
) -> Dict[str, Any]:
    plan = build_sync_plan(root, harness=harness, installed_skills_dir=installed_skills_dir)
    applied_at = _utc_now()
    repo_skills = {skill.name: skill for skill in discover_repo_skills(root)}
    results: List[Dict[str, Any]] = []

    # Group actions by harness so we can use the right dirs/backup paths
    selected = list(SUPPORTED_HARNESSES) if harness == "all" else [harness]
    for h in selected:
        installed_root_path = (
            installed_skills_dir.resolve()
            if installed_skills_dir is not None and len(selected) == 1
            else user_skills_dir(h)
        )
        # Skip harnesses whose parent directory doesn't exist (harness not installed on this machine)
        if not installed_root_path.parent.exists() and installed_skills_dir is None:
            for action in plan["actions"]:
                if action["harness"] == h:
                    results.append({
                        "harness": h,
                        "skill": action["skill"],
                        "action": action["action"],
                        "status": "skipped-harness-absent",
                        "targetDirectory": str(Path(action["targetDirectory"])),
                        "backupDirectory": None,
                    })
            continue
        installed_root_path.mkdir(parents=True, exist_ok=True)
        harness_backup_base = (backup_root or backup_root_for_harness(h)) / applied_at

        for action in plan["actions"]:
            if action["harness"] != h:
                continue
            name = action["skill"]
            target_dir = Path(action["targetDirectory"])
            action_type = action["action"]

            if action_type == "unknown-collision":
                results.append({
                    "harness": h,
                    "skill": name,
                    "action": action_type,
                    "status": "blocked",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": None,
                })
                continue

            if action_type == "install":
                repo_skill = repo_skills[name]
                _copy_skill_directory(repo_skill.directory, target_dir)
                _write_marker(root, repo_skill, target_dir, applied_at)
                results.append({
                    "harness": h,
                    "skill": name,
                    "action": action_type,
                    "status": "applied",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": None,
                })
                continue

            if action_type == "update":
                repo_skill = repo_skills[name]
                backup_dir = _backup_directory(target_dir, harness_backup_base)
                shutil.rmtree(target_dir)
                _copy_skill_directory(repo_skill.directory, target_dir)
                _write_marker(root, repo_skill, target_dir, applied_at)
                results.append({
                    "harness": h,
                    "skill": name,
                    "action": action_type,
                    "status": "applied",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": str(backup_dir),
                })
                continue

            if action_type == "remove":
                backup_dir = _backup_directory(target_dir, harness_backup_base)
                shutil.rmtree(target_dir)
                results.append({
                    "harness": h,
                    "skill": name,
                    "action": action_type,
                    "status": "applied",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": str(backup_dir),
                })
                continue

            if action_type == "skip":
                results.append({
                    "harness": h,
                    "skill": name,
                    "action": action_type,
                    "status": "unchanged",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": None,
                })
                continue

            raise ValueError(f"Unsupported sync action: {action_type}")

    return {
        "mode": "apply",
        "harness": harness,
        "appliedAt": applied_at,
        "source": plan["source"],
        "targets": plan["targets"],
        "actions": plan["actions"],
        "results": results,
        "summary": _summarize_results(results, plan["summary"]),
        "backupRoot": str(BACKUP_ROOT / applied_at) if any(r["backupDirectory"] for r in results) else None,
    }


def _summarize_actions(
    actions: List[Dict[str, Any]], targets: List[Dict[str, Any]]
) -> Dict[str, int]:
    unknown_installed_total = sum(len(t["unknown"]) for t in targets)
    summary: Dict[str, int] = {
        "sourceSkills": sum(1 for a in actions if a["sourceDirectory"] is not None and a["harness"] == (targets[0]["harness"] if len(targets) == 1 else actions[0]["harness"] if actions else "")),
        "unknownInstalled": unknown_installed_total,
        "install": 0,
        "update": 0,
        "remove": 0,
        "skip": 0,
        "unknownCollision": 0,
    }
    # sourceSkills = unique repo skills (same regardless of harness count)
    seen_skills: set = set()
    for a in actions:
        if a["sourceDirectory"] is not None:
            seen_skills.add(a["skill"])
    summary["sourceSkills"] = len(seen_skills)
    for action in actions:
        if action["action"] == "install":
            summary["install"] += 1
        elif action["action"] == "update":
            summary["update"] += 1
        elif action["action"] == "remove":
            summary["remove"] += 1
        elif action["action"] == "skip":
            summary["skip"] += 1
        elif action["action"] == "unknown-collision":
            summary["unknownCollision"] += 1
    return summary


def _summarize_results(results: List[Dict[str, Any]], plan_summary: Dict[str, int]) -> Dict[str, int]:
    summary = dict(plan_summary)
    summary.update({
        "applied": sum(1 for r in results if r["status"] == "applied"),
        "blocked": sum(1 for r in results if r["status"] == "blocked"),
        "unchanged": sum(1 for r in results if r["status"] == "unchanged"),
        "skippedHarnessAbsent": sum(1 for r in results if r["status"] == "skipped-harness-absent"),
    })
    return summary


def _skills_match(root: Path, repo_skill: RepoSkill, installed_skill: InstalledSkill) -> bool:
    if _directory_digest(repo_skill.directory, exclude_relative_paths=None) != _directory_digest(
        installed_skill.directory,
        exclude_relative_paths={Path(AI_STACK_MARKER), ROUTER_INDEX_RELATIVE_PATH},
    ):
        return False

    if repo_skill.name != ROUTER_SKILL_NAME:
        return True

    expected_index = load_skill_index(root)
    generated_path = installed_skill.directory / ROUTER_INDEX_RELATIVE_PATH
    if not expected_index["found"] or expected_index["rowCount"] == 0:
        return False
    if not generated_path.exists():
        return False
    return generated_path.read_text() == expected_index["text"]


def _directory_digest(directory: Path, exclude_relative_paths: Optional[set[Path]]) -> str:
    digest = hashlib.sha256()
    exclude_relative_paths = exclude_relative_paths or set()
    for path in sorted(directory.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(directory)
        if relative in exclude_relative_paths:
            continue
        digest.update(str(relative).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _copy_skill_directory(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=False)


def _write_marker(root: Path, repo_skill: RepoSkill, target_dir: Path, synced_at: str) -> None:
    marker = {
        "managedBy": "ai-stack",
        "sourcePath": str(repo_skill.directory.relative_to(root)),
        "syncedAt": synced_at,
    }
    (target_dir / AI_STACK_MARKER).write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n")
    if repo_skill.name == ROUTER_SKILL_NAME:
        _write_router_index_reference(root, target_dir)


def _write_router_index_reference(root: Path, target_dir: Path) -> None:
    skill_index = load_skill_index(root)
    if not skill_index["found"] or skill_index["rowCount"] == 0 or skill_index["text"] is None:
        return
    destination = target_dir / ROUTER_INDEX_RELATIVE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(skill_index["text"])


def _backup_directory(source_dir: Path, backup_run_root: Path) -> Path:
    backup_run_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_run_root / source_dir.name
    shutil.copytree(source_dir, backup_dir, dirs_exist_ok=False)
    return backup_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Backward-compat shims: old callers used codex_user_skills_dir() and
# discover_installed_codex_skills(). Keep them pointing at the new logic.
# ---------------------------------------------------------------------------

def codex_user_skills_dir() -> Path:
    return user_skills_dir("codex")


def discover_installed_codex_skills(skills_dir: Optional[Path] = None) -> List[InstalledSkill]:
    return discover_installed_skills("codex", skills_dir=skills_dir)



