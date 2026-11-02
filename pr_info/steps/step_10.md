# Step 10 — implement logs the rebase outcome reason (#430)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_10.md` only.
> Write the test first, then the implementation. Run pylint, pytest (fast unit
> set, `-n auto`), mypy and lint-imports until they pass, run `run_format_code`,
> and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/implement/core.py` (step 1.5)
- Test: `tests/workflows/implement/test_core_workflow.py`

## WHAT / HOW

Keep the git-only call, outside `run_guarded`, result not acted on. No LLM rebase.

## ALGORITHM

```
outcome = _attempt_rebase_and_push(project_dir)
logger.log(OUTPUT, "Rebase result: %s", outcome.reason)
```

(`OUTPUT` from `mcp_coder.utils.log_utils`, same wording as create_pr.)

## DATA

None.

## Tests

- With `_attempt_rebase_and_push` mocked to `RebaseOutcome("dirty_tree")`, the log
  (caplog) contains `Rebase result: dirty_tree` and the workflow continues.
