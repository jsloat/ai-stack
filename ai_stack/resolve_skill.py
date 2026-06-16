from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_stack.adapter_contract import AdapterDetails, AdapterResult
from ai_stack.adapters import run_adapter_dry_mode, run_adapter_live
from ai_stack.skill_index import load_skill_index, parse_simple_yaml
from ai_stack.skill_sync import apply_sync_plan, build_sync_plan


DEFAULT_CONFIG = {
    "defaultHarness": "copilot",
    "yolo": False,
    "models": {
        "planner": "sonnet",
        "implementer": "gpt-5.5",
        "cheapVerifier": "gpt-5.5-mini",
    },
    "telemetry": {
        "enabled": True,
    },
}

def infer_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_local_config(root: Path) -> Dict[str, Any]:
    config_path = root / "config.local.yaml"
    effective = json.loads(json.dumps(DEFAULT_CONFIG))
    result = {
        "path": str(config_path.relative_to(root)),
        "localConfigFound": config_path.exists(),
        "effective": effective,
    }
    if not config_path.exists():
        return result

    parsed = parse_simple_yaml(config_path.read_text())
    _deep_merge(effective, parsed)
    return result


def _deep_merge(dest: Dict[str, Any], src: Dict[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dest.get(key), dict):
            _deep_merge(dest[key], value)
        else:
            dest[key] = value


def discover_skill_index(root: Path) -> Dict[str, Any]:
    result = load_skill_index(root)
    return {
        "found": result["found"],
        "path": result["path"],
        "parsed": result["parsed"],
        "rowCount": result["rowCount"],
        "rows": result["rows"],
    }


def resolve_skill(root: Path, skill_name: str) -> Dict[str, Any]:
    config = load_local_config(root)
    skill_index = discover_skill_index(root)
    match: Optional[Dict[str, str]] = None
    for row in skill_index["rows"]:
        if row["skill"] == skill_name:
            match = row
            break

    resolution = {
        "requestedSkill": skill_name,
        "matched": match is not None,
        "sourceRepo": None if match is None else match["sourceRepo"],
        "skillPath": None if match is None else match["skillPath"],
    }
    adapter = run_adapter_dry_mode(
        config["effective"]["defaultHarness"],
        resolution,
    )

    return {
        "config": config,
        "skillIndex": {
            "found": skill_index["found"],
            "path": skill_index["path"],
            "parsed": skill_index["parsed"],
            "rowCount": skill_index["rowCount"],
        },
        "resolution": resolution,
        "adapter": adapter,
    }


def _resolve_skill_file(root: Path, resolution: Dict[str, Any]) -> Dict[str, Any]:
    if not resolution["matched"]:
        return {
            "found": False,
            "path": None,
            "content": None,
        }

    source_repo = Path(resolution["sourceRepo"]).expanduser()
    if not source_repo.is_absolute():
        source_repo = (root / source_repo).resolve()

    skill_path = (source_repo / resolution["skillPath"]).resolve()
    if not skill_path.exists():
        return {
            "found": False,
            "path": str(skill_path),
            "content": None,
        }

    return {
        "found": True,
        "path": str(skill_path),
        "content": skill_path.read_text(),
    }


def _build_skill_prompt(skill_content: str, prompt: str) -> str:
    return (
        "Follow the resolved skill below before responding.\n\n"
        "Resolved skill:\n"
        f"{skill_content}\n\n"
        "User request:\n"
        f"{prompt}"
    )


def get_model_for_role(config_effective: Dict[str, Any], role: str) -> Optional[str]:
    models = config_effective.get("models", {})
    if not isinstance(models, dict):
        return None
    model = models.get(role)
    return str(model) if model else None


def run_skill(root: Path, skill_name: str, prompt: str) -> Dict[str, Any]:
    trace = resolve_skill(root, skill_name)
    if not trace["resolution"]["matched"]:
        return trace

    skill_file = _resolve_skill_file(root, trace["resolution"])
    trace["skillFile"] = {
        "found": skill_file["found"],
        "path": skill_file["path"],
    }
    if not skill_file["found"]:
        trace["adapter"] = AdapterResult(
            selected=trace["config"]["effective"]["defaultHarness"],
            found=True,
            mode="live",
            status="failed",
            attempted=False,
            details=AdapterDetails(
                reason="skill-file-missing",
                requestedSkill=trace["resolution"]["requestedSkill"],
                sourceRepo=trace["resolution"]["sourceRepo"],
                skillPath=trace["resolution"]["skillPath"],
            ),
        ).to_dict()
        return trace

    trace["adapter"] = run_adapter_live(
        trace["config"]["effective"]["defaultHarness"],
        _build_skill_prompt(skill_file["content"], prompt),
        context={
            "requestedSkill": trace["resolution"]["requestedSkill"],
            "sourceRepo": trace["resolution"]["sourceRepo"],
            "skillPath": trace["resolution"]["skillPath"],
            "resolvedSkillFilePath": skill_file["path"],
            "model": get_model_for_role(trace["config"]["effective"], "implementer"),
            "yolo": trace["config"]["effective"].get("yolo", False),
        },
    )
    return trace


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-stack")
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve-skill")
    resolve_parser.add_argument("skill")
    resolve_parser.add_argument("--root", type=Path)
    run_skill_parser = subparsers.add_parser("run-skill")
    run_skill_parser.add_argument("skill")
    run_skill_parser.add_argument("--prompt", required=True)
    run_skill_parser.add_argument("--root", type=Path)
    sync_skills_parser = subparsers.add_parser("sync-skills")
    sync_skills_parser.add_argument("--dry-run", action="store_true")
    sync_skills_parser.add_argument("--apply", action="store_true")
    sync_skills_parser.add_argument("--root", type=Path)
    sync_skills_parser.add_argument("--installed-skills-dir", type=Path, help=argparse.SUPPRESS)
    sync_skills_parser.add_argument("--backup-root", type=Path, help=argparse.SUPPRESS)
    adapter_parser = subparsers.add_parser("adapter")
    adapter_parser.add_argument("harness")
    adapter_parser.add_argument("--prompt", required=True)
    adapter_parser.add_argument("--root", type=Path)

    args = parser.parse_args(argv)

    if args.command == "resolve-skill":
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        trace = resolve_skill(root, args.skill)
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0 if trace["resolution"]["matched"] else 1
    if args.command == "run-skill":
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        trace = run_skill(root, args.skill, args.prompt)
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0 if trace["adapter"]["status"] == "completed" else 1
    if args.command == "adapter":
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        config = load_local_config(root)
        trace = {
            "adapter": run_adapter_live(
                args.harness,
                args.prompt,
                context={
                    "model": get_model_for_role(config["effective"], "implementer"),
                    "yolo": config["effective"].get("yolo", False),
                },
            ),
        }
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0 if trace["adapter"]["status"] == "completed" else 1
    if args.command == "sync-skills":
        if args.dry_run and args.apply:
            parser.error("sync-skills accepts only one of --dry-run or --apply")
        if not args.dry_run and not args.apply:
            parser.error("sync-skills requires --dry-run or --apply")
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        installed_skills_dir = args.installed_skills_dir.resolve() if args.installed_skills_dir is not None else None
        backup_root = args.backup_root.resolve() if args.backup_root is not None else None
        trace = (
            build_sync_plan(root, installed_skills_dir=installed_skills_dir)
            if args.dry_run
            else apply_sync_plan(root, installed_skills_dir=installed_skills_dir, backup_root=backup_root)
        )
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
