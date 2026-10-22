# Step 3 — create_plan deliberate failure on the builder

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 3** exactly as described in
> `pr_info/steps/step_3.md`. If `build_failure_comment` does not exist in
> `src/mcp_coder/workflow_utils/failure_handling.py`, write one line to
> `pr_info/.blocked.txt` and stop. Tests first, then implementation. Run pylint,
> pytest (fast unit set, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/create_plan/core.py` — delete `_format_failure_comment`; `_handle_workflow_failure` calls the builder
- `src/mcp_coder/workflows/create_plan/__init__.py` — drop `_format_failure_comment` import and `__all__` entry
- `tests/workflows/create_plan/test_failure_handling.py`

## WHAT

```python
def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_issue_labels: bool,
    post_issue_comments: bool,
    issue_number: int,
) -> None:  # signature unchanged
```

## HOW

- Import `build_failure_comment` from `mcp_coder.workflow_utils.failure_handling`;
  drop the `format_elapsed_time` import if now unused.
- Search for other `_format_failure_comment` references under `src/` and `tests/`
  for create_plan and update them.

## ALGORITHM

```
diff_stat = get_diff_stat(project_dir)
extra = f"### Uncommitted Changes\n```\n{diff_stat}\n```" if diff_stat else None
comment_body = build_failure_comment(project_dir, title="Planning", kind="Failed",
    fields=[("Stage", failure.stage), ("Error", failure.message)],
    elapsed=failure.elapsed_time, extra_section=extra)
handle_workflow_failure(... comment_body=comment_body ...)   # as today
```

## DATA

Comment: `## ❌ Planning Failed` / Stage / Error / Branch / Elapsed / Build, then
the Uncommitted Changes section only when there is a diff (current behaviour kept).

## Tests

Rewrite the `_format_failure_comment` tests as `_handle_workflow_failure` tests
(patch `handle_workflow_failure`, `get_diff_stat` and `_branch_head`; read the
`comment_body` kwarg):
- heading `## ❌ Planning Failed`; Stage / Error lines present
- Elapsed present when `elapsed_time` set, absent when `None`
- section present with a diff, absent with an empty diff
