# Step 4: Automated code review reports a rejected push

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`. Write the tests first, then the code. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflows/review/steps.py`
- `src/mcp_coder/workflows/review/handoff.py`
- `src/mcp_coder/workflows/review/config.py`
- `src/mcp_coder/workflows/review/core.py` (comment only)
- `tests/workflows/review/test_config.py`
- `tests/workflows/review/test_core_flush_ci.py`

## WHAT

```python
# config.py: REVIEW_IMPLEMENTATION.failure_labels only; REVIEW_PLAN is unchanged
"branch_moved": "code_review_ci",

# handoff.py
_FAIL_REASONS["branch_moved"] = (
    "Branch moved",
    PUSH_REJECTED_ERROR,
)
```

## HOW

- **`steps._after_steps`:** add `except PushRejectedError` before the broad `except Exception`, and return `"branch_moved"`. Use `comment_safe(str(exc))`. Do not use `comment_safe(exception_summary(exc))`, which adds a type-name prefix. Add `"branch_moved"` to the docstring's reason list.
- **`handoff._fail`:** compute the next step from the reason, and add `("Next step", next_step)` to the fields. No `review/core.py` call site changes.
- **`review/core.py`:** the `elif reason:` branch is already terminal after writing and flushing the round log. Only add `branch_moved` to its comment's reason list. Do not reuse `"ci"`, which is non-terminal mid-loop and would rebase and push with a lease in the next round.

## ALGORITHM

```python
# steps.py
except PushRejectedError as exc:
    logger.error("CI fix push was rejected; failing the review: %s", exc)
    return "branch_moved", outcome, comment_safe(str(exc))

# handoff.py, inside _fail
next_step = (
    f"{BRANCH_MOVED_NEXT_STEP} Then set `status-17:code-review-bot`."
    if reason == "branch_moved"
    else None
)
```

## DATA

- `_after_steps` returns `("branch_moved", RebaseOutcome, "<sentence>: <status line>")`.
- `_fail` returns `1`, with label `code_review_ci`.
- The status line can lose only its end to the 300-character cap, because the sentence comes first.

## TESTS

- `test_config.py`: add `"branch_moved": "code_review_ci"` to the exact dict in `test_failure_labels`. `REVIEW_PLAN` stays unchanged.
- `test_core_flush_ci.py`, using the shared `env` fixture, with `env.check_and_fix_ci.side_effect = PushRejectedError(...)`:
  - **Dismiss path:** the result is `1`, the label is `code_review_ci`, and the comment has `Branch moved`, the error text with no `PushRejectedError:` prefix, and `status-17:code-review-bot`.
  - **Mid-loop `tasks` path:** the result is `1`, the label is `code_review_ci`, `env.attempt_rebase_and_push.call_count == 1` (no further rebase), and no second reviewer round runs.
  - **Long status line:** the `Error` field is at most 300 characters and starts with the fixed sentence.
