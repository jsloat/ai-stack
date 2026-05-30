# ai-stack

`ai-stack` is a harness-agnostic backbone for AI coding workflows. The project is intended to sit above tools like Codex, Copilot CLI, OpenCode, and similar agents, and provide the infrastructure they usually lack: shared instructions, curated skills, task routing, benchmark data, telemetry, and repeatable workflow definitions.

The repository is currently in the initialization phase. The first artifacts are design and operating docs that define how the project should grow before implementation hardens around the wrong shape.

## Core Idea

Treat AI coding as an operations problem, not just a prompt problem.

The long-term platform direction is:

- route work to the right harness, model, and skill set
- keep reusable context in stable, versioned project artifacts
- separate sharable project assets from private local additions
- measure model and workflow performance with both benchmarks and telemetry
- make multi-phase workflows explicit instead of burying them inside ad hoc prompts

One explicit requirement for this repo is that it should be operable by both Codex and GitHub Copilot without maintaining two divergent documentation systems.

## Expected Repository Shape

This is the current intended structure, not yet a full implementation contract:

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

## Documentation First

Feature design lives in `docs/features/`. These files are not lightweight notes. Each one should define scope, architecture, phased delivery, and completion criteria clearly enough that an engineer or agent can execute without recovering intent from chat history.

Start here:

- `README.md`
- `AGENTS.md`
- `docs/features/README.md`
- `docs/features/20260529-project-initialization.md`

## Design Principles

- Prefer harness-native mechanisms such as `AGENTS.md`, instructions files, and skills over custom prompt glue.
- Keep `shared` content safe to commit and distribute.
- Keep `local` content private, environment-specific, and optional.
- Use workflows only when a task crosses distinct phases with different tools, models, or success criteria.
- Separate benchmark evidence from runtime telemetry. Both inform routing, but they answer different questions.

## Current Status

There is not yet a runnable implementation in this repository. The repo currently defines the intended operating model and initial project structure so later code can follow a stable contract.

## Agent Guidance

This repository uses a simple documentation split:

- `README.md` is the human-facing repo summary
- `docs/features/*.md` hold durable design and implementation planning
- `AGENTS.md` is the primary agent operating guide
- `.github/copilot-instructions.md` is a thin Copilot compatibility layer

New durable rules should go in shared docs first. New agent workflow guidance should go in `AGENTS.md`.

Feature docs should be treated as active backlog artifacts, not archival notes. Incomplete phases, unchecked checklist items, and unresolved open questions in `docs/features/*.md` should stay visible and inform what happens next.

## Config Bootstrap

The repository currently provides a committed template at `config.example.yaml`.

Expected flow:

1. Copy `config.example.yaml` to `config.local.yaml`
2. Fill in local preferences and environment-specific values
3. Keep `config.local.yaml` untracked

The example config should stay focused on real behavioral choices. Repo-owned paths and layout should remain hardcoded until there is a concrete need for relocation or external sources.

## Current Scaffold

The repository now includes the first structural pass for:

- `skills/` and `skill-indexes/`
- `adapters/`
- `model-benchmarks/`
- `telemetry/`
- `memory/`
- `tests/`
- `agents/`, `templates/`, `dashboard/`, and `bin/`

At this stage these directories mainly establish boundaries and naming. Most still need executable contracts.

For `skill-indexes/`, the currently justified use case is local-only curation: private or global skill references that a user wants this repo to know about. Shared committed indexes should be added only if the repo later needs curated bundles of repo-owned skills.

The current intended model is one conventional local index file that points to multiple external or local-only skills. If that file exists, future tooling can incorporate it. If it does not exist, the repo should proceed without error.

There is currently a standardized example artifact at `skill-indexes/local/skill-index.example.md`, but the exact runtime index contract is still intentionally narrow and may be refined in a dedicated skill-index feature doc.
