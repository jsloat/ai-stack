# Skill Authoring Router Evaluation Prompts

Use these prompts in fresh sessions to check whether the router skill triggers when it should.

## Should Trigger

1. `Turn the workflow from this chat into a new skill.`
2. `Update the skill that handles backlog handoffs so its trigger description is tighter.`
3. `Restructure this skill so the long instructions move into references/ and keep SKILL.md lean.`

## Should Not Trigger

1. `How do Codex skills work in this repo?`
2. `Sync my installed skills and show me the dry-run plan.`
3. `Use the existing task-processor skill to clean up my Todoist inbox.`

## Execution Check

Use this prompt in a fresh session after configuring `repos.aiStack`:

`Create a new shared skill for converting recurring chat cleanup workflows into reusable instructions.`

Success looks like:

- the agent routes the work into `ai-stack` without asking for the repo path
- the agent treats the request as skill authoring rather than generic repo editing
- the agent then follows `skill-creator` style guidance for the actual skill contents
