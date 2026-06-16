# Codex Skill Sync

## Summary

Define and implement the first `sync-skills` flow for Codex. The goal is to install repo-owned skills into Codex's native skill location, preserve a native harness experience, and do so safely enough that existing user-managed skills are not silently overwritten.

## Problem

`ai-stack` currently proves skill resolution and adapter execution, but it still relies on prompt injection for external skill use. That is functional but not the intended long-term architecture.

The intended model is:

- `ai-stack` manages skills and skill metadata
- Codex discovers and loads skills natively
- a sync flow bridges the two

Without a sync contract:

- repo-owned skills have no native Codex install path
- `run-skill` remains a temporary workaround
- existing user skills could be overwritten unsafely
- repeat sync runs could behave inconsistently

## Goals

- Install repo-owned skills into Codex's native skill directory.
- Preserve a native Codex skill experience rather than inventing an `ai-stack` namespace.
- Make sync idempotent.
- Back up replaced skills safely.
- Distinguish `ai-stack`-managed skills from unknown pre-existing skills.
- Report unknown installed skills that may be candidates for import into this repo later.

## Non-Goals

- Modify `~/.codex/skills` in this design phase.
- Support every harness in the first sync implementation.
- Define a Copilot sync flow yet.
- Implement automatic import of unknown installed skills.
- Solve every skill packaging nuance before the first sync command exists.

## Proposed Design

### Target Install Location

Repo-owned skills should sync directly into Codex's native user skill directory:

- `~/.codex/skills/<skill-name>`

This preserves the native Codex experience and avoids requiring a wrapper namespace such as `ai-stack/<skill-name>`.

### Ownership Model

Each synced skill should carry a small ownership marker so later sync runs can distinguish:

- skills previously installed by `ai-stack`
- unknown pre-existing skills

The exact marker file can be decided during implementation, but it should at minimum record:

- managed-by: `ai-stack`
- source path within this repo
- sync timestamp

This marker is what makes repeat sync runs idempotent rather than ambiguous.

### Idempotency Rules

If a target skill directory already exists:

- if it is already `ai-stack`-managed:
  - update it in place if contents changed
  - do nothing if contents are unchanged
- if it is not `ai-stack`-managed:
  - treat it as an unknown collision
  - do not overwrite by default

So the only blocking collision is:

- same target skill name
- existing directory not managed by `ai-stack`

### Backup Behavior

When replacing an existing skill directory, create a backup first.

Backup location:

- `~/.codex/skills-sync-backups/`

Each sync run should create a timestamped snapshot directory or equivalent manifest-backed structure so replaced skills can be restored if needed.

Backups should be created for:

- unknown skills that the user explicitly chooses to replace
- `ai-stack`-managed skills that are about to be updated

### Backup Cleanup

Backup cleanup should be conservative.

Initial policy:

- keep recent backups by default
- prune older backups later with explicit retention rules

Recommended first retention defaults:

- keep the last 10 sync backup snapshots
- optionally prune snapshots older than 30 days
- never prune the newest backup for a given skill

This can be implemented after the first sync command exists; it does not need to block initial sync support.

### Unknown Skill Reporting

The sync flow should report unknown installed skills under `~/.codex/skills` even when they do not collide with repo-owned names.

Why:

- they may be candidates to import into this repo later
- they provide useful visibility into the current Codex environment

So sync output should distinguish:

- managed installed skills
- unknown installed skills
- managed updates
- new installs
- unknown collisions

### Execution Modes

The first sync command should support at least:

- dry-run mode
- apply mode

Dry-run should show planned actions without modifying any installed skills.

Suggested action categories:

- `install`
- `update`
- `skip`
- `remove`
- `backup-and-replace`
- `unknown-installed`
- `unknown-collision`

### Deletion Propagation

If a skill was previously installed by `ai-stack` but no longer exists under the current repo-local source tree, sync should treat it as a managed removal candidate.

Rules:

- only `ai-stack`-managed installed skills may be removed automatically
- unknown installed skills must never be removed just because they are absent from the repo source
- managed removals should be shown in dry-run output and backed up before deletion during apply mode

This makes the repo-local skill tree the source of truth for managed skills while preserving safety for unrelated user-installed skills.

### Relationship to `run-skill`

`run-skill` should be treated as a temporary bridge.

Once Codex-native sync exists and works for repo-owned skills plus the top-level index-skill pattern, `run-skill` can be deprecated and then removed.

It should not be deleted before the native sync path exists.

## Repository Impact

This feature affects:

- `ai_stack/`
- `bin/`
- tests
- config docs
- skill packaging expectations
- future removal of `run-skill`

It also intersects with:

- configuration contract
- adapter contract
- skill index contract

## Phases

### Phase 1: Sync Contract

Objective:
Document the Codex sync design and safety rules.

Outputs:

- feature doc
- target directory decision
- ownership and collision rules
- backup directory decision

Checklist:

- [x] Decide the native Codex install target.
- [x] Define `ai-stack` ownership semantics.
- [x] Define idempotent update behavior.
- [x] Define unknown collision behavior.
- [x] Define backup location.

Exit Criteria:
An implementer can build sync behavior without guessing overwrite policy.

### Phase 2: Dry-Run Implementation

Objective:
Implement discovery and reporting without mutating installed skills.

Outputs:

- `sync-skills --dry-run`
- classification of managed skills, unknown skills, and collisions
- tests for idempotent planning behavior

Checklist:

- [x] Define the source of repo-owned skills to sync.
- [x] Implement installed-skill discovery under `~/.codex/skills`.
- [x] Implement ownership detection.
- [x] Implement dry-run action reporting.
- [x] Add tests for unknown collision detection.
- [x] Define managed-skill removal planning when a repo-local skill is deleted.

Exit Criteria:
The repo can explain exactly what sync would do without modifying Codex skills.

Current source decision:

- the sync source set should include both `skills/local/<skill-name>/` and `skills/shared/<skill-name>/`
- `skills/local/` remains the place for gitignored machine-specific skills
- `skills/shared/` remains the place for committed repo-owned skills

### Phase 3: Apply Mode

Objective:
Implement safe Codex skill installation and update behavior.

Outputs:

- live sync command
- backups before replacement
- ownership marker writing
- update and skip behavior

Checklist:

- [x] Implement install of new repo-owned skills.
- [x] Implement managed update behavior.
- [x] Implement backup creation before replacement.
- [x] Implement managed-skill removal after backup when absent from source.
- [x] Block unknown collisions by default.
- [x] Add tests for idempotent second-run behavior.

Exit Criteria:
Repeated sync runs are safe and deterministic.

### Phase 4: Index-Skill Integration

Objective:
Replace prompt-injection dependence with a native top-level routing skill pattern.

Outputs:

- one native skill that instructs Codex how to use the external skill registry pattern
- updated guidance for local skill index usage
- a clear deprecation path for `run-skill`

Checklist:

- [x] Define the top-level native routing/index skill.
- [x] Decide how external skill references are surfaced from that skill.
- [ ] Validate the native experience manually with Codex.
- [ ] Deprecate `run-skill`.

Exit Criteria:
Repo-owned skill behavior can be exercised natively through Codex skill discovery.

Current Phase 4 decision:

- the top-level native router skill is `skills/shared/skill-index-router/`
- it should only be installed when the local skill index exists and contains at least one entry
- sync should bundle the current local index into the installed router skill as `references/skill-index.yaml`
- the installed router should inspect that bundled reference only when a specialized external skill may apply
- it should resolve `repo` + `path`, read the referenced external `SKILL.md`, and follow it
- absence of the bundled index reference or a matching entry is a normal no-op path

## Acceptance Criteria

- Codex sync target is clearly defined as the native `~/.codex/skills/<skill-name>` location.
- Sync behavior is idempotent for `ai-stack`-managed skills.
- Unknown collisions are blocked by default.
- Backup behavior and location are clearly defined.
- Unknown installed skills are reported.
- The design leaves room to remove `run-skill` only after native sync exists.

## Open Questions

- What exact ownership marker file should live inside synced skill directories?
- Should apply mode require an explicit force flag to replace unknown collisions after backup?
- How should repo-owned skills be discovered inside `ai-stack` once we start authoring them here?
- Should backup pruning be automatic in the first implementation or deferred?

## Follow-Up Work

- Implement `sync-skills --dry-run` first.
- Decide the ownership marker file format.
- Add Codex sync tests before touching installed skills.
- Design the native top-level routing/index skill.
- Remove `run-skill` only after native sync is working.
