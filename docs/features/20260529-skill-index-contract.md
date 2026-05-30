# Skill Index Contract

## Summary

Define the first contract for a local skill index in `ai-stack`. The index should be a human-readable markdown registry of external or local-only skills that this repo may use, while remaining structured enough for future tooling to discover, resolve, and trace skill loading.

## Problem

The repository now has a conventional example file for a local skill index, but there is no contract for what information the file must contain, what parts are meant for humans versus tooling, or how operational concerns like “update the source repo first” should be represented.

Without a skill index contract:

- skill registries will drift in format
- future tooling will have to parse arbitrary prose
- local operational steps will get mixed into core resolution logic
- it will be unclear what “if present, use it; if absent, ignore it” means in practice

## Goals

- Standardize the skill index as a markdown registry file.
- Define the minimum structure future tooling should be able to extract.
- Preserve room for optional local operational guidance such as pre-flight update steps.
- Keep the contract compatible with the “ignore if absent” model.
- Separate portable registry data from local machine or team-specific procedures.

## Non-Goals

- Require the engine to perform git pulls automatically.
- Define the full runtime parser implementation.
- Require all indexes to include frontmatter or pre-flight steps.
- Standardize one global update procedure for every environment.
- Replace skill packaging or configuration contracts.

## Proposed Design

The local skill index should be a markdown file that acts as both:

- a registry of skills outside the shared repo
- a local operator guide for how to use and refresh them

### File Location

The current conventional example artifact is:

- `skill-indexes/local/skill-index.example.md`

Future implementation may decide whether the runtime reads:

- that file directly
- or a sibling non-example file with a similar contract

For now, the contract should focus on file structure, not final discovery mechanics.

### File Shape

The index should support four layers:

1. optional frontmatter
2. human-readable overview
3. optional operational sections such as pre-flight or update guidance
4. a required skill registry table

### Frontmatter

Frontmatter is optional but recommended.

Useful fields include:

- `name`
- `description`

These fields are helpful for documentation and future tooling, but they should not be required for initial human use.

### Required Registry Table

The core portable structure is a markdown table with these columns:

- `Skill`
- `When to use`
- `Source Repo`
- `Skill Path`

Meanings:

`Skill`

- short identifier for the skill
- should generally align with the skill directory name when possible

`When to use`

- trigger description for routing or manual lookup
- should describe the kinds of tasks that should cause this skill to be consulted

`Source Repo`

- location of the repository containing the skill
- may be a local path or another repo reference, depending on environment

`Skill Path`

- path from the source repo root to the skill’s `SKILL.md`

Future tooling should be able to extract registry rows even if the rest of the file contains prose it does not understand.

### Optional Operational Sections

The index may include local operational sections such as:

- pre-flight protocol
- update guidance
- loading instructions
- team-specific maintenance notes

These sections are useful, and your work example shows a legitimate need for them.

However, they should be treated as optional policy/content, not as a mandatory core engine contract.

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

- human-readable pre-flight instructions
- future structured metadata that indicates whether a source repo has an update/freshness step

But early implementations can stop at:

- parse registry entries
- optionally record that a pre-flight section exists
- leave execution of that procedure to a higher-level workflow or later feature

### Loading Contract

The minimum future runtime behavior should be:

1. if the local skill index file is absent, continue normally
2. if present, parse the registry table
3. resolve referenced skill locations deterministically
4. emit a load trace when a referenced skill is selected and loaded

The runtime does not initially need to:

- execute arbitrary shell from the index
- guarantee repo freshness
- parse every prose section semantically

## Repository Impact

This feature affects:

- `skill-indexes/README.md`
- `skill-indexes/local/skill-index.example.md`
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
- required registry columns
- distinction between required registry data and optional operational sections

Checklist:

- [x] Define markdown as the source format.
- [x] Define the required registry table columns.
- [x] Define frontmatter as optional.
- [x] Define operational sections such as pre-flight guidance as optional.

Exit Criteria:
An author can create a skill index that both humans and future tooling can understand.

### Phase 2: Example Alignment

Objective:
Align the example index file with the new contract.

Outputs:

- updated example index
- clearer README guidance

Checklist:

- [ ] Update `skill-indexes/local/skill-index.example.md` to include a realistic example registry table.
- [ ] Distinguish portable registry structure from local-only operational guidance in the example.
- [ ] Update `skill-indexes/README.md` to reflect the new contract.

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

- [ ] Define how the runtime discovers the index file.
- [ ] Define how registry rows are parsed and validated.
- [ ] Define how missing or invalid rows are handled.
- [ ] Define how load traces report index-driven skill resolution.
- [ ] Decide whether freshness/update behavior is only documented, or later becomes a structured optional capability.

Exit Criteria:
Future tooling can consume the index reliably while leaving environment-specific pre-flight logic optional.

## Acceptance Criteria

- The repo defines a clear markdown-based skill index contract.
- Required portable structure is separated from optional local operational guidance.
- The contract supports your work-laptop style pre-flight/update instructions without making them universal engine requirements.
- Future runtime behavior can ignore a missing index and still operate normally.
- Registry entries contain enough information to resolve a skill deterministically.

## Open Questions

- Should the eventual real runtime file use the same filename as the example file, or a sibling non-example file?
- Should freshness/update guidance remain prose-only, or later gain lightweight structured metadata?
- Should shared indexes ever exist, and if so, should they be allowed to carry update procedures too?
- Should the engine ever execute pre-flight/update steps directly, or should that remain a workflow-layer concern?

## Follow-Up Work

- Update `skill-indexes/local/skill-index.example.md` to reflect this contract.
- Update `skill-indexes/README.md` to reflect this contract.
- Use this contract when defining the first load-trace-based skill resolution tests.
- Revisit freshness/update behavior after the first executable slice exists.
