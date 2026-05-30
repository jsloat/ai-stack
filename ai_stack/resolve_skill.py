from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG = {
    "defaultHarness": "copilot",
    "models": {
        "planner": "sonnet",
        "implementer": "gpt-5.5",
        "cheapVerifier": "gpt-5.5-mini",
    },
    "telemetry": {
        "enabled": True,
    },
}

INDEX_PATH = Path("skill-indexes/local/skill-index.example.md")


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


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[tuple[int, Dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"Unsupported YAML line: {raw_line!r}")

        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()

        while indent <= stack[-1][0]:
            stack.pop()

        container = stack[-1][1]
        if rest == "":
            child: Dict[str, Any] = {}
            container[key] = child
            stack.append((indent, child))
        else:
            container[key] = _parse_scalar(rest)

    return root


def _deep_merge(dest: Dict[str, Any], src: Dict[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dest.get(key), dict):
            _deep_merge(dest[key], value)
        else:
            dest[key] = value


def discover_skill_index(root: Path) -> Dict[str, Any]:
    index_path = root / INDEX_PATH
    result: Dict[str, Any] = {
        "found": index_path.exists(),
        "path": str(INDEX_PATH),
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
    lines = text.splitlines()
    rows: List[Dict[str, str]] = []
    for idx, line in enumerate(lines):
        if line.strip() == "| Skill | When to use | Source Repo | Skill Path |":
            if idx + 1 >= len(lines):
                break
            data_start = idx + 2
            for data_line in lines[data_start:]:
                stripped = data_line.strip()
                if not stripped.startswith("|"):
                    break
                parts = [part.strip() for part in stripped.strip("|").split("|")]
                if len(parts) != 4:
                    continue
                rows.append(
                    {
                        "skill": parts[0].strip("`"),
                        "whenToUse": parts[1],
                        "sourceRepo": parts[2].strip("`"),
                        "skillPath": parts[3].strip("`"),
                    }
                )
            break
    return rows


def resolve_skill(root: Path, skill_name: str) -> Dict[str, Any]:
    config = load_local_config(root)
    skill_index = discover_skill_index(root)
    match: Optional[Dict[str, str]] = None
    for row in skill_index["rows"]:
        if row["skill"] == skill_name:
            match = row
            break

    return {
        "config": config,
        "skillIndex": {
            "found": skill_index["found"],
            "path": skill_index["path"],
            "parsed": skill_index["parsed"],
            "rowCount": skill_index["rowCount"],
        },
        "resolution": {
            "requestedSkill": skill_name,
            "matched": match is not None,
            "sourceRepo": None if match is None else match["sourceRepo"],
            "skillPath": None if match is None else match["skillPath"],
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-stack")
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve-skill")
    resolve_parser.add_argument("skill")

    args = parser.parse_args(argv)

    if args.command == "resolve-skill":
        trace = resolve_skill(Path.cwd(), args.skill)
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0 if trace["resolution"]["matched"] else 1

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
