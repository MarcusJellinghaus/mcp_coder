# Step 7 — Part 3: review loop fails on commit/push failure

**Depends on step 6** (fallback commit message) — without it, transient LLM failures would abort whole review runs.

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_7.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/workflows/review/core.py` — the fix-application block in `run_review_workflow` (~lines 259–261):
  ```python
  run_formatters(project_dir)
  commit_changes(project_dir, provider)   # return value discarded  ← bug
  push_changes(project_dir)               # return value discarded  ← bug
  ```
- Tests: `tests/workflows/review/test_core.py`

## WHAT

Check both return values. On `False`: write a round-log entry naming the failed step, then route through the existing `_fail(...)` path (same as the `LLMTimeoutError`/`McpServersUnavailableError` handler directly above) with reason `"commit-failed"` / `"push-failed"`.

Note on labels: `_fail` resolves `reason` via `config.failure_labels.get(reason, config.failure_labels["general"])`, so the new reasons fall back to the `general` failure label **by design** — do NOT add new entries to `failure_labels` (the label ids would have to exist in every repo's label config). The distinct reason still lands in the failure message (`"... review failed: commit-failed"`) and in the round log.

## ALGORITHM

```
run_formatters(project_dir)                       # unchanged (non-fatal today; leave as-is)
for step_name, ok in (("commit-failed", commit_changes(...)), ("push-failed", push_changes(...))):
    # evaluate sequentially; skip push when commit already failed
    if not ok:
        write_round_log(project_dir, config, run_number, round_number,
                        findings=report, decisions=str(verdict),
                        changes=step_name, escalate_reason=step_name)
        return _fail(config, project_dir, step_name,
                     update_issue_labels=update_issue_labels,
                     post_issue_comments=post_issue_comments)
```
(Plain sequential `if not commit_changes(...)` / `if not push_changes(...)` blocks are fine — the loop above is only illustrating the shape. Push must not run when commit failed.)

Keep passing the step-5 session params to `commit_changes` (already done in step 5 at this call site).

## DATA

- `run_review_workflow` returns `1` via `_fail` on either failure (matches the timeout/MCP handler above).
- Round log entry: `changes` and `escalate_reason` carry `"commit-failed"` or `"push-failed"` so the log names the failed step.

## TESTS (write first)

In `tests/workflows/review/test_core.py` (existing pattern mocks `commit_changes`/`push_changes` at module path `mcp_coder.workflows.review.core`):
- `commit_changes` returns `False` → run returns `1`, `handle_workflow_failure` (or `_fail`'s observable effects per existing test style) invoked with the `general` fallback label, round log written with `"commit-failed"`, and `push_changes` NOT called.
- `push_changes` returns `False` → run returns `1`, round log written with `"push-failed"`.
- Both return `True` → loop continues as before (existing tests must pass).
- Clean-tree round: `commit_changes` mocked `True` (per step 6 semantics) → proceeds normally — acceptance "a round with no file changes proceeds normally".

## Commit

`fix: fail review run when commit or push fails instead of looping on invisible state (#1090)`
