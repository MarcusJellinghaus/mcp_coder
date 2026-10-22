# Step 4 — create_pr deliberate failure on the builder

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 4** exactly as described in
> `pr_info/steps/step_4.md`. If `build_failure_comment` does not exist in
> `src/mcp_coder/workflow_utils/failure_handling.py`, write one line to
> `pr_info/.blocked.txt` and stop. Tests first, then implementation. Run pylint,
> pytest (fast unit set, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/create_pr/helpers.py` — delete `format_failure_comment`; `handle_create_pr_failure` calls the builder
- `src/mcp_coder/workflows/create_pr/core.py` — delete the `_format_failure_comment` alias and its import; **keep** the `_handle_create_pr_failure` alias (tests patch it)
- `tests/workflows/create_pr/test_failure_handling.py`

## WHAT

```python
def handle_create_pr_failure(
    stage: str, message: str, project_dir: Path, update_issue_labels: bool,
    post_issue_comments: bool = False, elapsed_time: float | None = None,
    issue_number: int | None = None, pr_url: str | None = None,
    pr_number: int | None = None, is_cleanup_failure: bool = False,
    category: str = "pr_creating_failed",
) -> None:  # signature unchanged
```

## HOW

- Import `build_failure_comment`; drop `format_elapsed_time` import if unused.
- Search `src/` and `tests/` for `format_failure_comment` /
  `_format_failure_comment` in create_pr and update them.

## ALGORITHM

```
pr = f"[#{pr_number}]({pr_url})" if pr_url and pr_number else None
note = "> **Note:** pr_info/ directory may still exist on the branch" if is_cleanup_failure else None
comment = build_failure_comment(project_dir, title="PR Creation", kind="Failed",
    fields=[("Stage", stage), ("Error", message), ("PR", pr)],
    elapsed=elapsed_time, extra_section=note)
handle_workflow_failure(... comment_body=comment ...)   # as today
```

## DATA

Comment: `## ❌ PR Creation Failed` / Stage / Error / Branch / PR / Elapsed / Build,
then the cleanup note when `is_cleanup_failure`.

## Tests

Rewrite the four `_format_failure_comment` tests as `handle_create_pr_failure`
tests (patch `handle_workflow_failure` in `helpers` and `_branch_head`):
- heading `## ❌ PR Creation Failed`
- `**PR:** [#42](https://…/pull/42)` when both given; absent otherwise
- cleanup note present only with `is_cleanup_failure=True`
- Elapsed present/absent
Existing tests patching `create_pr.core._handle_create_pr_failure` stay unchanged.
