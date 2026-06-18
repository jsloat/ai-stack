# Orchestration Tool

## Summary

Define the orchestration tool as the part of `ai-stack` that turns a spec or higher-order project definition into a staged execution flow across one or more agent steps.

This feature is not about normal interactive agent sessions, and it is not about setup utilities such as sync or config validation. It is specifically about coordinating multi-step work that should be planned, executed, tracked, and synthesized over time.

## Problem

The repository already has useful runtime utilities:

- config loading and validation
- skill-index resolution
- adapter execution
- native skill sync
- global instruction sync
- inline telemetry

Those are support systems, not orchestration.

The missing piece is a tool that can take a larger unit of work, such as a spec, and drive it through multiple explicit stages with stored outputs and visible progress.

Without a dedicated orchestration-tool contract:

- “bigger than a chat session” work has no clear runtime home
- staged execution may get improvised ad hoc in prompts or separate chats
- it will be unclear how outputs from one step should feed the next
- progress, status, and synthesis behavior will not have a consistent design

## Goals

- Define orchestration as spec-driven, multi-step execution.
- Keep it clearly separate from setup utilities and native harness behavior.
- Define what kinds of artifacts and progress tracking orchestration should own.
- Create a phased backlog for moving from single commands toward real staged project execution.

## Non-Goals

- Replace normal Codex or Copilot interactive sessions.
- Reimplement native harness skill selection.
- Treat sync commands or config validation as orchestration.
- Finalize the long-term UI in this document.
- Define every future workflow shape now.

## Proposed Design

The orchestration tool should be used when the unit of work is larger than a normal session and benefits from explicit staged execution.

### When Orchestration Is Used

Use orchestration for work like:

- starting from a spec doc
- breaking a project into multiple named steps
- choosing model or harness settings per step
- storing outputs from each step
- feeding outputs into later steps
- showing progress or status while the plan runs
- synthesizing final outputs from intermediate artifacts

Do not use orchestration for:

- ordinary interactive coding chats
- simple one-off tasks that fit in one session
- syncing instructions or skills
- validating whether local config is well-formed

### Relationship to Native Sessions

The default experience for most work should remain:

- start a Codex session
- rely on installed skills and instruction files
- work interactively

That should stay the normal path for simple tasks.

Orchestration is the higher-order path for project execution, not the default wrapper around every session.

### Inputs

The main orchestration input should be a project definition such as:

- a spec doc
- a plan doc
- later, possibly a structured task manifest

The orchestration layer should treat that input as the source for:

- step boundaries
- success criteria
- output expectations
- dependencies between steps

### Responsibilities

The orchestration tool should own:

- reading the project definition
- turning it into explicit steps or phases
- choosing runtime settings per step
- invoking the right lower-level execution mechanisms
- persisting intermediate outputs
- determining whether each step succeeded, failed, or needs revision
- exposing progress and final synthesis

It should not own:

- native skill installation or sync
- global instruction installation or sync
- generic config bootstrap
- low-level harness invocation details already handled by adapters

### Relationship to Other Runtime Pieces

Supporting runtime pieces remain separate:

- config validation prepares the environment
- sync commands prepare installed instructions and skills
- adapters talk to specific harnesses
- telemetry records what happened

Orchestration composes those things for project execution, but it is not the same feature as any of them.

### Outputs

Orchestration should eventually produce:

- a step plan
- per-step outputs and status
- stored intermediate artifacts
- a final synthesized result
- progress information suitable for a UI or structured status view

The long-term UI may evolve, but the core contract is that orchestration owns progress and artifact flow for multi-step work.

## Repository Impact

This feature affects:

- `ai_stack/`
- `bin/`
- tests
- telemetry
- future artifact storage decisions
- future UI/progress surfaces
- spec and plan conventions

It intersects with:

- adapter contract
- telemetry foundation
- future dashboard work
- any future workflow/spec conventions

## Phases

### Phase 1: Definition
Objective:
Define orchestration as a distinct runtime concept.

Outputs:

- orchestration-tool feature doc
- clear boundary between orchestration and setup/runtime utilities
- input/output expectations

Checklist:
- [x] Define what counts as orchestration.
- [x] Define what does not count as orchestration.
- [x] Define the relationship to native interactive sessions.
- [x] Define the core inputs and outputs.

Exit Criteria:
Future work can distinguish orchestration from setup tooling and ordinary agent sessions.

### Phase 2: Spec-to-Steps Contract
Objective:
Define how a project definition becomes a staged execution plan.

Outputs:

- step model
- dependency model
- output handoff model

Checklist:
- [ ] Decide what orchestration input formats are supported first.
- [ ] Define the minimum step schema or runtime equivalent.
- [ ] Define how one step’s output becomes input to a later step.
- [ ] Define how failures, retries, or revisions are represented.

Exit Criteria:
An implementer can build the first spec-driven execution path without inventing ad hoc step semantics.

### Phase 3: First Executable Orchestration Flow
Objective:
Build one real multi-step orchestration flow.

Outputs:

- one orchestration command or entrypoint
- per-step artifact storage
- progress reporting
- orchestration-level tests

Checklist:
- [ ] Select the first concrete orchestration use case.
- [ ] Implement step sequencing across more than one stage.
- [ ] Persist intermediate outputs between stages.
- [ ] Surface progress and final synthesis in a stable way.
- [ ] Add tests for orchestration-level success and failure handling.

Exit Criteria:
The repo can execute one spec-driven multi-step flow end to end.

## Acceptance Criteria

- The repo has a feature doc that defines orchestration as spec-driven multi-step execution.
- The design clearly separates orchestration from sync, config validation, and ordinary interactive sessions.
- Future staged workflow work has a clear home in the repo.
- The contract includes step planning, artifact flow, and progress visibility as core concerns.

## Open Questions

- What should the first supported orchestration input be: Markdown spec, feature doc, or a separate structured manifest?
- How much of the step plan should be explicit in files versus computed at runtime?
- What is the first useful progress UI: terminal output, structured JSON status, or a lightweight app view?
- How should human review or approval gates fit into a multi-step run?

## Follow-Up Work

- Define the first spec-to-steps contract.
- Pick the first end-to-end orchestration use case.
- Revisit artifact storage once the first orchestration flow exists.
