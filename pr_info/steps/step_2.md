# Step 2 — `run_guarded(workflow_title=…)` and every crash net on the builder

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 2** exactly as described in
> `pr_info/steps/step_2.md`. Step 1's `build_failure_comment` must already exist in
> `src/mcp_coder/workflow_utils/failure_handling.py`; if it does not, write one line
> to `pr_info/.blocked.txt` and stop. Update tests first, then the implementation.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflow_utils/failure_handling.py` — `run_guarded`
- `src/mcp_coder/workflows/implement/failure_reporting.py` — replace `format_failure_comment` with `_comment_parts`; `_fail` uses the builder; drop `build_url`
- `src/mcp_coder/workflows/implement/core.py` — net `build_comment`, drop `build_url` and `import os`
- `src/mcp_coder/workflows/create_plan/core.py`, `create_pr/core.py`, `fix_ci/core.py`, `fix_conflict/core.py` — `workflow_title=`
- `src/mcp_coder/workflows/review/config.py` — `display_name`
- `src/mcp_coder/workflows/review/core.py` — `workflow_title=config.display_name`
- Tests: `tests/workflow_utils/test_run_guarded.py`, `tests/workflows/implement/test_failure_reporting.py`, `test_core_workflow.py`, `test_core_failure_routing.py`, `tests/workflows/review/test_core.py` (`:496`), `tests/workflows/review/test_config.py`, plus net assertions in create_plan / create_pr / fix_ci / fix_conflict tests

## WHAT

```python
# failure_handling.py
def run_guarded(
    body: Callable[[], int],
    *,
    project_dir: Path,
    from_label_id: str,
    general_category: str,
    workflow_title: str,                      # replaces comment_header
    build_comment: Callable[[GuardOutcome], tuple[list[CommentField], str | None]] | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
    issue_number: int | None = None,
) -> int:

# implement/failure_reporting.py
def _comment_parts(
    reason: str, progress: Progress, project_dir: Path
) -> tuple[list[CommentField], str]:
    """Category + Progress fields and the ### Uncommitted Changes section."""

def _fail(project_dir, reason, *, stage, message, progress, start_time,
          update_issue_labels=False, post_issue_comments=False) -> int:  # build_url removed

# review/config.py
@dataclass(frozen=True)
class ReviewConfig:
    name: str
    display_name: str          # new, right after `name`
    ...
REVIEW_IMPLEMENTATION = ReviewConfig(name="review-implementation", display_name="Implementation Review", ...)
REVIEW_PLAN = ReviewConfig(name="review-plan", display_name="Plan Review", ...)
```

## HOW

- `_net` in `run_guarded`:
  ```
  extra_fields, extra = build_comment(outcome) if build_comment else ([], None)
  comment = build_failure_comment(project_dir, title=workflow_title, kind="Crashed",
      fields=[("Stage", stage), ("Error", message), *extra_fields],
      elapsed=outcome.elapsed_time, extra_section=extra)
  ```
- Titles: implement `"Implementation"`, create_plan `"Planning"`, create_pr
  `"PR Creation"`, fix_ci `"CI Fix"`, fix_conflict `"Fix Conflict"`, review
  `config.display_name`.
- implement net: `build_comment=lambda o: _comment_parts("general", progress, project_dir)`
  (or a small named closure, matching surrounding style).
- implement `_fail`:
  ```
  fields, extra = _comment_parts(reason, progress, project_dir)
  body = build_failure_comment(project_dir, title="Implementation", kind="Failed",
      fields=[("Stage", stage), ("Error", message), *fields],
      elapsed=elapsed, extra_section=extra)
  ```
- Remove `build_url` from `_fail`, the `partial(...)` in `implement/core.py`, and
  `build_url = os.environ.get("BUILD_URL")`; remove `import os` (only use).
- Replace the module docstring / `CATEGORY_DISPLAY` comment wording about
  "byte-identical to earlier releases" — `CATEGORY_DISPLAY` stays (still renders
  `"Llm Timeout"`), only the byte-identical claim goes.
- Update `implement/core.py` import list (`format_failure_comment` →
  `_comment_parts`; drop `get_diff_stat` if now unused there).

## ALGORITHM (`_comment_parts`)

```
category = CATEGORY_DISPLAY.get(reason, CATEGORY_DISPLAY["general"])
progress_value = f"{progress.completed}/{progress.total} tasks completed" if progress.total > 0 else None
diff = get_diff_stat(project_dir)
section = f"### Uncommitted Changes\n```\n{diff or 'No uncommitted changes'}\n```"
return [("Category", category), ("Progress", progress_value)], section
```

## DATA

- Net comment: `## ❌ <title> Crashed` / Stage / Error / … / Branch / Elapsed / Build.
- `build_comment` returns `(list[CommentField], str | None)`.

## Tests

- Autouse fixture (or `patch`) stubbing
  `mcp_coder.workflow_utils.failure_handling._branch_head` → `("feat", "abc1234")`
  in every test that renders a comment through the builder.
- `test_run_guarded.py`: `_run` default kwarg `workflow_title="Test Workflow"`;
  net comment starts with `## ❌ Test Workflow Crashed`, contains Stage / Error /
  Elapsed; `build_comment` extra fields and section are included; a
  `build_comment` cannot change the heading.
- implement tests: `format_failure_comment` tests become `_fail` / `_comment_parts`
  tests (heading `## ❌ Implementation Failed`, Category, Progress, section).
  Tests that passed `build_url=` now set `BUILD_URL` via `patch.dict(os.environ, …)`;
  tests asserting no Build line clear it.
- `review/test_core.py:496`: assert `"## ❌ Plan Review Crashed"`.
- `review/test_config.py`: assert both `display_name` values.
- Other workflows' net tests: assert their `## ❌ <title> Crashed` heading where
  they currently assert the old header.
