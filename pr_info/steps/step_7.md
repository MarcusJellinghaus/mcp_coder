# Step 7: Empty analysis on attempt 2 or later counts as a failed attempt

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md`. Write the tests first, and confirm they fail before changing the code. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflow_steps/ci.py`
- `tests/workflow_steps/test_ci_fix_loop.py`

## WHAT

In `_run_ci_analysis_and_fix`, an empty analysis returns `(True, None)` on every attempt. The `fix_attempt == 0` branch and its `False, True` return go away.

## HOW

Only this one branch changes. The other graceful exit, "No failed jobs found" returning `False, True`, stays as it is.

## ALGORITHM

```python
if not problem_description:
    logger.warning("CI analysis produced no problem description")
    return True, None  # Consumes this attempt
```

## DATA

The return shape `(should_continue, return_value)` is unchanged.

## TESTS (`test_ci_fix_loop.py`)

- With `patch_ci_fix_externals` and `prompt_llm` returning empty text for every call: `check_and_fix_ci` returns `False`, `prompt_llm` is called `CI_MAX_FIX_ATTEMPTS` times, and `commit_changes` is not called.
- `_run_ci_analysis_and_fix` with `fix_attempt=1` and an empty analysis returns `(True, None)`.
