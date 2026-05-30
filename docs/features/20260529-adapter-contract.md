# Adapter Contract

## Summary

Define the first contract for adapters in `ai-stack`. An adapter is the boundary layer between shared orchestration concepts and a specific harness such as Codex or Copilot. The initial contract should be narrow enough to support the current resolution-and-trace slice while leaving room for future task execution.

## Problem

The repository has an `adapters/` directory and a clear intent to support multiple harnesses, but there is no contract yet for what an adapter actually must do.

Without an adapter contract:

- harness-specific logic will leak into core resolution code
- adding a second harness will require refactoring instead of extension
- it will be unclear which runtime concepts are core versus harness-specific
- future tests will have no stable boundary to assert against

## Goals

- Define the minimum responsibilities of an adapter.
- Separate adapter concerns from core resolution and tracing concerns.
- Support at least one narrow first execution path beyond pure skill resolution.
- Keep the contract compatible with both Codex and Copilot style harnesses.
- Make adapter behavior observable in tests and traces.

## Non-Goals

- Implement every harness integration now.
- Standardize every future adapter hook or lifecycle event.
- Solve all prompt/instruction translation details in one pass.
- Define full orchestration workflows.
- Commit to one final adapter API forever.

## Proposed Design

An adapter should translate shared `ai-stack` runtime inputs into harness-specific execution behavior and report back structured results.

### Core Runtime Owns

The core runtime should continue to own:

- config loading
- skill-index discovery and parsing
- skill resolution
- trace assembly
- high-level routing decisions

### Adapter Owns

An adapter should own:

- harness identity
- how shared instructions or context are handed to the harness
- how a request is invoked
- how adapter-level results are normalized back into shared runtime structures

### Minimum Adapter Responsibilities

For the first contract, an adapter should expose enough behavior to support:

1. adapter identification
2. a dry-run or traceable handoff
3. normalized result reporting

At minimum, an adapter should be able to answer:

- what harness is this
- what input would be handed to the harness
- whether the handoff was attempted
- what normalized result came back

### Initial Shared Input Shape

The first shared adapter input should stay narrow and include only:

- selected harness id
- requested skill identifier
- resolved skill location, if any
- effective config snapshot or relevant subset

The first adapter contract does not need:

- full conversation history
- multi-step workflow plans
- benchmark metadata
- persistent telemetry sinks

### Initial Result Shape

Adapters should return a normalized structure that future traces and tests can inspect.

Example fields:

- `adapter`
- `attempted`
- `mode`
- `status`
- `details`

For early work, a dry-run mode is enough if it proves the handoff contract.

### First Adapter Mode

The first adapter implementation should probably support a dry-run or inspection mode before real harness execution.

That would allow the runtime to prove:

- the selected adapter was found
- the resolved skill was handed off in normalized form
- the trace captured the adapter interaction

without immediately coupling the runtime to a live Codex or Copilot invocation path.

### Likely First Adapters

Short-term likely targets:

- `codex`
- `copilot`

But the contract should stay generic enough that adding another harness does not require changing core runtime semantics.

## Repository Impact

This feature affects:

- `adapters/README.md`
- future adapter code under `adapters/`
- runtime command shape
- execution traces
- tests for adapter selection and handoff

It also influences:

- configuration contract through `defaultHarness`
- first executable slice follow-up work
- core vs convention boundary discipline

## Phases

### Phase 1: Contract Definition

Objective:
Define the boundary between core runtime and harness-specific adapter logic.

Outputs:

- adapter contract feature doc
- minimum adapter responsibilities
- initial shared input and result shape

Checklist:

- [x] Define what core runtime owns versus what an adapter owns.
- [x] Define minimum adapter responsibilities.
- [x] Define a narrow initial shared input shape.
- [x] Define a normalized initial result shape.

Exit Criteria:
An implementer can build a first adapter without guessing where harness-specific behavior belongs.

### Phase 2: Dry-Run Adapter Implementation

Objective:
Implement the first adapter path in a way that is testable before live harness integration.

Outputs:

- one adapter module
- dry-run handoff behavior
- adapter trace integration

Checklist:

- [x] Choose the first adapter target.
- [x] Implement adapter lookup by harness id.
- [x] Implement dry-run handoff behavior.
- [x] Include adapter details in the runtime trace.

Exit Criteria:
The runtime can exercise adapter selection and handoff without needing full live execution.

### Phase 3: Live Execution Follow-Up

Objective:
Extend the dry-run adapter into a real harness invocation path when the repo is ready.

Outputs:

- live execution behavior
- normalized adapter result handling
- stronger adapter tests

Checklist:

- [ ] Define the first real harness invocation contract.
- [ ] Normalize success, failure, and unsupported cases.
- [ ] Add tests for adapter-specific edge cases.

Exit Criteria:
One harness can be exercised through the adapter boundary in a real execution mode.

## Acceptance Criteria

- The repo defines a clear adapter boundary.
- Core runtime and harness-specific logic are separated conceptually.
- The first adapter implementation can be tested through a dry-run or traceable handoff.
- Adding a second harness will not require redesigning the core runtime concepts introduced here.

## Open Questions

- Should the first live execution target be Codex or Copilot?
- How much instruction translation should happen in the adapter versus in shared runtime preparation?

## Follow-Up Work

- Update `adapters/README.md` to reflect this contract.
- Choose the first adapter target.
- Extend the current runtime trace to include adapter information.
