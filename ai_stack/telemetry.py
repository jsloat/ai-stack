from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Dict, Mapping, Optional


def start_command_timer() -> Dict[str, Any]:
    return {
        "startedAt": _utc_now_iso(),
        "perfStart": time.perf_counter(),
    }


def finalize_telemetry(
    timer: Mapping[str, Any],
    command: str,
    outcome: str,
    route: Mapping[str, Any],
    capture_enabled: bool,
) -> Dict[str, Any]:
    finished_at = _utc_now_iso()
    duration_ms = int((time.perf_counter() - float(timer["perfStart"])) * 1000)
    return {
        "command": command,
        "captureEnabled": capture_enabled,
        "startedAt": str(timer["startedAt"]),
        "finishedAt": finished_at,
        "durationMs": duration_ms,
        "outcome": outcome,
        "route": dict(route),
    }


def telemetry_enabled_from_config(config: Optional[Mapping[str, Any]]) -> bool:
    if not config or not config.get("valid", False):
        return False
    telemetry = config.get("effective", {}).get("telemetry", {})
    if not isinstance(telemetry, dict):
        return False
    return bool(telemetry.get("enabled", False))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
