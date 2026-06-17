from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping, Optional

from ai_stack.adapter_contract import (
    AdapterDebug,
    AdapterDetails,
    AdapterResult,
    AdapterRuntime,
    HarnessDetails,
    RtkDetails,
)

@dataclass(frozen=True)
class BasicAdapter:
    harness_id: str

    def dry_run(self, resolution: Mapping[str, Any]) -> AdapterResult:
        if not resolution["matched"]:
            return AdapterResult(
                selected=self.harness_id,
                found=True,
                mode="dry-run",
                status="skipped",
                attempted=False,
                details=AdapterDetails(reason="no-skill-match"),
            )

        return AdapterResult(
            selected=self.harness_id,
            found=True,
            mode="dry-run",
            status="ready",
            attempted=True,
            details=AdapterDetails(
                requestedSkill=resolution["requestedSkill"],
                sourceRepo=resolution["sourceRepo"],
                skillPath=resolution["skillPath"],
            ),
        )

    def run_prompt(self, prompt: str, context: Optional[Mapping[str, Any]] = None) -> AdapterResult:
        return AdapterResult(
            selected=self.harness_id,
            found=True,
            mode="live",
            status="unsupported",
            attempted=False,
            details=AdapterDetails(
                reason="live-execution-not-supported",
                rtk=RtkDetails(
                    status="exempt",
                    mediation="exempt",
                    command="",
                    reason="harness-exempt-from-rtk",
                ),
                harness=HarnessDetails(
                    id=self.harness_id,
                    command=self.harness_id,
                    executionSupport="dry-run-only",
                    rtkSupport="exempt",
                    toolSurface="native-cli",
                ),
            ),
        )


@dataclass(frozen=True)
class CodexAdapter(BasicAdapter):
    def run_prompt(self, prompt: str, context: Optional[Mapping[str, Any]] = None) -> AdapterResult:
        rtk_bin = resolve_required_bin("rtk")
        codex_bin = resolve_required_bin("codex")
        context = context or {}
        model = context.get("model")
        yolo = bool(context.get("yolo", False))
        cmd = [rtk_bin, "proxy", codex_bin, "exec"]
        if model:
            cmd.extend(["-m", str(model)])
        if yolo:
            cmd.extend(["--sandbox", "danger-full-access", "--skip-git-repo-check"])
        cmd.append(prompt)

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
            return AdapterResult(
                selected=self.harness_id,
                found=True,
                mode="live",
                status="failed",
                attempted=True,
                exitCode=None,
                resultText="",
                debug=AdapterDebug(stderr=str(exc)),
                details=AdapterDetails(
                    command=cmd,
                    reason=reason,
                    requestedSkill=context.get("requestedSkill"),
                    sourceRepo=context.get("sourceRepo"),
                    skillPath=context.get("skillPath"),
                    resolvedSkillFilePath=context.get("resolvedSkillFilePath"),
                    rtk=RtkDetails(
                        status=rtk_status,
                        mediation="required",
                        command=rtk_bin,
                        reason="binary-not-found" if reason == "rtk-missing" else None,
                        install=rtk_install_hint() if reason == "rtk-missing" else None,
                    ),
                    harness=HarnessDetails(
                        id=self.harness_id,
                        command=codex_bin,
                        executionSupport="live",
                        rtkSupport="required",
                        toolSurface="native-cli",
                        model=str(model) if model is not None else None,
                        yolo=yolo,
                        install=None,
                    ),
                ),
            )

        failure_reason = None
        if proc.returncode != 0:
            failure_reason = infer_harness_failure_reason(proc.stderr, codex_bin)
        return AdapterResult(
            selected=self.harness_id,
            found=True,
            mode="live",
            status="completed" if proc.returncode == 0 else "failed",
            attempted=True,
            exitCode=proc.returncode,
            resultText=proc.stdout.strip(),
            debug=AdapterDebug(stdout=proc.stdout, stderr=proc.stderr),
            details=AdapterDetails(
                command=cmd,
                reason=failure_reason,
                requestedSkill=context.get("requestedSkill"),
                sourceRepo=context.get("sourceRepo"),
                skillPath=context.get("skillPath"),
                resolvedSkillFilePath=context.get("resolvedSkillFilePath"),
                rtk=RtkDetails(
                    status="active",
                    mediation="required",
                    command=rtk_bin,
                ),
                harness=HarnessDetails(
                    id=self.harness_id,
                    command=codex_bin,
                    executionSupport="live",
                    rtkSupport="required",
                    toolSurface="native-cli",
                    model=str(model) if model is not None else None,
                    yolo=yolo,
                    install=None,
                ),
            ),
        )


ADAPTERS = {
    "codex": CodexAdapter("codex"),
    "copilot": BasicAdapter("copilot"),
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


def run_adapter_dry_mode(harness_id: str, resolution: Mapping[str, Any]) -> dict[str, Any]:
    adapter: Optional[AdapterRuntime] = ADAPTERS.get(harness_id)
    if adapter is None:
        return AdapterResult(
            selected=harness_id,
            found=False,
            mode="dry-run",
            status="unsupported",
            attempted=False,
            details=AdapterDetails(reason="unknown-adapter"),
        ).to_dict()

    return adapter.dry_run(resolution).to_dict()


def run_adapter_live(harness_id: str, prompt: str, context: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
    adapter: Optional[AdapterRuntime] = ADAPTERS.get(harness_id)
    if adapter is None:
        return AdapterResult(
            selected=harness_id,
            found=False,
            mode="live",
            status="unsupported",
            attempted=False,
            details=AdapterDetails(reason="unknown-adapter"),
        ).to_dict()

    return adapter.run_prompt(prompt, context=context).to_dict()
