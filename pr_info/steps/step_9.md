# Step 9: tests/ W0612 — unused variables (43 occurrences)

## Goal
Fix unused variables in `tests/`. Replace with `_` or use `_` in tuple unpacks.

## WHERE — Files Modified

**`tests/workflows/vscodeclaude/test_cleanup.py`** (~14 occurrences):
Tuple unpacks like `session, git_status = stale_sessions[0]` where only one side is used.
Fix: use `_` for the unused side.

**Other files (one per test):**
- `tests/cli/commands/test_check_branch_status_ci_waiting.py` — `ci_status` unused (x2) -> `_`
- `tests/cli/commands/test_commit.py` — `captured_out` unused -> `_`
- `tests/cli/commands/test_define_labels.py` — `repo` unused (x3) -> `_`
- `tests/cli/commands/test_gh_tool.py` — `result` unused -> `_`
- `tests/cli/commands/test_verify_integration.py` — `call_args` unused -> `_`
- `tests/formatters/test_integration.py` — `i` unused in for-loop -> `_`
- `tests/llm/test_mlflow_logger.py` — `logger` (x2), `result` unused -> `_`
- `tests/llm/providers/claude/test_claude_cli_stream_integration.py` — `result` unused -> `_`
- `tests/llm/session/test_resolver.py` — `fake_path` unused -> `_`
- `tests/utils/test_folder_deletion.py` — `mock_move` unused -> `_`
- `tests/utils/git_operations/test_commits.py` — `repo` unused -> `_`
- `tests/utils/git_operations/test_remotes.py` — `expected_sha` unused -> `_`
- `tests/workflows/test_create_pr_integration.py` — `repo` (x3) unused -> `_`
- `tests/workflows/vscodeclaude/test_closed_issues_integration.py` — `mock_launch`, `result` unused -> `_`
- `tests/workflows/vscodeclaude/test_issues.py` — `issues_without_branch` unused -> `_`
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` — `mock_execute` unused -> `_`

## WHAT

- `varname = expr` -> `_ = expr`
- `a, b = expr` -> `_, b = expr` or `a, _ = expr` (unused side)

## DATA

Pylint count reduced by: **43 warnings**.

---

## LLM Prompt

```
Please implement Step 9: fix W0612 (unused variables) in tests/.
See pr_info/steps/step_9.md for exact locations.
Rules: replace unused vars with _. No test logic changes.
Run pylint, pytest (fast unit tests), and mypy to verify.
```
