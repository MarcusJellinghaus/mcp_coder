# Step 11 — `workflow_steps/rebase._classify_failed_rebase` merge-tree probe

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_11.md`. Implement step 11 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(rebase-step): classify failed rebase via probe_rebase_conflicts`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `probe_rebase_conflicts` (from `mcp_workspace.git_operations.rebase`)
- `src/mcp_coder/workflow_steps/rebase.py` — `_classify_failed_rebase`; delete `_TREE_OID`, the `re` import and the `execute_command` import
- `tests/workflow_steps/test_rebase.py` — merge-tree tests (exact argv ~140) and remaining `execute_command` patches

## WHAT

```python
def _classify_failed_rebase(project_dir: Path, base: str) -> tuple[RebaseReason, tuple[str, ...]]:
    try:
        probe = probe_rebase_conflicts(project_dir, f"origin/{base}")
    except Exception:  # pylint: disable=broad-exception-caught  # never fail the workflow
        return "rebase_failed", ()
    if probe["status"] == "conflict":
        return "conflict", tuple(probe["files"])
    return "rebase_failed", ()   # clean / unsupported (git < 2.38) / error
```

Check `status`, not `success` (`success` is True only for `clean`). Docstring: replace the
`git merge-tree` exit-code description with the `RebaseProbe.status` mapping.

## Tests (write first)

Patch `mcp_coder.workflow_steps.rebase.probe_rebase_conflicts`.

- `status="conflict", files=["a.py", "b.py"]` → `("conflict", ("a.py", "b.py"))`; called with `(project_dir, "origin/main")`.
- `status="clean"` / `"unsupported"` / `"error"` → `("rebase_failed", ())`.
- raises → `("rebase_failed", ())`.
- After this step no test in the file patches `mcp_coder.workflow_steps.rebase.execute_command`.

## DATA

- `RebaseProbe` keys read: `status`, `files`. `RebaseOutcome` unchanged.
