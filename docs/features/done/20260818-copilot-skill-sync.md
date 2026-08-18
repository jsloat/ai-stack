# Copilot Skill Sync

## Summary

Extend `sync-skills` to support Copilot CLI's native skill directory (`~/.copilot/skills/`) with the same semantics already implemented for Codex.

## Problem

`skill_sync.py` was written with Codex as the only target. It hardcodes `~/.codex/skills/` as the install root and uses a Codex-only backup path. Copilot CLI has an equivalent native skill directory at `~/.copilot/skills/`, but the sync command has no knowledge of it.

This means:
- skill sync only benefits Codex users
- Copilot users must manage `~/.copilot/skills/` manually
- feature parity between harnesses is broken from the first real use

The principle that feature parity across supported harnesses is always expected makes this a gap to close, not a deferred nice-to-have.

## Goals

- Extend `sync-skills` to install repo-owned skills into `~/.copilot/skills/` when Copilot is a target harness.
- Reuse the existing ownership marker, install, update, remove, backup, and collision logic.
- Support targeting a single harness (`--harness copilot`, `--harness codex`) or all at once (default).
- Keep Codex behavior unchanged.

## Non-Goals

- Change the skill format or SKILL.md contract.
- Support harnesses beyond Codex and Copilot in this phase.
- Reconcile the `superpowers-skills` directory (`~/.copilot/superpowers-skills/`) — that is a separate surface managed by the Copilot runtime, not user-owned.

## Proposed Design

### Target Install Location

Copilot native user skill directory:

```
~/.copilot/skills/<skill-name>/
```

This mirrors the Codex convention exactly.

### Harness Dispatch

`build_sync_plan` and `apply_sync_plan` should accept an optional `harness` argument (defaulting to `"all"`) consistent with how `agent_sync.py` works:

- `"all"` — sync to all supported harnesses
- `"codex"` — sync only to `~/.codex/skills/`
- `"copilot"` — sync only to `~/.copilot/skills/`

The CLI `--harness` flag should be added to the `sync-skills` command to expose this.

### Backup Root

Copilot backups should go to a separate path to avoid mixing with Codex backups:

- Codex: `~/.codex/skills-sync-backups/<timestamp>/`
- Copilot: `~/.copilot/skills-sync-backups/<timestamp>/`

Or use a shared location under `~/.ai-stack/skills-sync-backups/<harness>/<timestamp>/` — consistent with the agent sync backup location.

### Marker File

Reuse the same `.ai-stack-skill.json` marker, already defined in `skill_sync.py`.

### Output Format

The plan/result JSON should include which harness each action targets, consistent with how `agent_sync.py` structures its output.

## Repository Impact

- `ai_stack/skill_sync.py`: primary change — add multi-harness dispatch, Copilot target dir, harness-scoped backup paths
- `ai_stack/resolve_skill.py`: add `--harness` flag to `sync-skills` subcommand
- `README.md`: update Supported Harnesses section once implemented
- `docs/features/done/20260603-codex-skill-sync.md`: no changes needed; this doc extends that work

## Phases

### Phase 1: Refactor and Generalize
Objective: Separate the Codex-specific install root from the core sync logic.

Outputs:
- `codex_user_skills_dir()` generalized to `user_skills_dir(harness: str) -> Path`
- `BACKUP_ROOT` generalized to be harness-scoped
- `build_sync_plan` and `apply_sync_plan` accept `harness: str = "all"`
- Codex behavior is unchanged

Checklist:
- [ ] Add `user_skills_dir(harness)` function returning the right path per harness
- [ ] Add `backup_root_for_harness(harness)` or use a shared `~/.ai-stack/skills-sync-backups/<harness>/` path
- [ ] Refactor `build_sync_plan` to iterate over target harnesses
- [ ] Refactor `apply_sync_plan` to match
- [ ] All existing Codex tests still pass

Exit Criteria: `sync-skills --dry-run` produces the same Codex output as before; plan structure includes harness field per action.

### Phase 2: Copilot Target
Objective: Add `~/.copilot/skills/` as a real sync target.

Outputs:
- Copilot actions appear in dry-run output
- `--apply` installs, updates, and removes skills in `~/.copilot/skills/` with markers
- Collision detection works for pre-existing unmanaged Copilot skills

Checklist:
- [ ] `user_skills_dir("copilot")` returns `~/.copilot/skills/`
- [ ] `sync-skills --dry-run` shows actions for both Codex and Copilot by default
- [ ] `sync-skills --dry-run --harness copilot` shows only Copilot actions
- [ ] `sync-skills --apply` installs to both harnesses
- [ ] Unmanaged pre-existing Copilot skills are reported as `unknown-collision`, not overwritten
- [ ] Markers written to Copilot skill directories

Exit Criteria: A skill in `skills/shared/` can be installed into `~/.copilot/skills/` via `sync-skills --apply --harness copilot`.

### Phase 3: CLI Flag and Docs
Objective: Surface `--harness` flag and update documentation.

Outputs:
- `sync-skills --harness <copilot|codex|all>` accepted
- README Supported Harnesses section updated
- README Quick Start updated to mention `--harness` option

Checklist:
- [ ] `--harness` flag added to `sync-skills` subcommand in `resolve_skill.py`
- [ ] README updated
- [ ] Feature doc moved to `done/`

Exit Criteria: A new machine can run `sync-skills --apply --harness copilot` and get skills installed without knowing about Codex.

## Acceptance Criteria

- `sync-skills` with no flags syncs to all supported harnesses (Codex and Copilot).
- `sync-skills --harness copilot` syncs only to `~/.copilot/skills/`.
- Pre-existing unmanaged Copilot skills are never silently overwritten.
- Codex sync behavior is unchanged.
- A contributor can confirm feature parity from the README alone.

## Open Questions

- Should the shared backup root be `~/.ai-stack/skills-sync-backups/<harness>/` (consistent with agent sync) or keep per-harness roots (`~/.codex/`, `~/.copilot/`)? Recommend the shared `~/.ai-stack/` path for consistency.

## Follow-Up Work

- Migration guide for users who have unmanaged skills in `~/.copilot/skills/` that should be adopted into the repo (run sync, observe `unknown-collision` entries, decide whether to import or leave unmanaged).
