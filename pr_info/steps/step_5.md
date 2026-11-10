# Step 5: Run the final check on a re-run with all tasks ticked

Today `progress.completed > 0` skips the final check when a run finds every task already ticked, so relabelling an issue would bypass the gate.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 only: add the test to `tests/workflows/implement/test_core_final_check.py` first, then remove the `progress.completed > 0` condition from the final check in `core.py`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflows/implement/test_core_final_check.py`
- Any existing core test asserting the final check is skipped when no task was completed (search for `mock_check_mypy.assert_not_called()` in `tests/workflows/implement/test_core*.py`).

## WHAT
Remove the `if progress.completed > 0:` wrapper around the final-check block (dedent the block). Nothing else changes.

## HOW
The final-check block runs unconditionally after the task loop exits via `no_tasks`. Step 7's final progress logging (`if progress.completed > 0:`) stays.

## ALGORITHM
None.

## DATA
Unchanged.

## Tests (write first)
- `process_task_with_retry` returns `TaskOutcome(False, "no_tasks")` immediately → `check_and_fix_mypy` is called once with `entry="implement_final"`.
- Same setup with the final check returning `cap` → the run fails as `checks_exhausted`.
- Update existing tests that asserted the final check is not called when no task was completed.
