"""Tests for orchestration models."""

import unittest
from pathlib import Path
import tempfile
import json
from datetime import datetime

from ai_stack.orchestration.models import (
    Step, Stage, Run, Project,
    StepStatus, ProjectStatus
)


class TestStep(unittest.TestCase):
    def test_step_creation(self):
        step = Step(
            id="step1",
            stage_id="stage1",
            title="Test step",
            kind="task",
        )
        self.assertEqual(step.id, "step1")
        self.assertEqual(step.status, StepStatus.PENDING)
        self.assertEqual(step.attempt_count, 0)

    def test_step_serialization(self):
        step = Step(
            id="step1",
            stage_id="stage1",
            title="Test step",
            kind="task",
            status=StepStatus.RUNNING,
        )
        data = step.to_dict()
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["id"], "step1")
        
    def test_step_deserialization(self):
        data = {
            "id": "step1",
            "stage_id": "stage1",
            "title": "Test step",
            "kind": "task",
            "status": "completed",
            "inputs": {},
            "artifacts": {},
            "attempt_count": 1,
            "depends_on": None,
            "updated_at": "2026-08-18T20:00:00.000000",
        }
        step = Step.from_dict(data)
        self.assertEqual(step.status, StepStatus.COMPLETED)
        self.assertEqual(step.attempt_count, 1)


class TestStage(unittest.TestCase):
    def test_stage_creation(self):
        stage = Stage(
            id="stage1",
            phase_name="Phase 1",
            index=0,
        )
        self.assertEqual(stage.id, "stage1")
        self.assertEqual(stage.phase_name, "Phase 1")
        self.assertEqual(stage.status, ProjectStatus.DRAFT)

    def test_stage_with_steps(self):
        step = Step(
            id="step1",
            stage_id="stage1",
            title="Task 1",
            kind="task",
        )
        stage = Stage(
            id="stage1",
            phase_name="Phase 1",
            index=0,
            steps=[step],
        )
        self.assertEqual(len(stage.steps), 1)
        self.assertEqual(stage.steps[0].title, "Task 1")


class TestRun(unittest.TestCase):
    def test_run_creation(self):
        run = Run(
            id="run1",
            project_id="proj1",
            spec_path=Path("/tmp/spec.md"),
        )
        self.assertEqual(run.id, "run1")
        self.assertEqual(run.overall_status, ProjectStatus.PLANNED)

    def test_run_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "runs" / "run1"
            run = Run(
                id="run1",
                project_id="proj1",
                spec_path=Path("/tmp/spec.md"),
            )
            run.save(run_dir)
            
            # Verify file was created
            run_file = run_dir / "run.json"
            self.assertTrue(run_file.exists())
            
            # Verify we can load it back
            loaded = Run.load(run_dir)
            self.assertEqual(loaded.id, "run1")
            self.assertEqual(loaded.project_id, "proj1")


class TestProject(unittest.TestCase):
    def test_project_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Project(
                id="proj1",
                name="Test Project",
                root_dir=Path(tmpdir),
            )
            self.assertEqual(project.id, "proj1")
            self.assertEqual(project.status, ProjectStatus.DRAFT)

    def test_project_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = Project(
                id="proj1",
                name="Test Project",
                root_dir=root,
            )
            project.save()
            
            # Verify file was created
            project_file = root / "project.json"
            self.assertTrue(project_file.exists())
            
            # Verify we can load it back
            loaded = Project.load(root)
            self.assertEqual(loaded.id, "proj1")
            self.assertEqual(loaded.name, "Test Project")


if __name__ == "__main__":
    unittest.main()

