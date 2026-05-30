# Feature Docs

`docs/features/` holds the tracked design and delivery documents for this project. These files are expected to survive longer than chat history and should be detailed enough to drive implementation work without reconstructing intent from memory.

Use `docs/features/` for active backlog and ongoing design work. Use `docs/features/done/` for completed feature docs that still matter as reference material.

## What Belongs Here

Create a feature doc when work has any of the following:

- multiple phases or milestones
- architecture or boundary decisions
- tradeoffs that should stay visible in git
- cross-cutting impact on config, routing, skills, adapters, telemetry, or benchmarks
- enough complexity that a checklist will prevent drift

Do not use this directory for scratch notes, raw transcripts, or generic meeting summaries.

This directory is design documentation, not an instruction-loading mechanism. Agent workflow guidance belongs in `AGENTS.md`. Copilot compatibility guidance belongs in `.github/copilot-instructions.md`.

## File Naming

Feature docs should be named with the date the work started, followed by a short slug:

```text
YYYYMMDD-short-feature-name.md
```

Examples:

- `20260529-project-initialization.md`
- `20260529-configuration-contract.md`
- `20260530-telemetry-foundation.md`

The date is the feature's inception date, not the last modified date.

## Required Structure

Each feature file should use this shape:

```md
# Feature Name

## Summary
## Problem
## Goals
## Non-Goals
## Proposed Design
## Repository Impact
## Phases
## Acceptance Criteria
## Open Questions
## Follow-Up Work
```

The section names can vary slightly when that improves readability, but the document still needs to cover those concerns.

## Phase Model

Feature docs should describe phased implementation explicitly. Use phases when work crosses different success criteria or when early steps need to establish structure before later steps add behavior.

Recommended default phases:

1. Discovery
   Confirm intent, constraints, and dependencies.
2. Foundation
   Create structure, contracts, and scaffolding.
3. Core Implementation
   Build the main behavior or data model.
4. Verification
   Add or run tests, validate docs, confirm operating behavior.
5. Follow-Through
   Finish adjacent docs, cleanup, rollout notes, or future hooks.

You can rename or compress phases, but every phase should have:

- objective
- concrete outputs
- completion checklist
- explicit exit criteria

## Checklists

Use markdown checklists inside each phase. They should be operational, not aspirational.

Good checklist item:

- [ ] Add `config.yaml` support for `paths.featureDocs`

Weak checklist item:

- [ ] Make config better

Checklists should be:

- concrete
- scoped to one phase
- reviewable in git
- possible to mark complete with evidence

Unchecked items are active backlog, not passive documentation. Future sessions should look for incomplete checklist items before deciding what to work on next or before claiming a feature area is done.

When a feature doc is substantially complete and no longer the primary place to look for unfinished work, move it to `docs/features/done/` instead of leaving it mixed into the active backlog.

## Repository Impact Section

Every feature doc should say which areas of the repo it changes or expects to change. That usually includes one or more of:

- docs
- config
- skills
- skill indexes
- adapters
- telemetry
- benchmarks
- dashboard
- tests

This is the fastest way for a future implementer to understand blast radius.

## Acceptance Criteria

Acceptance criteria should read like observable conditions, not vague intentions.

Examples:

- A new contributor can identify the difference between `shared` and `local` assets from repo docs alone.
- An implementer can initialize the repo structure without consulting the ideation chat.
- Feature docs consistently include phased checklists and clear exit criteria.

## Template

Use this as the starting point for new files:

```md
# <Feature Name>

## Summary

## Problem

## Goals

## Non-Goals

## Proposed Design

## Repository Impact

## Phases

### Phase 1: <Name>
Objective:

Outputs:

Checklist:
- [ ]

Exit Criteria:

### Phase 2: <Name>
Objective:

Outputs:

Checklist:
- [ ]

Exit Criteria:

## Acceptance Criteria

## Open Questions

## Follow-Up Work
```

## Style

- Optimize for clarity over completeness theater.
- Prefer explicit boundaries over vague flexibility.
- Record unresolved decisions in `Open Questions` rather than hiding them in prose.
- Treat these files as working design contracts, not marketing docs.
- Keep feature docs safe to share: avoid absolute local paths, private machine context, and secrets.

Open questions are also active backlog signals. If a relevant feature doc has unresolved questions, future sessions should consider whether the current task should answer or narrow them.

## Relationship To Instruction Files

Feature docs are part of the shared truth layer for the repository. If a future session needs to add guidance:

- use feature docs for durable design, architecture, scope, and process conventions
- use `AGENTS.md` for primary agent workflow behavior
- use `.github/copilot-instructions.md` only as a thin Copilot-facing compatibility layer

Do not create policy only in instruction files if that policy should remain visible as part of the repository's durable design record.

Use the same principle for configuration examples: shared templates should be committed, while filled local variants should remain outside shared repo history.
