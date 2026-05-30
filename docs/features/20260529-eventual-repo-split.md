# Eventual Repo Split

## Summary

Define the architectural boundary between the future `ai-stack` orchestration engine and the opinionated conventions, content, and defaults currently being designed in this repository. The goal is to preserve fast iteration now while preventing personal or team-specific preferences from silently becoming core platform requirements.

## Problem

This repository currently mixes two different kinds of value:

- platform contracts needed to make orchestration work at all
- opinionated conventions, defaults, skills, and documentation patterns that are useful but not universally required

That is acceptable during early design, but it becomes a liability if left implicit.

Without an explicit split model:

- the engine will absorb personal workflow assumptions
- teammates will have to adopt opinionated skills or docs conventions just to use the tool
- shared content and core runtime contracts will evolve at different speeds but remain tightly coupled
- a later repo split will be more painful and riskier

## Goals

- Define what belongs in a future core orchestration repo.
- Define what belongs in a future conventions/content repo.
- Keep the current repository usable for fast iteration before the split.
- Make future extraction of the core engine a low-friction move.
- Ensure teammates can adopt the engine without adopting all of the opinionated content.

## Non-Goals

- Perform the repo split now.
- Finalize package names, org names, or publishing strategy.
- Define every future distribution or versioning detail.
- Require the engine and conventions layers to never reference each other.

## Proposed Design

The long-term architecture should assume two layers:

1. Core engine
2. Convention and content bundle

They may temporarily live in one repository, but the contracts should be designed as if they could be separated cleanly.

### Core Engine

The core engine should contain only what is required to make orchestration function.

Likely core concerns:

- config loading and validation
- adapter interfaces and implementations
- harness selection and invocation
- model role resolution
- skill discovery and loading contracts
- skill-index discovery and loading contracts
- load traces and execution observability
- deterministic tests for resolution and handoff

Core principles:

- minimal opinionated defaults
- no dependence on one person’s preferred skill set
- no dependence on one repo’s docs layout unless truly required by runtime
- content should be optional wherever practical

### Convention and Content Bundle

The conventions/content layer should contain useful defaults and patterns that are not required for the engine to function.

Likely convention/content concerns:

- `docs/features/` process and templates
- `AGENTS.md` style and repo guidance conventions
- example configs
- example skills
- shared skill collections
- benchmark content
- team-specific or personal workflows
- example skill indexes

This layer is where opinionated productivity choices should live.

### Current Repository Strategy

For now, the repository can continue to host both layers to preserve iteration speed.

However, new additions should be classified implicitly as either:

- `core`
- `convention`
- `content`

If something is hard to classify, that is a signal the boundary is still fuzzy and should be clarified before implementation deepens.

### Classification Heuristic

Use this rule:

- if removing it would make the orchestration engine impossible to run, it is probably core
- if removing it only removes defaults, examples, or preferences, it is probably convention or content

Examples:

Core:

- config loading behavior
- adapter contracts
- skill package discovery rules
- skill load traces

Convention/content:

- feature doc structure in `docs/features/`
- local skill-index example files
- example skills
- recommended benchmark suites
- repo-specific agent guidance style

### Split Readiness Principle

The repo does not need to split now, but it should be organized so that split pressure reveals itself early.

Good signs that the split is justified:

- teammates want the engine but not the bundled conventions
- content evolves faster than runtime contracts
- packaging, release, or versioning needs diverge
- engine tests and content tests become conceptually separate

## Repository Impact

This feature affects:

- top-level architecture docs
- how future directories are described
- how new features are classified during planning
- future packaging and release decisions

It should influence how current directories are interpreted:

- `adapters/`, `tests/`, future config/runtime code trend toward core
- `docs/features/`, example configs, example indexes, example skills trend toward convention/content
- `skills/shared/` may eventually contain both reusable core-adjacent examples and optional content packs, so authors should stay explicit about which one a skill is

## Phases

### Phase 1: Boundary Definition

Objective:
Define the conceptual split before code hardens around the wrong shape.

Outputs:

- repo-split feature doc
- core versus convention/content classification guidance
- split-readiness criteria

Checklist:

- [x] Define the two-layer model.
- [x] Define likely core responsibilities.
- [x] Define likely convention/content responsibilities.
- [x] Define a practical heuristic for classifying future additions.

Exit Criteria:
Future contributors can reason about whether new work belongs to the engine or the conventions layer.

### Phase 2: Directory Classification

Objective:
Map current directories and planned features onto the split model.

Outputs:

- directory-level classification notes
- clarified ownership of current scaffolding

Checklist:

- [ ] Classify each current top-level directory as core, convention, content, or mixed.
- [ ] Identify any directories whose purpose is still too ambiguous.
- [ ] Update README or directory READMEs where classification needs to be visible.

Exit Criteria:
The current repo layout is understandable through the split lens.

### Phase 3: Split-Ready Implementation

Objective:
Implement early executable slices without increasing coupling unnecessarily.

Outputs:

- first runtime features built with extraction in mind
- test boundaries that reflect the core/content distinction

Checklist:

- [ ] Keep runtime code independent from example content where practical.
- [ ] Ensure tests can isolate core runtime behavior from optional content bundles.
- [ ] Avoid making `docs/features/` or example skills a hard runtime dependency unless intentionally part of the engine contract.

Exit Criteria:
The first executable slice can later be extracted with modest effort.

## Acceptance Criteria

- The repo clearly distinguishes eventual core engine responsibilities from optional conventions and content.
- Teammates could adopt the future engine without being forced to adopt repo-specific skills and docs conventions.
- Future contributors have a practical rule for classifying new work.
- The current repository can continue iterating quickly without pretending the split already happened.

## Open Questions

- Should the eventual split produce two repos, or one repo plus separately published content packs?
- Which current directories are genuinely mixed and need a stronger boundary before implementation starts?
- At what milestone should the split decision be revisited: after the first executable slice, after the first adapter, or later?

## Follow-Up Work

- Classify the current top-level directories using this model.
- Draft the skill index contract with the core/content distinction in mind.
- Use this boundary when selecting the first executable slice.
