# Skill Packaging

## Summary

Define the first packaging contract for skills in `ai-stack`. The goal is to make skills portable, inspectable, and easy to share across agents and harnesses without forcing every skill to carry a heavy bundle of unused structure.

## Problem

The repo intends to support a `skills/` directory, but that directory should not exist until it carries real content. The contract for what a skill actually is still needs to be defined independently of the directory being present.

Without a packaging contract:

- skills will be represented inconsistently
- future tooling will need skill-specific special cases
- reusable assets and scripts will end up in ad hoc places
- sharable and local-only skills will blur together

This matters because skills are one of the main ways `ai-stack` can package specialized behavior without encoding everything into repo-wide instructions.

## Goals

- Define the minimum required shape of a skill package.
- Define which supporting directories are optional and what they mean.
- Keep the packaging model compatible with both lightweight markdown skills and richer multi-file skills.
- Preserve the `shared` versus `local` split.
- Avoid overcommitting to a single harness-specific skill format.

## Non-Goals

- Define the full skill index format.
- Define runtime loading behavior in code.
- Finalize adapter-specific translation rules for every harness.
- Require every skill to include scripts, assets, or agents.
- Standardize every possible metadata field up front.

## Proposed Design

A skill should be a directory with one required file and several optional companion directories.

### Required Shape

Each skill package should live under one of:

- `skills/shared/<skill-name>/`
- `skills/local/<skill-name>/`

Each skill package must include:

- `SKILL.md`

`SKILL.md` is the primary human-readable contract for the skill. It should explain:

- what the skill is for
- when to use it
- any prerequisites
- how to apply it
- any important constraints or warnings

### Optional Companion Directories

The following directories are allowed when a skill needs them:

- `scripts/`
- `references/`
- `assets/`
- `agents/`

Their intended meanings are:

`scripts/`

- executable helpers used by the skill
- should be small, purposeful, and directly relevant to the skill

`references/`

- supporting documents, schemas, examples, or notes the skill relies on
- should not duplicate the primary instruction text unnecessarily

`assets/`

- non-code files such as templates, images, fixtures, or other packaged artifacts

`agents/`

- subordinate prompts or agent-specific helper artifacts when a skill needs to coordinate specialized sub-roles

### Optional Top-Level Companion Files

Skills may also include small supporting files at the skill root when that is the clearest packaging choice, for example:

- additional prompt files
- sample inputs
- validation notes

However, the root should stay sparse. If a skill grows beyond a couple of helper files, use the companion directories above.

### Shared vs Local

`skills/shared/`

- contains skills safe to commit and distribute
- should avoid private environment assumptions, secrets, or organization-specific references unless intentionally public

`skills/local/`

- contains private or environment-specific skills
- may reference private tools, internal systems, or personal workflows
- should not become part of the shared repo contract by default

### Naming

Skill directory names should be short, lowercase, and hyphenated where needed.

Examples:

- `pr-review`
- `ado-auth`
- `react-review`
- `internal-logs`

### Packaging Principles

- Prefer a minimal skill package until richer structure is justified.
- Keep skills task-shaped, not repo-policy-shaped.
- Put durable repository truth in shared docs and `AGENTS.md`, not in a random skill.
- Keep packaged scripts and assets tightly scoped to the skill that uses them.

## Repository Impact

This feature affects:

- `docs/repository-structure.md`
- future skills placed under `skills/shared/` and `skills/local/`
- future skill discovery logic
- future adapter behavior when translating skills into harness-native concepts

It also influences future documentation:

- skill authoring guidance
- examples and templates
- local versus shared contribution expectations

## Phases

### Phase 1: Package Contract

Objective:
Define the minimum on-disk shape of a skill.

Outputs:

- skill packaging feature doc
- required and optional structure definitions
- shared/local packaging guidance

Checklist:

- [x] Define the required `SKILL.md` file.
- [x] Define allowed optional companion directories and their meanings.
- [x] Define shared versus local expectations.
- [x] Define naming expectations and minimal packaging principles.

Exit Criteria:
An implementer can create a new skill directory without inventing the structure.

### Phase 2: Authoring Guidance

Objective:
Turn the package contract into repeatable authoring guidance.

Outputs:

- updated shared structure docs
- example skill skeleton
- criteria for when to add scripts, references, assets, or agents

Checklist:

- [ ] Update shared structure docs to reflect the packaging contract once `skills/` becomes a real directory.
- [ ] Add a minimal example shared skill package.
- [ ] Add a minimal example local skill package if useful.
- [ ] Define when a simple `SKILL.md` is enough versus when a richer package is justified.

Exit Criteria:
A contributor can author a new skill consistently from repo docs alone.

### Phase 3: Runtime Integration

Objective:
Make the packaging contract consumable by future tooling.

Outputs:

- skill discovery assumptions
- loading expectations
- adapter-facing skill translation rules

Checklist:

- [ ] Define how skill discovery identifies valid skill packages.
- [ ] Define what happens when optional companion directories are absent.
- [ ] Define how adapters should consume skill packages without assuming a single harness-native format.
- [ ] Confirm that local-only skills can be ignored safely when they are absent.

Exit Criteria:
Future tooling can consume skill packages without special-casing every skill.

## Acceptance Criteria

- The repo defines a clear minimum skill package structure.
- The contract supports both simple markdown-only skills and richer packaged skills.
- The `shared` versus `local` split is preserved in skill packaging.
- The packaging model does not depend on any single harness-specific implementation.
- A future contributor can add a skill without guessing where supporting materials belong.

## Open Questions

- Should a skill package eventually include a small metadata file in addition to `SKILL.md`, or is markdown alone enough for early stages?
- Should example skill skeletons be committed now, or only once the skill index contract exists?
- How much harness-specific translation, if any, should be encoded in the package versus handled entirely by adapters?

## Follow-Up Work

- Update `docs/repository-structure.md` if the repository starts carrying real `skills/` content.
- Draft the skill index contract.
- Add one or two example skill packages once the repo is ready to demonstrate authoring patterns.
- Use this contract to guide the first runtime skill discovery implementation.
