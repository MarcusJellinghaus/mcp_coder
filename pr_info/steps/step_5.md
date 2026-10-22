# Step 5 — fix_ci deliberate failure on the builder

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 5** exactly as described in
> `pr_info/steps/step_5.md`. If `build_failure_comment` does not exist in
> `src/mcp_coder/workflow_utils/failure_handling.py`, write one line to
> `pr_info/.blocked.txt` and stop. Tests first, then implementation. Run pylint,
> pytest (fast unit set, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/fix_ci/core.py` — `_fail`
- `tests/workflows/fix_ci/test_core.py`

## WHAT

```python
def _fail(project_dir: Path, category_display: str, stage: str, message: str,
          *, update_issue_labels: bool, post_issue_comments: bool) -> int:  # unchanged
```

## HOW

Import `build_failure_comment` from `mcp_coder.workflow_utils.failure_handling`
and replace the hand-written string.

## ALGORITHM

```
comment = build_failure_comment(project_dir, title="CI Fix", kind="Failed",
    fields=[("Category", category_display), ("Stage", stage), ("Error", message)])
handle_workflow_failure(...)   # unchanged
return 1
```

## DATA

Comment: `## ❌ CI Fix Failed` / Category / Stage / Error / Branch / Build.

## Tests

Update the assertions on the posted comment (patch `_branch_head`): heading
`## ❌ CI Fix Failed`, Category (`Ci Fix Exhausted`, `Llm Timeout`, `General`),
Stage and Error lines. Tests asserting no Build line clear `BUILD_URL`.
