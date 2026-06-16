---
name: skill-index-router
description: Consult the synced external skill index when a task may benefit from a specialized skill that is not already installed natively. Use when the user requests a workflow that sounds domain-specific, organization-specific, or tool-specific and the relevant guidance may live in the router's bundled index reference.
---

# Skill Index Router

Use the synced skill index reference to find and load external skills that are not shipped directly as native installed skills.

When this skill is installed by `ai-stack`, it may include a bundled reference file at:

- `references/skill-index.yaml`

If that reference file is absent, continue normally.

## When to use this skill

Use this skill when:

- the task sounds specialized and may rely on a local-only or external skill
- the user references a workflow that is likely captured outside the repo's shared installed skills
- you suspect a private, machine-local, or externally stored skill may apply

Do not use this skill for every trivial request. Use it when there is a plausible specialized skill to route to.

## What the index contains

The local index is a small YAML registry with entries like:

- `id`
- `when`
- `repo`
- `path`

The router's job is to:

1. inspect the index if it exists
2. identify whether any entry plausibly matches the current task
3. read the referenced external `SKILL.md` when a match is found
4. follow that external skill's guidance

## Routing workflow

1. Check whether `references/skill-index.yaml` exists.
2. If it does not exist, stop and continue normally.
3. Read the skill entries and compare their `when` descriptions to the user's task.
4. If no entry matches clearly, stop and continue normally.
5. If one entry matches:
   - resolve `repo` and `path`
   - read the referenced `SKILL.md`
   - follow that skill
6. If multiple entries seem relevant:
   - pick the narrowest/best match
   - if the ambiguity matters materially, tell the user which one you chose

## Safety and boundaries

- Do not assume the index exists.
- Do not assume the referenced repo or `SKILL.md` exists.
- If the referenced skill cannot be read, say so briefly and continue with the best fallback.
- Do not mutate the local index unless the user asks.
- Do not invent routing entries that are not present in the file.

## Freshness

Some external skills may live in repos that the user updates independently.

This skill does not require you to auto-update those repos. If the referenced skill exists, use it. If the user has a preferred repo-refresh workflow, they can ask for it explicitly.

## Output behavior

When you route to an external skill:

- say briefly which skill you selected
- then follow it

When no route is found:

- do not make the absence of a matching external skill a blocker
- proceed with normal repo and harness guidance
