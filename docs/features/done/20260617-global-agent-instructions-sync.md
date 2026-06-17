# Global Agent Instructions Sync

## Summary

Define and implement a first sync flow for machine-global agent instructions. The repo should maintain one shared global instruction source, allow an optional local overlay, and install the rendered result into the correct per-harness location for Codex and Copilot.

## Problem

The repo currently manages native skills for Codex, but it does not manage machine-global instruction files. That leaves an important policy surface unmanaged, including safeguards that should apply before repository-local context is even loaded.

This is especially risky for rules such as:

- never commit without explicit user confirmation
- never push without explicit user confirmation
- never run destructive Git operations without explicit user confirmation

Without a sync contract:

- global instruction files drift or remain empty
- the repo cannot consistently establish machine-level guardrails
- Codex and Copilot customization stay inconsistent
- future harness support will have no shared pattern to follow

## Goals

- Support Codex and Copilot in the first implementation.
- Use one harness-agnostic source plus one optional local overlay.
- Make sync behavior depend on the target harness.
- Keep local machine customization outside shared git history.
- Back up managed updates conservatively.
- Block overwriting unmanaged target files by default.

## Non-Goals

- Support every harness immediately.
- Depend on `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` in the first implementation.
- Auto-merge arbitrary unmanaged target files.
- Generate repository `AGENTS.md` or Copilot repo instruction files from the global source.
- Ship the `global-instructions.updater` skill in the first implementation.

## Proposed Design

### Source Layout

Use one top-level directory:

- `global-agent-instructions/shared.md`
- `global-agent-instructions/local.md`
- `global-agent-instructions/local.example.md`

Rules:

- `shared.md` is tracked and contains durable, harness-agnostic global policy.
- `local.md` is optional, gitignored, and holds machine-local overlays.
- `local.example.md` is tracked and gives users a copyable starting point.

The first critical shared rule should be:

- never commit, push, or create/update pull requests without explicit user confirmation

### Rendering Model

Render the installed global instructions from:

1. `shared.md`
2. `local.md` if present

The rendered file should stay plain Markdown without hidden management boilerplate inside the instruction body.

Management metadata should live in a sidecar marker file instead.

### Harness Targets

The first supported targets are:

- Codex: `~/.codex/AGENTS.md`
- Copilot CLI: `~/.copilot/copilot-instructions.md`

The sync command should route by harness, but the content source should remain shared.

### Sync Behavior

The command should support:

- dry-run
- apply
- target selection for `codex`, `copilot`, or `all`

If a target file:

- does not exist: install it
- exists and is `ai-stack` managed: update or skip depending on content changes
- exists and is not `ai-stack` managed: block with an unknown-collision result

### Marker and Backup Behavior

Each managed target should have a sidecar marker in the same directory recording:

- `managedBy: ai-stack`
- harness id
- source directory
- source files
- sync timestamp

Managed updates should back up the current target and marker before replacement.

Recommended first backup root:

- `~/.ai-stack/agent-sync-backups/`

### README vs AGENTS Split

For this repo:

- `README.md` should be written for human operators and users of the repo
- repo `AGENTS.md` should describe how agents should maintain and evolve the implementation

So:

- README should explain how to customize `global-agent-instructions/local.md`
- repo `AGENTS.md` should describe implementation guidance for future agent sessions

### Future Skill

A future shared skill should help agents update global instruction policy correctly:

- `skills/shared/global-instructions.updater/`

That skill belongs in the shared skills surface, but it should come after the sync contract exists.

## Repository Impact

This feature affects:

- `global-agent-instructions/`
- `ai_stack/`
- `bin/`
- tests
- `README.md`
- `AGENTS.md`
- repository-structure docs

It also intersects with:

- adapter contract
- instruction placement guidance
- future multi-harness support

## Phases

### Phase 1: Contract
Objective:
Define the shared source layout, target harnesses, and safety rules.

Outputs:

- feature doc
- source layout decision
- harness target decision
- backup and collision rules

Checklist:
- [x] Define the source directory and file names.
- [x] Define Codex and Copilot target files.
- [x] Define unmanaged collision behavior.
- [x] Define backup behavior.

Exit Criteria:
An implementer can build sync behavior without guessing file layout or overwrite policy.

### Phase 2: Runtime Sync
Objective:
Implement the sync command and target-specific installation behavior.

Outputs:

- sync module
- CLI command
- dry-run and apply behavior
- marker writing

Checklist:
- [x] Implement target discovery for Codex and Copilot.
- [x] Implement dry-run planning.
- [x] Implement apply mode with backup behavior.
- [x] Add tests for install, update, and collision behavior.

Exit Criteria:
The repo can plan and apply global instruction sync safely for Codex and Copilot.

### Phase 3: Docs and Follow-Through
Objective:
Explain the new user-facing flow and future follow-up skill direction.

Outputs:

- README updates
- repo structure updates
- follow-up note for shared updater skill

Checklist:
- [x] Document `global-agent-instructions/local.md` in README.
- [x] Clarify README versus repo `AGENTS.md` responsibilities.
- [x] Note the future `global-instructions.updater` shared skill.

Exit Criteria:
Users know how to customize global instructions, and future sessions know where the next governance skill belongs.

## Acceptance Criteria

- The repo defines one shared global-instructions source plus one optional local overlay.
- Codex and Copilot install targets are both supported.
- Sync behavior is dry-runable, idempotent, and conservative about unmanaged targets.
- The shared baseline includes the explicit confirmation guard for commit/push/PR actions.
- README explains the human/operator customization path.

## Open Questions

- Should future harnesses use the same shared render directly, or require harness-specific transforms?
- Should unmanaged collisions eventually support an explicit force-replace mode after backup?
- Should global instruction sync later gain pruning rules for old backups?

## Follow-Up Work

- Add the runtime sync command.
- Test the command against temporary target files before touching real home-directory targets.
- Add the future shared `global-instructions.updater` skill after the sync model stabilizes.
