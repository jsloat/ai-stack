# Hermetic Agents

## Summary

Capture the idea of using isolated agents with restricted context, tool access, and communication paths for implementation and verification work.

The motivating pattern is a coder agent, a test or verifier agent, and a QA or adjudication layer that can detect disagreement without freely leaking information across roles.

## Why It Is Interesting

- it may reduce confirmation bias between implementation and verification
- it fits the repo's interest in durable orchestration rather than one-off chats
- it encourages explicit artifact handoff instead of hidden conversational state
- it could support stronger review and audit behavior for larger runs

## Fit With Current Repo Scope

This fits the repo better as a future orchestration extension than as a current top-level feature.

The current orchestration docs define a first slice that is:

- lightweight
- staged
- artifact-driven
- linear before DAG-style execution

That makes a full hermetic multi-agent runtime a poor first implementation target, but a plausible later-stage extension once the base orchestration lifecycle exists.

## Prerequisites

- first executable orchestration flow implemented end to end
- persisted run state and artifact handoff in code
- explicit implementation and verification stages
- clear retry and revision semantics
- stable CLI lifecycle for `init`, `approve`, `plan`, `run`, and `status`

## Reasons Not To Do It Yet

- the repo does not have orchestration runtime code yet
- the current design intentionally avoids general workflow-engine scope in the first slice
- context isolation, channel restrictions, and DAG dependencies would add substantial complexity early
- harness-agnostic support would be harder to preserve if this lands before the simpler baseline exists

## Promotion Signals

Promote this into `docs/features/` when one or more of these become true:

- the first orchestration workflow is implemented and tested
- verification-stage design needs stronger separation from implementation-stage context
- multiple real workflows need restricted role boundaries rather than simple linear staging
- artifact-only handoff is working well enough that stricter isolation becomes practical

## Promotion Target

If promoted, this should likely become a feature doc for a narrow first slice such as:

- verifier isolation
- hidden-test or hidden-check guidance
- restricted artifact-only feedback between implementation and verification stages

It should not start as a full general-purpose multi-agent mesh.

## Sources

- Hacker News comment thread: <https://news.ycombinator.com/item?id=48779784>
- Captured on 2026-07-04 from a discussion about "hermetic agents" and related replies on isolated coder, tester, and QA roles
