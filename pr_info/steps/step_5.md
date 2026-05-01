# Step 5 — Remove `get_active_session_count`; add invariant test

## Goal
With all four call sites converted (steps 1-4), `get_active_session_count` is dead code. Remove it. Add a mock-based invariant test asserting `is_session_active.call_count == N_sessions` for one `launch` and one `status` run.

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/sessions.py` (delete function)
- Modified: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (drop from `__all__` and from imports)
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (drop unused import if still present)
- Modified: `tests/workflows/vscodeclaude/test_sessions.py` (delete `test_get_active_session_count` at line ~277)
- New or modified: invariant test (see below)

## WHAT
- Delete `def get_active_session_count() -> int` from `sessions.py`.
- Drop `"get_active_session_count"` from the `__all__` list and the corresponding import line in `src/mcp_coder/workflows/vscodeclaude/__init__.py`.
- Drop `get_active_session_count` from the import block in `commands.py` (still referenced in commands.py? as of step 3 the call was removed; if pylint already flagged it as unused and step 3 dropped it, this is a no-op).
- Delete the existing `test_get_active_session_count` test in `tests/workflows/vscodeclaude/test_sessions.py` (~line 277). It is superseded by `test_build_active_session_set` (added in step 1).

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

## ALGORITHM (test outline)
```
build N mock sessions in tmp_path
patch is_session_active with a Mock(return_value=False)
patch external dependencies (config load, GitHub IssueManager, restart_closed_sessions inner calls)
run execute_coordinator_vscodeclaude(args)  # or _status
assert is_session_active.call_count == N
```

## DATA
- N is the number of sessions in the mock store. Pick a small concrete number (e.g. 3).
- `call_counter.call_count` is an int.

## TDD: Tests first

1. Write the two invariant tests. They should pass already if steps 1-4 were correctly implemented (since `is_session_active` is now only invoked from `build_active_session_set`).
2. If the tests fail with `call_count > N`, identify the leftover call site in steps 1-4 and fix it before proceeding to the deletion.
3. Once the tests pass, delete `get_active_session_count` and the old test.

## Acceptance
- New invariant tests pass with `call_count == N_sessions`.
- The old `test_get_active_session_count` test is deleted.
- `get_active_session_count` no longer appears anywhere in `src/`.
- pylint, pytest, mypy clean (with marker exclusion).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 exactly as described.

Approach:
1. **Add the invariant tests first** (see "Invariant test" section). Decide their location based on whether `tests/cli/commands/` already covers `execute_coordinator_vscodeclaude` — extend if yes, create `tests/workflows/vscodeclaude/test_active_set_invariant.py` if no. Run pytest. They should pass; if `call_count > N_sessions`, find and fix the leftover `is_session_active` call site (likely missed during steps 1-4).
2. Delete `get_active_session_count` from `src/mcp_coder/workflows/vscodeclaude/sessions.py`.
3. Drop `"get_active_session_count"` from `__all__` and from the imports in `src/mcp_coder/workflows/vscodeclaude/__init__.py`.
4. Drop `get_active_session_count` from the imports in `src/mcp_coder/cli/commands/coordinator/commands.py` (if not already removed in step 3).
5. Delete the existing `test_get_active_session_count` test in `tests/workflows/vscodeclaude/test_sessions.py` (~line 277).
6. Run pylint, mypy, pytest (with marker exclusion). Fix until all green.

Commit message: `vscodeclaude: remove get_active_session_count and add call-count invariant test`.
