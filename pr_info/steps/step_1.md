# Step 1: Add tests for new `is_session_active()` behavior

> **Context:** See [summary.md](summary.md) for the full issue and design.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.
Implement Step 1: add 4 new tests to tests/workflows/vscodeclaude/test_sessions.py
for the new is_session_active() behavior described in issue #547.
Do NOT modify src/ code yet — only add tests. The new tests will fail until Step 2.
Run pylint and mypy checks (tests should fail at this point, so skip pytest).
Commit with message: "test: add tests for window-title-priority in is_session_active #547"
```

## WHERE

- `tests/workflows/vscodeclaude/test_sessions.py` — add a new test class

## WHAT

Add a new `TestIsSessionActiveWindowPriority` class with 4 test methods:

### Test 1: `test_pid_alive_but_window_gone_returns_inactive`

**Scenario:** The exact bug — PID is alive but no window title matches.
- Mock `HAS_WIN32GUI = True`
- Mock `session_has_artifacts` → `True`
- Mock `is_vscode_window_open_for_folder` → `False`
- Mock `check_vscode_running` → `True`
- Session has `issue_number=542`, `repo="owner/repo"`, `vscode_pid=28036`
- **Assert:** `is_session_active()` returns `False`

### Test 2: `test_repo_none_falls_through_to_pid_check`

**Scenario:** Guard condition not met — `repo` is `None`, so fallback to PID path.
- Mock `HAS_WIN32GUI = True`
- Mock `session_has_artifacts` → `True`
- Mock `check_vscode_running` → `True`
- Session has `issue_number=100`, `repo=None`, `vscode_pid=1234`
- **Assert:** `is_session_active()` returns `True` (PID fallback used)

### Test 3: `test_warning_logged_when_pid_alive_but_window_gone`

**Scenario:** Same as Test 1, but verify the diagnostic warning is logged.
- Same mocks as Test 1
- **Assert:** `logger.warning` called with message containing "window title not found but PID"

### Test 4: `test_non_windows_uses_pid_fallback`

**Scenario:** `HAS_WIN32GUI = False` — existing behavior preserved.
- Mock `HAS_WIN32GUI = False`
- Mock `session_has_artifacts` → `True`
- Mock `check_vscode_running` → `True`
- Session has `issue_number=100`, `repo="owner/repo"`, `vscode_pid=1234`
- **Assert:** `is_session_active()` returns `True` (PID fallback used)

## HOW

- All mocks use `monkeypatch.setattr` on the `mcp_coder.workflows.vscodeclaude.sessions` module
- For the warning log test, use `caplog` pytest fixture with `logging.WARNING` level
- Each test creates a minimal `VSCodeClaudeSession` dict with a `folder` pointing to a real `tmp_path` subdirectory (so `session_has_artifacts` can be mocked or the folder can exist)
- Import `is_session_active` (already imported in the test file)

## DATA

Each test operates on a `VSCodeClaudeSession` TypedDict:
```python
{
    "folder": str,        # path to tmp dir
    "repo": str | None,   # "owner/repo" or None
    "issue_number": int,
    "status": "s",
    "vscode_pid": int,
    "started_at": "2024-01-01T00:00:00Z",
    "is_intervention": False,
}
```
