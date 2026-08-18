"""CLI interface for orchestration commands."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .project import ProjectManager

_ORCHESTRATE_HELP = """\
Usage: ai orch <subcommand> [options]

Subcommands:
  init <name>              Initialize a new project (creates working spec)
  approve <project>        Validate and approve a draft project for execution
  plan <project>           Generate execution plan from approved spec
  status [project]         Show lifecycle status (all projects if omitted)
  list                     List all projects

Options (all subcommands):
  --output-json            Output result as JSON instead of human-readable text

Examples:
  ai orch init "My Feature"
  ai orch init "My Feature" --source docs/features/my-feature.md
  ai orch approve "My Feature"
  ai orch plan "My Feature"
  ai orch status
  ai orch list --filter staging
"""


def add_orchestration_commands(subparsers: argparse._SubParsersAction) -> None:
    """Add orchestration command group to the subparsers."""
    import argparse as _ap
    import sys as _sys

    class _CleanOrchParser(_ap.ArgumentParser):
        def error(self, message: str) -> None:
            print(f"Error: {message}\n", file=_sys.stderr)
            print(_ORCHESTRATE_HELP.rstrip(), file=_sys.stderr)
            _sys.exit(2)

    orchestrate_parser = _CleanOrchParser(
        prog="ai orch",
        formatter_class=_ap.RawDescriptionHelpFormatter,
        description=_ORCHESTRATE_HELP,
        add_help=False,
    )
    subparsers._name_parser_map["orch"] = orchestrate_parser
    subparsers._choices_actions.append(
        type("_Action", (), {"dest": "orch", "help": "Manage orchestrated projects", "option_strings": []})()
    )
    orchestrate_parser.add_argument("-h", "--help", action="store_true", default=False)
    orchestrate_subparsers = orchestrate_parser.add_subparsers(dest="orchestrate_cmd")

    # init
    init_parser = orchestrate_subparsers.add_parser(
        "init",
        help="Initialize a new orchestrated project",
    )
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument(
        "--source",
        help="Path to existing spec or source material",
    )
    init_parser.add_argument(
        "--template",
        help="Use provided template content instead of default",
    )
    init_parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON",
    )
    init_parser.set_defaults(func=cmd_init)

    # approve
    approve_parser = orchestrate_subparsers.add_parser(
        "approve",
        help="Approve a draft project for execution",
    )
    approve_parser.add_argument(
        "project_id",
        help="Project ID or partial name to match",
    )
    approve_parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON",
    )
    approve_parser.set_defaults(func=cmd_approve)

    # plan
    plan_parser = orchestrate_subparsers.add_parser(
        "plan",
        help="Generate execution plan from approved spec",
    )
    plan_parser.add_argument(
        "project_id",
        help="Project ID or partial name to match",
    )
    plan_parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON",
    )
    plan_parser.set_defaults(func=cmd_plan)

    # status
    status_parser = orchestrate_subparsers.add_parser(
        "status",
        help="Show project status",
    )
    status_parser.add_argument(
        "project_id",
        nargs="?",
        help="Project ID or partial name to match (optional, lists all if omitted)",
    )
    status_parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON",
    )
    status_parser.set_defaults(func=cmd_status)

    # list
    list_parser = orchestrate_subparsers.add_parser(
        "list",
        help="List all projects",
    )
    list_parser.add_argument(
        "--filter",
        help="Filter by name pattern",
    )
    list_parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON",
    )
    list_parser.set_defaults(func=cmd_list)


def get_project_manager(config: Optional[dict] = None) -> ProjectManager:
    """Get a ProjectManager instance from config."""
    if config is None:
        config = {}

    orchestration_root = config.get("orchestration", {}).get("root")
    if not orchestration_root:
        raise ValueError(
            "orchestration.root not configured in config.local.yaml. "
            "See README.md for setup instructions."
        )

    return ProjectManager(Path(orchestration_root).expanduser())


def cmd_init(args, config: Optional[dict] = None) -> int:
    """Initialize a new project."""
    try:
        mgr = get_project_manager(config)
        project = mgr.init_project(args.name, spec_source=args.source, spec_template=args.template)

        if args.output_json:
            print(json.dumps(project.to_dict(), indent=2))
        else:
            print(f"✓ Project initialized: {project.name}")
            print(f"  ID: {project.id}")
            print(f"  Root: {project.root_dir}")
            print(f"  Status: {project.status.value}")
            print(f"  Working spec: {project.working_spec_path}")
            print("\nNext: Review the working spec, then run:")
            print(f"  ai orch approve {project.id}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_approve(args, config: Optional[dict] = None) -> int:
    """Approve a project for execution."""
    try:
        mgr = get_project_manager(config)
        project = _find_project(mgr, args.project_id)

        mgr.approve_project(project)

        if args.output_json:
            print(json.dumps(mgr.get_project_status(project), indent=2))
        else:
            print(f"✓ Project approved: {project.name}")
            print(f"  Status: {project.status.value}")
            print(f"  Approved spec: {project.approved_spec_path}")
            print("\nNext: Create and run the execution plan:")
            print(f"  ai orch plan {project.id}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_plan(args, config: Optional[dict] = None) -> int:
    """Generate execution plan from approved spec."""
    try:
        mgr = get_project_manager(config)
        project = _find_project(mgr, args.project_id)

        run = mgr.create_run_from_approved(project)

        if args.output_json:
            print(json.dumps(run.to_dict(), indent=2))
        else:
            print(f"✓ Execution plan created: {project.name}")
            print(f"  Run ID: {run.id}")
            print(f"  Status: {run.overall_status.value}")
            print(f"  Stages: {len(run.stages)}")
            for i, stage in enumerate(run.stages, 1):
                print(f"    {i}. {stage.phase_name} ({len(stage.steps)} steps)")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_status(args, config: Optional[dict] = None) -> int:
    """Show project status."""
    try:
        mgr = get_project_manager(config)

        if args.project_id:
            project = _find_project(mgr, args.project_id)
            status = mgr.get_project_status(project)

            if args.output_json:
                print(json.dumps(status, indent=2))
            else:
                _print_project_status(status)
        else:
            # No project specified - list all
            projects = mgr.find_projects()
            if not projects:
                print("No projects found.")
                return 0

            if args.output_json:
                statuses = [mgr.get_project_status(p) for p in projects]
                print(json.dumps(statuses, indent=2))
            else:
                print(f"Found {len(projects)} project(s):\n")
                for project in projects:
                    status = mgr.get_project_status(project)
                    _print_project_status(status, compact=True)
                    print()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args, config: Optional[dict] = None) -> int:
    """List all projects."""
    try:
        mgr = get_project_manager(config)
        projects = mgr.find_projects(name_pattern=args.filter)

        if not projects:
            print("No projects found.")
            return 0

        if args.output_json:
            statuses = [mgr.get_project_status(p) for p in projects]
            print(json.dumps(statuses, indent=2))
        else:
            print(f"Projects ({len(projects)}):\n")
            for project in projects:
                status = mgr.get_project_status(project)
                _print_project_status(status, compact=True)
                print()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _find_project(mgr: ProjectManager, identifier: str):
    """Find a project by ID or name pattern."""
    # Try exact ID match first
    project = mgr.load_project(identifier)
    if project:
        return project

    # Try name pattern match
    matches = mgr.find_projects(name_pattern=identifier)
    if not matches:
        raise ValueError(f"No project found matching: {identifier}")
    if len(matches) > 1:
        raise ValueError(f"Multiple projects match '{identifier}'. Be more specific.")

    return matches[0]


def _print_project_status(status: dict, compact: bool = False) -> None:
    """Pretty-print project status."""
    if compact:
        print(f"{status['name']:<30} {status['status']:<15} {status['root_dir']}")
    else:
        print(f"Project: {status['name']}")
        print(f"  ID: {status['project_id']}")
        print(f"  Status: {status['status']}")
        print(f"  Created: {status['created_at']}")
        print(f"  Updated: {status['updated_at']}")
        print(f"  Root: {status['root_dir']}")
        if status['working_spec']:
            print(f"  Working spec: {status['working_spec']}")
        if status['approved_spec']:
            print(f"  Approved spec: {status['approved_spec']}")
        if status['latest_run']:
            run = status['latest_run']
            print(f"  Latest run: {run['id'][:8]}...")
            print(f"    Status: {run['status']}")
            print(f"    Progress: {run['stages_completed']}/{run['stages_total']} stages")
