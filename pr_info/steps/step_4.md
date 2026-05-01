# Step 4 — Thread `active_set` into `display_status_table` (status command)

## Goal
`vscodeclaude status` builds the snapshot once at command entry and passes it to `display_status_table`. The cache-clear inside `display_status_table` is removed (now handled by `build_active_session_set`).

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/status.py`
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (build snapshot in `execute_coordinator_vscodeclaude_status`)
- Modified: `tests/workflows/vscodeclaude/test_status_display.py`
- Modified: `tests/workflows/vscodeclaude/test_closed_issues_integration.py`

## WHAT
```python
# status.py
def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    workspace_base: str,
    active_set: dict[str, bool],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,
) -> None: ...
```

## HOW
- In `status.py`:
  - Drop these imports from `.sessions`: `clear_vscode_process_cache`, `clear_vscode_window_cache`, `is_session_active`.
  - Remove the two `clear_vscode_*_cache()` calls at the top of `display_status_table` (lines 280-281) — the snapshot, built at command entry, has already cleared and refreshed them.
  - Replace `is_running = is_session_active(session)` (line 333) with `is_running = active_set[session["folder"]]`.
- In `commands.py` `execute_coordinator_vscodeclaude_status`:
  - After `sessions = store["sessions"]`, call `active_set = build_active_session_set(sessions)`.
  - Pass `active_set=active_set` as a kwarg into the `display_status_table(...)` call.

## ALGORITHM (status command entry)
```
store = load_sessions()
sessions = store["sessions"]
active_set = build_active_session_set(sessions)
# ... existing repo/cache build ...
display_status_table(sessions=sessions, ..., active_set=active_set, ...)
```

## DATA
- `active_set: dict[str, bool]` keyed by `session["folder"]`. Required parameter.
- Return type unchanged (`None`; prints to stdout).

## TDD: Tests first

In `test_status_display.py` and `test_closed_issues_integration.py`, replace `is_session_active` patches:

Before:
```python
monkeypatch.setattr(
    "mcp_coder.workflows.vscodeclaude.status.is_session_active",
    lambda s: <bool>,
)
display_status_table(sessions=..., ...)
```

After:
```python
active_set = {s["folder"]: <bool> for s in sessions}
display_status_table(sessions=..., active_set=active_set, ...)
```

Tests that depend on the cache-clear side effect inside `display_status_table` (none should — caches are sessions.py concern) should be removed.

Run pytest; confirm failures with the missing parameter, then implement.

## Acceptance
- `test_status_display.py` and `test_closed_issues_integration.py` pass.
- pylint, pytest, mypy clean (with marker exclusion).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4 exactly as described.

Apply TDD:
1. Rewrite `is_session_active` patches in `tests/workflows/vscodeclaude/test_status_display.py` and `tests/workflows/vscodeclaude/test_closed_issues_integration.py` to pass an explicit `active_set` argument. Run pytest, confirm failures.
2. Update `display_status_table` signature in `status.py`: add `active_set` parameter, remove the cache-clear, replace the `is_session_active` lookup. Drop the now-unused imports. In `commands.py`, build the snapshot at the top of `execute_coordinator_vscodeclaude_status` and pass it through.
3. Run pylint, mypy, pytest (with marker exclusion). Fix until all green.

Do not remove `get_active_session_count` from `sessions.py` or `__init__.py` yet — that is step 5.

Commit message: `vscodeclaude: thread active_set into display_status_table`.
