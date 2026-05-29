# Copilot Instructions

This file is a thin GitHub Copilot compatibility layer.

Use these sources in order:

1. `README.md` for project summary
2. `AGENTS.md` for primary agent workflow guidance
3. `docs/features/*.md` for durable design and planning

Repository-wide rules:

- Treat `docs/features/` as the first-class design surface when implementation is incomplete.
- Keep committed content shareable; do not include private machine details, absolute local paths, private account references, or secrets.
- Use `config.example.yaml` as the committed template and keep `config.local.yaml` untracked.
- Keep config focused on real behavioral choices; do not add configurable repo-owned paths without a demonstrated need.
- Prefer reusable structure, explicit boundaries, and shared conventions over one-off local automation.

Do not duplicate the full agent guide here. Update `AGENTS.md` first when changing agent workflow behavior.
