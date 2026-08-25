# Global Agent Instructions

- Never create commits, push branches, or create or update pull requests without explicit user confirmation in the current conversation. Confirmation from an earlier task or message does not carry forward — each commit requires its own confirmation at the time it is made.
- This applies per commit/push action, not per task: a single approval (e.g. "proceed," "go ahead," "do it") authorizing a multi-step task does NOT authorize every commit/push that task produces. If a task is expected to involve more than one commit or push, say so up front and still pause to confirm before each individual one. Treat "I'll commit this now" as a stop-and-ask point, not a statement of intent to execute.
- Never run destructive Git operations such as `git reset --hard`, `git checkout -- <path>`, branch deletion, or history rewrites without explicit user confirmation.
- When the user asks to create, update, refine, or restructure a skill and does not name a different target repo, treat that as work in the configured `repos.aiStack` checkout.
- If `repos.aiStack` is missing, invalid, or unavailable, ask for the target repo instead of guessing from surrounding directories.
- Always prefer minimal code changes. Make only the changes needed to address the task — avoid refactoring, restructuring, or "cleaning up" surrounding code unless explicitly asked.
- Code comments should describe the current code's purpose or behavior, not the history of how it got there — never reference a prior bug, a fix that was just made, or how the code differs from an earlier/broken version. Only add a comment when it explains something not already obvious from reading the code; skip comments that just restate what the code plainly does.
