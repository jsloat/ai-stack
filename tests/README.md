# Tests

This directory will hold automated tests for the platform as executable behavior is added.

The current suite is intentionally runnable through the default entrypoint:

- `python3 -m unittest`

Prefer tests that validate shared contracts such as:

- config loading
- instruction resolution
- skill index parsing
- adapter boundaries
- routing behavior
