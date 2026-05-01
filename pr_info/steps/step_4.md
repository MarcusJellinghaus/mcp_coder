# Step 4 — Remove `get_active_session_count`

## Goal
With all four call sites converted (steps 1-3), `get_active_session_count` is dead code. Remove it and clean up the old single-purpose test. The cross-flow invariant test was added in step 3, so this step is deletion-only — no new tests are added here.

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/sessions.py` (delete function)
- Modified: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (drop from `__all__` and from imports)
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (drop unused import if still present)
- Modified: `tests/workflows/vscodeclaude/test_sessions.py` (delete `test_get_active_session_count_with_mocked_pid_check` at line 224)

## WHAT
- Delete `def get_active_session_count() -> int` from `sessions.py`.
- Drop `"get_active_session_count"` from the `__all__` list and the corresponding import line in `src/mcp_coder/workflows/vscodeclaude/__init__.py`.
- Drop `get_active_session_count` from the import block in `commands.py` (still referenced in commands.py? as of step 2 the call was removed; if pylint already flagged it as unused and step 2 dropped it, this is a no-op).
- Delete the existing `test_get_active_session_count_with_mocked_pid_check` test in `tests/workflows/vscodeclaude/test_sessions.py` (line 224). It is superseded by `test_build_active_session_set` (added in step 1).

## DATA
- No new tests in this step. The cross-flow invariant test (`is_session_active.call_count == N_sessions` for launch and status) lives in step 3, alongside the status conversion that completed the conversion of every call site.

## TDD: Tests first

1. Confirm there are no remaining references to `get_active_session_count` in `src/` (use `Grep` / `mcp__workspace__search_files`). The only consumer left should be the `test_get_active_session_count_with_mocked_pid_check` test that this step deletes.
2. Run the existing test suite (with marker exclusion). The invariant test from step 3 should still report `call_count == N_sessions` once `get_active_session_count` is gone.

## Acceptance
- The old `test_get_active_session_count_with_mocked_pid_check` test is deleted.
- `get_active_session_count` no longer appears anywhere in `src/`.
- The step-3 invariant test still passes (`call_count == N_sessions`).
- pylint, pytest, mypy clean (with marker exclusion).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4 exactly as described.

Approach:
1. Confirm no remaining references to `get_active_session_count` in `src/` other than the function definition itself. If a reference remains in `commands.py` or anywhere else, that means a previous step missed something — fix that first.
2. Delete `get_active_session_count` from `src/mcp_coder/workflows/vscodeclaude/sessions.py`.
3. Drop `"get_active_session_count"` from `__all__` and from the imports in `src/mcp_coder/workflows/vscodeclaude/__init__.py`.
4. Drop `get_active_session_count` from the imports in `src/mcp_coder/cli/commands/coordinator/commands.py` (if not already removed in step 2).
5. Delete the existing `test_get_active_session_count_with_mocked_pid_check` test in `tests/workflows/vscodeclaude/test_sessions.py` (line 224).
6. Run pylint, mypy, pytest (with marker exclusion). Fix until all green.

Commit message: `vscodeclaude: remove dead get_active_session_count`.
