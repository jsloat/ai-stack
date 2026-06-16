from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


LOCAL_INDEX_PATH = Path("skill-indexes/local/skill-index.yaml")


def parse_skill_index(text: str) -> List[Dict[str, str]]:
    parsed = parse_simple_yaml(text)
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


def load_skill_index(root: Path) -> Dict[str, Any]:
    index_path = root / LOCAL_INDEX_PATH
    result: Dict[str, Any] = {
        "found": index_path.exists(),
        "path": str(LOCAL_INDEX_PATH),
        "parsed": False,
        "rowCount": 0,
        "rows": [],
        "text": None,
    }
    if not index_path.exists():
        return result

    text = index_path.read_text()
    rows = parse_skill_index(text)
    result["parsed"] = True
    result["rowCount"] = len(rows)
    result["rows"] = rows
    result["text"] = text
    return result


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
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


def _parse_yaml_block(lines: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Any, int]:
    if idx >= len(lines):
        return {}, idx
    _, line = lines[idx]
    if line.startswith("- "):
        return _parse_yaml_list(lines, idx, indent)
    return _parse_yaml_mapping(lines, idx, indent)


def _parse_yaml_mapping(lines: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Dict[str, Any], int]:
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


def _parse_yaml_list(lines: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[List[Any], int]:
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


def _split_yaml_key_value(line: str) -> Tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Unsupported YAML line: {line!r}")
    key, rest = line.split(":", 1)
    return key.strip(), rest.strip()
