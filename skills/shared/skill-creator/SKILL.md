---
name: skill-creator
description: Create or improve agent skills. Use when defining a new SKILL.md-style skill, restructuring an existing skill, tightening trigger descriptions, deciding what belongs in SKILL.md vs references/scripts/assets, or validating whether a skill is lean, reusable, and likely to trigger correctly.
---

# Skill Creator

Create compact, reusable skills for AI agents.

Skills should add context the agent does not already have:

- brittle command syntax
- trigger guidance
- non-obvious workflow steps
- domain-specific constraints
- reusable scripts, references, and templates

Do not bloat the skill with generic advice the model already knows.

## Core rules

1. Keep `SKILL.md` lean.
2. Put trigger-critical information in frontmatter `description`.
3. Put all "when to use this" guidance in `description`, not the body.
4. Move long or variant-specific material to `references/`.
5. Put deterministic, repeated logic in `scripts/`.
6. Put templates or output resources in `assets/`.
7. Do not create extra docs unless they directly help the future agent do the work.
8. Validate frontmatter and test any scripts you add.

## Skill shape

```text
skill-name/
  SKILL.md
  references/   optional docs loaded when needed
  scripts/      optional deterministic helpers
  assets/       optional templates or output resources
```

## Description guidance

The frontmatter `description` is the primary trigger surface.

A good default pattern:

- sentence 1: what the skill does
- sentence 2: when to use it, including likely user phrasings or adjacent intents

Good descriptions are specific enough to trigger reliably, but not padded with unnecessary prose.

## Workflow

### 1. Understand the intended skill

Figure out:

- what the skill should enable
- what kinds of prompts should trigger it
- what outputs or behavior matter
- what edge cases or boundaries matter

If the current conversation already contains a workflow worth turning into a skill, extract as much as you can before asking more questions.

### 2. Plan reusable contents

Before writing the final `SKILL.md`, decide what should become reusable artifacts.

Ask:

- what logic would be repeated every time
- what information would be looked up repeatedly
- what scaffolding or templates would be recreated repeatedly

Use:

- `scripts/` for repeated deterministic work
- `references/` for detailed documentation or variant-specific guidance
- `assets/` for templates, sample outputs, or reusable resources

### 3. Draft the skill

Write:

- `name`
- `description`
- the smallest useful body
- only the support files the skill actually needs

Prefer operational guidance over explanation. Keep only information that will materially improve future agent behavior.

## Writing guidance

- Use imperative or direct instructional phrasing.
- Prefer bullets over long exposition.
- Keep examples short and task-relevant.
- Do not duplicate detailed content across `SKILL.md` and `references/`.
- If a skill supports multiple variants, keep the selection logic in `SKILL.md` and move variant detail to references.

## Validation

After drafting or editing the skill:

1. Validate YAML/frontmatter.
2. Check the folder shape and naming.
3. Test any added or modified scripts.
4. Re-read the skill and remove anything generic, redundant, or non-reusable.

## Lightweight evaluation

Do not declare the skill done until you have run a minimum evaluation pass.

Minimum required evaluation:

1. Create 2-5 realistic test prompts.
2. Include both:
   - prompts that should trigger the skill
   - near-miss prompts that should not trigger the skill
3. Ask the user to run those prompts in fresh sessions and report whether the skill triggered.
4. Ask the user to run at least one safe, realistic task prompt and report whether the skill improved execution.
5. Revise the skill based on what failed, then rerun the same prompts.

Focus on two separate questions:

- does the skill trigger when it should
- does the skill help execution when it does trigger

## Evaluation protocol

By default, evaluation is user-run and author-guided.

The skill authoring agent should:

1. prepare the test prompts
2. tell the user exactly how to run them
3. ask the user to report what happened
4. revise the skill based on those results

## Trigger testing

When testing triggering:

- use realistic prompts, not toy prompts
- include near-miss negatives, not only obviously irrelevant negatives
- refine the description if the skill under-triggers or over-triggers

Do not rely on keyword matching alone. The description should capture both capability and context.

### Trigger check

Have the user run the trigger check in fresh sessions that have access to the candidate skill and do not already contain the drafting context.

Give the user instructions like:

1. Start a new session.
2. Paste one test prompt exactly as written.
3. Observe whether the agent uses the skill.
4. Report back in a simple format like:
   - `<prompt 1>: triggered`
   - `<prompt 2>: did not trigger`
5. Repeat for the remaining prompts.

Do not evaluate triggering in the same conversation where the skill was authored. That contaminates the result.

### Execution check

Have the user run at least one realistic should-trigger task in a fresh session and report the result.

The authoring agent should give the user:

- one concrete task prompt
- what success looks like
- what failure modes to watch for

Prefer a reversible, sandboxed, read-only, staged, or otherwise safe task.

Do not ask the user to test against production systems, irreversible operations, or privileged side effects unless they explicitly choose to do that and understand the risk.

If the skill commonly affects live state, evaluate it using one of these instead:

- a dry run
- a staging environment
- a mock or sample dataset
- a plan/review task that checks whether the agent would take the correct actions

Execution should be judged with concrete questions like:

- did the agent follow the intended workflow
- did it use the bundled scripts, references, or assets appropriately
- did the result avoid the errors the skill was meant to prevent
- did the skill make the output more correct, complete, or reusable
- did the skill reduce obvious wasted effort or repeated rediscovery

If neither the authoring agent nor the user can state what success and failure look like, the skill is still under-specified.

## Keep the shipped artifact small

A rigorous authoring process is good.

The final runtime-loaded skill should still be compact:

- keep the main body short
- move heavy detail into references
- keep only reusable, non-obvious guidance
- avoid shipping your full authoring process inside the skill

## Optional advanced work

These are optional additions for larger or more correctness-sensitive skills.

Examples:

- a larger trigger eval set with more positive and negative cases
- lightweight assertions for objective tasks
- formal side-by-side baseline comparison
- multiple revision rounds using the same test set

Do not assume subagents, browser tooling, or harness-specific evaluation infrastructure.

## Review checklist

- Does the `description` clearly say what the skill does and when to use it?
- Is `SKILL.md` lean?
- Did long detail move into `references/`?
- Did repeated deterministic work move into `scripts/`?
- Did you avoid extra non-functional docs?
- Did you test at least a few realistic prompts?
- Did you check both triggering and execution quality?
