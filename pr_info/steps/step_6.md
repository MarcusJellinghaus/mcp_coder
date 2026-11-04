# Step 6: The CI fix loop stops on a rejected push

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md`. Write the tests first, then the code. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflow_steps/ci.py`
- `tests/workflow_steps/test_ci_fix_loop.py` (new)

## WHAT

- `_run_ci_fix` calls `push_changes(config.project_dir, raise_on_rejected=True)`.
- `check_and_fix_ci`'s docstring gains `PushRejectedError` under `Raises:`.
- The comment "max 3 attempts" becomes "bounded by `CI_MAX_FIX_ATTEMPTS`".
- The log line "Git push failed during CI fix - failing fast" becomes "Git push failed during CI fix", because a non-rejected failure does continue.

## HOW

Nothing in `_run_ci_fix`, `_run_ci_analysis_and_fix` or `check_and_fix_ci` catches the exception. The fix phase's broad `except` wraps only `prompt_llm`.

## ALGORITHM

```
attempt 1: analysis -> fix -> commit -> push raises PushRejectedError
the exception leaves check_and_fix_ci; no further LLM calls
```

## DATA

`check_and_fix_ci` still returns `bool` in every other case.

## TESTS (`test_ci_fix_loop.py`)

Use `patch_ci_fix_externals` from `tests/ci_fix_drive.py`, and also patch `ci.run_formatters`. Patch `commit.git_push` for detection, and set `ci.push_changes` back to the real function.

- For both `fetch first` and `non-fast-forward`, in a realistic multi-line error string: `check_and_fix_ci` raises `PushRejectedError`, and `prompt_llm` is called exactly twice (one analysis, one fix).
- A non-rejected push failure (`ci.push_changes` returning `False`) still continues to the next attempt and ends as `False` once attempts run out. `prompt_llm` is called `2 * CI_MAX_FIX_ATTEMPTS` times.
- `ci.push_changes` is called with `raise_on_rejected=True`.

Do not edit `tests/workflow_steps/test_ci.py`.
