from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SKILL_SOURCE_ROOTS = (
    ("local", Path("skills/local")),
    ("shared", Path("skills/shared")),
)
AI_STACK_MARKER = ".ai-stack-skill.json"
BACKUP_ROOT = Path.home() / ".codex" / "skills-sync-backups"


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


def codex_user_skills_dir() -> Path:
    return Path.home() / ".codex" / "skills"


def discover_repo_skills(root: Path) -> List[RepoSkill]:
    skills: List[RepoSkill] = []
    for scope, source_root in SKILL_SOURCE_ROOTS:
        skills_root = root / source_root
        if not skills_root.exists():
            continue
        for child in sorted(skills_root.iterdir()):
            if not child.is_dir():
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


def discover_installed_codex_skills(skills_dir: Optional[Path] = None) -> List[InstalledSkill]:
    skills_root = skills_dir or codex_user_skills_dir()
    if not skills_root.exists():
        return []

    installed: List[InstalledSkill] = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
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


def build_sync_plan(root: Path, installed_skills_dir: Optional[Path] = None) -> Dict[str, Any]:
    repo_skills = discover_repo_skills(root)
    installed_root = installed_skills_dir or codex_user_skills_dir()
    installed = discover_installed_codex_skills(installed_root)
    installed_by_name = {skill.name: skill for skill in installed}
    repo_skill_names = {skill.name for skill in repo_skills}
    actions: List[Dict[str, Any]] = []

    for repo_skill in repo_skills:
        installed_skill = installed_by_name.get(repo_skill.name)
        if installed_skill is None:
            actions.append(
                {
                    "skill": repo_skill.name,
                    "action": "install",
                    "sourceDirectory": str(repo_skill.directory.relative_to(root)),
                    "targetDirectory": str(installed_root / repo_skill.name),
                }
            )
            continue

        if not installed_skill.managed:
            actions.append(
                {
                    "skill": repo_skill.name,
                    "action": "unknown-collision",
                    "sourceDirectory": str(repo_skill.directory.relative_to(root)),
                    "targetDirectory": str(installed_skill.directory),
                }
            )
            continue

        action = "skip" if _skills_match(repo_skill, installed_skill) else "update"
        actions.append(
            {
                "skill": repo_skill.name,
                "action": action,
                "sourceDirectory": str(repo_skill.directory.relative_to(root)),
                "targetDirectory": str(installed_skill.directory),
            }
        )

    for installed_skill in installed:
        if installed_skill.managed and installed_skill.name not in repo_skill_names:
            actions.append(
                {
                    "skill": installed_skill.name,
                    "action": "remove",
                    "sourceDirectory": None,
                    "targetDirectory": str(installed_skill.directory),
                }
            )

    unknown_installed = [
        skill.to_dict()
        for skill in installed
        if not skill.managed and skill.name not in repo_skill_names
    ]

    managed_installed = [
        skill.to_dict()
        for skill in installed
        if skill.managed
    ]

    return {
        "mode": "dry-run",
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
        "installed": {
            "root": str(installed_root.resolve()),
            "managed": managed_installed,
            "unknown": unknown_installed,
        },
        "actions": actions,
        "summary": _summarize_actions(actions, unknown_installed),
    }


def apply_sync_plan(root: Path, installed_skills_dir: Optional[Path] = None, backup_root: Optional[Path] = None) -> Dict[str, Any]:
    plan = build_sync_plan(root, installed_skills_dir=installed_skills_dir)
    installed_root = Path(plan["installed"]["root"])
    backup_base = backup_root or BACKUP_ROOT
    applied_at = _utc_now()
    backup_run_root = backup_base / applied_at
    results: List[Dict[str, Any]] = []

    repo_skills = {skill.name: skill for skill in discover_repo_skills(root)}
    installed_root.mkdir(parents=True, exist_ok=True)

    for action in plan["actions"]:
        name = action["skill"]
        target_dir = Path(action["targetDirectory"])
        action_type = action["action"]

        if action_type == "unknown-collision":
            results.append(
                {
                    "skill": name,
                    "action": action_type,
                    "status": "blocked",
                    "targetDirectory": str(target_dir),
                }
            )
            continue

        if action_type == "install":
            repo_skill = repo_skills[name]
            _copy_skill_directory(repo_skill.directory, target_dir)
            _write_marker(root, repo_skill, target_dir, applied_at)
            results.append(
                {
                    "skill": name,
                    "action": action_type,
                    "status": "applied",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": None,
                }
            )
            continue

        if action_type == "update":
            repo_skill = repo_skills[name]
            backup_dir = _backup_directory(target_dir, backup_run_root)
            shutil.rmtree(target_dir)
            _copy_skill_directory(repo_skill.directory, target_dir)
            _write_marker(root, repo_skill, target_dir, applied_at)
            results.append(
                {
                    "skill": name,
                    "action": action_type,
                    "status": "applied",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": str(backup_dir),
                }
            )
            continue

        if action_type == "remove":
            backup_dir = _backup_directory(target_dir, backup_run_root)
            shutil.rmtree(target_dir)
            results.append(
                {
                    "skill": name,
                    "action": action_type,
                    "status": "applied",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": str(backup_dir),
                }
            )
            continue

        if action_type == "skip":
            results.append(
                {
                    "skill": name,
                    "action": action_type,
                    "status": "unchanged",
                    "targetDirectory": str(target_dir),
                    "backupDirectory": None,
                }
            )
            continue

        raise ValueError(f"Unsupported sync action: {action_type}")

    return {
        "mode": "apply",
        "appliedAt": applied_at,
        "source": plan["source"],
        "installed": plan["installed"],
        "actions": plan["actions"],
        "results": results,
        "summary": _summarize_results(results, plan["summary"]),
        "backupRoot": str(backup_run_root) if any(result["backupDirectory"] for result in results) else None,
    }


def _summarize_actions(actions: List[Dict[str, Any]], unknown_installed: List[Dict[str, Any]]) -> Dict[str, int]:
    summary: Dict[str, int] = {
        "sourceSkills": sum(1 for action in actions if action["sourceDirectory"] is not None),
        "unknownInstalled": len(unknown_installed),
        "install": 0,
        "update": 0,
        "remove": 0,
        "skip": 0,
        "unknownCollision": 0,
    }
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
    summary.update(
        {
            "applied": sum(1 for result in results if result["status"] == "applied"),
            "blocked": sum(1 for result in results if result["status"] == "blocked"),
            "unchanged": sum(1 for result in results if result["status"] == "unchanged"),
        }
    )
    return summary


def _skills_match(repo_skill: RepoSkill, installed_skill: InstalledSkill) -> bool:
    return _directory_digest(repo_skill.directory, exclude_names=None) == _directory_digest(
        installed_skill.directory,
        exclude_names={AI_STACK_MARKER},
    )


def _directory_digest(directory: Path, exclude_names: Optional[set[str]]) -> str:
    digest = hashlib.sha256()
    exclude_names = exclude_names or set()
    for path in sorted(directory.rglob("*")):
        if path.name in exclude_names:
            continue
        if path.is_dir():
            continue
        relative = path.relative_to(directory)
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


def _backup_directory(source_dir: Path, backup_run_root: Path) -> Path:
    backup_run_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_run_root / source_dir.name
    shutil.copytree(source_dir, backup_dir, dirs_exist_ok=False)
    return backup_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
