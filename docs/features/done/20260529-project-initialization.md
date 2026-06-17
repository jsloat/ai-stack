# Project Initialization

## Summary

Initialize `ai-stack` as a documentation-led repository for a future AI coding operations platform. The immediate goal is not to ship orchestration code. It is to establish the repo contract, naming conventions, and feature-document discipline that later implementation will follow.

This document started as the bootstrap plan. Parts of that plan are now complete and have been superseded by dedicated feature docs plus a small implemented runtime slice.

## Problem

AI coding workflows tend to accrete as ad hoc prompts, one-off scripts, and harness-specific conventions. That makes them hard to share, hard to reason about, and nearly impossible to measure consistently across tools.

This project needs a clean initialization pass that defines:

- what the repository is for
- how sharable versus private assets are separated
- where feature design lives
- which repository areas are expected to exist later
- how future implementation work should be phased

Without that initialization, early code will set accidental architecture.

## Goals

- Establish `docs/features/` as the first-class design surface.
- Define the top-level repo purpose and architectural direction.
- Document `shared` versus `local` conventions for future skills and indexes.
- Describe the intended repository layout clearly enough to guide the first executable scaffolding.
- Create agent-readable repo instructions that future harnesses can consume.
- Ensure the repository is legible and operable through both Codex and GitHub Copilot instruction mechanisms.
- Provide a shareable config template that users can copy into an untracked local config file.

## Non-Goals

- Implement the orchestrator.
- Implement adapters, telemetry storage, or model benchmarks.
- Finalize all configuration schema details.
- Commit to a single harness or model vendor.
- Design every future feature in depth.

## Proposed Design

The project should begin with stable guidance files before executable modules:

- `README.md` explains the project in human terms.
- `AGENTS.md` provides the primary agent-oriented workflow entrypoint.
- `.github/copilot-instructions.md` provides a thin GitHub Copilot compatibility layer.
- `docs/features/README.md` defines how this repo writes and uses feature docs.
- `docs/features/20260529-project-initialization.md` records the bootstrap contract for the repository itself.

The design direction from the ideation work is that `ai-stack` is a harness-agnostic coordination layer. It should favor harness-native primitives such as instructions files and skills, while standardizing routing, benchmarks, telemetry, and repo structure above them.

The documentation model should also be harness-agnostic:

- shared durable truth lives in `README.md` and `docs/features/`
- `AGENTS.md` acts as the primary agent-facing operating guide
- `.github/copilot-instructions.md` acts as a thin Copilot-facing compatibility file

Instruction placement should be explicit:

- add durable architectural or process truth to shared docs first
- add agent workflow guidance to `AGENTS.md`
- update `.github/copilot-instructions.md` only when Copilot still needs a compatible pointer or repo-wide rule

The config model should stay conservative:

- configure behavior, not repo-owned structure
- keep directory layout hardcoded until relocation is an actual requirement
- prefer convention-based local skill-index curation before inventing shared index taxonomy or config hooks

The initialization should also lock in one important naming decision early:

- `shared` = safe to commit and distribute
- `local` = private or environment-specific additions

That convention is more durable than labels like `work`, `machine`, or `personal`, because it describes scope rather than usage.

## Repository Impact

This feature primarily affects:

- docs
- repo-level instructions
- future config conventions
- future skill and skill-index layout
- cross-harness instruction interoperability

Expected future directories:

```text
ai-stack/
  AGENTS.md
  README.md
  .github/
    copilot-instructions.md
    instructions/
  config.example.yaml
  config.local.yaml
  docs/
    features/
  skills/
    shared/
    local/
  skill-indexes/
    local/
  agents/
  adapters/
  templates/
  model-benchmarks/
  telemetry/
  dashboard/
  memory/
  tests/
  bin/
```

## Phases

### Phase 1: Documentation Bootstrap

Objective:
Define the repo’s purpose, design conventions, and feature-doc contract.

Outputs:

- top-level project README
- agent entrypoint guidance
- GitHub-style compatibility instructions
- feature-doc README
- initialization feature document

Checklist:

- [x] Add a top-level `README.md` describing the project and intended repository shape.
- [x] Add `AGENTS.md` as the primary agent operating guide.
- [x] Add `.github/copilot-instructions.md` as a thin Copilot compatibility layer.
- [x] Add `docs/features/README.md` defining the required structure for future feature docs.
- [x] Add this initialization feature doc as a tracked design artifact.
- [x] Define the intended split between Codex-facing and Copilot-facing instruction surfaces.
- [x] Define where future sessions should add new instructions based on scope and consumer.

Exit Criteria:
A contributor can understand the project’s direction and documentation model without the ideation chat.

### Phase 2: Structural Scaffolding

Objective:
Create the initial empty directories and baseline config files implied by the docs.

Outputs:

- top-level directory skeleton
- placeholder config files
- gitignore strategy for local-only files

Checklist:

- [x] Create first-pass directories for `skills`, `skill-indexes`, `adapters`, `model-benchmarks`, `telemetry`, `dashboard`, `memory`, `tests`, and `bin`.
- [x] Add committed `config.example.yaml` defaults that users can copy and fill in locally.
- [x] Define treatment of `config.local.yaml` and other private local artifacts.
- [x] Add placeholder README files where empty directories need intent.

Exit Criteria:
The repository shape described in docs exists on disk with minimal, coherent scaffolding.

### Phase 3: Configuration and Context Contracts

Objective:
Define the first executable contract for configuration, skill sources, and repo-local overrides.

Outputs:

- config schema draft
- shared/local loading model
- initial skill-index contract

Checklist:

- [x] Define the config fields needed for harness defaults, model roles, telemetry toggles, and skill-index references.
- [x] Document how `shared` skills and `local` additions are discovered and merged.
- [x] Define the minimum shape of a skill index file.
- [x] Decide whether `AGENTS.md` and `.github/copilot-instructions.md` remain hand-maintained or are generated from shared policy.

Exit Criteria:
An implementation can read configuration and resolve repo context without inventing new naming or layout rules.

### Phase 4: First Executable Slice

Objective:
Ship one thin vertical path that proves the docs support real behavior.

Outputs:

- one adapter path
- one simple workflow or command
- basic telemetry capture

Checklist:

- [x] Select the first harness target.
- [x] Implement the smallest useful command path, likely around context resolution or skill discovery.
- [x] Capture enough telemetry to observe route, duration, and outcome.
- [x] Validate that the implementation still matches the documented repo contract.

Exit Criteria:
The repo has a minimal executable path that confirms the initialization docs were concrete enough to build against.

## Acceptance Criteria

- The repo has clear top-level documentation describing purpose, architecture, and future structure.
- `docs/features/` has a documented contract for future feature files, including phases and checklists.
- The initialization doc explains both what exists now and what work remains before executable scaffolding starts.
- The `shared` versus `local` convention is clearly documented and reusable.
- A future implementer can start structural scaffolding without reopening the ideation transcript.
- A contributor can identify the primary agent guide, the Copilot compatibility layer, and where shared truth should live.
- A future agent session can determine where to add new guidance without introducing redundant instruction files.
- A new user can discover a committed config template and create an untracked local config from it.
- The docs do not imply configurable repo-owned paths or shared skill-index structures without a concrete use case.
- Future sessions are cued by incomplete phases, unchecked items, and open questions in feature docs rather than treating them as static notes.
- Completed feature docs move out of active `docs/features/` once they no longer carry live checklist work.

## Open Questions

- Should `AGENTS.md` remain hand-authored, or should future tooling generate harness-specific instruction surfaces from a shared source?
- Should GitHub instruction files remain hand-authored, or should the repo eventually generate them from a single canonical source?
- Should the repo favor `skills/shared` and `skills/local`, or a flatter convention such as `skills/` plus `.gitignore` patterns for local-only assets?
- What is the smallest initial executable slice that proves the architecture without overcommitting to one harness?
- How much of the config schema should be declared before the first adapter exists?

## Follow-Up Work

- Extend the telemetry foundation toward persisted events and later dashboard work once there is more than one meaningful event source.
- Keep moving settled structure from feature docs into README-style shared docs as runtime behavior stabilizes.
- Draft a dedicated feature doc for model benchmarks and routing inputs.
