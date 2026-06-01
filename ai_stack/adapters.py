from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
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


def rtk_install_hint() -> Dict[str, Any]:
    return {
        "expectedLocations": [
            str(Path.home() / ".local" / "bin" / "rtk"),
            "/opt/homebrew/bin/rtk",
            "/usr/local/bin/rtk",
        ],
        "installCommands": [
            "curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh",
            "brew install rtk-ai/tap/rtk",
        ],
        "verifyCommands": [
            "rtk --version",
            "rtk gain",
        ],
        "pathSuggestion": 'export PATH="$HOME/.local/bin:$PATH"',
    }


def resolve_required_bin(command_name: str) -> str:
    discovered = shutil.which(command_name)
    if discovered:
        return discovered
    return command_name


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

    rtk_bin = resolve_required_bin("rtk")
    codex_bin = resolve_required_bin("codex")
    cmd = [rtk_bin, "proxy", codex_bin, "exec", prompt]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        reason = "spawn-failed"
        rtk_status = "active"
        if exc.filename == rtk_bin:
            reason = "rtk-missing"
            rtk_status = "missing"
        elif exc.filename == codex_bin:
            reason = "codex-missing"
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
                "reason": reason,
                "rtk": {
                    "status": rtk_status,
                    "command": rtk_bin,
                    "install": rtk_install_hint() if reason == "rtk-missing" else None,
                },
                "harnessCommand": codex_bin,
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
            "rtk": {
                "status": "active",
                "command": rtk_bin,
            },
            "harnessCommand": codex_bin,
        },
    }
