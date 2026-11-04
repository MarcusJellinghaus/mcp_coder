# Step 3: `fix-ci` reports a rejected push

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`. Write the tests first, then the code. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflows/fix_ci/core.py`
- `tests/workflows/fix_ci/test_core.py`

## WHAT

```python
def _fail(project_dir, category_display, stage, message, *,
          update_issue_labels, post_issue_comments,
          next_step: str | None = None) -> int: ...
```

## HOW

- `_fail` adds `("Next step", next_step)` to the comment fields. `WorkflowFailure.category` stays `pr_ci_failed`.
- Import `BRANCH_MOVED_NEXT_STEP` and `PushRejectedError` from `mcp_coder.workflow_steps.commit`.
- Add a separate `except PushRejectedError` next to the `LLMTimeoutError` handler. Do not call `_refresh_if_pushed()` in it, including when an earlier attempt in the run pushed successfully. Without the handler, `run_guarded` would set `status-83`.

## ALGORITHM

```python
except PushRejectedError as exc:
    # No refresh: local HEAD holds a commit the remote does not have.
    return _fail(
        project_dir, "Branch Moved", "CI pipeline fix", str(exc),
        next_step=f"{BRANCH_MOVED_NEXT_STEP} Then set `status-10:pr-created` so CI is re-detected.",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
```

## DATA

- Returns `1`.
- The label moves from `fixing_ci` to `pr_ci_failed`.
- The comment contains `**Category:** Branch Moved` and a `**Next step:**` line.

## TESTS (`test_core.py`)

With `check_and_fix_ci` raising `PushRejectedError`:

- The result is `1`, `failure.category == "pr_ci_failed"`, and the comment has the category, the error text and `status-10:pr-created`.
- `refresh_pr_description` is not called, even with `refresh_mocks.sha` returning a different value after the loop, which is what an unpushed fix commit looks like.

Existing behaviour stays pinned: an `LLMTimeoutError` with a moved HEAD still refreshes.
