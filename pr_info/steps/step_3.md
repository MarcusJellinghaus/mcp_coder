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
- `src/mcp_coder/workflows/implement/rebase.py` → removed (after the split below, no test
  references `implement.rebase.*`, so it has no remaining patch target); keep it as a
  thin re-export shim only if some test unexpectedly still needs it.
- `tests/workflows/implement/test_rebase.py` → **emptied and deleted** — all its test
  classes move to `tests/workflow_steps/test_rebase.py` (see TDD).

**Do NOT move `test_rebase.py` wholesale as-is**, but **all of its test classes do move**
to `tests/workflow_steps/test_rebase.py` (with patch targets repointed). The file
contains two kinds of test, and **both exercise the moved step**:
- `TestGetRebaseTargetBranch` — unit tests of `_get_rebase_target_branch`.
- `TestRebaseIntegration` — **five** methods
  (`test_rebase_and_push_called_after_prerequisites`,
  `test_push_with_force_with_lease_after_successful_rebase`,
  `test_workflow_continues_when_rebase_fails`,
  `test_rebase_skipped_when_no_target_branch`,
  `test_workflow_continues_when_push_after_rebase_fails`). Despite the "integration"
  name, they drive `run_implement_workflow` only to reach the rebase step, then assert on
  the **internals of the real `_attempt_rebase_and_push`** (push called with
  `force_with_lease=True`; workflow never blocked when rebase or push fails). They patch
  the step's callees at `mcp_coder.workflows.implement.rebase.*` (`.push_changes`,
  `.rebase_onto_branch`, `._get_rebase_target_branch`) — **not** `_attempt_rebase_and_push`
  itself — so they belong with the moved step, and their patch targets must be repointed
  to `mcp_coder.workflow_steps.rebase.*`.

**Do NOT** keep any rebase test under `tests/workflows/implement/`, and do **not** repoint
these five to `core._attempt_rebase_and_push` — patching that function wholesale would
delete the internal assertions they exist for. Core-level orchestration coverage that
patches `_attempt_rebase_and_push` **wholesale** already exists **separately** in
`tests/workflows/implement/test_core_workflow.py` (and `test_failure_reporting.py`),
patching `mcp_coder.workflows.implement.core._attempt_rebase_and_push`; it needs **no
change**.

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

Move **all** test classes from `tests/workflows/implement/test_rebase.py` into
`tests/workflow_steps/test_rebase.py`, repointing patch targets:
- **`TestGetRebaseTargetBranch`** (unit tests of `_get_rebase_target_branch`) → repoint
  patch targets to `mcp_coder.workflow_steps.rebase.*` (e.g. `detect_base_branch`).
- **`TestRebaseIntegration`** — all **five** methods
  (`test_rebase_and_push_called_after_prerequisites`,
  `test_push_with_force_with_lease_after_successful_rebase`,
  `test_workflow_continues_when_rebase_fails`,
  `test_rebase_skipped_when_no_target_branch`,
  `test_workflow_continues_when_push_after_rebase_fails`) → move alongside the unit tests.
  Repoint their callee patches from `mcp_coder.workflows.implement.rebase.*` to
  `mcp_coder.workflow_steps.rebase.*` (`.push_changes`, `.rebase_onto_branch`,
  `._get_rebase_target_branch`). **Leave their `mcp_coder.workflows.implement.core.*`
  prerequisite patches unchanged** (those symbols stay bound on `implement.core`). Do
  **not** patch/replace `_attempt_rebase_and_push` wholesale — these tests exercise its
  real body and assert on its internals (`force_with_lease=True`; workflow continues when
  rebase or push fails; "rebase succeeds but push fails → False"; "no target → False").

Do **not** leave any rebase test under `tests/workflows/implement/`. Core-level
orchestration coverage that patches `_attempt_rebase_and_push` wholesale already exists
separately in `tests/workflows/implement/test_core_workflow.py` (and
`test_failure_reporting.py`) and needs **no change**.

After the move, no test references `mcp_coder.workflows.implement.rebase.*`, so
**remove `implement/rebase.py`** (keep a thin re-export shim only if some test
unexpectedly still needs it). Make all tests green after the move.

## Checks / commit

All enforcers + pylint / pytest / mypy green. One commit:
`refactor(workflow_steps): move rebase step`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Move
> `_get_rebase_target_branch` and `_attempt_rebase_and_push` verbatim from
> `implement/rebase.py` into a new `workflow_steps/rebase.py`, importing `push_changes`
> from `mcp_coder.workflow_steps.commit`. Repoint `implement/core.py` to import the
> rebase step from `workflow_steps`. Move **all** test classes from `test_rebase.py`
> (both `TestGetRebaseTargetBranch` and all **five** `TestRebaseIntegration` methods) to
> `tests/workflow_steps/test_rebase.py`, repointing their callee patches from
> `mcp_coder.workflows.implement.rebase.*` to `mcp_coder.workflow_steps.rebase.*`
> (`.push_changes`, `.rebase_onto_branch`, `._get_rebase_target_branch`) while leaving
> their `implement.core.*` prerequisite patches unchanged. Do **not** patch
> `_attempt_rebase_and_push` wholesale (the integration tests assert on its internals,
> e.g. `force_with_lease=True`), and do **not** leave any rebase test under
> `tests/workflows/implement/` — core-level wholesale coverage already exists there in
> `test_core_workflow.py` / `test_failure_reporting.py` and stays unchanged. Remove
> `implement/rebase.py` (no patch target references it after the move); keep it as a
> thin re-export shim only if a test unexpectedly requires it. Do not change
> logic. Verify all enforcers (especially `run_lint_imports_check` — this is the step
> that would go RED if ordering were wrong) and the pylint/pytest/mypy trio are green,
> then produce one commit.
