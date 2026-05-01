# Step 1 — Snapshot helper + threading into cleanup

## Goal
Introduce `build_active_session_set` helper. Update `execute_coordinator_vscodeclaude` to build the snapshot at command entry and pass it into `cleanup_stale_sessions`. Pass `active_set` through `cleanup_stale_sessions` to `get_stale_sessions`.

After this step, `cleanup` reads from the snapshot. `restart_closed_sessions` and the launch flow continue to call `is_session_active` themselves — addressed in subsequent steps.

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/sessions.py` (add helper)
- Modified: `src/mcp_coder/workflows/vscodeclaude/cleanup.py` (add `active_set` param)
- Modified: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (export helper)
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (build snapshot in `execute_coordinator_vscodeclaude`)
- Modified: `tests/workflows/vscodeclaude/test_cleanup.py` (~20 mock sites)
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
```

## HOW
- Add `build_active_session_set` to `sessions.py`. It uses `clear_vscode_window_cache`, `clear_vscode_process_cache`, `is_session_active`, `is_vscode_open_for_folder`, `update_session_pid` (all already in the module). The OUTPUT framing log uses `OUTPUT` from `mcp_coder.utils.log_utils` — add the import.
- Export `build_active_session_set` from `__init__.py` (`__all__`). Keep `get_active_session_count` for now (removed in step 5).
- In `cleanup.py`:
  - Drop `is_session_active` from the imports of `.sessions`.
  - Replace the `if is_session_active(session): continue` line in `get_stale_sessions` with `if active_set[session["folder"]]: continue`.
  - Pass `active_set` from `cleanup_stale_sessions` into `get_stale_sessions`.
- In `commands.py` `execute_coordinator_vscodeclaude`:
  - Import `build_active_session_set` from `....workflows.vscodeclaude`.
  - After `sessions_list = store["sessions"]`, call `active_set = build_active_session_set(sessions_list)`.
  - Pass `active_set=active_set` as a kwarg in both `cleanup_stale_sessions` calls (the dry_run=True/False branches).
- `restart_closed_sessions` is **unchanged** in this step — it continues to call `is_session_active` and clear caches itself. Tolerated transient state.

## ALGORITHM (`build_active_session_set`)
```
clear_vscode_window_cache()
clear_vscode_process_cache()
logger.log(OUTPUT, "Checking %d session(s)...", len(sessions))
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

## DATA
- Snapshot is `dict[folder_path_str, bool]`. All input sessions appear as keys.
- `True` = active, `False` = inactive.
- Side effects: cache clears + possible `update_session_pid` writes for active sessions.

## TDD: Tests first

**`tests/workflows/vscodeclaude/test_cleanup.py`** — for each test that does:
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

**`tests/workflows/vscodeclaude/test_sessions.py`** — add a new test `test_build_active_session_set`:
- Patch `is_session_active` to track calls (`Mock(side_effect=...)` or `monkeypatch.setattr` with a counter).
- Pass a list of N session dicts.
- Assert: returned dict has N keys (one per `session["folder"]`); `is_session_active` was called exactly N times; for active sessions where detected PID differs from stored PID, `update_session_pid` was called.

Confirm the new tests fail (helper missing / signatures wrong), then implement.

## Acceptance
- All `test_cleanup.py` tests pass after the mock rewrite.
- New `test_build_active_session_set` passes.
- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_mypy_check` clean.
- `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]` clean.

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1 exactly as described.

Apply TDD:
1. Update `tests/workflows/vscodeclaude/test_cleanup.py` to drop `is_session_active` monkeypatches and pass explicit `active_set` arguments (~20 sites). Add the `test_build_active_session_set` test in `tests/workflows/vscodeclaude/test_sessions.py`. Run pytest — confirm tests fail with import or signature errors.
2. Implement `build_active_session_set` in `sessions.py`, export it from `__init__.py`, update `cleanup.py` signatures and lookup, build the snapshot at the top of `execute_coordinator_vscodeclaude` in `commands.py`.
3. Run all three checks (`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, `mcp__tools-py__run_pytest_check` with the marker exclusion above). Fix until all green.

Do not modify `restart_closed_sessions`, `process_eligible_issues`, `display_status_table`, or `get_active_session_count` in this step — those belong to later steps.

Commit message: `vscodeclaude: snapshot active sessions in launch entry, thread into cleanup`.
