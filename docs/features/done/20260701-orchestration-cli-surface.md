# Orchestration CLI Surface

## Summary

Define the first CLI lifecycle for orchestration.

The orchestrator should be usable as a CLI tool, not only as a chat pattern.

## Problem

Without a CLI contract:

- orchestration remains fuzzy and chat-dependent
- lifecycle state transitions stay implicit
- status and rerun behavior are harder to standardize

## Goals

- Define a first command surface for project lifecycle management.
- Keep editing flexible while making state transitions explicit.
- Support multiple intake sources and one canonical execution spec.
- Expose both human-readable and machine-readable status.

## Non-Goals

- Force all spec editing through CLI flags.
- Finalize every future subcommand now.
- Make chat the only way to refine a spec.

## Proposed Design

### Lifecycle Model

The CLI should make these states visible:

- `draft`
- `approved`
- `planned`
- `running`
- `blocked`
- `completed`
- `needs-revision`

### First Command Set

Recommended first commands:

- `ai-stack orchestrate init`
- `ai-stack orchestrate approve`
- `ai-stack orchestrate plan`
- `ai-stack orchestrate run`
- `ai-stack orchestrate status`

### Command Responsibilities

`init`

- create the dated project folder
- create a draft spec from blank template or source material
- archive the initial intake doc

`approve`

- validate the current draft enough to become an execution baseline
- write or refresh the approved spec

`plan`

- derive the execution plan from the approved spec
- archive the generated plan

`run`

- execute the planned stages
- persist run state and artifacts

`status`

- show current lifecycle state
- show current stage and progress
- expose archived-doc and summary locations

### Source Material Input

`init` should be able to start from:

- a blank template
- an existing Markdown doc
- an environment-specific source handled by local skills or connectors

The CLI contract should not hardcode one external system.

### Editing Model

Spec refinement can happen outside the CLI in normal editing tools or chat.

The CLI owns state transitions and archived outputs, not every keystroke of spec authoring.

### Output Modes

The first CLI should support:

- human-readable default output
- structured JSON output for status-oriented commands

### Idempotency And Reruns

The first contract should define:

- whether `approve` and `plan` refresh existing artifacts or create new versions
- how `run` behaves when a project is already completed or blocked
- how reruns or revisions are requested later

The initial implementation can stay conservative as long as the behavior is explicit.

## Repository Impact

This feature affects:

- `bin/`
- future orchestration code in `ai_stack/`
- tests for CLI behavior
- README/operator guidance once implemented

## Phases

### Phase 1: Lifecycle Surface
Objective:
Define the first user-facing orchestration commands.

Outputs:

- command set
- lifecycle states

Checklist:
- [x] Define the first command group.
- [x] Define visible lifecycle states.
- [x] Separate editing from state transitions.

Exit Criteria:
An implementer can build the CLI without inventing the basic orchestration UX.

### Phase 2: Behavior Contract
Objective:
Define command behavior and outputs.

Outputs:

- command responsibilities
- output-mode expectations
- rerun/idempotency boundary

Checklist:
- [x] Define what each first command owns.
- [x] Define input flexibility for `init`.
- [x] Define JSON versus human-readable output expectations.
- [x] Identify rerun/idempotency questions.

Exit Criteria:
An implementer can wire the first commands into runtime code and tests coherently.

## Acceptance Criteria

- The repo defines a CLI-driven orchestration lifecycle.
- The CLI is compatible with flexible intake and approved-spec execution.
- Editing remains flexible while lifecycle transitions are explicit.
- Status output is specifiable without relying on chat history.

## Open Questions

- Should `plan` be implicit in `run`, or always explicit?
- Which approval checks should `approve` enforce first?
- Should reruns create a new run id automatically, or allow resuming the same run?

## Follow-Up Work

- ~~Implement the first `orchestrate` command group.~~ Done — implemented as `ai orch` (init/approve/plan/status/list).
- ~~Update README once the commands exist.~~ Done.
- Add CLI tests for init/approve/plan/run/status. (Unit tests exist for models and ProjectManager; integration tests for the CLI surface are pending.)
- `run` command is not yet implemented — staged execution is the next phase.
