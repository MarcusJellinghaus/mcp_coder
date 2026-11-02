# Step 9 — create_pr sends a still-`dirty` PR to fix-conflict

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_9.md` only.
> Adjust the tests first, then the implementation. Run pylint, pytest (fast unit
> set, `-n auto`), mypy and lint-imports until they pass, run `run_format_code`,
> and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/create_pr/post_creation.py` (`_check_mergeability_and_ci`,
  `run_post_creation`, module docstring)
- `src/mcp_coder/workflows/create_pr/core.py` (workflow docstring only)
- Tests: `tests/workflows/create_pr/test_post_creation.py`,
  `tests/workflows/create_pr/test_workflow_labels.py`

## WHAT / HOW

- Still `dirty` after the rebase → `return "merge_conflict"` (status-71) instead of
  `"pr_merge_conflict"`. Log line: "...; handing to fix-conflict".
- Docstrings: label set `"merge_conflict", "failing_ci" or "pr_created"`;
  `create_pr/core.py`: "final label pr_created / merge_conflict / failing_ci, i.e. 10 / 71 / 81".
- No loop: fix-conflict ends at `status-10` or `status-74`.

## ALGORITHM

```
if state == "dirty":
    ...existing rebase + reset...
    if _poll_mergeable_state(...) == "dirty": return "merge_conflict"
```

## DATA

Label id string.

## Tests

- `test_dirty_after_rebase_returns_merge_conflict` and
  `test_merge_conflict_still_refreshes` expect `"merge_conflict"`.
- `test_workflow_labels.py` parametrize: replace `"pr_merge_conflict"` with `"merge_conflict"`.
