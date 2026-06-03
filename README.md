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
- route execution through RTK as a standard part of the stack so harnesses see filtered, lower-noise command output by default
- prefer compact, typed tool surfaces for large API or MCP integrations when raw tool catalogs would overwhelm context

One explicit requirement for this repo is that it should be operable by both Codex and GitHub Copilot without maintaining two divergent documentation systems.

## Current Repository Shape

This is the current real structure. Planned future areas should stay in docs until they contain real code or user-managed assets.

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
    repository-structure.md
  skill-indexes/
    local/
  ai_stack/
  tests/
  bin/
```

## Documentation First

Feature design lives in `docs/features/`. These files are not lightweight notes. Each one should define scope, architecture, phased delivery, and completion criteria clearly enough that an engineer or agent can execute without recovering intent from chat history.

Start here:

- `README.md`
- `AGENTS.md`
- `docs/features/README.md`
- `docs/repository-structure.md`
- `docs/features/20260529-project-initialization.md`

Key design docs:

- `docs/features/20260529-configuration-contract.md`
- `docs/features/20260529-skill-packaging.md`
- `docs/features/20260529-skill-index-contract.md`
- `docs/features/20260529-eventual-repo-split.md`
- `docs/features/20260529-adapter-contract.md`

Completed implementation docs move to `docs/features/done/` so the top-level `docs/features/` directory stays focused on active work.

## Design Principles

- Prefer harness-native mechanisms such as `AGENTS.md`, instructions files, and skills over custom prompt glue.
- Keep `shared` content safe to commit and distribute.
- Keep `local` content private, environment-specific, and optional.
- Treat RTK-style command-output filtering as required execution infrastructure for supported harnesses, not as an optional local add-on.
- Treat Cloudflare Code Mode as a useful adapter pattern for large tool surfaces, not as a universal replacement for normal tool calling.
- Use workflows only when a task crosses distinct phases with different tools, models, or success criteria.
- Separate benchmark evidence from runtime telemetry. Both inform routing, but they answer different questions.

## Harness Startup Best Practice

For consumers of this repo, the preferred operating model is to start agent sessions through RTK rather than launching a harness directly.

That is a best practice, not something the repository can universally enforce for every shell or machine. The reason is simple: once an agent session is already running, the repo can shape behavior inside that session, but it cannot retroactively change how the session was launched.

So the recommended pattern is:

- launch Codex, Copilot, or future supported harnesses through RTK whenever possible
- treat raw harness startup as a fallback or compatibility path, not the preferred default
- let repo-level adapters and instructions assume RTK-mediated startup is the normal case

For code inside this repository, the rule is stronger:

- any harness process launched by `ai-stack` code should go through RTK unless a documented exemption exists

Common RTK install paths on macOS are:

- `~/.local/bin/rtk`
- `/opt/homebrew/bin/rtk`

If RTK is missing, the preferred install commands are:

- `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh`
- `brew install rtk-ai/tap/rtk`

`ai-stack` code expects `rtk` to be available on `PATH`. If RTK is installed to a standard user-local path such as `~/.local/bin` but still not found, fix the environment instead of relying on repo-local overrides.

Supported harness binaries such as `codex` are treated as prerequisites. `ai-stack` expects them to already be installed and available on `PATH`.

## Current Status

The repository now has one narrow runnable slice:

```bash
python3 bin/ai-stack resolve-skill <skill-name>
```

That slice proves optional local config discovery, local skill-index discovery, deterministic skill resolution, and structured load tracing. The broader orchestration platform is still in the early implementation phase.

The runtime also now has:

- dry-run adapter routing for `codex` and `copilot`
- a live `codex` adapter smoke path via `python3 bin/ai-stack adapter codex --prompt "Reply with OK"`
- an end-to-end skill execution path via `python3 bin/ai-stack run-skill <skill-name> --prompt "..."`
- normalized adapter result output with debug traces separated from primary result text

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

The current repository keeps only a small number of real top-level directories:

- `ai_stack/` for runtime code
- `bin/` for CLI entrypoints
- `docs/` for shared design and structure docs
- `skill-indexes/` for the current local index convention
- `tests/` for runtime tests

Planned areas such as `skills/`, `memory/`, `telemetry/`, and `model-benchmarks/` are still part of the design, but they should not exist as top-level directories until they contain real assets.

For `skill-indexes/`, the currently justified use case is local-only curation: private or global skill references that a user wants this repo to know about. Shared committed indexes should be added only if the repo later needs curated bundles of repo-owned skills.

The current intended model is one conventional local index file that points to multiple external or local-only skills. If that file exists, future tooling can incorporate it. If it does not exist, the repo should proceed without error.

From the core-vs-conventions perspective, the current live areas are:

- `ai_stack/`, `bin/`, and `tests/` for runtime behavior
- `docs/` and `.github/` for shared guidance and compatibility
- `skill-indexes/` for the current optional local registry artifact

There is currently a standardized example artifact at `skill-indexes/local/skill-index.example.md`, aligned with the current skill-index contract.
