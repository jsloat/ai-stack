from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional, Protocol


@dataclass(frozen=True)
class AdapterDebug:
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class RtkDetails:
    status: str
    mediation: str
    command: str
    reason: Optional[str] = None
    install: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class HarnessDetails:
    id: str
    command: str
    executionSupport: str = "unsupported"
    rtkSupport: str = "exempt"
    toolSurface: str = "native-cli"
    model: Optional[str] = None
    yolo: bool = False
    install: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class AdapterDetails:
    reason: Optional[str] = None
    requestedSkill: Optional[str] = None
    sourceRepo: Optional[str] = None
    skillPath: Optional[str] = None
    resolvedSkillFilePath: Optional[str] = None
    command: Optional[list[str]] = None
    rtk: Optional[RtkDetails] = None
    harness: Optional[HarnessDetails] = None


@dataclass(frozen=True)
class AdapterResult:
    selected: str
    found: bool
    mode: str
    status: str
    attempted: bool
    exitCode: Optional[int] = None
    resultText: str = ""
    debug: AdapterDebug = field(default_factory=AdapterDebug)
    details: AdapterDetails = field(default_factory=AdapterDetails)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdapterRuntime(Protocol):
    harness_id: str

    def dry_run(self, resolution: Mapping[str, Any]) -> AdapterResult:
        ...

    def run_prompt(self, prompt: str, context: Optional[Mapping[str, Any]] = None) -> AdapterResult:
        ...
