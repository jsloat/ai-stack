# Adapters

Adapters isolate harness-specific behavior from the rest of the platform.

Current first-pass behavior:

- adapter lookup by harness id
- dry-run handoff from shared runtime state into a normalized adapter trace
- deterministic reporting of `ready`, `skipped`, and `unsupported` adapter outcomes
- a live non-interactive `codex` smoke path for basic harness invocation testing

Future adapter responsibilities may expand to:

- launch or invoke a harness
- translate shared context into harness-native instruction surfaces
- route supported harness execution through RTK by default
- compress large tool surfaces with patterns such as Cloudflare Code Mode when raw MCP or API catalogs are too large
- collect outputs needed for telemetry
- normalize harness-specific behavior into shared platform concepts
