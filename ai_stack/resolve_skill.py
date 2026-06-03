from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_stack.adapter_contract import AdapterDetails, AdapterResult
from ai_stack.adapters import run_adapter_dry_mode, run_adapter_live


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

LOCAL_INDEX_PATH = Path("skill-indexes/local/skill-index.yaml")


def infer_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


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

    parsed = _parse_simple_yaml(config_path.read_text())
    _deep_merge(effective, parsed)
    return result


def _deep_merge(dest: Dict[str, Any], src: Dict[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dest.get(key), dict):
            _deep_merge(dest[key], value)
        else:
            dest[key] = value


def discover_skill_index(root: Path) -> Dict[str, Any]:
    index_path = root / LOCAL_INDEX_PATH
    result: Dict[str, Any] = {
        "found": index_path.exists(),
        "path": str(LOCAL_INDEX_PATH),
        "parsed": False,
        "rowCount": 0,
        "rows": [],
    }
    if not index_path.exists():
        return result

    rows = parse_skill_index(index_path.read_text())
    result["parsed"] = True
    result["rowCount"] = len(rows)
    result["rows"] = rows
    return result


def parse_skill_index(text: str) -> List[Dict[str, str]]:
    parsed = _parse_simple_yaml(text)
    skills = parsed.get("skills", [])
    if not isinstance(skills, list):
        raise ValueError("skill index must define a top-level 'skills' list")

    rows: List[Dict[str, str]] = []
    for item in skills:
        if not isinstance(item, dict):
            continue
        skill = item.get("id")
        when_to_use = item.get("when")
        source_repo = item.get("repo")
        skill_path = item.get("path")
        if not all(isinstance(value, str) and value for value in [skill, when_to_use, source_repo, skill_path]):
            continue
        rows.append(
            {
                "skill": skill,
                "whenToUse": when_to_use,
                "sourceRepo": source_repo,
                "skillPath": skill_path,
            }
        )
    return rows


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    lines = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))

    root: Dict[str, Any] = {}
    idx = 0
    while idx < len(lines):
        indent, line = lines[idx]
        if indent != 0 or line.startswith("- "):
            raise ValueError(f"Unsupported YAML line: {line!r}")
        key, rest = _split_yaml_key_value(line)
        idx += 1
        if rest == "":
            if idx < len(lines) and lines[idx][0] > indent:
                value, idx = _parse_yaml_block(lines, idx, lines[idx][0])
            else:
                value = {}
            root[key] = value
        else:
            root[key] = _parse_scalar(rest)
    return root


def _parse_yaml_block(lines: List[tuple[int, str]], idx: int, indent: int) -> tuple[Any, int]:
    if idx >= len(lines):
        return {}, idx
    _, line = lines[idx]
    if line.startswith("- "):
        return _parse_yaml_list(lines, idx, indent)
    return _parse_yaml_mapping(lines, idx, indent)


def _parse_yaml_mapping(lines: List[tuple[int, str]], idx: int, indent: int) -> tuple[Dict[str, Any], int]:
    mapping: Dict[str, Any] = {}
    while idx < len(lines):
        line_indent, line = lines[idx]
        if line_indent < indent:
            break
        if line_indent != indent or line.startswith("- "):
            raise ValueError(f"Unsupported YAML line: {line!r}")

        key, rest = _split_yaml_key_value(line)
        idx += 1
        if rest == "":
            if idx < len(lines) and lines[idx][0] > line_indent:
                value, idx = _parse_yaml_block(lines, idx, lines[idx][0])
            else:
                value = {}
            mapping[key] = value
        else:
            mapping[key] = _parse_scalar(rest)
    return mapping, idx


def _parse_yaml_list(lines: List[tuple[int, str]], idx: int, indent: int) -> tuple[List[Any], int]:
    items: List[Any] = []
    while idx < len(lines):
        line_indent, line = lines[idx]
        if line_indent < indent:
            break
        if line_indent != indent or not line.startswith("- "):
            raise ValueError(f"Unsupported YAML line: {line!r}")

        rest = line[2:].strip()
        idx += 1
        if rest == "":
            if idx < len(lines) and lines[idx][0] > line_indent:
                item, idx = _parse_yaml_block(lines, idx, lines[idx][0])
            else:
                item = None
            items.append(item)
            continue

        if ":" not in rest:
            items.append(_parse_scalar(rest))
            continue

        key, value = _split_yaml_key_value(rest)
        item: Dict[str, Any] = {key: _parse_scalar(value)} if value else {key: {}}

        while idx < len(lines):
            next_indent, next_line = lines[idx]
            if next_indent <= line_indent:
                break
            if next_line.startswith("- "):
                break
            if next_indent != line_indent + 2:
                raise ValueError(f"Unsupported YAML line: {next_line!r}")

            nested_key, nested_value = _split_yaml_key_value(next_line)
            idx += 1
            if nested_value == "":
                if idx < len(lines) and lines[idx][0] > next_indent:
                    value_obj, idx = _parse_yaml_block(lines, idx, lines[idx][0])
                else:
                    value_obj = {}
                item[nested_key] = value_obj
            else:
                item[nested_key] = _parse_scalar(nested_value)

        items.append(item)
    return items, idx


def _split_yaml_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Unsupported YAML line: {line!r}")
    key, rest = line.split(":", 1)
    return key.strip(), rest.strip()


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

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
