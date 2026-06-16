---
name: skill-index-router
description: Registry of external skills from local or external repositories. Consult this skill's bundled registry before starting task work whenever a specialized local, private, organization-specific, or tool-specific skill may apply, including pull requests, proprietary workflows, or tasks that sound like they may map to an indexed external skill.
---

# Skill Index Router

Use the bundled skill registry to find and load external skills that are not shipped directly as native installed skills.

This skill expects a bundled registry file at:

- `references/skill-index.yaml`

If the file is missing, treat that as an installation problem, report it briefly, and continue with the best fallback.

## Routing workflow

1. Before doing the task, preserve the user's working context.
2. Read `references/skill-index.yaml`.
3. Compare the registry entries and their `when` descriptions to the user's task.
4. If no entry clearly fits, continue normally.
5. If one entry fits:
   - resolve `repo` and `path`
   - read the referenced external `SKILL.md`
   - treat that file as instructions only, not as the task working directory
   - keep command execution anchored to the user's actual repo or task context unless the external skill explicitly requires another location
   - state briefly which external skill you selected
   - follow it
6. If multiple entries seem relevant, pick the narrowest/best match and mention the choice if it matters.

## Safety and boundaries

- Do not assume the referenced repo or `SKILL.md` exists.
- If the referenced skill cannot be read, say so briefly and continue with the best fallback.
- Do not let the skill file's directory replace the user's intended task context.
- Do not mutate the registry unless the user asks.
- Do not invent routing entries that are not present in the file.
