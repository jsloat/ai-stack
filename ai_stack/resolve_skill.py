from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_stack.agent_sync import apply_agent_sync_plan, build_agent_sync_plan, SUPPORTED_HARNESSES as SUPPORTED_AGENT_HARNESSES
from ai_stack.skill_index import load_skill_index, parse_simple_yaml
from ai_stack.skill_sync import apply_sync_plan, build_sync_plan, SUPPORTED_HARNESSES as SUPPORTED_SKILL_HARNESSES
from ai_stack.telemetry import finalize_telemetry, start_command_timer, telemetry_enabled_from_config


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
    "orchestration": {
        "root": None,
    },
    "repos": {
        "aiStack": None,
    },
}


ALLOWED_TOP_LEVEL_CONFIG_KEYS = {"defaultHarness", "yolo", "models", "telemetry", "orchestration", "repos"}
ALLOWED_MODEL_ROLE_KEYS = {"planner", "implementer", "cheapVerifier"}
ALLOWED_TELEMETRY_KEYS = {"enabled"}
ALLOWED_ORCHESTRATION_KEYS = {"root"}
ALLOWED_REPO_KEYS = {"aiStack"}


def infer_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_local_config(root: Path) -> Dict[str, Any]:
    config_path = root / "config.local.yaml"
    effective = json.loads(json.dumps(DEFAULT_CONFIG))
    result = {
        "path": str(config_path.relative_to(root)),
        "localConfigFound": config_path.exists(),
        "parsed": False,
        "valid": True,
        "errors": [],
        "effective": effective,
    }
    if not config_path.exists():
        return result

    try:
        parsed = parse_simple_yaml(config_path.read_text())
    except ValueError as exc:
        result["errors"] = [str(exc)]
        result["valid"] = False
        return result

    result["parsed"] = True
    errors = validate_local_config(parsed, root=root)
    if errors:
        result["errors"] = errors
        result["valid"] = False
        return result

    _deep_merge(effective, parsed)
    return result


def _deep_merge(dest: Dict[str, Any], src: Dict[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dest.get(key), dict):
            _deep_merge(dest[key], value)
        else:
            dest[key] = value


def validate_local_config(parsed: Dict[str, Any], *, root: Optional[Path] = None) -> List[str]:
    errors: List[str] = []
    unknown_top_level = sorted(set(parsed) - ALLOWED_TOP_LEVEL_CONFIG_KEYS)
    for key in unknown_top_level:
        errors.append(f"Unknown top-level config key: {key}")

    default_harness = parsed.get("defaultHarness")
    if default_harness is not None and not isinstance(default_harness, str):
        errors.append("defaultHarness must be a string")

    yolo = parsed.get("yolo")
    if yolo is not None and not isinstance(yolo, bool):
        errors.append("yolo must be a boolean")

    models = parsed.get("models")
    if models is not None:
        if not isinstance(models, dict):
            errors.append("models must be a mapping")
        else:
            unknown_model_keys = sorted(set(models) - ALLOWED_MODEL_ROLE_KEYS)
            for key in unknown_model_keys:
                errors.append(f"Unknown models key: {key}")
            for key, value in models.items():
                if key in ALLOWED_MODEL_ROLE_KEYS and not isinstance(value, str):
                    errors.append(f"models.{key} must be a string")

    telemetry = parsed.get("telemetry")
    if telemetry is not None:
        if not isinstance(telemetry, dict):
            errors.append("telemetry must be a mapping")
        else:
            unknown_telemetry_keys = sorted(set(telemetry) - ALLOWED_TELEMETRY_KEYS)
            for key in unknown_telemetry_keys:
                errors.append(f"Unknown telemetry key: {key}")
            enabled = telemetry.get("enabled")
            if enabled is not None and not isinstance(enabled, bool):
                errors.append("telemetry.enabled must be a boolean")

    orchestration = parsed.get("orchestration")
    if orchestration is not None:
        if not isinstance(orchestration, dict):
            errors.append("orchestration must be a mapping")
        else:
            unknown_orchestration_keys = sorted(set(orchestration) - ALLOWED_ORCHESTRATION_KEYS)
            for key in unknown_orchestration_keys:
                errors.append(f"Unknown orchestration key: {key}")
            root = orchestration.get("root")
            if root is not None and not isinstance(root, str):
                errors.append("orchestration.root must be a string")

    repos = parsed.get("repos")
    if repos is not None:
        if not isinstance(repos, dict):
            errors.append("repos must be a mapping")
        else:
            unknown_repo_keys = sorted(set(repos) - ALLOWED_REPO_KEYS)
            for key in unknown_repo_keys:
                errors.append(f"Unknown repos key: {key}")
            ai_stack_repo = repos.get("aiStack")
            if ai_stack_repo is not None:
                if not isinstance(ai_stack_repo, str):
                    errors.append("repos.aiStack must be a string")
                elif root is not None:
                    ai_stack_path = Path(ai_stack_repo).expanduser()
                    if not ai_stack_path.is_absolute():
                        ai_stack_path = (root / ai_stack_path).resolve()
                    if not ai_stack_path.exists():
                        errors.append("repos.aiStack must point to an existing path")
                    elif not ai_stack_path.is_dir():
                        errors.append("repos.aiStack must point to a directory")

    return errors


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
    if not config["valid"]:
        return {
            "config": config,
            "skillIndex": {
                "found": False,
                "path": str((root / "skill-indexes" / "skill-index.yaml").relative_to(root)),
                "parsed": False,
                "rowCount": 0,
            },
            "resolution": {
                "requestedSkill": skill_name,
                "matched": False,
                "sourceRepo": None,
                "skillPath": None,
            },
            "adapter": {
                "selected": config["effective"]["defaultHarness"],
                "found": False,
                "mode": "dry-run",
                "status": "blocked",
                "attempted": False,
                "details": {
                    "reason": "invalid-config",
                },
            },
        }

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


def get_model_for_role(config_effective: Dict[str, Any], role: str) -> Optional[str]:
    models = config_effective.get("models", {})
    if not isinstance(models, dict):
        return None
    model = models.get(role)
    return str(model) if model else None


def _with_telemetry(
    trace: Dict[str, Any],
    *,
    timer: Dict[str, Any],
    command: str,
    outcome: str,
    route: Dict[str, Any],
    config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    enriched = dict(trace)
    enriched["telemetry"] = finalize_telemetry(
        timer,
        command=command,
        outcome=outcome,
        route=route,
        capture_enabled=telemetry_enabled_from_config(config),
    )
    return enriched


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-stack")
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve-skill")
    resolve_parser.add_argument("skill")
    resolve_parser.add_argument("--root", type=Path)
    sync_skills_parser = subparsers.add_parser("sync-skills")
    sync_skills_parser.add_argument("--dry-run", action="store_true")
    sync_skills_parser.add_argument("--apply", action="store_true")
    sync_skills_parser.add_argument("--harness", choices=(*SUPPORTED_SKILL_HARNESSES, "all"), default="all")
    sync_skills_parser.add_argument("--root", type=Path)
    sync_skills_parser.add_argument("--installed-skills-dir", type=Path, help=argparse.SUPPRESS)
    sync_skills_parser.add_argument("--backup-root", type=Path, help=argparse.SUPPRESS)
    sync_agents_parser = subparsers.add_parser("sync-global-instructions")
    sync_agents_parser.add_argument("--dry-run", action="store_true")
    sync_agents_parser.add_argument("--apply", action="store_true")
    sync_agents_parser.add_argument("--root", type=Path)
    sync_agents_parser.add_argument("--harness", choices=(*SUPPORTED_AGENT_HARNESSES, "all"), default="all")
    sync_agents_parser.add_argument("--codex-target-file", type=Path, help=argparse.SUPPRESS)
    sync_agents_parser.add_argument("--copilot-target-file", type=Path, help=argparse.SUPPRESS)
    sync_agents_parser.add_argument("--backup-root", type=Path, help=argparse.SUPPRESS)
    adapter_parser = subparsers.add_parser("adapter")
    adapter_parser.add_argument("harness")
    adapter_parser.add_argument("--prompt", required=True)
    adapter_parser.add_argument("--root", type=Path)

    args = parser.parse_args(argv)

    if args.command == "resolve-skill":
        timer = start_command_timer()
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        trace = resolve_skill(root, args.skill)
        trace = _with_telemetry(
            trace,
            timer=timer,
            command="resolve-skill",
            outcome="matched" if trace["config"]["valid"] and trace["resolution"]["matched"] else (
                "blocked" if not trace["config"]["valid"] else "not-matched"
            ),
            route={
                "root": str(root),
                "requestedSkill": args.skill,
                "selectedHarness": trace["adapter"]["selected"],
                "adapterMode": trace["adapter"]["mode"],
            },
            config=trace["config"],
        )
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0 if trace["config"]["valid"] and trace["resolution"]["matched"] else 1
    if args.command == "adapter":
        timer = start_command_timer()
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        config = load_local_config(root)
        if not config["valid"]:
            trace = {
                "config": config,
                "adapter": {
                    "selected": args.harness,
                    "found": False,
                    "mode": "live",
                    "status": "blocked",
                    "attempted": False,
                    "details": {
                        "reason": "invalid-config",
                    },
                },
            }
            trace = _with_telemetry(
                trace,
                timer=timer,
                command="adapter",
                outcome="blocked",
                route={
                    "root": str(root),
                    "selectedHarness": args.harness,
                    "adapterMode": "live",
                    "promptLength": len(args.prompt),
                },
                config=config,
            )
            print(json.dumps(trace, indent=2, sort_keys=True))
            return 1
        trace = {
            "config": config,
            "adapter": run_adapter_live(
                args.harness,
                args.prompt,
                context={
                    "model": get_model_for_role(config["effective"], "implementer"),
                    "yolo": config["effective"].get("yolo", False),
                },
            ),
        }
        trace = _with_telemetry(
            trace,
            timer=timer,
            command="adapter",
            outcome=str(trace["adapter"]["status"]),
            route={
                "root": str(root),
                "selectedHarness": args.harness,
                "adapterMode": trace["adapter"]["mode"],
                "promptLength": len(args.prompt),
            },
            config=config,
        )
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0 if trace["adapter"]["status"] == "completed" else 1
    if args.command == "sync-skills":
        timer = start_command_timer()
        if args.dry_run and args.apply:
            parser.error("sync-skills accepts only one of --dry-run or --apply")
        if not args.dry_run and not args.apply:
            parser.error("sync-skills requires --dry-run or --apply")
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        config = load_local_config(root)
        installed_skills_dir = args.installed_skills_dir.resolve() if args.installed_skills_dir is not None else None
        backup_root = args.backup_root.resolve() if args.backup_root is not None else None
        trace = (
            build_sync_plan(root, harness=args.harness, installed_skills_dir=installed_skills_dir)
            if args.dry_run
            else apply_sync_plan(root, harness=args.harness, installed_skills_dir=installed_skills_dir, backup_root=backup_root)
        )
        trace = _with_telemetry(
            trace,
            timer=timer,
            command="sync-skills",
            outcome="planned" if args.dry_run else "applied",
            route={
                "root": str(root),
                "syncMode": "dry-run" if args.dry_run else "apply",
                "targetHarness": args.harness,
            },
            config=config,
        )
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0
    if args.command == "sync-global-instructions":
        timer = start_command_timer()
        if args.dry_run and args.apply:
            parser.error("sync-global-instructions accepts only one of --dry-run or --apply")
        if not args.dry_run and not args.apply:
            parser.error("sync-global-instructions requires --dry-run or --apply")
        root = args.root.resolve() if args.root is not None else infer_repo_root()
        config = load_local_config(root)
        target_overrides = {
            harness: value.resolve()
            for harness, value in {
                "codex": args.codex_target_file,
                "copilot": args.copilot_target_file,
            }.items()
            if value is not None
        }
        backup_root = args.backup_root.resolve() if args.backup_root is not None else None
        trace = (
            build_agent_sync_plan(root, harness=args.harness, target_overrides=target_overrides)
            if args.dry_run
            else apply_agent_sync_plan(
                root,
                harness=args.harness,
                target_overrides=target_overrides,
                backup_root=backup_root,
            )
        )
        trace = _with_telemetry(
            trace,
            timer=timer,
            command="sync-global-instructions",
            outcome="planned" if args.dry_run else "applied",
            route={
                "root": str(root),
                "syncMode": "dry-run" if args.dry_run else "apply",
                "targetHarness": args.harness,
            },
            config=config,
        )
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
