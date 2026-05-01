# Step 2 — Thread `active_set` into `restart_closed_sessions`

## Goal
`restart_closed_sessions` reads activity from the snapshot built in step 1. Its internal cache-clear and in-loop PID-refresh are removed (now both handled by `build_active_session_set`).

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (pass `active_set` to restart)
- Modified: `tests/workflows/vscodeclaude/test_session_restart.py`
- Modified: `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`
- Modified: `tests/workflows/vscodeclaude/test_session_restart_cache.py`
- Modified: `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py`

## WHAT
```python
# session_restart.py
def restart_closed_sessions(
    active_set: dict[str, bool],
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[VSCodeClaudeSession]: ...
```

## HOW
- In `session_restart.py`:
  - Drop these imports from `.sessions`: `clear_vscode_process_cache`, `clear_vscode_window_cache`, `is_session_active`, `is_vscode_open_for_folder`, `update_session_pid` (the last three only if no longer referenced; keep `update_session_pid` since it's still used for the post-launch PID update).
  - Remove the two `clear_vscode_*_cache()` calls near the top of `restart_closed_sessions` (they now live in `build_active_session_set`).
  - Replace the block currently at `session_restart.py:262-267`:
    ```python
    if is_session_active(session):
        _, found_pid = is_vscode_open_for_folder(session["folder"])
        if found_pid and found_pid != session.get("vscode_pid"):
            update_session_pid(session["folder"], found_pid)
        continue
    ```
    with:
    ```python
    if active_set[session["folder"]]:
        continue
    ```
- In `commands.py` `execute_coordinator_vscodeclaude`:
  - Pass `active_set=active_set` as a kwarg into the `restart_closed_sessions(...)` call (line 541).

## ALGORITHM (relevant snippet inside the for-session loop)
```
folder_path = Path(session["folder"])
if active_set[session["folder"]]:
    continue
if not folder_path.exists():
    remove_session(session["folder"])
    continue
# ... rest of restart logic unchanged ...
```

## DATA
- `active_set` is `dict[str, bool]` keyed by `session["folder"]`. Required parameter.
- Return value unchanged: `list[VSCodeClaudeSession]` of restarted sessions.

## TDD: Tests first

For each test in the four `test_session_restart*.py` files that does:
```python
monkeypatch.setattr(
    "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
    lambda s: <bool>,
)
```
or equivalent `mock.patch(...)`:

1. Remove the patch.
2. Build an `active_set` dict at test setup time: `{s["folder"]: <bool> for s in sessions}`.
3. Pass `active_set=active_set` into `restart_closed_sessions(...)`.

Tests that previously asserted on the in-loop PID-refresh behavior (e.g. that `update_session_pid` was called when an active session's stored PID was stale) belong to `build_active_session_set` (covered in step 1's `test_build_active_session_set`). If any such assertions exist in `test_session_restart*.py`, delete them — they are no longer the responsibility of `restart_closed_sessions`.

Run tests; confirm they fail with the missing/wrong signature, then implement.

## Acceptance
- All four `test_session_restart*.py` files pass.
- pylint, pytest, mypy clean (use the `-m "not ..."` marker exclusion from CLAUDE.md).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2 exactly as described.

Apply TDD:
1. Rewrite the `is_session_active`/`mock.patch` patterns in `test_session_restart.py`, `test_session_restart_branch_integration.py`, `test_session_restart_cache.py`, `test_session_restart_closed_sessions.py` to pass an explicit `active_set` argument. Drop assertions that test the in-loop PID-refresh behavior (now belongs to `build_active_session_set`). Run pytest, confirm the relevant tests fail.
2. Update `restart_closed_sessions` signature and internals in `session_restart.py`. Remove the cache-clear calls and the in-loop PID-refresh block. Update `commands.py` to pass `active_set=active_set` to the call.
3. Run pylint, mypy, pytest (with the marker exclusion). Fix until all green.

Do not touch `process_eligible_issues`, `display_status_table`, `cleanup`, or `get_active_session_count` in this step.

Commit message: `vscodeclaude: thread active_set into restart_closed_sessions`.
