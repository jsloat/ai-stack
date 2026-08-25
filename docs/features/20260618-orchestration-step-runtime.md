# Orchestration Step Runtime Contract

## Summary

Define the minimum runtime model for orchestration runs.

The first model should stay simple: one run contains ordered stages, and each stage contains explicit steps with stable state transitions.

## Problem

Without a runtime contract:

- stage and step semantics will drift
- status handling will be inconsistent
- retries and revisions will blur together
- execution helpers such as skills will be hard to place cleanly

## Goals

- Define run, stage, and step.
- Define a small, stable status model.
- Define output handoff between stages.
- Define where skills fit.
- Keep the first execution path linear and reviewable.

## Non-Goals

- Build a general workflow engine.
- Support arbitrary DAG planning immediately.
- Force every project into multiple PRs.
- Reimplement skill routing inside orchestration.

## Proposed Design

### Core Entities

- `run`: one orchestration attempt for one approved spec
- `stage`: an ordered execution unit, typically derived from one spec phase
- `step`: a concrete action record within a stage

The first slice may use one main step per stage, but the model should still distinguish stage from step.

### Ordering Model

The first ordering model should be linear:

- stages run in document order
- each stage depends on earlier stages
- steps within a stage run in listed order

This is enough for the first flow and keeps review boundaries clear.

### Minimum Step Fields

Each step record should support:

- `id`
- `stageId`
- `title`
- `kind`
- `status`
- `inputs`
- `artifacts`
- `attemptCount`
- `dependsOn`
- `updatedAt`

### Status Model

The first stable step statuses should be:

- `pending`
- `ready`
- `running`
- `blocked`
- `failed`
- `needs-revision`
- `completed`

These should be enough to model approval pauses, validation failures, retries, and success.

### Retry Versus Revision

- retry: re-attempt after execution failure or transient blockage
- revision: produce a new attempt because the previous output was reviewable but insufficient

Both should increment `attemptCount`, but the reason should remain distinguishable.

### Output Handoff

Later stages should consume explicit artifacts, not hidden chat memory.

The handoff inputs are:

- the approved spec
- selected earlier artifacts
- run summary state

### Reviewable Units

Orchestrated work should be split into reviewable units.

Often that will map to separate PRs, but not always. A review unit can also be:

- a spec approval
- a verification checkpoint
- a migration checkpoint
- a non-code deliverable

The runtime should support staged validation even when the project lands as one PR.

### Step Kinds and RTK Mediation

The first concrete step kinds should include at minimum:

- `agent`: invokes a harness (e.g. Codex) to execute the step
- `shell`: runs a local shell command
- `review`: pauses for human approval before continuing
- `checkpoint`: marks a stage boundary without doing execution work

For `agent` steps, any harness that supports RTK (currently Codex) **must** be launched through `rtk` rather than directly. This is the primary cost-reduction mechanism — RTK filters noisy tool output before it reaches the model, reducing token consumption.

- `orch run` should check for `rtk` on `PATH` before executing an agent step against an RTK-required harness
- missing RTK should surface as a setup warning, not a silent bypass
- the run record should log whether RTK was active, bypassed, or unavailable for each agent step
- RTK-exempt harnesses (e.g. Copilot in the current runtime) should document why they are exempt

### Skills Boundary

Skills are execution helpers, not the plan itself.

They may help during:

- intake normalization
- implementation
- verification
- synthesis

Orchestration decides stages, steps, inputs, and expected outputs. Skills may help a step succeed, but they should not replace the runtime model.

## Repository Impact

This feature affects:

- future orchestration runtime code in `ai_stack/`
- tests for run-state transitions
- workflow-level telemetry follow-up

## Phases

### Phase 1: Runtime Model
Objective:
Define the minimum runtime nouns and statuses.

Outputs:

- run/stage/step model
- status model

Checklist:
- [x] Define run, stage, and step.
- [x] Define linear staged ordering.
- [x] Define the minimum step fields.
- [x] Define stable step statuses.

Exit Criteria:
An implementer can model one orchestration run without inventing ad hoc workflow state.

### Phase 2: Handoff And Review
Objective:
Define how staged work moves forward and is checked.

Outputs:

- handoff model
- retry/revision semantics
- review-unit boundary
- skills boundary

Checklist:
- [x] Define explicit artifact handoff.
- [x] Distinguish retry from revision.
- [x] Define reviewable units broadly, not just PRs.
- [x] Define where skills participate.

Exit Criteria:
An implementer can build staged execution that remains inspectable and reviewable.

## Acceptance Criteria

- The repo defines a stable first orchestration runtime model.
- Status semantics are explicit enough to test.
- Output handoff uses artifacts rather than hidden conversational state.
- Skills are clearly treated as helpers inside steps.

## Open Questions

- When should parallel steps be allowed, if ever?
- Should `blocked` later split into dependency-blocked and approval-blocked?
- Should some workflows declare expected skills per step?

## Follow-Up Work

- Implement run-state structures and transitions in `ai_stack/`.
- Choose the first concrete step kinds for the initial workflow.
- Implement `orch run` with RTK mediation for `agent` steps.
- Add RTK availability check before launching agent steps against RTK-required harnesses.
