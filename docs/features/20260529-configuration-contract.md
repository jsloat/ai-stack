# Configuration Contract

## Summary

Define the first explicit configuration contract for `ai-stack`. The goal is to keep configuration narrow, behavioral, and local-override-friendly without making the repository structure itself configurable before there is a real need.

## Problem

The repo now has a `config.example.yaml`, but there is not yet a documented contract for what belongs in configuration versus what should stay hardcoded in repository structure or shared docs.

Without a configuration contract, the repo will drift in predictable ways:

- repo-owned paths will get made configurable too early
- local-only concerns will leak into shared files
- future code will invent precedence rules ad hoc
- skill references and model roles will be represented inconsistently

This is especially risky for a shared AI tooling repo because configuration tends to become the dumping ground for every unresolved design choice.

## Goals

- Define the minimal config surface needed for the first executable slices.
- Keep repo-owned structure hardcoded unless there is a demonstrated relocation need.
- Establish the relationship between `config.example.yaml` and `config.local.yaml`.
- Define configuration precedence clearly enough that future code does not invent it.
- Keep local skill-index discovery convention-based rather than configurable unless a real need emerges.
- Standardize the example local skill-index filename without overcommitting to a heavy format contract.
- Define the smallest shared configuration needed once RTK is considered mandatory infrastructure.

## Non-Goals

- Define the full long-term orchestrator schema.
- Support every future harness or provider-specific option.
- Make repository directories relocatable.
- Finalize benchmark, telemetry, or adapter schemas.
- Define the full skill package format.

## Proposed Design

Configuration should remain intentionally small in the current phase.

The initial config contract should support:

- default harness selection
- model role selection
- telemetry enablement

It should not support:

- configurable repo-owned paths such as `docs/features`, `skills/shared`, or `telemetry/`
- arbitrary plugin-style extension points
- per-directory rule overrides that belong in docs or instruction files instead

### Files

- `config.example.yaml` is the committed template
- `config.local.yaml` is the user-filled local file and should remain untracked
- `skill-indexes/local/skill-index.example.md` is the committed example artifact for local skill indexing

The expected user flow is:

1. copy `config.example.yaml` to `config.local.yaml`
2. fill in local values
3. let runtime load the local file if it exists

### Precedence

The initial precedence contract should be:

1. hardcoded repository defaults in code
2. values from `config.example.yaml` if the runtime chooses to read it directly
3. values from `config.local.yaml` when present

For early implementation, a simpler model is acceptable:

- treat `config.example.yaml` as documentation only
- load only `config.local.yaml` at runtime
- hardcode the fallback defaults in code

That approach is less magical and avoids pretending the example file is authoritative runtime state.

### Local Skill Index Convention

The repo should standardize on one example filename for the local skill index:

- `skill-indexes/local/skill-index.example.md`

This standardizes the example artifact and location without requiring config indirection.

Future implementation may still decide:

- whether runtime looks for a non-example sibling file
- whether the example file doubles as the real file format template
- how the file is parsed or consumed

### Current Schema Direction

The schema should stay small:

```yaml
defaultHarness: copilot

models:
  planner: sonnet
  implementer: gpt-5.5
  cheapVerifier: gpt-5.5-mini

telemetry:
  enabled: true
```

### Config Field Rules

`defaultHarness`

- identifies the preferred harness for generic task execution
- should use a stable symbolic name such as `copilot`, `codex`, or another future adapter id

`models`

- maps stable execution roles to model ids
- roles should remain semantic, not task-specific
- early roles such as `planner`, `implementer`, and `cheapVerifier` are acceptable

`telemetry.enabled`

- only toggles whether runtime telemetry is captured
- does not define telemetry schema by itself

### RTK

RTK should be treated as part of the default execution environment for supported harnesses.

That does not automatically mean the initial config surface should be large. The current bias should still be:

- keep RTK behavior as implicit default infrastructure where possible
- expose only the minimum shared config needed to detect or control required RTK usage
- avoid turning RTK support into a general path-config dumping ground

## Repository Impact

This feature affects:

- `config.example.yaml`
- future config loading code
- adapter startup behavior
- documentation for local-only versus shared configuration

It also constrains what should remain hardcoded for now:

- feature docs path
- shared skills path
- local skills path
- telemetry directory
- benchmark directory

## Phases

### Phase 1: Contract Definition

Objective:
Define what configuration is allowed to do in the current phase.

Outputs:

- configuration feature doc
- documented field boundaries
- documented precedence model

Checklist:

- [x] Define the purpose of `config.example.yaml` and `config.local.yaml`.
- [x] Define which concerns are configurable versus hardcoded.
- [x] Define initial field semantics for harness, model roles, and telemetry enablement.
- [x] Define that local skill-index discovery is convention-based rather than configured.
- [x] Standardize the example local skill-index filename.
- [x] Define a conservative precedence model for future implementation.

Exit Criteria:
An implementer can write config-loading code without inventing the config surface.

### Phase 2: Runtime Loading Contract

Objective:
Turn the documented contract into a concrete loading model in code.

Outputs:

- config loader behavior
- validation rules
- default handling strategy

Checklist:

- [x] Decide whether runtime reads `config.example.yaml` or uses hardcoded defaults plus `config.local.yaml`.
- [x] Define what happens when `config.local.yaml` is missing.
- [ ] Define behavior for unknown keys.
- [ ] Define validation behavior for missing required values or malformed schema.

Exit Criteria:
Config loading behavior is deterministic and documented.

### Phase 3: Cross-Feature Integration

Objective:
Connect config to skill resolution, adapters, and telemetry without broadening scope prematurely.

Outputs:

- adapter-facing harness selection contract
- model role resolution contract
- local skill-index lookup contract

Checklist:

- [ ] Document how adapter selection consumes `defaultHarness`.
- [ ] Document how workflow code consumes model roles.
- [ ] Document the conventional local skill-index filename and how it is discovered.
- [ ] Confirm that no repo-owned paths need to become configurable yet.

Exit Criteria:
The first executable slice can consume config without forcing a schema redesign.

## Acceptance Criteria

- The repo clearly distinguishes configurable behavior from hardcoded structure.
- The config contract does not expose repo-owned paths without a concrete use case.
- A future implementer can build deterministic config loading with explicit precedence.
- The config schema supports local skill-index curation without implying unnecessary shared index taxonomy.
- Local skill-index handling is discoverable by convention and does not require config indirection.
- The contract stays small enough that early implementation can remain simple.

## Open Questions

- Should environment variables exist in the first implementation, or should they wait until there is a proven need?
- Should runtime eventually look for a concrete non-example local skill-index file alongside `skill-index.example.md`?
- At what point would configurable external skill directories become justified?
- Which RTK assumptions should be shared and explicit versus ambient and environment-driven?

## Follow-Up Work

- Update `config.example.yaml` if this feature doc changes the agreed schema.
- Draft the skill packaging contract.
- Draft the skill index contract.
- Use this contract as the basis for the first config-loading implementation.
- Replace any placeholder skill-index examples with a defined convention once the skill index contract exists.
