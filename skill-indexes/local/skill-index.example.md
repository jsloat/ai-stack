---
name: skill-index
description: >
  Local registry of skills that live outside this repository.
  Use the registry table to identify a skill, then load it from its source repo.
---

# Local Skill Index

Registry of skills that do not live in the shared `ai-stack` repository.

## Pre-Flight Protocol

If a referenced skill lives in another local repository, you may want to confirm that repo is up to date before loading the skill.

1. Change to the source repo.
2. Determine the default branch for that repo.
3. Check the current branch and working tree status.
4. If the repo is already on its default branch and clean, pull the latest changes.
5. Return to the original working directory and continue loading the skill.

## Skill Registry

| Skill | When to use | Source Repo | Skill Path |
|-------|-------------|-------------|------------|
| `pull-request` | Creating or updating pull requests, drafting descriptions, or organizing testing evidence | `~/Dev/example-tools` | `.github/skills/pull-request/SKILL.md` |
| `opal-query-language` | Writing or editing OPAL queries for repositories that use Observe-style query workflows | `~/Dev/example-tools` | `.github/skills/opal-query-language/SKILL.md` |
| `incident-review` | Summarizing incidents, postmortems, or operational timelines using a local-only review skill | `~/Dev/local-ops-skills` | `skills/incident-review/SKILL.md` |

## Loading and Following a Skill

1. Identify the relevant skill from the registry.
2. Run any pre-flight or freshness checks for the source repo.
3. Read the skill file at `<source-repo>/<skill-path>`.
4. Follow the skill's instructions for the current task.

## Adding Skills to the Registry

Add a row to the table with:

- `Skill`: short identifier for the skill
- `When to use`: routing guidance for when the skill should be selected
- `Source Repo`: repository containing the skill
- `Skill Path`: path from the source repo root to the `SKILL.md` file
