# Repository Structure

This file explains the current top-level structure of the repository and the rule for when new top-level directories should exist.

## Rule

Do not create placeholder top-level directories that contain only a README and no real code, tests, or user-managed assets.

If a future area is still mostly design, document it in `docs/` and add the actual directory only when it starts carrying real repository weight.

Keep runtime code independent from examples, templates, and backlog docs unless a runtime dependency is explicitly part of the contract.

## Current Top-Level Directories

- `.github/`
  Copilot compatibility files and any future narrow GitHub-specific instruction surfaces.
- `ai_stack/`
  The Python runtime package. This is where the real implementation lives.
- `bin/`
  Executable entrypoints such as `bin/ai-stack`.
- `docs/`
  Shared design and structure documentation.
- `global-agent-instructions/`
  Shared machine-global instruction sources plus the optional local overlay convention used by global instruction sync.
- `skill-indexes/`
  Local skill-index conventions and example artifacts consumed by the current runtime.
- `skills/`
  Repo-local and shared skill packages. This is now justified by real user-managed skill content under `skills/local/` and tracked shared skill content under `skills/shared/`.
- `tests/`
  Runtime tests.

## Boundary Notes

- Setup and sync utilities are part of the runtime surface, but they are distinct from higher-order orchestration.
- Example artifacts and design docs should inform runtime behavior by contract only, not become accidental hard dependencies.

## Planned Directories

These concepts still exist, but they should be added as real top-level directories only when they contain actual content:

- `dashboard/`
- `memory/`
- `model-benchmarks/`
- `templates/`
- `telemetry/`

For now, their contracts live in feature docs rather than in placeholder directories.
