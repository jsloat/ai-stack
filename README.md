# ai-stack

`ai-stack` is a harness-agnostic support layer for AI coding workflows. It provides shared instructions, global guardrails, skill sync, skill indexing, and lightweight orchestration around tools like Codex and GitHub Copilot.

This README is for people using and customizing the repo. Implementation and maintenance guidance for agents belongs in `AGENTS.md`.

## What This Repo Does

- keeps shareable agent behavior in versioned repo artifacts
- separates shared content from machine-local overlays
- syncs supported native skill and instruction surfaces into installed harnesses
- standardizes a small number of conventions for repo-local skills and external skill indexes
- assumes RTK-backed harness startup is the preferred operating model when supported
- keeps setup/sync utilities separate from higher-order orchestration work

## Repository Paths

Paths in this document are repository-relative unless otherwise noted.

## Supported Harnesses

The repo is designed to stay harness-agnostic, but the first supported machine-global instruction targets are:

- Codex: `$HOME/.codex/AGENTS.md`
- Copilot CLI: `$HOME/.copilot/copilot-instructions.md`

The first supported native skill sync target is:

- Codex: `$HOME/.codex/skills/`

## Prerequisites

- install the harness you want to use, such as `codex` or Copilot CLI
- install `rtk` and make sure it is available on `PATH`
- use Python 3 to run `bin/ai-stack`

Preferred RTK install commands:

- `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh`
- `brew install rtk-ai/tap/rtk`

`ai-stack` expects supported harness binaries and `rtk` to already be available on `PATH`.

## Quick Start

1. Copy `config.example.yaml` to `config.local.yaml`.
2. Adjust local preferences in `config.local.yaml`.
3. Review `global-agent-instructions/shared.md`.
4. Optionally copy `global-agent-instructions/local.example.md` to `global-agent-instructions/local.md` and customize it.
5. Dry-run global instruction sync:

```bash
python3 bin/ai-stack sync-global-instructions --dry-run
```

6. Apply global instruction sync:

```bash
python3 bin/ai-stack sync-global-instructions --apply
```

7. Dry-run skill sync:

```bash
python3 bin/ai-stack sync-skills --dry-run
```

8. Apply skill sync when the plan looks correct:

```bash
python3 bin/ai-stack sync-skills --apply
```

## Global Instructions

Machine-global instructions live under `global-agent-instructions/`.

Files:

- `shared.md`: tracked shared baseline
- `local.md`: optional gitignored machine-local overlay
- `local.example.md`: copyable starting point for `local.md`

The shared baseline currently installs explicit Git safety rules, including:

- no commit, push, or PR creation/update without explicit user confirmation
- no destructive Git operations without explicit user confirmation

Use:

```bash
python3 bin/ai-stack sync-global-instructions --dry-run
python3 bin/ai-stack sync-global-instructions --apply
```

Optional harness targeting:

```bash
python3 bin/ai-stack sync-global-instructions --dry-run --harness codex
python3 bin/ai-stack sync-global-instructions --apply --harness copilot
```

The sync is conservative:

- managed targets are updated in place
- unmanaged non-empty targets are treated as collisions and are not overwritten
- empty targets are adoptable
- managed updates are backed up before replacement

## Skills

Repo skills live under `skills/`.

- `skills/shared/`: tracked, shareable skills
- `skills/local/`: gitignored machine-local skills

Use:

```bash
python3 bin/ai-stack sync-skills --dry-run
python3 bin/ai-stack sync-skills --apply
```

Skill sync is currently implemented for Codex’s native skill directory.

## Skill Index

External skill references live in `skill-indexes/`.

Files:

- `skill-index.example.yaml`: tracked example
- `skill-index.yaml`: optional gitignored working file

The skill index is for repo-local curation of external or private skills that should be available to this repo’s workflows.

## Useful Commands

Resolve a skill identifier through the configured skill index:

```bash
python3 bin/ai-stack resolve-skill pull-request
```

Smoke-test the Codex adapter:

```bash
python3 bin/ai-stack adapter codex --prompt "Reply with OK"
```

## Documentation Layout

Use these files for the right job:

- `README.md`: user/operator guidance
- `AGENTS.md`: agent implementation guidance
- `docs/features/README.md`: feature-doc contract
- `docs/repository-structure.md`: top-level structure rules

Feature docs in `docs/features/` are the active backlog and design layer. Once behavior becomes settled repo policy, it should be reflected in README-style docs instead of living only in feature plans.
