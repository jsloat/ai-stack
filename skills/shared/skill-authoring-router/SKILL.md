---
name: skill-authoring-router
description: Route skill authoring, skill update, and global agent instruction update requests into the configured ai-stack repo. Use when the user asks to create, update, refine, or restructure a skill, or to update the global agent instructions, and does not clearly name another target repo, especially mid-chat in a different repository.
---

# Skill Authoring Router

Route skill-authoring work and global instruction edits into the configured `ai-stack` checkout before doing the actual work.

Use this skill to decide target repo and workflow ownership.

Use `skill-creator` for the actual skill design and editing once routing is settled. Global instruction edits are made directly — no `skill-creator` handoff needed.

## Routing workflow

1. Preserve the user's actual request.
2. Check whether the user explicitly named a target repo or explicitly said not to use `ai-stack`.
3. If the user explicitly named another repo, do not redirect to `ai-stack`.
4. Otherwise, treat the request as defaulting to the configured `repos.aiStack` checkout.
5. If `repos.aiStack` is missing, invalid, or unavailable, ask one narrow question instead of guessing.
6. Once the target repo is established:
   - For skill work: perform the work in that repo's `skills/` tree, then hand off to `skill-creator`.
   - For global instructions: edit `global-agent-instructions/shared.md` directly, then run `ai sync-global-instructions --apply` to push to harness targets.

## Trigger examples

This skill should usually apply to prompts like:

- make this into a skill
- create a skill for this workflow
- update the skill we discussed earlier
- tighten the trigger behavior for that skill
- restructure this skill's `SKILL.md` and references
- update the global instructions
- add a rule to the global agent instructions
- the global instructions should say X

This skill should usually not apply to prompts that only:

- ask how skills work in general
- ask to sync or install existing skills or instructions
- ask to use a skill rather than author one

## Boundaries

- Do not invent repo discovery logic beyond the configured `repos.aiStack` path.
- Do not override an explicit user repo choice.
- Do not guess from nearby directories when config is missing.
- Do not replace `skill-creator` for skill work; this skill only handles routing and handoff.
- Do not use `skill-creator` for global instruction edits; edit the shared source directly.
