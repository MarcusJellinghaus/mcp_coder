# Step 4: Update `session_restart.py` — remove from session reconstruction

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

Remove `install_from_github` from the `updated_session` dict constructed in `restart_closed_sessions()`.

## LLM Prompt
> Implement Step 4 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_4.md`). Remove `install_from_github` from the session reconstruction dict in `session_restart.py`. Update tests first (TDD), then source. Run all three code quality checks.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py`
- `tests/workflows/vscodeclaude/test_session_restart.py`

## WHAT

### `session_restart.py` — `restart_closed_sessions()`

In the `updated_session` dict construction (around line 340), remove:
```python
"install_from_github": session.get("install_from_github", False),
```

The dict should become:
```python
updated_session: VSCodeClaudeSession = {
    "folder": session["folder"],
    "repo": session["repo"],
    "issue_number": session["issue_number"],
    "status": session["status"],
    "vscode_pid": new_pid,
    "started_at": session["started_at"],
    "is_intervention": session.get("is_intervention", False),
}
```

## Test changes

### `test_session_restart_closed_sessions.py`

Remove `"install_from_github": False` from all session dict literals in this file. Search for all occurrences — there are session dicts in multiple test methods.

### `test_session_restart.py`

Remove `"install_from_github": False` (and variants) from all session dict literals (~11 occurrences). Same mechanical cleanup as above — these are session dicts that must match the updated TypedDict after field removal.

## Commit message
```
fix(vscodeclaude): remove install_from_github from session restart (#885)

Remove install_from_github from the session reconstruction dict in
restart_closed_sessions(). Install behavior is derived from
pyproject.toml at generation time, not stored state.
```
