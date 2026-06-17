from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


SOURCE_DIR = Path("global-agent-instructions")
SHARED_SOURCE_PATH = SOURCE_DIR / "shared.md"
LOCAL_SOURCE_PATH = SOURCE_DIR / "local.md"
LOCAL_EXAMPLE_PATH = SOURCE_DIR / "local.example.md"
BACKUP_ROOT = Path.home() / ".ai-stack" / "agent-sync-backups"
MARKER_FILE_NAME = ".ai-stack-global-instructions.json"
SUPPORTED_HARNESSES = ("codex", "copilot")


@dataclass(frozen=True)
class HarnessTarget:
    harness: str
    target_file: Path

    @property
    def marker_file(self) -> Path:
        return self.target_file.parent / MARKER_FILE_NAME


def default_target_file_for_harness(harness: str) -> Path:
    if harness == "codex":
        return Path.home() / ".codex" / "AGENTS.md"
    if harness == "copilot":
        return Path.home() / ".copilot" / "copilot-instructions.md"
    raise ValueError(f"Unsupported harness: {harness}")


def discover_instruction_sources(root: Path) -> Dict[str, Any]:
    shared_path = root / SHARED_SOURCE_PATH
    local_path = root / LOCAL_SOURCE_PATH
    example_path = root / LOCAL_EXAMPLE_PATH

    shared_found = shared_path.exists()
    local_found = local_path.exists()
    rendered_parts: List[str] = []
    if shared_found:
        rendered_parts.append(shared_path.read_text().strip())
    if local_found:
        rendered_parts.append(local_path.read_text().strip())
    rendered_text = "\n\n".join(part for part in rendered_parts if part)

    return {
        "directory": str(SOURCE_DIR),
        "shared": {
            "path": str(SHARED_SOURCE_PATH),
            "found": shared_found,
        },
        "local": {
            "path": str(LOCAL_SOURCE_PATH),
            "found": local_found,
        },
        "example": {
            "path": str(LOCAL_EXAMPLE_PATH),
            "found": example_path.exists(),
        },
        "renderedText": rendered_text,
        "renderedLength": len(rendered_text),
    }


def target_for_harness(harness: str, overrides: Optional[Mapping[str, Path]] = None) -> HarnessTarget:
    if harness not in SUPPORTED_HARNESSES:
        raise ValueError(f"Unsupported harness: {harness}")
    target_file = (
        overrides[harness].resolve()
        if overrides is not None and harness in overrides and overrides[harness] is not None
        else default_target_file_for_harness(harness).resolve()
    )
    return HarnessTarget(harness=harness, target_file=target_file)


def read_marker(marker_file: Path) -> Optional[Dict[str, Any]]:
    if not marker_file.exists():
        return None
    try:
        marker = json.loads(marker_file.read_text())
    except json.JSONDecodeError:
        return {"invalid": True}
    return marker if isinstance(marker, dict) else {"invalid": True}


def is_managed_target(target: HarnessTarget, marker: Optional[Dict[str, Any]]) -> bool:
    return bool(
        isinstance(marker, dict)
        and marker.get("managedBy") == "ai-stack"
        and marker.get("harness") == target.harness
    )


def build_agent_sync_plan(
    root: Path,
    *,
    harness: str = "all",
    target_overrides: Optional[Mapping[str, Path]] = None,
) -> Dict[str, Any]:
    selected_harnesses = list(SUPPORTED_HARNESSES if harness == "all" else (harness,))
    sources = discover_instruction_sources(root)
    actions: List[Dict[str, Any]] = []
    targets: List[Dict[str, Any]] = []

    for harness_id in selected_harnesses:
        target = target_for_harness(harness_id, overrides=target_overrides)
        marker = read_marker(target.marker_file)
        managed = is_managed_target(target, marker)
        existing_text = target.target_file.read_text() if target.target_file.exists() else None
        targets.append(
            {
                "harness": harness_id,
                "targetFile": str(target.target_file),
                "markerFile": str(target.marker_file),
                "exists": target.target_file.exists(),
                "managed": managed,
                "marker": marker,
            }
        )

        if not sources["shared"]["found"]:
            actions.append(
                {
                    "harness": harness_id,
                    "action": "blocked",
                    "reason": "missing-shared-source",
                    "targetFile": str(target.target_file),
                }
            )
            continue

        if not target.target_file.exists():
            actions.append(
                {
                    "harness": harness_id,
                    "action": "install",
                    "targetFile": str(target.target_file),
                }
            )
            continue

        if existing_text is not None and existing_text.strip() == "":
            actions.append(
                {
                    "harness": harness_id,
                    "action": "install",
                    "targetFile": str(target.target_file),
                }
            )
            continue

        if not managed:
            actions.append(
                {
                    "harness": harness_id,
                    "action": "unknown-collision",
                    "targetFile": str(target.target_file),
                }
            )
            continue

        action = "skip" if existing_text == sources["renderedText"] else "update"
        actions.append(
            {
                "harness": harness_id,
                "action": action,
                "targetFile": str(target.target_file),
            }
        )

    return {
        "mode": "dry-run",
        "harness": harness,
        "source": {
            "directory": sources["directory"],
            "shared": sources["shared"],
            "local": sources["local"],
            "example": sources["example"],
            "renderedLength": sources["renderedLength"],
        },
        "targets": targets,
        "actions": actions,
        "summary": summarize_agent_sync_actions(actions),
    }


def apply_agent_sync_plan(
    root: Path,
    *,
    harness: str = "all",
    target_overrides: Optional[Mapping[str, Path]] = None,
    backup_root: Optional[Path] = None,
) -> Dict[str, Any]:
    plan = build_agent_sync_plan(root, harness=harness, target_overrides=target_overrides)
    sources = discover_instruction_sources(root)
    rendered_text = sources["renderedText"]
    applied_at = utc_now()
    backup_base = backup_root.resolve() if backup_root is not None else BACKUP_ROOT
    backup_run_root = backup_base / applied_at
    results: List[Dict[str, Any]] = []

    for action in plan["actions"]:
        harness_id = action["harness"]
        target = target_for_harness(harness_id, overrides=target_overrides)
        action_type = action["action"]

        if action_type in {"blocked", "unknown-collision"}:
            results.append(
                {
                    "harness": harness_id,
                    "action": action_type,
                    "status": "blocked",
                    "targetFile": str(target.target_file),
                    "backupDirectory": None,
                }
            )
            continue

        target.target_file.parent.mkdir(parents=True, exist_ok=True)

        if action_type == "install":
            target.target_file.write_text(rendered_text)
            write_agent_sync_marker(root, target, applied_at)
            results.append(
                {
                    "harness": harness_id,
                    "action": action_type,
                    "status": "applied",
                    "targetFile": str(target.target_file),
                    "backupDirectory": None,
                }
            )
            continue

        if action_type == "update":
            backup_dir = backup_agent_target(target, backup_run_root)
            target.target_file.write_text(rendered_text)
            write_agent_sync_marker(root, target, applied_at)
            results.append(
                {
                    "harness": harness_id,
                    "action": action_type,
                    "status": "applied",
                    "targetFile": str(target.target_file),
                    "backupDirectory": str(backup_dir),
                }
            )
            continue

        if action_type == "skip":
            results.append(
                {
                    "harness": harness_id,
                    "action": action_type,
                    "status": "unchanged",
                    "targetFile": str(target.target_file),
                    "backupDirectory": None,
                }
            )
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
        "summary": summarize_agent_sync_results(results, plan["summary"]),
        "backupRoot": str(backup_run_root) if any(result["backupDirectory"] for result in results) else None,
    }


def backup_agent_target(target: HarnessTarget, backup_run_root: Path) -> Path:
    backup_dir = backup_run_root / target.harness
    backup_dir.mkdir(parents=True, exist_ok=True)
    if target.target_file.exists():
        shutil.copy2(target.target_file, backup_dir / target.target_file.name)
    if target.marker_file.exists():
        shutil.copy2(target.marker_file, backup_dir / target.marker_file.name)
    return backup_dir


def write_agent_sync_marker(root: Path, target: HarnessTarget, applied_at: str) -> None:
    target.marker_file.write_text(
        json.dumps(
            {
                "managedBy": "ai-stack",
                "harness": target.harness,
                "sourceDirectory": str(SOURCE_DIR),
                "sharedSourcePath": str(SHARED_SOURCE_PATH),
                "localSourcePath": str(LOCAL_SOURCE_PATH),
                "targetFile": target.target_file.name,
                "syncedAt": applied_at,
            },
            indent=2,
            sort_keys=True,
        )
    )


def summarize_agent_sync_actions(actions: List[Dict[str, Any]]) -> Dict[str, int]:
    summary = {
        "selectedHarnesses": len(actions),
        "install": 0,
        "update": 0,
        "skip": 0,
        "blocked": 0,
        "unknownCollision": 0,
    }
    for action in actions:
        if action["action"] == "install":
            summary["install"] += 1
        elif action["action"] == "update":
            summary["update"] += 1
        elif action["action"] == "skip":
            summary["skip"] += 1
        elif action["action"] == "blocked":
            summary["blocked"] += 1
        elif action["action"] == "unknown-collision":
            summary["unknownCollision"] += 1
    return summary


def summarize_agent_sync_results(results: List[Dict[str, Any]], plan_summary: Dict[str, int]) -> Dict[str, int]:
    summary = dict(plan_summary)
    summary.update(
        {
            "applied": sum(1 for result in results if result["status"] == "applied"),
            "unchanged": sum(1 for result in results if result["status"] == "unchanged"),
        }
    )
    return summary


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
