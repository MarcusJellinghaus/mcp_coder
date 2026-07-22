# Step 3 — Move rebase into `workflow_steps`

**Goal:** Relocate the rebase-and-push step. Must land **after** Step 2, because
`rebase` imports `push_changes` — moving it while `push_changes` still lived in
`implement` would make `workflow_steps.rebase → workflows.implement` an upward import
(import-linter RED).

## WHERE

Create:
- `src/mcp_coder/workflow_steps/rebase.py`
- `tests/workflow_steps/test_rebase.py`

Modify:
- `src/mcp_coder/workflows/implement/core.py` (import rebase from `workflow_steps`)
- `src/mcp_coder/workflows/implement/rebase.py` → becomes a thin re-export shim, or is
  removed if no test/patch target references it.

Move `tests/workflows/implement/test_rebase.py` → `tests/workflow_steps/test_rebase.py`.

## WHAT (signatures — unchanged)

In `workflow_steps/rebase.py`:
```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]
def _attempt_rebase_and_push(project_dir: Path) -> bool
```

## HOW (integration points)

- `rebase.py` imports `rebase_onto_branch` (mcp_workspace_git), `detect_base_branch`
  (workflow_utils.base_branch), and `push_changes` from
  `mcp_coder.workflow_steps.commit`.
- `implement/core.py`: change `from .rebase import _attempt_rebase_and_push` to
  `from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push`.
- If `implement/rebase.py` is kept as a shim, it re-exports
  `_attempt_rebase_and_push` for any lingering `patch()` targets; otherwise delete it.

## ALGORITHM

Pure move — copy both function bodies verbatim (rebase → on success `push_changes(...,
force_with_lease=True)`; never blocks the workflow) and repoint the `push_changes`
import to `workflow_steps.commit`. No logic edits.

## DATA

`_get_rebase_target_branch` → `Optional[str]` (branch name or `None`).
`_attempt_rebase_and_push` → `bool` (True only if rebase **and** force-push succeeded).

## TDD

Move `test_rebase.py` into `tests/workflow_steps/`, updating patch targets to
`mcp_coder.workflow_steps.rebase.*` (e.g. `rebase_onto_branch`, `detect_base_branch`,
`push_changes`). Confirm the "rebase succeeds but push fails → False" and "no target →
False" cases are preserved. Make the tests green after the move.

## Checks / commit

All enforcers + pylint / pytest / mypy green. One commit:
`refactor(workflow_steps): move rebase step`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Move
> `_get_rebase_target_branch` and `_attempt_rebase_and_push` verbatim from
> `implement/rebase.py` into a new `workflow_steps/rebase.py`, importing `push_changes`
> from `mcp_coder.workflow_steps.commit`. Repoint `implement/core.py` to import the
> rebase step from `workflow_steps`. Move `test_rebase.py` into
> `tests/workflow_steps/` with updated patch targets. Keep `implement/rebase.py` as a
> thin re-export shim only if a test requires it, otherwise remove it. Do not change
> logic. Verify all enforcers (especially `run_lint_imports_check` — this is the step
> that would go RED if ordering were wrong) and the pylint/pytest/mypy trio are green,
> then produce one commit.
