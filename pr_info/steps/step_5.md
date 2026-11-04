# Step 5: `check_branch_status` reports a rejected push

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`. Write the tests first, then the code. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/cli/commands/check_branch_status.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`

## WHAT

No new functions. Add one `except` clause to `_run_auto_fixes`.

## HOW

- Import `BRANCH_MOVED_NEXT_STEP` and `PushRejectedError` from `...workflow_steps.commit`.
- Add the clause before the broad outer `except Exception`. It covers both the single-attempt and retry paths, because both sit inside that `try`.

## ALGORITHM

```python
except PushRejectedError as exc:
    logger.error("CI fix stopped: %s. %s", exc, BRANCH_MOVED_NEXT_STEP)
    return False
```

## DATA

`_run_auto_fixes` returns `False`. No label or comment, because this caller has neither.

## TESTS

In `TestRunAutoFixes`, patching `check_and_fix_ci` to raise `PushRejectedError`, parametrized over `fix_attempts` of 1 and 3:

- The result is `False`.
- `check_and_fix_ci` is called exactly once, so there is no retry.
- `caplog` contains the error text and the next-step text.
