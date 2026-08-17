# Orchestration Artifacts And Progress Contract

## Summary

Define what orchestration persists and how it reports progress.

The first slice should be easy to inspect later without requiring chat history, but it should not overreach into a full dashboard or heavy event pipeline.

## Problem

Without a storage and progress contract:

- runs will be opaque
- archived project history will be inconsistent
- later stages may depend on transient in-memory state
- workflow state and telemetry will blur together

## Goals

- Define the minimum persisted run state.
- Require archived Markdown docs for human review.
- Define a first stable progress view.
- Keep workflow state separate from telemetry.

## Non-Goals

- Build a dashboard now.
- Finalize long-term retention policy.
- Store every raw prompt or tool transcript.
- Collapse run state and telemetry into one schema.

## Proposed Design

### Project Archive Shape

Each orchestrated project should live in a dated project folder:

```text
<orchestration-root>/
  projects/
    <YYYYMMDD-project-slug>/
      project.md
      runs/
        <run-id>/
          run.json
          stages/
            <stage-id>.json
          artifacts/
            <step-id>/
              <artifact files>
          docs/
            01-intake.md
            02-working-spec.md
            03-approved-spec.md
            04-plan.md
            05-summary.md
```

`<orchestration-root>` should come from config via `orchestration.root`.

Expected behavior:

- this root is machine-local rather than repo-local
- the actual local path commonly belongs in `config.local.yaml`
- the internal archive layout under that root is fixed by contract

Requirements:

- one named project folder per orchestrated project
- project folder prefixed with inception date in `YYYYMMDD`
- separation between run metadata, artifacts, and archived docs

### Minimum Persisted State

`run.json` should capture:

- run id
- source spec path
- overall status
- stage order
- started/finished timestamps
- pointer to final summary, if any

Stage records should capture:

- stage id
- source phase name
- current status
- step ids

### Required Archived Markdown Docs

At minimum, archive Markdown copies of:

- intake summary
- working spec
- approved spec
- generated plan
- final human-readable summary

Archive additional Markdown docs when the workflow generates them, such as:

- implementation reports
- verification reports
- review notes
- revision summaries

The archive is meant to support later recall for reviews, portfolio updates, and historical inspection.

### Archive Naming

Archived docs should be easy to scan in order.

The first contract should require:

- stable filenames
- simple ordering prefixes
- generated-at metadata in file content, metadata, or both

### Artifact Types

Useful first artifact roles include:

- `draft`
- `plan`
- `report`
- `patch`
- `summary`

When an artifact is meant for long-term human review, orchestration should prefer a Markdown form even if structured data also exists.

### Progress Contract

The first stable progress surface should be structured JSON.

Minimum fields:

- run id
- current stage
- overall status
- completed stages versus total
- blocked/failed reason, if any
- latest summary or artifact pointer

Human-readable terminal summaries can be layered on top of the same state.

### Separation From Telemetry

- workflow state answers: what exists, what stage is current, what artifacts were produced
- telemetry answers: what happened, how long it took, and what route ran

Persisted run-state files should not double as a telemetry sink.

## Repository Impact

This feature affects:

- future orchestration runtime code in `ai_stack/`
- tests for persisted run state
- future UI/dashboard work
- telemetry follow-up boundaries

## Phases

### Phase 1: Archive Contract
Objective:
Define the minimum stored project history.

Outputs:

- project-folder contract
- run-state contract
- archived-doc contract

Checklist:
- [x] Define the dated project folder shape.
- [x] Define minimum run metadata.
- [x] Require archived Markdown docs.
- [x] Keep workflow state separate from telemetry.

Exit Criteria:
An implementer can persist a run and leave behind a usable project history.

### Phase 2: Progress Contract
Objective:
Define the first status surface.

Outputs:

- JSON progress view
- minimum progress fields

Checklist:
- [x] Choose JSON as the stable first status surface.
- [x] Define the minimum progress fields.
- [x] Keep the storage model resume-friendly.

Exit Criteria:
An implementer can expose stable progress without inventing a UI first.

## Acceptance Criteria

- The repo defines what orchestration persists.
- The archive includes durable Markdown project docs.
- Progress reporting has a stable first contract.
- Workflow state and telemetry remain distinct.

## Open Questions

- What metadata belongs in `project.md`?
- When, if ever, should raw prompts or tool logs become first-class archived assets?

## Follow-Up Work

- Define the minimum metadata block for archived docs.
- Add persisted-state tests once runtime code exists.
