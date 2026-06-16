# AGENTS.md

This file is the primary agent operating guide for this repository.

It should remain compatible with Codex-style agent workflows. Copilot compatibility lives in `.github/copilot-instructions.md`, which should stay thin and refer back here plus the shared docs.

When working in this repository:

- read `README.md` for project intent
- read `docs/features/README.md` for the feature-doc contract
- read the relevant file in `docs/features/` before making architectural or structural changes
- treat feature docs as the design source of truth only while work is still unsettled or implementation is incomplete
- move settled architectural truth into README-style docs once it becomes durable repo structure or operating behavior
- check for incomplete phases, unchecked items, and open questions in relevant feature docs before declaring work complete or starting adjacent design work
- update docs when you change architecture, conventions, or intended repo structure
- keep committed content shareable; do not introduce private machine details, absolute local paths, or secrets

If a task is primarily documentation work, prefer changing the relevant feature doc or README instead of burying intent in agent-only instructions.

Instruction placement:

- keep durable project truth in shared docs
- keep this file concise, but treat it as the main agentic source of truth
- keep `.github/copilot-instructions.md` as a compatibility shim, not a second full instruction system
- use `.github/instructions/*.instructions.md` only when narrow Copilot-only path scoping is genuinely needed

When future sessions need to add instructions:

- add durable repo architecture and operating rules to `README.md` or other README-style shared docs
- use `docs/features/*.md` for active design work, backlog, phased implementation plans, and open questions
- add agent workflow guidance here
- update `.github/copilot-instructions.md` only when Copilot still needs the rule or pointer
- avoid adding `.github/instructions/*.instructions.md` unless the narrower scope is clearly justified
