# First Executable Slice

## Summary

Define the first runnable end-to-end slice of `ai-stack`. The initial implementation should prove that the repository’s contracts are usable in code by discovering optional local context, resolving an external skill reference from the local skill index, and emitting a deterministic load trace.

## Problem

The repository now has several foundational design contracts:

- configuration contract
- skill packaging contract
- skill index contract
- repo boundary guidance

But there is no executable path yet that proves these contracts are coherent.

Without a narrow first slice:

- docs may drift from implementation reality
- future code may overreach into broader orchestration too early
- testability for skill resolution will remain theoretical
- “if present, use it; if absent, ignore it” behavior will stay underspecified

## Goals

- Implement the smallest useful runtime path that exercises the current contracts.
- Keep the slice deterministic and testable.
- Prove optional local config and optional local skill index handling.
- Prove that a referenced skill can be resolved and traced from a fresh run.
- Avoid pulling in full orchestration, multi-model workflows, or benchmark logic.

## Non-Goals

- Execute a full coding task through a harness.
- Implement multi-step orchestration workflows.
- Implement benchmark execution or telemetry storage.
- Execute pre-flight shell commands from the skill index.
- Design a final CLI surface for every future feature.

## Proposed Design

The first executable slice should be a thin resolution-and-trace path.

### High-Level Flow

1. Start from a fresh invocation.
2. Load hardcoded defaults.
3. Load `config.local.yaml` if present.
4. Look for the conventional local skill index if present.
5. Parse the skill registry table if the index exists.
6. Resolve a requested skill identifier to its source repo and `SKILL.md` path.
7. Emit a structured load trace showing what was discovered and resolved.

### Initial Command Shape

The exact command name can still change, but the behavior should be equivalent to something like:

```bash
ai-stack resolve-skill pull-request
```

Possible future alternatives are acceptable as long as the slice remains deterministic and scriptable.

### Input Model

The slice should operate with these inputs:

- hardcoded defaults from code
- optional `config.local.yaml`
- optional `skill-indexes/local/skill-index.example.md` or future real local index file
- one requested skill identifier from the command line or test harness

### No-Op Behavior

The slice must behave safely when optional artifacts are absent.

If `config.local.yaml` is absent:

- continue with hardcoded defaults

If the local skill index is absent:

- continue without error
- report that no skill index was found

If a requested skill is not found in the index:

- return a deterministic not-found result
- emit a trace that shows the index was consulted and the skill was not resolved

### Load Trace

The key output of this slice is a structured load trace.

At minimum, the trace should record:

- whether `config.local.yaml` was found
- whether the local skill index was found
- whether the index parsed successfully
- which skill identifier was requested
- whether a registry match was found
- the resolved source repo
- the resolved skill path

The trace should be machine-readable. JSON is the simplest likely choice.

Example shape:

```json
{
  "config": {
    "localConfigFound": false
  },
  "skillIndex": {
    "found": true,
    "path": "skill-indexes/local/skill-index.example.md",
    "parsed": true
  },
  "resolution": {
    "requestedSkill": "pull-request",
    "matched": true,
    "sourceRepo": "~/Dev/example-tools",
    "skillPath": ".github/skills/pull-request/SKILL.md"
  }
}
```

This does not need to be the final trace schema, but the slice should establish the principle that skill loading is observable.

### Parser Scope

For the first slice, the runtime only needs to extract the registry table.

It does not need to:

- parse arbitrary prose semantically
- execute pre-flight instructions
- interpret every frontmatter field

Optional pre-flight sections may be preserved as content and ignored by the first runtime implementation.

## Repository Impact

This feature will likely touch:

- future CLI or executable entrypoint code under `bin/`
- config loading code
- skill index parsing code
- skill resolution code
- tests for deterministic fresh-run behavior
- docs that describe the slice and its trace output

It should remain mostly inside the current “core” side of the repo boundary:

- config loading
- parsing
- resolution
- tracing
- tests

## Phases

### Phase 1: Execution Contract

Objective:
Define exactly what the first runnable path does and does not do.

Outputs:

- first executable slice feature doc
- explicit no-op behavior
- initial trace contract

Checklist:

- [x] Define the high-level flow.
- [x] Define the input model.
- [x] Define absent-file behavior.
- [x] Define the minimum load trace fields.

Exit Criteria:
An implementer can build the first slice without broadening scope into full orchestration.

### Phase 2: Implementation

Objective:
Build the thin resolution-and-trace runtime path.

Outputs:

- initial command implementation
- config discovery
- skill index parser
- skill resolution logic
- trace output

Checklist:

- [x] Implement hardcoded-default plus optional `config.local.yaml` loading.
- [x] Implement local skill-index discovery by convention.
- [x] Implement registry-table parsing.
- [x] Implement deterministic skill resolution by identifier.
- [x] Implement machine-readable load trace output.

Exit Criteria:
A fresh invocation can resolve a skill reference and emit a trace of how it got there.

### Phase 3: Verification

Objective:
Prove the slice works from a fresh run and handles no-op paths cleanly.

Outputs:

- deterministic tests
- fixture index file usage
- absent-file coverage

Checklist:

- [x] Add a test where both local config and local index are absent.
- [x] Add a test where the index exists and a skill resolves successfully.
- [x] Add a test where the index exists but the requested skill is missing.
- [x] Add assertions against the load trace rather than human-oriented prose.

Exit Criteria:
The first slice is testable and proves the current contracts are executable.

## Acceptance Criteria

- The repo has one runnable path that exercises configuration discovery, skill-index discovery, resolution, and tracing.
- Missing optional files are handled as clean no-op cases.
- Skill resolution can be proven from a fresh invocation through a structured load trace.
- The implementation does not yet depend on executing full harness workflows.
- The slice stays narrow enough to validate the contracts without overcommitting the runtime architecture.

## Open Questions

- Should future runtime versions continue reading `skill-index.example.md` directly, or introduce a non-example sibling file convention?
- Should the trace support file output in addition to stdout?

## Follow-Up Work

- Use the resulting trace shape to inform broader telemetry and observability design.
- Revisit pre-flight/update behavior after basic resolution and tracing work end to end.
