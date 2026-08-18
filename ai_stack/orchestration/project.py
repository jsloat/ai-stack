"""Project management for orchestration."""

from pathlib import Path
from datetime import datetime
import uuid
import re
from typing import Optional, List, Tuple

from .models import Project, ProjectStatus, Run, Stage, Step, StepStatus


class ProjectManager:
    """Manages orchestration projects and their lifecycle."""

    def __init__(self, orchestration_root: Path):
        """Initialize with orchestration root directory."""
        self.root = Path(orchestration_root)
        self.projects_dir = self.root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def init_project(
        self,
        name: str,
        spec_source: Optional[str] = None,
        spec_template: Optional[str] = None,
    ) -> Project:
        """
        Initialize a new project.

        Args:
            name: Human-readable project name
            spec_source: Path to existing spec or source material
            spec_template: Template content if starting fresh

        Returns:
            Created Project instance
        """
        # Create dated project folder
        now = datetime.utcnow()
        date_prefix = now.strftime("%Y%m%d")
        project_slug = self._slugify(name)
        project_dir_name = f"{date_prefix}-{project_slug}"
        project_root = self.projects_dir / project_dir_name

        # Ensure unique directory
        counter = 1
        base_dir_name = project_dir_name
        while project_root.exists():
            project_dir_name = f"{base_dir_name}-{counter}"
            project_root = self.projects_dir / project_dir_name
            counter += 1

        project_root.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (project_root / "runs").mkdir(exist_ok=True)
        (project_root / "artifacts").mkdir(exist_ok=True)
        (project_root / "docs").mkdir(exist_ok=True)

        # Create project instance
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            root_dir=project_root,
            status=ProjectStatus.DRAFT,
            intake_source=spec_source,
        )

        # Handle spec initialization
        if spec_source:
            # Normalize from existing source
            self._create_working_spec_from_source(project, spec_source)
        elif spec_template:
            # Use provided template
            self._create_working_spec_from_template(project, spec_template)
        else:
            # Create minimal template
            self._create_working_spec_from_template(project, self._default_template(project.name))

        project.save()
        return project

    def approve_project(self, project: Project) -> None:
        """
        Approve a draft project for execution.

        Validates the working spec and transitions it to approved.
        """
        working_spec = project.working_spec_path
        if not working_spec or not working_spec.exists():
            raise ValueError(f"Working spec not found: {working_spec}")

        # Validate spec structure
        self._validate_spec_structure(working_spec)

        # Copy working spec to approved spec
        approved_spec = project.root_dir / "docs" / "03-approved-spec.md"
        with open(working_spec) as src:
            content = src.read()
        with open(approved_spec, "w") as dst:
            dst.write(content)

        # Update project status
        project.approved_spec_path = approved_spec
        project.status = ProjectStatus.APPROVED
        project.updated_at = datetime.utcnow()
        project.save()

    def create_run_from_approved(self, project: Project) -> Run:
        """
        Create a run from an approved project spec.

        Extracts phases and checklist items from the approved spec.
        """
        if project.status != ProjectStatus.APPROVED:
            raise ValueError(f"Project must be approved before creating run: {project.status.value}")

        approved_spec = project.approved_spec_path
        if not approved_spec or not approved_spec.exists():
            raise ValueError(f"Approved spec not found: {approved_spec}")

        # Parse spec to extract phases and create stages
        stages = self._extract_stages_from_spec(approved_spec)

        # Create run
        run = Run(
            id=str(uuid.uuid4()),
            project_id=project.id,
            spec_path=approved_spec,
            overall_status=ProjectStatus.PLANNED,
            stages=stages,
        )

        # Create run directory and save
        run_dir = project.root_dir / "runs" / run.id
        run.save(run_dir)

        # Track run in project
        project.runs.append(run.id)
        project.status = ProjectStatus.PLANNED
        project.updated_at = datetime.utcnow()
        project.save()

        return run

    def get_project_status(self, project: Project) -> dict:
        """
        Get human-readable status of a project.

        Returns structured status dict suitable for JSON or terminal output.
        """
        latest_run = None
        if project.runs:
            latest_run_dir = project.root_dir / "runs" / project.runs[-1]
            if latest_run_dir.exists():
                latest_run = Run.load(latest_run_dir)

        return {
            "project_id": project.id,
            "name": project.name,
            "status": project.status.value,
            "root_dir": str(project.root_dir),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "working_spec": str(project.working_spec_path) if project.working_spec_path else None,
            "approved_spec": str(project.approved_spec_path) if project.approved_spec_path else None,
            "runs": len(project.runs),
            "latest_run": {
                "id": latest_run.id,
                "status": latest_run.overall_status.value,
                "started_at": latest_run.started_at.isoformat() if latest_run.started_at else None,
                "finished_at": latest_run.finished_at.isoformat() if latest_run.finished_at else None,
                "stages_completed": sum(1 for s in latest_run.stages if s.status == ProjectStatus.COMPLETED),
                "stages_total": len(latest_run.stages),
            } if latest_run else None,
        }

    def load_project(self, project_id: str) -> Optional[Project]:
        """Load a project by ID, searching all dated folders."""
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    project = Project.load(project_dir)
                    if project.id == project_id:
                        return project
        return None

    def find_projects(self, name_pattern: Optional[str] = None) -> List[Project]:
        """Find all projects, optionally filtered by name pattern."""
        projects = []
        for project_dir in sorted(self.projects_dir.iterdir(), reverse=True):
            if project_dir.is_dir():
                project_file = project_dir / "project.json"
                if project_file.exists():
                    project = Project.load(project_dir)
                    if name_pattern is None or name_pattern.lower() in project.name.lower():
                        projects.append(project)
        return projects

    # Private helpers

    def _slugify(self, name: str) -> str:
        """Convert a name to a URL-safe slug."""
        s = name.lower()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[-\s]+", "-", s)
        return s.strip("-")

    def _create_working_spec_from_source(self, project: Project, spec_path: str) -> None:
        """Create working spec by copying and normalizing an existing spec."""
        source = Path(spec_path)
        if not source.exists():
            raise FileNotFoundError(f"Spec source not found: {spec_path}")

        working_spec = project.root_dir / "docs" / "02-working-spec.md"
        with open(source) as src:
            content = src.read()

        # Archive the original intake
        intake_doc = project.root_dir / "docs" / "01-intake.md"
        with open(intake_doc, "w") as f:
            f.write(f"# Intake Source\n\nSource: {spec_path}\n\n```\n{content}\n```\n")

        # Write working spec
        with open(working_spec, "w") as f:
            f.write(content)

        project.working_spec_path = working_spec

    def _create_working_spec_from_template(self, project: Project, template: str) -> None:
        """Create working spec from a template."""
        working_spec = project.root_dir / "docs" / "02-working-spec.md"
        with open(working_spec, "w") as f:
            f.write(template)
        project.working_spec_path = working_spec

    def _default_template(self, project_name: str) -> str:
        """Return default feature-doc-style template."""
        return """# {name}

## Summary

Define what this project does.

## Problem

What problem does this project solve?

## Goals

- Goal 1
- Goal 2

## Non-Goals

- Non-goal 1

## Proposed Design

## Repository Impact

## Phases

### Phase 1: Foundation
Objective: Set up the foundational work.

Outputs:
- Core structure
- Tests

Checklist:
- [ ] Task 1
- [ ] Task 2

Exit Criteria:
Describe when this phase is complete.

### Phase 2: Core Implementation
Objective: Build the main behavior.

Outputs:
- Main feature
- Documentation

Checklist:
- [ ] Task 1
- [ ] Task 2

Exit Criteria:
Describe when this phase is complete.

## Acceptance Criteria

- The feature works as described
- Tests pass
- Documentation is complete

## Open Questions

- Any unresolved decisions?

## Follow-Up Work

- Future improvements
""".format(name=project_name)

    def _validate_spec_structure(self, spec_path: Path) -> None:
        """Validate that a spec has required sections."""
        with open(spec_path) as f:
            content = f.read()

        required_sections = [
            "## Phases",
            "### Phase ",
            "Objective:",
            "Checklist:",
            "Exit Criteria:",
        ]

        for section in required_sections:
            if section not in content:
                raise ValueError(f"Spec missing required section: {section}")

    def _extract_stages_from_spec(self, spec_path: Path) -> List[Stage]:
        """Extract phases from spec and create stages."""
        with open(spec_path) as f:
            content = f.read()

        stages = []
        lines = content.split("\n")

        phase_index = 0
        current_phase_name = ""
        current_checklist_items = []
        in_phases_section = False
        phases_ended = False

        for i, line in enumerate(lines):
            # Detect start of Phases section
            if line.strip() == "## Phases":
                in_phases_section = True
                continue

            if not in_phases_section or phases_ended:
                continue

            # Detect end of Phases section (next ## )
            if in_phases_section and line.startswith("##") and not line.startswith("###"):
                # End of Phases section
                if current_phase_name:
                    stage = self._create_stage_from_phase(
                        phase_index, current_phase_name, current_checklist_items
                    )
                    stages.append(stage)
                phases_ended = True
                break

            # Detect phase headers: ### Phase N: Name
            if line.startswith("### Phase "):
                # Save the previous phase if any
                if current_phase_name:
                    stage = self._create_stage_from_phase(
                        phase_index, current_phase_name, current_checklist_items
                    )
                    stages.append(stage)
                    phase_index += 1

                current_phase_name = line.replace("### ", "").strip()
                current_checklist_items = []

            # Detect checklists within a phase
            elif current_phase_name and (line.strip().startswith("- [ ]") or line.strip().startswith("- [x]")):
                # Extract checklist text
                checklist_text = line.strip()[6:].strip()
                current_checklist_items.append(checklist_text)

        return stages

    def _create_stage_from_phase(
        self, index: int, phase_name: str, checklist_items: List[str]
    ) -> Stage:
        """Create a stage from phase info, with one step per checklist item."""
        stage_id = str(uuid.uuid4())
        steps = []

        # Create one step per checklist item, or a single placeholder step
        if checklist_items:
            for checklist_item in checklist_items:
                step = Step(
                    id=str(uuid.uuid4()),
                    stage_id=stage_id,
                    title=checklist_item,
                    kind="task",
                    status=StepStatus.PENDING,
                )
                steps.append(step)
        else:
            step = Step(
                id=str(uuid.uuid4()),
                stage_id=stage_id,
                title=f"Execute {phase_name}",
                kind="task",
                status=StepStatus.PENDING,
            )
            steps.append(step)

        return Stage(
            id=stage_id,
            phase_name=phase_name,
            index=index,
            status=ProjectStatus.DRAFT,
            steps=steps,
        )
