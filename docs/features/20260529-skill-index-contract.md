# Skill Index Contract

## Summary

Define the first contract for the skill index in `ai-stack`. The index should be a small YAML registry of external or local-only skills that this repo may use, while remaining simple enough to edit by hand and structured enough for future tooling to discover, resolve, and trace skill loading.

## Problem

The repository now has a conventional example file for its skill index, but there is no contract for what information the file must contain, how tooling should parse it reliably, or how operational concerns like “update the source repo first” should be represented without bloating the runtime format.

Without a skill index contract:

- skill registries will drift in format
- future tooling will have to parse ad hoc formats
- local operational steps will get mixed into core resolution logic
- it will be unclear what “if present, use it; if absent, ignore it” means in practice

## Goals

- Standardize the skill index as a lightweight YAML registry file.
- Define the minimum structure future tooling should be able to extract.
- Preserve room for optional local operational guidance without forcing it into the runtime file.
- Keep the contract compatible with the “ignore if absent” model.
- Separate portable registry data from local machine or team-specific procedures.

## Non-Goals

- Require the engine to perform git pulls automatically.
- Define the full runtime parser implementation.
- Require all indexes to include prose, frontmatter, or pre-flight steps.
- Standardize one global update procedure for every environment.
- Replace skill packaging or configuration contracts.

## Proposed Design

The skill index should be a small YAML file that acts as a routing registry for skills outside the shared repo.

### File Location

The current conventional example artifact is:

- `skill-indexes/skill-index.example.yaml`

The runtime working file is:

- `skill-indexes/skill-index.yaml`

The runtime should only read the non-example working file. The example exists to document the shape and provide a copyable starting point.

### File Shape

The core portable structure is a top-level `skills` list. Other top-level fields may exist for human context, but the runtime should only require the `skills` list.

Example:

```yaml
name: skill-index
description: Local registry of external skills.

skills:
  - id: pull-request
    when: Creating or updating pull requests
    repo: ~/Dev/example-tools
    path: .github/skills/pull-request/SKILL.md
```

### Required Skill Entry Fields

Each skill entry must contain:

- `id`
- `when`
- `repo`
- `path`

Meanings:

`id`

- short identifier for the skill
- should generally align with the skill directory name when possible

`when`

- trigger description for routing or manual lookup
- should describe the kinds of tasks that should cause this skill to be consulted

`repo`

- location of the repository containing the skill
- may be a local path or another repo reference, depending on environment

`path`

- path from the source repo root to the skill’s `SKILL.md`

The runtime file should stay narrow. Local operational guidance such as pre-flight or refresh procedures can live in surrounding docs or local workflow notes instead of being mixed into the required machine-readable schema.

### Pre-Flight and Freshness Policy

“Update the source repo before loading a skill” is a valid use case, but it should be modeled as a configurable or content-level policy, not a universal engine invariant.

The contract should allow an index to describe a pre-flight flow such as:

- determine source repo state
- optionally update main/default branch when safe
- continue regardless of outcome

Important boundaries:

- the engine should not assume every skill source wants automatic updates
- local shell functions or private scripts should not become platform requirements
- shared indexes may also want freshness guidance, but that still does not mean the engine must own the whole procedure

So the contract should permit:

- local docs that explain pre-flight expectations
- future lightweight metadata if update behavior later needs structure

But early implementations can stop at:

- parse registry entries
- leave execution of that procedure to a higher-level workflow or later feature

### Loading Contract

The minimum future runtime behavior should be:

1. if the skill index file is absent, continue normally
2. if present, parse the `skills` list
3. resolve referenced skill locations deterministically
4. emit a load trace when a referenced skill is selected and loaded

Rows missing any required field should be skipped rather than crashing the whole lookup.

The runtime does not initially need to:

- execute arbitrary shell from the index
- guarantee repo freshness
- understand broader operational prose

### Native Router Integration

If the repo ships a native routing skill that consults the skill index, that skill does not need to read the repo-relative working file directly at runtime.

A valid pattern is:

- keep the editable source-of-truth file at `skill-indexes/skill-index.yaml`
- during skill sync, copy the current file into the installed router skill as a bundled reference
- install the router skill only when the index contains at least one entry

This keeps the editable repo artifact and the installed native skill aligned without forcing the installed skill to guess the repo root.

## Repository Impact

This feature affects:

- `skill-indexes/README.md`
- `skill-indexes/skill-index.example.yaml`
- future skill resolution and load tracing
- future workflow decisions about freshness/update behavior

It also intersects with:

- configuration contract
- skill packaging contract
- eventual core vs conventions split

## Phases

### Phase 1: Index Contract

Objective:
Define the minimum portable structure of the index.

Outputs:

- skill index feature doc
- required skill entry fields
- distinction between required registry data and optional operational guidance

Checklist:

- [x] Define YAML as the source format.
- [x] Define the required skill entry fields.
- [x] Keep non-registry top-level fields optional.
- [x] Keep operational guidance outside the required runtime schema.

Exit Criteria:
An author can create a skill index that tooling can parse reliably and humans can still edit directly.

### Phase 2: Example Alignment

Objective:
Align the example index file with the new contract.

Outputs:

- updated example index
- clearer README guidance

Checklist:

- [x] Update `skill-indexes/skill-index.example.yaml` to include a realistic example entry.
- [x] Keep the runtime file schema small instead of mixing in operational guidance.
- [x] Update `skill-indexes/README.md` to reflect the new contract.

Exit Criteria:
The example file demonstrates the contract instead of just referencing it abstractly.

### Phase 3: Runtime Consumption

Objective:
Make the index contract consumable by future tooling without overfitting to one local workflow.

Outputs:

- parser expectations
- resolution behavior
- trace expectations

Checklist:

- [x] Define how the runtime discovers the index file.
- [x] Define how registry rows are parsed and validated.
- [x] Define how missing or invalid rows are handled.
- [ ] Define how load traces report index-driven skill resolution.
- [ ] Decide whether freshness/update behavior is only documented, or later becomes a structured optional capability.

Exit Criteria:
Future tooling can consume the index reliably while leaving environment-specific pre-flight logic optional.

## Acceptance Criteria

- The repo defines a clear YAML-based skill index contract.
- Required portable structure stays small and separate from optional operational guidance.
- The contract supports your work-laptop style pre-flight/update instructions without making them universal engine requirements.
- Future runtime behavior can ignore a missing index and still operate normally.
- Registry entries contain enough information to resolve a skill deterministically.

## Open Questions

- Should freshness/update guidance remain prose-only, or later gain lightweight structured metadata?
- Should shared indexes ever exist, and if so, should they be allowed to carry update procedures too?
- Should the engine ever execute pre-flight/update steps directly, or should that remain a workflow-layer concern?

## Follow-Up Work

- Update `skill-indexes/skill-index.example.yaml` to reflect this contract.
- Update `skill-indexes/README.md` to reflect this contract.
- Use this contract when defining the first load-trace-based skill resolution tests.
- Revisit freshness/update behavior after the first executable slice exists.
