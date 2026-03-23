# Step 2: Implement the fix and update existing test

> **Context:** See [summary.md](summary.md) for the full issue and design.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.
Implement Step 2: update the VSCodeClaudeSession TypedDict to allow repo=None,
modify is_session_active() in sessions.py to prioritize window title check on
Windows, and update the existing test that now needs adjusted mocks.
Run all three code quality checks (pylint, mypy, pytest).
Commit with message: "fix: prioritize window title over PID in is_session_active #547"
```

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/sessions.py` — modify `is_session_active()`
- `tests/workflows/vscodeclaude/test_sessions.py` — update `test_get_active_session_count_with_mocked_pid_check`

## WHAT

### 1. Update `VSCodeClaudeSession` TypedDict (types.py)

Change `repo: str` to `repo: str | None` in the `VSCodeClaudeSession` TypedDict to reflect
that `repo` can be `None` when the guard condition is not met.

### 2. Modify `is_session_active()` (sessions.py)

Replace the body of `is_session_active()` with the new check order:

**ALGORITHM (pseudocode):**
```
if not session_has_artifacts(folder): return False
if HAS_WIN32GUI and issue_num is not None and repo is not None:
    found = is_vscode_window_open_for_folder(folder, issue_num, repo)
    if not found and check_vscode_running(pid):
        logger.warning("window not found but PID alive — treating as inactive")
    return found
if check_vscode_running(pid): return True
is_open, _ = is_vscode_open_for_folder(folder)
return is_open
```

Also update the docstring to reflect the new check order:
- On Windows (with issue_num + repo): window title check is authoritative
- Non-Windows fallback: PID → cmdline (unchanged)

### 3. Update `test_get_active_session_count_with_mocked_pid_check`

This test currently mocks only `check_vscode_running`. After the fix, on Windows
the window check runs first. The test needs to also mock the window check path
so it exercises the correct code path.

**Options (pick simplest):**
- Set `HAS_WIN32GUI = False` so the test uses the PID fallback (preserving original intent)
- OR mock `is_vscode_window_open_for_folder` to return `True` for the active session

The simplest is `HAS_WIN32GUI = False` — one extra `monkeypatch.setattr` line,
no other changes to the test.

## HOW

- The `is_session_active()` function signature and imports do not change
- The `session.get("repo")` call is already used downstream — no new dict keys needed
- The warning log uses the existing `logger` instance in the module

## DATA

No new data structures. Return value of `is_session_active()` remains `bool`.
