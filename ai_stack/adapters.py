from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Adapter:
    harness_id: str

    def dry_run(self, resolution: Dict[str, Any]) -> Dict[str, Any]:
        if not resolution["matched"]:
            return {
                "selected": self.harness_id,
                "found": True,
                "mode": "dry-run",
                "status": "skipped",
                "attempted": False,
                "details": {
                    "reason": "no-skill-match",
                },
            }

        return {
            "selected": self.harness_id,
            "found": True,
            "mode": "dry-run",
            "status": "ready",
            "attempted": True,
            "details": {
                "requestedSkill": resolution["requestedSkill"],
                "sourceRepo": resolution["sourceRepo"],
                "skillPath": resolution["skillPath"],
            },
        }


ADAPTERS = {
    "codex": Adapter("codex"),
    "copilot": Adapter("copilot"),
}


def run_adapter_dry_mode(harness_id: str, resolution: Dict[str, Any]) -> Dict[str, Any]:
    adapter: Optional[Adapter] = ADAPTERS.get(harness_id)
    if adapter is None:
        return {
            "selected": harness_id,
            "found": False,
            "mode": "dry-run",
            "status": "unsupported",
            "attempted": False,
            "details": {
                "reason": "unknown-adapter",
            },
        }

    return adapter.dry_run(resolution)


def run_adapter_live(harness_id: str, prompt: str) -> Dict[str, Any]:
    if harness_id != "codex":
        return {
            "selected": harness_id,
            "found": harness_id in ADAPTERS,
            "mode": "live",
            "status": "unsupported",
            "attempted": False,
            "exitCode": None,
            "resultText": "",
            "debug": {
                "stdout": "",
                "stderr": "",
            },
            "details": {
                "reason": "live-execution-not-supported",
            },
        }

    codex_bin = os.environ.get(
        "AI_STACK_CODEX_BIN",
        os.path.expanduser("~/.nvm/versions/node/v24.12.0/bin/codex"),
    )
    cmd = [codex_bin, "exec", prompt]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {
            "selected": harness_id,
            "found": True,
            "mode": "live",
            "status": "failed",
            "attempted": True,
            "exitCode": None,
            "resultText": "",
            "debug": {
                "stdout": "",
                "stderr": str(exc),
            },
            "details": {
                "command": cmd,
                "reason": "spawn-failed",
            },
        }

    result_text = proc.stdout.strip()
    return {
        "selected": harness_id,
        "found": True,
        "mode": "live",
        "status": "completed" if proc.returncode == 0 else "failed",
        "attempted": True,
        "exitCode": proc.returncode,
        "resultText": result_text,
        "debug": {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        },
        "details": {
            "command": cmd,
        },
    }
