# Step 4 — Review pre-flight

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/review/core.py`
- `tests/workflows/review/test_core_formatter_preflight.py` (created in step 3) — add the
  pre-flight test there (`tests/workflows/review/test_core_after_steps.py` is at 736/750).

## WHAT

At the top of `body()` in `run_review_workflow` (shared by implementation and plan lanes),
beside Gate 1:

```python
formatter_err = check_formatter_config(project_dir, warn_legacy_key=True)
if formatter_err:
    return _fail(
        config, project_dir, "general",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
        details=formatter_err,
        elapsed=time.time() - start_time,
    )
```

## HOW

- Extend the existing import:
  `from mcp_coder.workflow_steps.commit import check_formatter_config, commit_changes, push_changes, run_formatters`.
- Place it before Gate 1 so it runs for both lanes before any LLM call.
- Backstop: `run_formatters` at `core.py:468` may raise `FormatterConfigError` → `run_guarded`;
  the CI gate in `review/steps.py:140` already maps any exception to `"general"`. No change.

## ALGORITHM

```
msg = check_formatter_config(project_dir, warn_legacy_key=True)
if msg: return _fail(..., "general", details=msg, ...)
... existing Gate 1 ...
```

## DATA

Returns `_fail(...)`'s exit code; failure comment carries mcp-tools-py's message in `details`.

## Tests

- Patch `mcp_coder.workflows.review.core.check_formatter_config` → `"No formatter declared: X"`:
  `_fail` called with reason `"general"` and `details` containing the message; reviewer LLM not called.
  Use the existing review conftest mocks.
- Patched to `None` → workflow proceeds (existing tests cover this via the root fixture).
