# Step 2: `implement` reports a rejected push

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. Write the tests first, then the code. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflows/implement/failure_reporting.py`
- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflows/implement/test_failure_reporting.py`
- `tests/workflows/implement/test_core_failure_categories.py`

## WHAT

```python
# failure_reporting.py
FAILURE_LABELS["branch_moved"] = "ci_fix_needed"
CATEGORY_DISPLAY["branch_moved"] = "Branch Moved"

def _fail(project_dir, reason, *, stage, message, start_time,
          update_issue_labels=False, post_issue_comments=False,
          next_step: str | None = None) -> int: ...
```

## HOW

- `_fail` adds `("Next step", next_step)` to the comment fields. `build_failure_comment` drops `None` values and orders fields by `FIELD_ORDER`.
- In `core.py`, import `BRANCH_MOVED_NEXT_STEP` and `PushRejectedError` from `mcp_coder.workflow_steps.commit`.
- Add a separate `except PushRejectedError` to the `try` around `check_and_fix_ci`. Without it, the exception reaches `run_guarded` and lands on `implementing_failed`.

## ALGORITHM

```python
except PushRejectedError as exc:
    return fail(
        "branch_moved",
        stage="CI pipeline fix",
        message=str(exc),
        next_step=f"{BRANCH_MOVED_NEXT_STEP} Then set `status-05:plan-ready`.",
    )
```

## DATA

- `_fail` returns `1` as today.
- `WorkflowFailure.category` is `ci_fix_needed`.
- The comment contains `**Category:** Branch Moved` and a `**Next step:**` line.

## TESTS

- `test_failure_reporting.py`:
  - The two new mapping entries exist.
  - `_fail` with `next_step` renders the field.
  - `_fail` without it renders no `Next step` line.
- `test_core_failure_categories.py`: follow `test_ci_analysis_timeout_categorized_as_llm_timeout`, with `mock_check_ci.side_effect = PushRejectedError(...)`. Assert:
  - The result is `1`.
  - `failure.category == "ci_fix_needed"` and `failure.stage == "CI pipeline fix"`.
  - The comment body contains `status-05:plan-ready`.

Do not edit `tests/workflows/implement/test_core_workflow.py`.
