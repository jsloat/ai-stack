from __future__ import annotations

from dataclasses import dataclass
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


def infer_harness_failure_reason(stderr_text: str, harness_command: str) -> Optional[str]:
    normalized = stderr_text.lower()
    command_name = Path(harness_command).name.lower()
    missing_markers = [
        "no such file or directory",
        "command not found",
        "filenotfounderror",
    ]
    if command_name in normalized and any(marker in normalized for marker in missing_markers):
        return f"{command_name}-missing"
    return None


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
                "harness": {
                    "id": harness_id,
                    "command": codex_bin,
                    "install": None,
                },
            },
        }

    result_text = proc.stdout.strip()
    failure_reason = None
    if proc.returncode != 0:
        failure_reason = infer_harness_failure_reason(proc.stderr, codex_bin)
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
            "reason": failure_reason,
            "rtk": {
                "status": "active",
                "command": rtk_bin,
            },
            "harness": {
                "id": harness_id,
                "command": codex_bin,
                "install": None,
            },
        },
    }
