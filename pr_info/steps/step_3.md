# Step 3 — Thread `active_set` into `display_status_table` (status command) + invariant test

## Goal
`vscodeclaude status` builds the snapshot once at command entry and passes it to `display_status_table`. The cache-clear inside `display_status_table` is removed (now handled by `build_active_session_set`). With launch (steps 1-2) and status now both routed through `build_active_session_set`, add a mock-based invariant test asserting `is_session_active.call_count == N_sessions` for one `launch` and one `status` flow.

**Status side effect (intentional):** because the status command now builds the snapshot via `build_active_session_set`, status will write updated PIDs to `sessions.json` whenever window-title detection finds a different PID than the stored one. This closes today's PID-refresh asymmetry between launch and status. Add an explicit test for this behaviour.

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/status.py`
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (build snapshot in `execute_coordinator_vscodeclaude_status`)
- Modified: `tests/workflows/vscodeclaude/test_status_display.py`
- Modified: `tests/workflows/vscodeclaude/test_closed_issues_integration.py`
- New or modified: invariant test (see below)
- Possibly modified: a status test module — add the "status refreshes stale stored PID" assertion (see below)

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
  - Replace `is_running = is_session_active(session)` (line 333) with `is_running = active_set.get(session["folder"], False)`. Use `.get(folder, False)` (not `[folder]`) so that any session not present in the snapshot is treated as inactive (defensive against future changes that may filter the snapshot mid-flow).
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
- Lookups inside `display_status_table` use `.get(folder, False)` for the same defensive reason as cleanup/restart.
- Return type unchanged (`None`; prints to stdout).

## Invariant test

**Location decision:** check first whether `tests/cli/commands/` already contains tests for `execute_coordinator_vscodeclaude` or `execute_coordinator_vscodeclaude_status`. If yes, extend that file. If no, create `tests/workflows/vscodeclaude/test_active_set_invariant.py`.

**Test content (one test per command):**

```python
def test_launch_calls_is_session_active_n_times(monkeypatch, tmp_path):
    """Verify is_session_active is called exactly N_sessions times per launch."""
    sessions = <build N mock sessions on tmp_path>
    call_counter = mock.Mock(return_value=False)
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.sessions.is_session_active",
        call_counter,
    )
    # Mock GitHub / config / IssueManager / restart_closed_sessions etc.
    # so the command runs without external I/O.
    args = argparse.Namespace(
        repo=None, max_sessions=5, cleanup=False,
        intervene=False, issue=None, no_install_from_github=True,
    )
    execute_coordinator_vscodeclaude(args)
    assert call_counter.call_count == len(sessions)


def test_status_calls_is_session_active_n_times(monkeypatch, tmp_path):
    """Verify is_session_active is called exactly N_sessions times per status."""
    # Same shape as above, calling execute_coordinator_vscodeclaude_status.
```

The exact mocking depends on what the command needs at runtime (config files, GitHub credentials, repo loading). Reuse mock fixtures from existing tests where possible.

## Status PID-refresh test

In `test_status_display.py` (or wherever the status flow tests live), add a test that:
- Sets up a session whose stored `vscode_pid` does not match what `is_vscode_open_for_folder` returns.
- Patches `is_session_active` to return `True` (so the `active_set` records the session as active).
- Patches `update_session_pid` with a Mock.
- Runs `execute_coordinator_vscodeclaude_status` (or directly invokes `build_active_session_set` if the integration mocking is too heavy).
- Asserts `update_session_pid` was called with the new PID.

This documents (and protects) the intentional new behaviour that status now refreshes stale stored PIDs the same way launch does.

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

Add the two invariant tests and the status PID-refresh test as described above. Run pytest; confirm failures with the missing parameter, then implement. After implementation the invariant tests should pass with `call_count == N_sessions`; if they fail with `call_count > N`, find and fix the leftover `is_session_active` call site.

## Acceptance
- `test_status_display.py` and `test_closed_issues_integration.py` pass.
- New invariant tests pass with `call_count == N_sessions` for both launch and status.
- New status PID-refresh test passes (`update_session_pid` called with the freshly-detected PID).
- pylint, pytest, mypy clean (with marker exclusion).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 exactly as described.

Apply TDD:
1. Rewrite `is_session_active` patches in `tests/workflows/vscodeclaude/test_status_display.py` and `tests/workflows/vscodeclaude/test_closed_issues_integration.py` to pass an explicit `active_set` argument. Add the launch/status invariant tests (decide location: extend existing `tests/cli/commands/` test file if present, otherwise create `tests/workflows/vscodeclaude/test_active_set_invariant.py`). Add the status PID-refresh test. Run pytest, confirm failures.
2. Update `display_status_table` signature in `status.py`: add `active_set` parameter, remove the cache-clear, replace the `is_session_active` lookup with `active_set.get(session["folder"], False)`. Drop the now-unused imports. In `commands.py`, build the snapshot at the top of `execute_coordinator_vscodeclaude_status` and pass it through.
3. Run pylint, mypy, pytest (with marker exclusion). Fix until all green. If the invariant test reports `call_count > N`, find and fix the leftover call site before moving on.

Do not remove `get_active_session_count` from `sessions.py` or `__init__.py` yet — that is step 4.

Commit message: `vscodeclaude: thread active_set into display_status_table and add invariant test`.
