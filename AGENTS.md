# AGENTS.md

This file is the primary agent operating guide for this repository.

It should focus on implementation and maintenance behavior for agents working on this repo. Human/operator usage guidance belongs in `README.md`.

It should remain compatible with Codex-style agent workflows. Copilot compatibility lives in `.github/copilot-instructions.md`, which should stay thin and refer back here plus the shared docs.

When working in this repository:

- read `README.md` for project intent
- read `docs/features/README.md` for the feature-doc contract
- read the relevant file in `docs/features/` before making architectural or structural changes
- treat feature docs as the design source of truth only while work is still unsettled or implementation is incomplete
- move settled architectural truth into README-style docs once it becomes durable repo structure or operating behavior
- check for incomplete phases, unchecked items, and open questions in relevant feature docs before declaring work complete or starting adjacent design work
- when a feature doc no longer has active checklist items and is no longer the main live backlog for that area, move it to `docs/features/done/`
- update docs when you change architecture, conventions, or intended repo structure
- keep committed content shareable; do not introduce private machine details, absolute local paths, or secrets

## CLI Conventions

The `bin/ai-stack` CLI is exposed to users as `ai` (via a shell alias). All user-facing text must use `ai` as the program name — never `ai-stack`.

The CLI uses a custom help system instead of argparse's default formatter. When adding or modifying commands, follow these rules:

- The top-level `_HELP` string in `resolve_skill.py` is the canonical help surface. Update it whenever commands are added, renamed, or removed.
- The top-level parser uses `add_help=False` with a manual `-h/--help` handler. **Do not use `required=True` on subparsers** — missing command is handled manually to show clean help.
- The top-level parser subclasses `argparse.ArgumentParser` as `_CleanParser`, overriding `error()` to print the clean `_HELP` string instead of argparse's raw `usage:` line. Any new parser that can produce user-facing errors must do the same — never allow argparse's default `usage: ai [-h] {cmd1,cmd2,...}` format to reach the terminal.
- Subcommand groups (like `orch`) that have their own help text must also subclass `ArgumentParser` and override `error()` in the same way.
- Each subcommand group has its own `_*_HELP` string. Update it whenever its subcommands change.
- `prog=` must be set explicitly on every parser and subparser (e.g. `prog="ai orch"`) so error messages show the right invocation.
- Next-step prompt strings in command output must use `ai <cmd>` form, not `ai-stack`.
- `sync-skills` and `sync-global-instructions` default to dry-run when no mode flag is given. Human-readable output is the default; pass `--json` for raw JSON.

If a task is primarily documentation work, prefer changing the relevant feature doc or README instead of burying intent in agent-only instructions.

Instruction placement:

- keep durable project truth in shared docs
- keep this file concise, but treat it as the main agentic source of truth
- keep `.github/copilot-instructions.md` as a compatibility shim, not a second full instruction system
- use `.github/instructions/*.instructions.md` only when narrow Copilot-only path scoping is genuinely needed

When future sessions need to add instructions:

- add durable repo architecture and operating rules to `README.md` or other README-style shared docs
- use `docs/features/*.md` for active design work, backlog, phased implementation plans, and open questions
- add agent workflow guidance here
- update `.github/copilot-instructions.md` only when Copilot still needs the rule or pointer
- avoid adding `.github/instructions/*.instructions.md` unless the narrower scope is clearly justified
