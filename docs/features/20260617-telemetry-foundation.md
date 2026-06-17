# Telemetry Foundation

## Summary

Define and implement the first telemetry contract for `ai-stack`. The immediate goal is not a full event pipeline or dashboard. It is to make the current CLI command paths emit a small, stable telemetry envelope that records route, duration, and outcome in a way tests and later persistence can build on.

## Problem

The repository already emits structured command results, but those results are command-specific traces rather than a shared telemetry contract.

Without a small telemetry foundation:

- duration is not measured consistently across commands
- route decisions are visible only indirectly through command-specific payloads
- later persistence work would need to reverse-engineer existing trace shapes
- the initialization backlog item for observing route, duration, and outcome stays only partially satisfied

## Goals

- Define one shared telemetry envelope for current CLI commands.
- Capture route, duration, and outcome for `resolve-skill`, `adapter`, and `sync-skills`.
- Keep the contract small enough to emit inline with command JSON output.
- Respect `telemetry.enabled` without making file persistence mandatory yet.
- Make the telemetry payload easy to assert in tests.

## Non-Goals

- Build a telemetry storage directory or retention policy yet.
- Design the long-term analytics schema for workflows, benchmarks, or dashboards.
- Capture interactive harness session events.
- Add cost accounting, token accounting, or model-provider metrics yet.
- Introduce a top-level `telemetry/` directory before real persisted assets exist.

## Proposed Design

### First Telemetry Envelope

Each current CLI command should include a top-level `telemetry` object with:

- `command`
- `captureEnabled`
- `startedAt`
- `finishedAt`
- `durationMs`
- `outcome`
- `route`

This envelope is intentionally transportable and command-agnostic. It should sit beside the command-specific payload rather than replacing it.

### Route

`route` should contain only the minimum fields needed to understand how the command was directed.

Current command expectations:

- `resolve-skill`
  - `root`
  - `requestedSkill`
  - `selectedHarness`
  - `adapterMode`
- `adapter`
  - `root`
  - `selectedHarness`
  - `adapterMode`
  - `promptLength`
- `sync-skills`
  - `root`
  - `syncMode`

The route contract should stay compact. It is for observability, not payload duplication.

### Outcome

Outcomes should summarize the command result at a stable, low-cardinality level.

Current mapping:

- `resolve-skill`
  - `matched`
  - `not-matched`
  - `blocked`
- `adapter`
  - adapter `status`, such as `completed`, `failed`, `unsupported`, or `blocked`
- `sync-skills`
  - `planned`
  - `applied`

### Relationship To `telemetry.enabled`

The command JSON output is the immediate user-visible trace, so the telemetry envelope should still be emitted inline even when future persisted telemetry is disabled.

For the first slice:

- `captureEnabled` reflects whether runtime telemetry capture is enabled by valid config
- inline telemetry output remains present regardless, because it is part of the command trace contract
- invalid config disables capture eligibility rather than blocking telemetry metadata from appearing in output

### Timing

Use a monotonic timer for elapsed duration and UTC timestamps for start and finish times.

This keeps the first implementation:

- deterministic enough for tests
- readable in CLI output
- compatible with later persistence or export work

### Storage Deferral

Do not create a top-level `telemetry/` directory yet.

Persisted telemetry should wait until the repository has:

- a clearer event schema
- retention decisions
- a reason to store assets instead of only emitting trace output

## Repository Impact

This feature affects:

- `ai_stack/`
- CLI command output shape
- config semantics around `telemetry.enabled`
- tests
- initialization docs
- future dashboard and telemetry storage work

## Phases

### Phase 1: Contract Definition
Objective:
Define the minimum telemetry envelope for the current runtime.

Outputs:

- telemetry feature doc
- route contract
- outcome contract

Checklist:
- [x] Define a shared telemetry envelope.
- [x] Define the first route fields per current command.
- [x] Define the first outcome mapping.
- [x] Define how `telemetry.enabled` interacts with inline trace output.

Exit Criteria:
An implementer can add telemetry to the current commands without inventing per-command semantics.

### Phase 2: Runtime Envelope
Objective:
Add telemetry to the current CLI commands and verify it in tests.

Outputs:

- shared telemetry helper code
- inline telemetry on current commands
- telemetry assertions in tests

Checklist:
- [x] Add shared timer and envelope helpers.
- [x] Emit telemetry for `resolve-skill`.
- [x] Emit telemetry for `adapter`.
- [x] Emit telemetry for `sync-skills`.
- [x] Add tests that verify route, duration, and outcome fields.

Exit Criteria:
Current CLI commands emit a consistent telemetry envelope that tests can inspect.

### Phase 3: Persistence Follow-Up
Objective:
Prepare for later persisted telemetry without overcommitting now.

Outputs:

- backlog for storage and retention
- boundary between inline traces and persisted events

Checklist:
- [ ] Decide when persisted telemetry assets justify a real top-level directory.
- [ ] Define whether persisted events should mirror CLI output exactly or use a normalized event schema.
- [ ] Decide how sync and adapter events should connect to later workflow-level telemetry.
- [ ] Define the minimum privacy/redaction stance before prompts, outputs, or external metadata are stored.

Exit Criteria:
Future telemetry persistence work has clear boundaries and does not need to reinterpret the first runtime envelope.

## Acceptance Criteria

- Current CLI commands expose route, duration, and outcome in a shared telemetry object.
- `telemetry.enabled` affects capture eligibility without requiring storage support yet.
- Tests can assert telemetry fields without depending on unstable command-specific internals.
- The repository does not add a top-level `telemetry/` directory before it holds real persisted assets.

## Open Questions

- Should future persisted telemetry reuse the inline envelope exactly, or split into summary and raw event layers?
- Which later workflow dimensions should be first-class: model route, cost, token usage, or step timings?
- How should interactive harness sessions participate if they do not expose reliable event hooks?

## Follow-Up Work

- Add a telemetry-specific README or storage layout only when persisted assets exist.
- Connect this envelope to later workflow orchestration work.
- Draft the future dashboard/storage contract once there is more than one event source.
