# Step 4: Update `session_restart.py` — remove from session reconstruction

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

Remove `install_from_github` from the `updated_session` dict constructed in `restart_closed_sessions()`.

## LLM Prompt
> Implement Step 4 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_4.md`). The source change in `session_restart.py` was already done in Step 1. Remove `install_from_github` from test session dicts in `test_session_restart.py` and `test_session_restart_closed_sessions.py`. Run all three code quality checks.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py`
- `tests/workflows/vscodeclaude/test_session_restart.py`

## WHAT

### `session_restart.py` — Source change already done in Step 1

The `"install_from_github": session.get("install_from_github", False)` line was already removed from the `updated_session` dict in Step 1 (to prevent mypy failure after TypedDict field removal). No source changes needed here.

This step now only contains test changes.

## Test changes

### `test_session_restart_closed_sessions.py`

Remove `"install_from_github": False` from all session dict literals in this file. Search for all occurrences — there are session dicts in multiple test methods.

### `test_session_restart.py`

Remove `"install_from_github": False` (and variants) from all session dict literals (~11 occurrences). Same mechanical cleanup as above — these are session dicts that must match the updated TypedDict after field removal.

## Commit message
```
fix(vscodeclaude): remove install_from_github from session restart tests (#885)

Remove install_from_github from session dict literals in
test_session_restart.py and test_session_restart_closed_sessions.py.
The source change in session_restart.py was already done in Step 1.
```
