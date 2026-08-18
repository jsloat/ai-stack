"""Tests for orchestration project management."""

import unittest
from pathlib import Path
import tempfile

from ai_stack.orchestration.project import ProjectManager
from ai_stack.orchestration.models import ProjectStatus


class TestProjectManager(unittest.TestCase):
    def test_init_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            self.assertTrue((Path(tmpdir) / "projects").exists())

    def test_init_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            project = mgr.init_project("Test Project")
            
            self.assertEqual(project.name, "Test Project")
            self.assertEqual(project.status, ProjectStatus.DRAFT)
            self.assertIsNotNone(project.working_spec_path)
            self.assertTrue(project.working_spec_path.exists())

    def test_approve_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            project = mgr.init_project("Test Project")
            
            # Approve the project
            mgr.approve_project(project)
            
            self.assertEqual(project.status, ProjectStatus.APPROVED)
            self.assertIsNotNone(project.approved_spec_path)
            self.assertTrue(project.approved_spec_path.exists())

    def test_create_run_from_approved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            project = mgr.init_project("Test Project")
            mgr.approve_project(project)
            
            # Create a run
            run = mgr.create_run_from_approved(project)
            
            self.assertEqual(run.project_id, project.id)
            self.assertGreater(len(run.stages), 0)
            self.assertEqual(project.status, ProjectStatus.PLANNED)

    def test_get_project_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            project = mgr.init_project("Test Project")
            status = mgr.get_project_status(project)
            
            self.assertEqual(status["name"], "Test Project")
            self.assertEqual(status["status"], "draft")
            self.assertEqual(status["runs"], 0)

    def test_find_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            project1 = mgr.init_project("Test Project 1")
            project2 = mgr.init_project("Test Project 2")
            
            projects = mgr.find_projects()
            self.assertGreaterEqual(len(projects), 2)
            
            # Filter by pattern
            filtered = mgr.find_projects(name_pattern="Project 1")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0].name, "Test Project 1")

    def test_extract_stages_from_spec(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ProjectManager(Path(tmpdir))
            
            # Create a spec with known phases
            spec_content = """# Test
## Phases
### Phase 1: First
Checklist:
- [ ] Task 1
- [ ] Task 2

### Phase 2: Second
Checklist:
- [ ] Task 3

## Acceptance Criteria
"""
            spec_path = Path(tmpdir) / "spec.md"
            spec_path.write_text(spec_content)
            
            stages = mgr._extract_stages_from_spec(spec_path)
            self.assertEqual(len(stages), 2)
            self.assertEqual(stages[0].phase_name, "Phase 1: First")
            self.assertEqual(len(stages[0].steps), 2)
            self.assertEqual(stages[1].phase_name, "Phase 2: Second")
            self.assertEqual(len(stages[1].steps), 1)


if __name__ == "__main__":
    unittest.main()

