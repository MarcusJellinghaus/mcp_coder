# Step 6: Run the final check on a re-run with all tasks ticked

Today `progress.completed > 0` skips the final check when a run finds every task already ticked, so relabelling an issue would bypass the gate.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement step 6 only: add the test to `tests/workflows/implement/test_core_final_check.py` and patch the unpatched `no_tasks` core tests first, then remove the `progress.completed > 0` condition from the final check in `core.py`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflows/implement/test_core_final_check.py`
- Any existing core test asserting the final check is skipped when no task was completed (search for `mock_check_mypy.assert_not_called()` in `tests/workflows/implement/test_core*.py`).
- Any core test whose task loop ends with `no_tasks` and that does not patch `core.check_and_fix_mypy` (see Tests).

## WHAT
Remove the `if progress.completed > 0:` wrapper around the final-check block (dedent the block). Nothing else changes.

## HOW
The final-check block runs unconditionally after the task loop exits via `no_tasks`. The final progress logging in `core.py`'s "Step 7" block (`if progress.completed > 0:`) stays.

## ALGORITHM
None.

## DATA
Unchanged.

## Tests (write first)
- `process_task_with_retry` returns `TaskOutcome(False, "no_tasks")` immediately → `check_and_fix_mypy` is called once with `entry="implement_final"`.
- Same setup with the final check returning `cap` → the run fails as `checks_exhausted`.
- Update existing tests that asserted the final check is not called when no task was completed.
- Find every core test (`tests/workflows/implement/test_core*.py`) where `process_task_with_retry` returns `no_tasks` (on the first or a later round) and `core.check_and_fix_mypy` is not patched. Patch it with `return_value=CheckOutcome("clean")`; otherwise, once the gate is gone, those tests run the real check loop (and after step 7, `check@standard` and `test@quick`). Put new patches only where the file stays under 750 lines; `test_core_workflow.py` is near the limit, so a file-level autouse fixture there is fine if decorators don't fit.
