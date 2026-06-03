# Repository Structure

This file explains the current top-level structure of the repository and the rule for when new top-level directories should exist.

## Rule

Do not create placeholder top-level directories that contain only a README and no real code, tests, or user-managed assets.

If a future area is still mostly design, document it in `docs/` and add the actual directory only when it starts carrying real repository weight.

## Current Top-Level Directories

- `.github/`
  Copilot compatibility files and any future narrow GitHub-specific instruction surfaces.
- `ai_stack/`
  The Python runtime package. This is where the real implementation lives.
- `bin/`
  Executable entrypoints such as `bin/ai-stack`.
- `docs/`
  Shared design and structure documentation.
- `skill-indexes/`
  Local skill-index conventions and example artifacts consumed by the current runtime.
- `tests/`
  Runtime tests.

## Planned Directories

These concepts still exist, but they should be added as real top-level directories only when they contain actual content:

- `skills/`
- `agents/`
- `dashboard/`
- `memory/`
- `model-benchmarks/`
- `templates/`
- `telemetry/`

For now, their contracts live in feature docs rather than in placeholder directories.
