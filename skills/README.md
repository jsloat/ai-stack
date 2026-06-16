# Skills

This directory holds skill packages that `ai-stack` owns.

Use:

- `skills/shared/` for committed, shareable skills that belong to the repo contract
- `skills/local/` for gitignored local-only skills that should not be committed

Minimum package shape:

- one directory per skill
- required `SKILL.md`
- optional `references/`, `scripts/`, `assets/`, or other tightly scoped support files if the skill genuinely needs them

Keep the structure lightweight. The repo-wide contract here is intentionally minimal.

If you need detailed authoring guidance, use the repo-owned `skill-creator` skill rather than expanding this README into a long style manual.
