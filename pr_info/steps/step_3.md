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
  removed if no test/patch target references it (see the TDD note — after the split
  below, it likely has **no** remaining patch target and can be cleanly removed).
- `tests/workflows/implement/test_rebase.py` (split — do **not** move wholesale; see TDD)
- `tests/workflows/implement/test_core.py` (receives the orchestration integration test)

**Do NOT move `test_rebase.py` wholesale.** It contains two distinct kinds of test:
- Unit tests of `_get_rebase_target_branch` / `_attempt_rebase_and_push` → move to
  `tests/workflow_steps/test_rebase.py` (these test the moved step).
- `TestRebaseIntegration::test_rebase_and_push_called_after_prerequisites` → this is an
  `implement/core` orchestration test (it calls `run_implement_workflow` and patches
  `implement.core.*` prerequisites). It **stays** under `tests/workflows/implement/`
  (e.g. moved into `test_core.py`), because tests must mirror the source they exercise.

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

Split `test_rebase.py`:
- **Unit tests** (`TestGetRebaseTargetBranch` + the `_attempt_rebase_and_push` cases) →
  `tests/workflow_steps/test_rebase.py`, updating patch targets to
  `mcp_coder.workflow_steps.rebase.*` (e.g. `rebase_onto_branch`, `detect_base_branch`,
  `push_changes`). Confirm the "rebase succeeds but push fails → False" and "no target →
  False" cases are preserved.
- **`TestRebaseIntegration::test_rebase_and_push_called_after_prerequisites`** → stays
  under `tests/workflows/implement/` (e.g. `test_core.py`). Repoint its rebase-call patch
  target to `mcp_coder.workflows.implement.core._attempt_rebase_and_push` — the name
  `core` binds after the repoint — **not** `mcp_coder.workflows.implement.rebase.*`. Its
  `implement.core.*` prerequisite patches keep working unchanged.

After the split, verify whether `implement/rebase.py` has any remaining patch target. If
none does, **remove `implement/rebase.py`** rather than leaving an unused shim. Make all
tests green after the split.

## Checks / commit

All enforcers + pylint / pytest / mypy green. One commit:
`refactor(workflow_steps): move rebase step`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Move
> `_get_rebase_target_branch` and `_attempt_rebase_and_push` verbatim from
> `implement/rebase.py` into a new `workflow_steps/rebase.py`, importing `push_changes`
> from `mcp_coder.workflow_steps.commit`. Repoint `implement/core.py` to import the
> rebase step from `workflow_steps`. **Split** `test_rebase.py`: the unit tests go to
> `tests/workflow_steps/test_rebase.py` with `workflow_steps.rebase.*` patch targets, but
> the `TestRebaseIntegration` orchestration test stays under `tests/workflows/implement/`
> (e.g. `test_core.py`) with its rebase-call patch repointed to
> `mcp_coder.workflows.implement.core._attempt_rebase_and_push`. Remove
> `implement/rebase.py` if no patch target references it after the split; keep it as a
> thin re-export shim only if a test requires it. Do not change
> logic. Verify all enforcers (especially `run_lint_imports_check` — this is the step
> that would go RED if ordering were wrong) and the pylint/pytest/mypy trio are green,
> then produce one commit.
