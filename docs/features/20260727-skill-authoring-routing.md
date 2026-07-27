# Skill Authoring Routing

## Summary

Define a cross-machine way for `ai-stack` to intercept skill-authoring requests and route them into the correct `ai-stack` checkout without requiring the user to restate the repo path in every chat.

## Problem

The repo already defines how skills are packaged and synced, but it does not yet define how an agent should recognize "create or update a skill" as work that belongs in the `ai-stack` repo.

That gap creates repeated friction:

- users must restate the `ai-stack` repo path in the middle of unrelated chats
- skill-authoring requests are not consistently redirected into the repo that owns the skill workflow
- cross-machine setup is unclear because the routing behavior is shared but the actual checkout path is machine-local

Without an explicit contract:

- agents will handle the same request differently across sessions
- local machine paths will leak into ad hoc prompt habits instead of config
- future routing skills or instruction sync will invent their own detection rules

## Goals

- Define one machine-local config field that identifies the `ai-stack` checkout path.
- Define shared routing behavior for skill-authoring requests.
- Make the default behavior work across machines without committing private paths.
- Keep the contract simple enough to support both instruction-based routing and a future repo-owned routing skill.

## Non-Goals

- Implement the full runtime loader or config parser in this doc.
- Finalize every future repo-routing use case beyond skill authoring.
- Replace explicit user overrides when the user names a different target repo.
- Define a generic multi-repo workspace registry.

## Proposed Design

### Config Field

Add one machine-local config field:

```yaml
repos:
  aiStack: /path/to/ai-stack
```

Rules:

- `repos.aiStack` is the canonical configured checkout path for `ai-stack`.
- it should be set in `config.local.yaml`
- `config.example.yaml` should show the field with a commented example, not a real path
- the field may point to any local checkout location on a given machine

This is a justified exception to the earlier bias against configurable repo-owned paths.

The path is not making internal repo structure configurable. It only tells shared routing behavior where the owning repo checkout exists on the current machine.

### Routing Trigger

Shared agent behavior should treat requests like these as skill-authoring intents unless the user clearly specifies a different target:

- create a new skill
- update an existing skill
- turn this workflow into a skill
- tighten the trigger behavior for that skill
- restructure a skill's `SKILL.md`, `references/`, `scripts/`, or `assets/`

The routing behavior should activate both when the user says "skill" explicitly and when the request is unambiguously about authoring or refining a repo-owned skill artifact.

### Default Routing Rule

When a skill-authoring intent is detected and the user does not name another repo:

1. resolve `repos.aiStack`
2. treat that repo as the default working repo for the task
3. perform skill edits in that repo's `skills/` tree
4. continue using normal shared versus local skill rules inside that repo

The key split is:

- config answers where `ai-stack` is on this machine
- shared instructions or a shared routing skill answer when skill requests should be redirected there

### User Override Rule

If the user explicitly names a different target repo or says not to use `ai-stack`, that explicit instruction wins.

The default should only apply when the repo target is omitted.

### Failure And Fallback Behavior

If `repos.aiStack` is missing:

- do not guess from unrelated directories
- ask the user to configure the repo path or name the target repo explicitly

If `repos.aiStack` is set but does not exist:

- report that the configured path is unavailable
- ask for correction or explicit override

If the request is ambiguous about whether it is actually skill authoring:

- do not forcibly redirect
- ask a narrow clarification question

### Shared Routing Surface

This contract should be consumable by two shared surfaces:

- global instructions that tell the agent to route skill-authoring requests into `repos.aiStack` by default
- a future shared routing or repo-maintenance skill that handles the detailed workflow once the intent is detected

The routing skill should not invent its own repo-discovery logic. It should consume the configured path.

## Repository Impact

This feature affects:

- `config.example.yaml`
- future config loading and validation code
- global instruction rendering
- shared routing skill design
- skill authoring workflow docs

It also updates the prior configuration stance:

- a machine-local repo checkout path is now a justified configurable concern when shared routing behavior needs to cross repo boundaries

## Phases

### Phase 1: Contract Definition
Objective:
Define the minimal configuration and routing behavior.

Outputs:

- feature doc
- config field contract
- routing trigger contract

Checklist:
- [x] Define the machine-local `repos.aiStack` field.
- [x] Define when skill-authoring routing should trigger.
- [x] Define explicit user override behavior.
- [x] Define failure behavior for missing or invalid config.

Exit Criteria:
An implementer can add the config field and shared routing logic without inventing the behavior.

### Phase 2: Config And Instruction Integration
Objective:
Apply the contract to shared config and instruction surfaces.

Outputs:

- updated `config.example.yaml`
- updated global instruction templates or sync inputs
- validation rules for `repos.aiStack`

Checklist:
- [x] Add the commented `repos.aiStack` example to `config.example.yaml`.
- [x] Define config validation for missing, malformed, or nonexistent `repos.aiStack` values.
- [x] Update shared instruction sources to route skill-authoring requests by default.

Exit Criteria:
A machine can be configured once and then reuse the same routing behavior in future sessions.

### Phase 3: Shared Routing Skill
Objective:
Add a repo-owned skill that handles the redirected skill-authoring workflow.

Outputs:

- shared routing skill or repo-maintenance skill
- documented relationship to `skill-creator`
- trigger examples and fallback rules

Checklist:
- [x] Define the shared routing skill surface.
- [x] Decide whether to extend `skill-creator` or add a separate router skill.
- [x] Document how the routing skill hands off to `skill-creator`.
- [x] Add a small evaluation set for should-trigger and should-not-trigger prompts.

Exit Criteria:
Future sessions can route skill-authoring requests into `ai-stack` consistently without path restatement.

## Acceptance Criteria

- The repo defines one clear machine-local path field for finding `ai-stack`.
- The repo defines when skill-authoring requests should default into `ai-stack`.
- Shared routing behavior respects explicit user overrides.
- Missing or invalid config produces a clear fallback instead of silent guessing.
- The design stays shareable without committing private machine paths.

## Open Questions

- Should the long-term default rely more on global instructions or on native skill triggering once field testing shows which surface is more reliable?
- Should nonexistent `repos.aiStack` values fail validation at config-load time or only when routing is attempted?
- Should the first implementation support only `ai-stack`, or leave room for a small future `repos` map without using it yet?

## Follow-Up Work

- Update `config.example.yaml` to show the new field once implementation starts.
- Revisit the earlier configuration-contract docs to note this justified exception.
- Add the shared routing skill and connect it to `skill-creator`.
- Update README-style docs only after the behavior is implemented and durable.
