"""Core data models for orchestration."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import uuid


class ProjectStatus(Enum):
    """Project lifecycle states."""
    DRAFT = "draft"
    APPROVED = "approved"
    PLANNED = "planned"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    NEEDS_REVISION = "needs-revision"


class StepStatus(Enum):
    """Step execution states."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    NEEDS_REVISION = "needs-revision"
    COMPLETED = "completed"


@dataclass
class Step:
    """A concrete action record within a stage."""
    id: str
    stage_id: str
    title: str
    kind: str
    status: StepStatus = StepStatus.PENDING
    inputs: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    attempt_count: int = 0
    depends_on: Optional[List[str]] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        d = asdict(self)
        d["status"] = self.status.value
        d["updated_at"] = self.updated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """Deserialize from dict."""
        data = data.copy()
        data["status"] = StepStatus(data["status"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


@dataclass
class Stage:
    """An ordered execution unit, typically derived from a spec phase."""
    id: str
    phase_name: str
    index: int
    status: ProjectStatus = ProjectStatus.DRAFT
    steps: List[Step] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "phase_name": self.phase_name,
            "index": self.index,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stage":
        """Deserialize from dict."""
        data = data.copy()
        data["status"] = ProjectStatus(data["status"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["steps"] = [Step.from_dict(s) for s in data.get("steps", [])]
        return cls(**data)


@dataclass
class Run:
    """One orchestration attempt for one approved spec."""
    id: str
    project_id: str
    spec_path: Path
    overall_status: ProjectStatus = ProjectStatus.PLANNED
    stages: List[Stage] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    summary_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "spec_path": str(self.spec_path),
            "overall_status": self.overall_status.value,
            "stages": [s.to_dict() for s in self.stages],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "summary_path": str(self.summary_path) if self.summary_path else None,
        }

    def save(self, run_dir: Path) -> None:
        """Persist run to run.json."""
        run_dir.mkdir(parents=True, exist_ok=True)
        run_file = run_dir / "run.json"
        with open(run_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, run_dir: Path) -> "Run":
        """Load run from run.json."""
        run_file = run_dir / "run.json"
        with open(run_file) as f:
            data = json.load(f)
        data["spec_path"] = Path(data["spec_path"])
        data["overall_status"] = ProjectStatus(data["overall_status"])
        data["started_at"] = datetime.fromisoformat(data["started_at"]) if data["started_at"] else None
        data["finished_at"] = datetime.fromisoformat(data["finished_at"]) if data["finished_at"] else None
        data["summary_path"] = Path(data["summary_path"]) if data["summary_path"] else None
        data["stages"] = [Stage.from_dict(s) for s in data.get("stages", [])]
        return cls(**data)


@dataclass
class Project:
    """An orchestrated project with metadata and run history."""
    id: str
    name: str
    root_dir: Path
    status: ProjectStatus = ProjectStatus.DRAFT
    intake_source: Optional[str] = None
    working_spec_path: Optional[Path] = None
    approved_spec_path: Optional[Path] = None
    runs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "name": self.name,
            "root_dir": str(self.root_dir),
            "status": self.status.value,
            "intake_source": self.intake_source,
            "working_spec_path": str(self.working_spec_path) if self.working_spec_path else None,
            "approved_spec_path": str(self.approved_spec_path) if self.approved_spec_path else None,
            "runs": self.runs,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def save(self) -> None:
        """Persist project metadata to project.json."""
        project_file = self.root_dir / "project.json"
        with open(project_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, root_dir: Path) -> "Project":
        """Load project metadata from project.json."""
        project_file = root_dir / "project.json"
        with open(project_file) as f:
            data = json.load(f)
        data["root_dir"] = Path(data["root_dir"])
        data["status"] = ProjectStatus(data["status"])
        data["working_spec_path"] = Path(data["working_spec_path"]) if data["working_spec_path"] else None
        data["approved_spec_path"] = Path(data["approved_spec_path"]) if data["approved_spec_path"] else None
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
