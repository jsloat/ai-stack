# ai-stack

`ai-stack` is a harness-agnostic support layer for AI coding workflows. It provides shared instructions, global guardrails, skill sync, skill indexing, and orchestration design work around tools like Codex and GitHub Copilot.

This README is for people using and customizing the repo. Implementation and maintenance guidance for agents belongs in `AGENTS.md`.

## What This Repo Does

- keeps shareable agent behavior in versioned repo artifacts
- separates shared content from machine-local overlays
- syncs supported native skill and instruction surfaces into installed harnesses
- standardizes a small number of conventions for repo-local skills and external skill indexes
- assumes RTK-backed harness startup is the preferred operating model when supported
- keeps setup/sync utilities separate from higher-order orchestration work
- documents orchestration contracts before shipping orchestration runtime code

## Repository Paths

Paths in this document are repository-relative unless otherwise noted.

## Supported Harnesses

The repo is designed to stay harness-agnostic, but the first supported machine-global instruction targets are:

- Codex: `$HOME/.codex/AGENTS.md`
- Copilot CLI: `$HOME/.copilot/copilot-instructions.md`

The first supported native skill sync targets are:

- Codex: `$HOME/.codex/skills/`
- Copilot CLI: `$HOME/.copilot/skills/`

## Prerequisites

- install the harness you want to use, such as `codex` or Copilot CLI
- install `rtk` and make sure it is available on `PATH`
- use Python 3 to run `bin/ai-stack`

Install `rtk`:

```bash
brew install rtk-ai/tap/rtk
# or
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh
```

`ai-stack` expects supported harness binaries and `rtk` to already be available on `PATH`.

## Quick Start

### 1. Create a local config

```bash
cp config.example.yaml config.local.yaml
```

Edit `config.local.yaml` with your machine-local values. At minimum:

```yaml
defaultHarness: copilot   # or codex
repos:
  aiStack: ~/Dev/ai-stack  # absolute or ~ path to this checkout
orchestration:
  root: ~/projects          # root for orchestrated project work
```

### 2. Set up a local instruction overlay (optional)

```bash
cp global-agent-instructions/local.example.md global-agent-instructions/local.md
```

Edit `local.md` to add machine-specific preferences (personal tool guidance, workflow conventions). This file is gitignored and will be merged into the synced output alongside `shared.md`.

### 3. Sync global agent instructions

The files in `global-agent-instructions/` are the source of truth for machine-global agent behavior. They sync to:

- Codex: `~/.codex/AGENTS.md`
- Copilot CLI: `~/.copilot/copilot-instructions.md`

```bash
python3 bin/ai-stack sync-global-instructions --dry-run
python3 bin/ai-stack sync-global-instructions --apply
```

**If you see an `unknown-collision`** for a harness target: that file already exists and was not written by `ai-stack`. The sync tool will not overwrite it automatically. Options:

- **Adopt it**: If the existing file has content you want to keep, manually merge it into `global-agent-instructions/local.md`, then clear or delete the target file and re-run `--apply`. The sync will install the merged result and take ownership.
- **Replace it**: If the existing content is redundant, delete or empty the target file and re-run `--apply`.

### 4. Sync skills

Skills in `skills/shared/` and `skills/local/` sync to the harness native skill directory.

```bash
python3 bin/ai-stack sync-skills --dry-run
python3 bin/ai-stack sync-skills --apply
```

Currently targets both Codex (`~/.codex/skills/`) and Copilot CLI (`~/.copilot/skills/`). Target a specific harness with `--harness codex` or `--harness copilot`.

**If you see `unknown-collision` for a skill**: an existing unmanaged skill with the same name is in the target directory. The sync tool will not overwrite it. Either rename the existing skill directory to adopt it into the repo, or remove it and re-run.

### 5. Set up the skill index (optional)

The skill index lets you reference skills from other repositories by short ID.

```bash
cp skill-indexes/skill-index.example.yaml skill-indexes/skill-index.yaml
```

Edit `skill-index.yaml` with your local external skill registrations. This file is gitignored.

## Global Instructions

Machine-global instructions live under `global-agent-instructions/`.

Files:

- `shared.md`: tracked shared baseline
- `local.md`: optional gitignored machine-local overlay
- `local.example.md`: copyable starting point for `local.md`

These files are the source of truth for machine-global agent behavior. For Copilot CLI, this is equivalent to `~/.copilot/copilot-instructions.md` — the sync command writes there. For Codex it writes to `~/.codex/AGENTS.md`. Both are managed targets once adopted.

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

Skill sync is currently implemented for Codex (`$HOME/.codex/skills/`) and Copilot CLI (`$HOME/.copilot/skills/`).

## Skill Index

External skill references live in `skill-indexes/`.

Files:

- `skill-index.example.yaml`: tracked example
- `skill-index.yaml`: optional gitignored working file

The skill index is for repo-local curation of external or private skills that should be available to this repo’s workflows.

## Orchestration Status

Orchestration is currently documented as an active feature area, not yet a shipped CLI/runtime workflow.

Use the feature docs under `docs/features/` as the source of truth for current orchestration design work.

## Useful Commands

Resolve a skill identifier through the configured skill index:

```bash
python3 bin/ai-stack resolve-skill pull-request
```

Smoke-test the Codex adapter:

```bash
python3 bin/ai-stack adapter codex --prompt "Reply with OK"
```

## Migrating from an Existing Setup

If you already have skills, global instructions, or agent configuration on this machine before setting up `ai-stack`, use this section to migrate safely.

### Pre-existing global instructions

If `~/.copilot/copilot-instructions.md` or `~/.codex/AGENTS.md` already exist with content you want to keep:

1. Review what's in the existing file.
2. Move any machine-local preferences into `global-agent-instructions/local.md`.
3. Verify that `global-agent-instructions/shared.md` covers anything that should be shared.
4. Clear or delete the target file.
5. Run `python3 bin/ai-stack sync-global-instructions --apply`.

The sync will take ownership and write the merged result.

### Pre-existing skills

If you have skills in `~/.copilot/skills/` or `~/.codex/skills/` that you want `ai-stack` to own going forward:

- Skills you authored and want to keep: copy them into `skills/shared/` or `skills/local/` as appropriate, then run `sync-skills --apply`. The sync will detect the new installs.
- Skills you don't want to migrate: leave them in place — the sync tool treats unmanaged skills as `unknown-collision` and will not touch them.
- Skills that are older versions of something now in this repo: remove or rename the old installed version first to clear the collision, then run `sync-skills --apply`.

### Skill index

If you have an existing skill registry in a harness skill (e.g., `~/.copilot/skills/skill-index/SKILL.md`), migrate those entries into `skill-indexes/skill-index.yaml`. The `skill-index.yaml` file is machine-local (gitignored) and is the canonical source for external skill resolution via `resolve-skill`.

### Projects directory

The `orchestration.root` config key points to the directory where `ai-stack orchestrate` stores project work. If that directory already contains plan files from another workflow (for example, flat Markdown files used by a cascade-worker or similar execution harness), those are safe to leave in place — `ai-stack orchestrate` creates dated subdirectories per project and will not conflict with existing flat files. Once the orchestration CLI is shipped, migrating old plans to the new format is optional and can be done project by project.

## Documentation Layout

Use these files for the right job:

- `README.md`: user/operator guidance
- `AGENTS.md`: agent implementation guidance
- `docs/ideas/`: speculative ideas and deferred concepts that are not active backlog yet
- `docs/features/README.md`: feature-doc contract
- `docs/repository-structure.md`: top-level structure rules

Feature docs in `docs/features/` are the active backlog and design layer. Once behavior becomes settled repo policy, it should be reflected in README-style docs instead of living only in feature plans.
