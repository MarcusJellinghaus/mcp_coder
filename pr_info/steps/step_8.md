# Step 8: Failure-comment progress from the tracker

See `pr_info/steps/summary.md` (§6 of issue #1093, #1107).

## WHERE
- `src/mcp_coder/workflows/implement/failure_reporting.py`: `_comment_parts`, `_fail`
- `src/mcp_coder/workflows/implement/core.py`: the `fail` partial and `build_comment`
- Tests: `tests/workflows/implement/test_failure_reporting.py`, affected `test_core*.py`

## WHAT
```python
def _comment_parts(reason: str, project_dir: Path) -> tuple[list[CommentField], str]: ...
def _fail(project_dir, reason, *, stage, message, start_time,
          update_issue_labels=False, post_issue_comments=False) -> int: ...
```
`progress` is no longer a parameter of either. `Progress` stays in `failure_reporting.py`;
`core.py` still uses it for the final mypy gate (`completed`) and `round_cap` (`total`).

## HOW
- `_comment_parts` reads `get_task_counts(str(project_dir / PR_INFO_DIR))`
  (`from mcp_coder.workflow_utils.task_tracker import get_task_counts`, `from .constants import PR_INFO_DIR`).
- `core.py`: remove `progress=progress` from `partial(_fail, ...)`; `build_comment` calls
  `_comment_parts("general", project_dir)`.

## ALGORITHM
```
try: total, done = get_task_counts(pr_info)
except Exception: total, done = 0, 0   # missing / unparseable tracker
progress_value = f"{done}/{total} tasks completed" if total > 0 else None
```

## DATA
Fields unchanged in shape: `[("Category", ...), ("Progress", value_or_None)]` plus the Uncommitted Changes section.

## Tests (write first)
- A tracker with 21 tasks, 5 checked → Progress `"5/21 tasks completed"`.
- No tracker / tracker without `## Tasks` → Progress value `None` (line omitted by the builder).
- Net-path `build_comment` uses the same tracker-sourced value.
- Update existing tests that built `Progress(...)` for the comment.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`. Implement step 8 only:
> write the tests first, then make `_comment_parts` take done/total from `get_task_counts()`
> (omitted when unreadable), drop the `progress` parameter from `_comment_parts` / `_fail`
> and update `core.py`. Run pylint, pytest (`-n auto`, unit markers) and mypy.
