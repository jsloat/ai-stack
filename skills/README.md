# Skills

This directory holds skill packages that `ai-stack` owns.

Use:

- `skills/shared/` for committed, shareable skills that belong to the repo contract
- `skills/local/` for gitignored local-only skills that should not be committed

Minimum package shape:

- one directory per skill
- required `SKILL.md`
- optional `references/`, `scripts/`, `assets/`, or other tightly scoped support files if the skill genuinely needs them

Runtime expectations:

- a valid skill package is a directory containing `SKILL.md`
- missing optional companion directories are normal
- absent `skills/local/` content should be ignored cleanly
- harness-specific translation belongs in adapters or harness-native sync logic, not in required package metadata

Keep the structure lightweight. Prefer a single `SKILL.md` unless the skill clearly needs packaged references, scripts, or assets.

If you need detailed authoring guidance, use the repo-owned `skill-creator` skill rather than expanding this README into a long style manual.
