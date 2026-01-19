# Implementation Decisions

Decisions made during plan review discussion.

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Commit message file path | Use `PR_INFO_DIR` + `COMMIT_MESSAGE_FILE` joined in code | Consistent with existing path handling in `core.py` |
| 2 | LLM error handling | Return `False` on empty/failed LLM response | Matches `prepare_task_tracker` pattern (strict) |
| 3 | Missing task tracker | Return `False` with error log when `TASK_TRACKER.md` missing | Missing tracker is an error condition |
| 4 | Additional test case | Add `test_run_finalisation_returns_false_when_task_tracker_missing` | Cover the error handling from decision #3 |
| 5 | Slash command tools | Omit `allowed-tools` - inherit from session configuration | Simpler, uses whatever tools are available (including MCP) |
