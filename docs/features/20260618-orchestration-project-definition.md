# Orchestration Project Definition Contract

## Summary

Define the first canonical project-definition format for orchestration.

The orchestrator should accept multiple source materials, but it should execute from one normalized Markdown spec.

## Problem

Without a canonical execution spec:

- intake sources will leak into runtime semantics
- external systems will shape the engine too early
- plan extraction will be inconsistent
- archived project history will be harder to trust

## Goals

- Support flexible intake sources.
- Normalize them into one execution spec.
- Reuse repo-native feature-doc structure first.
- Archive the execution spec durably.

## Non-Goals

- Make every Markdown file executable.
- Require a single external system such as ADO.
- Define the final long-term manifest format.

## Proposed Design

### Intake Model

Source material may be:

- a blank template
- an existing feature doc
- a loose Markdown brief
- an external work item pulled in by local skills or connectors
- other environment-specific inputs

These are intake sources, not execution contracts.

### Canonical Execution Input

The first canonical execution input should be a feature-doc-style Markdown file.

It should contain, at minimum:

- title
- `## Phases`
- one or more `### Phase N: Name` sections
- `Objective`
- `Outputs`
- `Checklist`
- `Exit Criteria`
- acceptance criteria

This reuses the existing `docs/features/README.md` contract instead of inventing a new planning system.

### Normalization Step

If the source material is not already in canonical form, orchestration should first create a normalized draft spec.

That gives a simple two-phase model:

1. intake and spec authoring
2. execution from approved spec

### Approval Boundary

Execution should not start from a mutable draft by default.

The lifecycle should distinguish:

- source intake
- working spec
- approved spec

The approved spec is the execution baseline.

### Runtime Parsing Boundary

The first runtime only needs to extract:

- document identity
- phase order
- checklist items per phase
- acceptance criteria

It does not need full natural-language understanding of every section.

### Archived Spec Copies

The project archive should preserve:

- the normalized spec used for execution
- enough metadata to identify the original intake source later

This matters because source material may change after execution starts.

## Repository Impact

This feature affects:

- `docs/features/`
- future parsing code in `ai_stack/`
- tests for normalization and plan extraction

## Phases

### Phase 1: Canonical Input
Objective:
Choose the first execution-spec format.

Outputs:

- canonical Markdown spec contract
- intake-versus-execution distinction

Checklist:
- [x] Define flexible intake sources.
- [x] Define one canonical execution spec.
- [x] Reuse the feature-doc structure first.

Exit Criteria:
An implementer knows what the orchestrator executes from, regardless of how the project started.

### Phase 2: Approval And Parsing
Objective:
Define how drafts become executable.

Outputs:

- working-spec to approved-spec boundary
- minimum parsing contract

Checklist:
- [x] Define the approval boundary.
- [x] Define the minimum fields the runtime extracts.
- [x] Require archival of the execution spec.

Exit Criteria:
An implementer can build intake, refinement, approval, and plan extraction without inventing new document semantics.

## Acceptance Criteria

- Source material can be flexible.
- Execution input is standardized.
- The approved spec is the baseline for execution.
- The project archive preserves the spec used for the run.

## Open Questions

- Should eligibility remain structural, or later require explicit opt-in?
- Which source metadata should always be preserved in the archive?
- When should a separate structured manifest exist beside the Markdown spec?

## Follow-Up Work

- Define the exact normalized spec template.
- Define the approval checks required before planning/execution.
