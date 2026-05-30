# Adapters

Adapters isolate harness-specific behavior from the rest of the platform.

Current first-pass behavior:

- adapter lookup by harness id
- dry-run handoff from shared runtime state into a normalized adapter trace
- deterministic reporting of `ready`, `skipped`, and `unsupported` adapter outcomes

Future adapter responsibilities may expand to:

- launch or invoke a harness
- translate shared context into harness-native instruction surfaces
- collect outputs needed for telemetry
- normalize harness-specific behavior into shared platform concepts
