# Global Agent Instructions

- Never create commits, push branches, or create or update pull requests without explicit user confirmation in the current conversation. Confirmation from an earlier task or message does not carry forward — each commit requires its own confirmation at the time it is made.
- Never run destructive Git operations such as `git reset --hard`, `git checkout -- <path>`, branch deletion, or history rewrites without explicit user confirmation.
- When the user asks to create, update, refine, or restructure a skill and does not name a different target repo, treat that as work in the configured `repos.aiStack` checkout.
- If `repos.aiStack` is missing, invalid, or unavailable, ask for the target repo instead of guessing from surrounding directories.
