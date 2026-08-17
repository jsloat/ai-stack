# Orchestration Tool

## Summary

Define orchestration as the project-execution layer of `ai-stack`.

Orchestration is for work that deserves a durable spec, explicit stages, archived artifacts, and resumable status. It is not the default wrapper around normal interactive coding chats.

Detailed follow-on specs live in:

- `docs/features/20260618-orchestration-project-definition.md`
- `docs/features/20260618-orchestration-step-runtime.md`
- `docs/features/20260618-orchestration-artifacts-and-progress.md`
- `docs/features/20260701-orchestration-cli-surface.md`

Use this file as the umbrella contract.

Use the follow-on specs for the concrete boundaries:

- `20260618-orchestration-project-definition.md`: intake normalization, canonical spec shape, approval boundary
- `20260618-orchestration-step-runtime.md`: run/stage/step model, statuses, retries, review units
- `20260618-orchestration-artifacts-and-progress.md`: archive layout, persisted run state, progress surface
- `20260701-orchestration-cli-surface.md`: lifecycle commands and user-facing orchestration states

## Problem

The repo already has useful runtime pieces:

- config loading and validation
- skill resolution
- adapter execution
- sync commands
- inline telemetry

Those are support systems, not project execution.

Without an orchestration contract:

- larger work has no clear runtime home
- execution can drift across ad hoc chats
- progress and artifacts are hard to inspect later
- medium and large projects leave weak historical records

## Goals

- Define when orchestration is useful versus a normal chat.
- Define orchestration as spec-driven, staged execution.
- Make archived project history a first-class outcome.
- Keep the runtime harness-agnostic.
- Create a clear path to a CLI-driven workflow.

## Non-Goals

- Replace normal interactive sessions.
- Reimplement native skill selection.
- Turn setup utilities into orchestration.
- Define every future workflow now.
- Require every orchestrated project to use multiple PRs.

## Proposed Design

### When To Use Orchestration

Use orchestration when at least one of these is true:

- the project should outlive one chat session
- the project needs an approved spec before execution
- the project needs archived artifacts for future review
- the work has multiple stages or checkpoints
- the work should be resumable, inspectable, or auditable later

Use a normal chat when:

- the task fits in one session
- the plan can stay implicit
- the conversation itself is an acceptable workspace
- no durable project archive is needed

Short version:

- chat is for doing work
- orchestration is for running a project

### Core Lifecycle

The intended lifecycle is:

1. intake source
2. normalized draft spec
3. approved execution spec
4. generated plan
5. staged execution
6. archived summaries and outputs

Execution should run from the approved spec, not directly from mutable intake material.

### Responsibilities

Orchestration should own:

- intake normalization into a canonical spec
- spec approval boundary
- stage and step planning
- staged execution
- persisted run state
- archived Markdown project docs
- progress and final synthesis

It should not own:

- harness installation or sync
- generic config bootstrap
- adapter internals already handled elsewhere

### Reviewable Chunking

Orchestrated work should be decomposed into reviewable units.

Often that will mean multiple PR-sized chunks, but the contract should stay broader than PRs. A review unit may also be:

- a spec approval checkpoint
- a verification report
- a migration checkpoint
- a staged implementation slice

The principle is incremental review, not mandatory multi-PR delivery.

## Repository Impact

This feature affects:

- `ai_stack/`
- `bin/`
- tests
- telemetry follow-up
- future storage layout
- future CLI UX

## Phases

### Phase 1: Boundary
Objective:
Define orchestration as a distinct runtime concept and decide when it is worth using.

Outputs:

- umbrella orchestration contract
- usage boundary versus chat

Checklist:
- [x] Define what orchestration is.
- [x] Define when normal chat is still the better tool.
- [x] Define orchestration as a project-level rather than session-level runtime.

Exit Criteria:
Future work can clearly distinguish orchestration from ordinary interactive use.

### Phase 2: Detailed Contracts
Objective:
Define the input, runtime, storage, and CLI contracts.

Outputs:

- project-definition spec
- step runtime spec
- artifacts/progress spec
- CLI surface spec

Checklist:
- [x] Define the first canonical spec input.
- [x] Define the minimum run/stage/step model.
- [x] Define artifact archival and progress reporting.
- [x] Define the first CLI lifecycle surface.

Exit Criteria:
An implementer can build the first orchestration path without inventing major runtime semantics.

### Phase 3: First Executable Flow
Objective:
Build one real orchestration workflow end to end.

Outputs:

- one CLI entrypoint
- persisted run state
- archived project docs
- orchestration-level tests

Checklist:
- [ ] Choose the first concrete orchestration use case.
- [ ] Implement spec approval and planning flow.
- [ ] Implement staged execution and status reporting.
- [ ] Add success, failure, and resume-oriented tests.

Exit Criteria:
The repo can run one project workflow end to end outside a single chat session.

## Acceptance Criteria

- The repo clearly defines when orchestration is useful.
- Orchestration is specified as spec-driven project execution.
- Archived project history is a core output, not an afterthought.
- The design stays harness-agnostic and CLI-oriented.

## Open Questions

- What should the first end-to-end workflow be?
- Which approval checks should be required before execution starts?
- When should review units map to separate PRs versus non-PR checkpoints?

## Follow-Up Work

- Implement the CLI lifecycle from the supporting specs.
- Choose the first concrete workflow to exercise the full path.
