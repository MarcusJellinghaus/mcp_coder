# review-implementation review log 1

## Round 1 — 2026-10-22
**Findings**:
Still reviewing: checking whether the out-of-scope `author_association` test edits are needed because of a dependency change.`tests/workflows/vscodeclaude/test_checks.py:103` — low — Edits outside the issue's scope: `author_association=None` is added here and in `tests/workflows/vscodeclaude/test_status_note.py:21`. They are needed because the installed `mcp_workspace` now has an `author_association` field on `CommentData`/`PullRequestData`. But they went into the step-1 commit `0b3b88a`, whose message doesn't mention them, and no plan step covers them. Move them to their own commit or mention them in the PR summary.
`tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py:251` — low — The skip reason says the CLI "ignored CLAUDE_CODE_MCP_STARTUP_WAIT_MS", which is only one possible cause. The issue's Constraints name another: `init` time may grow with the stub delay until it passes 20 s. State only the observed status, e.g. "stub 'connected' at init; pending-at-init not reached", so the reason doesn't point to the wrong cause.
**Decisions**:
Verdict(decision='tasks', tasks=['At tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py:251, change the skip reason so it states only what was observed, not a cause. Remove the claim that the CLI \'ignored CLAUDE_CODE_MCP_STARTUP_WAIT_MS\' and use wording like: "stub \'connected\' at init; pending-at-init not reached". Keep any existing diagnostic values, such as timings or status, that are already in the message.'], escalate_reason=None)
**Changes**:
applied
