# Step 1 — Snapshot helper + threading into cleanup AND restart

## Goal
Introduce `build_active_session_set` helper. Update `execute_coordinator_vscodeclaude` to build the snapshot at command entry — BEFORE both `cleanup_stale_sessions` and `restart_closed_sessions` — and pass it into both. Inside `cleanup_stale_sessions`, propagate `active_set` to `get_stale_sessions`. Inside `restart_closed_sessions`, remove its now-redundant cache-clear and in-loop PID-refresh (both centralized in the helper).

After this step, `cleanup` and `restart` both read activity from the snapshot. The launch flow's `process_eligible_issues` and the status command continue to use their own paths — addressed in subsequent steps.

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/sessions.py` (add helper)
- Modified: `src/mcp_coder/workflows/vscodeclaude/cleanup.py` (add `active_set` param)
- Modified: `src/mcp_coder/workflows/vscodeclaude/session_restart.py` (add `active_set` param; drop cache-clear and in-loop PID-refresh)
- Modified: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (export helper)
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (build snapshot in `execute_coordinator_vscodeclaude`; pass into cleanup AND restart)
- Modified: `tests/workflows/vscodeclaude/test_cleanup.py` (~20 mock sites)
- Modified: `tests/workflows/vscodeclaude/test_session_restart.py`
- Modified: `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`
- Modified: `tests/workflows/vscodeclaude/test_session_restart_cache.py`
- Modified: `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py`
- Modified: `tests/workflows/vscodeclaude/test_closed_issues_integration.py` (3 `session_restart.is_session_active` patches at lines 79, 332, 429)
- Modified: `tests/workflows/vscodeclaude/test_sessions.py` (add `test_build_active_session_set` test)

## WHAT
```python
# sessions.py — new helper
def build_active_session_set(
    sessions: list[VSCodeClaudeSession],
) -> dict[str, bool]:
    """Build active-set snapshot.

    Side effects: clears VSCode window/process caches, may call
    update_session_pid for active sessions whose stored PID differs
    from the currently-detected PID.
    """

# cleanup.py — signatures
def cleanup_stale_sessions(
    workspace_base: str,
    active_set: dict[str, bool],
    dry_run: bool = True,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, list[str]]: ...

def get_stale_sessions(
    active_set: dict[str, bool],
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[tuple[VSCodeClaudeSession, str, str]]: ...

# session_restart.py — signature
def restart_closed_sessions(
    active_set: dict[str, bool],
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[VSCodeClaudeSession]: ...
```

## HOW
- Add `build_active_session_set` to `sessions.py`. It uses `clear_vscode_window_cache`, `clear_vscode_process_cache`, `is_session_active`, `is_vscode_open_for_folder`, `update_session_pid` (all already in the module). The framing log uses `INFO` level (matching the existing per-session INFO logs from `is_session_active`) — use the standard `logger.info(...)` API, no extra imports needed.
- Export `build_active_session_set` from `__init__.py` (`__all__`). Keep `get_active_session_count` for now (removed in step 4).
- In `cleanup.py`:
  - Drop `is_session_active` from the imports of `.sessions`.
  - Replace the `if is_session_active(session): continue` line in `get_stale_sessions` with `if active_set.get(session["folder"], False): continue`. Use `.get(folder, False)` (not `[folder]`) so a session removed from the snapshot mid-flow is treated as inactive.
  - Pass `active_set` from `cleanup_stale_sessions` into `get_stale_sessions`.
- In `session_restart.py`:
  - Drop these imports from `.sessions`: `clear_vscode_process_cache`, `clear_vscode_window_cache`, `is_session_active`, `is_vscode_open_for_folder`. Keep `update_session_pid` (still used for the post-launch PID update).
  - Remove the two `clear_vscode_*_cache()` calls near the top of `restart_closed_sessions` (now done in `build_active_session_set`).
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
    if active_set.get(session["folder"], False):
        continue
    ```
- In `commands.py` `execute_coordinator_vscodeclaude`:
  - Import `build_active_session_set` from `....workflows.vscodeclaude`.
  - After `sessions_list = store["sessions"]`, call `active_set = build_active_session_set(sessions_list)` BEFORE the cleanup and restart calls.
  - Pass `active_set=active_set` as a kwarg in both `cleanup_stale_sessions` calls (the dry_run=True/False branches).
  - Pass `active_set=active_set` as a kwarg into the `restart_closed_sessions(...)` call (line 541).

## ALGORITHM (`build_active_session_set`)
```
clear_vscode_window_cache()
clear_vscode_process_cache()
logger.info("Checking %d session(s)...", len(sessions))
active_set: dict[str, bool] = {}
for session in sessions:
    is_active = is_session_active(session)
    active_set[session["folder"]] = is_active
    if is_active:
        _, found_pid = is_vscode_open_for_folder(session["folder"])
        if found_pid is not None and found_pid != session.get("vscode_pid"):
            update_session_pid(session["folder"], found_pid)
return active_set
```

## ALGORITHM (relevant snippet inside the restart for-session loop)
```
folder_path = Path(session["folder"])
if active_set.get(session["folder"], False):
    continue
if not folder_path.exists():
    remove_session(session["folder"])
    continue
# ... rest of restart logic unchanged ...
```

## DATA
- Snapshot is `dict[folder_path_str, bool]`. All input sessions appear as keys.
- `True` = active, `False` = inactive.
- Lookups use `.get(folder, False)` so that sessions removed mid-flow (e.g. by cleanup) are treated as inactive.
- Side effects: cache clears + possible `update_session_pid` writes for active sessions.

## TDD: Tests first

**`tests/workflows/vscodeclaude/test_cleanup.py`** — for each test (~20 sites) that does:
```python
monkeypatch.setattr(
    "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
    lambda session: <bool>,
)
```
Remove that monkeypatch and instead build an `active_set` dict before the call:
```python
active_set = {session["folder"]: <bool> for session in <sessions>}
result = get_stale_sessions(active_set=active_set, ...)
# or:
result = cleanup_stale_sessions(workspace_base=..., active_set=active_set, ...)
```

**Four `test_session_restart*.py` files AND `test_closed_issues_integration.py`** — for each test that does:
```python
monkeypatch.setattr(
    "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
    lambda s: <bool>,
)
```
or equivalent `mock.patch(...)` (in `test_closed_issues_integration.py` the three sites at lines 79, 332, 429 use `patch(...)` as a context manager binding `mock_active`):

1. Remove the patch.
2. Build an `active_set` dict at test setup time: `{s["folder"]: <bool> for s in sessions}`.
3. Pass `active_set=active_set` into `restart_closed_sessions(...)`.

Tests that previously asserted on the in-loop PID-refresh behavior (e.g. that `update_session_pid` was called when an active session's stored PID was stale) belong to `build_active_session_set` (covered by `test_build_active_session_set` below). If any such assertions exist in `test_session_restart*.py`, delete them — they are no longer the responsibility of `restart_closed_sessions`.

**`tests/workflows/vscodeclaude/test_sessions.py`** — add a new test `test_build_active_session_set`:
- Patch `is_session_active` to track calls (`Mock(side_effect=...)` or `monkeypatch.setattr` with a counter).
- Pass a list of N session dicts.
- Assert: returned dict has N keys (one per `session["folder"]`); `is_session_active` was called exactly N times; for active sessions where detected PID differs from stored PID, `update_session_pid` was called.

Confirm the new tests fail (helper missing / signatures wrong), then implement.

## Acceptance
- All `test_cleanup.py` tests pass after the mock rewrite.
- All four `test_session_restart*.py` files pass.
- `test_closed_issues_integration.py` passes (3 `session_restart.is_session_active` patches converted to `active_set`).
- New `test_build_active_session_set` passes.
- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_mypy_check` clean.
- `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]` clean.

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1 exactly as described.

Apply TDD:
1. Update `tests/workflows/vscodeclaude/test_cleanup.py` to drop `is_session_active` monkeypatches and pass explicit `active_set` arguments (~20 sites). Rewrite the `is_session_active`/`mock.patch` patterns in `test_session_restart.py`, `test_session_restart_branch_integration.py`, `test_session_restart_cache.py`, `test_session_restart_closed_sessions.py`, AND `test_closed_issues_integration.py` (3 `session_restart.is_session_active` patches at lines 79, 332, 429) to pass an explicit `active_set` argument. Drop assertions that test the in-loop PID-refresh behavior (now belongs to `build_active_session_set`). Add the `test_build_active_session_set` test in `tests/workflows/vscodeclaude/test_sessions.py`. Run pytest — confirm tests fail with import or signature errors.
2. Implement `build_active_session_set` in `sessions.py`, export it from `__init__.py`, update `cleanup.py` signatures and lookup, update `restart_closed_sessions` signature and internals (remove cache-clear and in-loop PID-refresh block), build the snapshot at the top of `execute_coordinator_vscodeclaude` in `commands.py` BEFORE both cleanup and restart, and pass `active_set` to both.
3. Run all three checks (`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, `mcp__tools-py__run_pytest_check` with the marker exclusion above). Fix until all green.

Do not modify `process_eligible_issues`, `display_status_table`, or `get_active_session_count` in this step — those belong to later steps.

Commit message: `vscodeclaude: snapshot active sessions and thread into cleanup and restart`.
