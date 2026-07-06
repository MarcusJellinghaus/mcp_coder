# Step 2 — Move the `rebase` group (src + tests)

> Read `pr_info/steps/summary.md` first. **Pure move** — no logic changes.

## WHERE

- **New source:** `src/mcp_coder/workflows/implement/rebase.py`
- **New test:** `tests/workflows/implement/test_rebase.py`
- **Modified:** `core.py`, `test_core.py`

## WHAT (symbols moved verbatim)

```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]: ...
def _attempt_rebase_and_push(project_dir: Path) -> bool: ...
```

Test classes → `test_rebase.py`: `TestGetRebaseTargetBranch`,
`TestRebaseIntegration`.

## HOW

- `move_symbol(core.py, ["_get_rebase_target_branch","_attempt_rebase_and_push"],
  rebase.py)`. `_attempt_rebase_and_push` calls `_get_rebase_target_branch`
  (same module) and `push_changes`/`rebase_onto_branch`; move_symbol adds the
  needed imports to `rebase.py` and a `from .rebase import _attempt_rebase_and_push`
  to `core.py` (called inside `run_implement_workflow`).
- Not in `__all__`; no `__init__.py` change.
- **Confirm the import-rewrite form in the dry-run (critical).** Ensure
  `move_symbol(..., dry_run=True)` adds a **direct** import to `core.py`
  (`from .rebase import _attempt_rebase_and_push`, leaving bare call sites) so
  `core._attempt_rebase_and_push` / `core._get_rebase_target_branch` stay
  patchable module attributes; **STOP and revisit** if qualified references
  (`from . import rebase` + `rebase._attempt_rebase_and_push(...)`) appear
  instead (retained orchestrator UNIT tests patch these).
- **`patch()` retargeting (manual):** in the moved tests, change
  `patch("mcp_coder.workflows.implement.core.<name>")` →
  `...implement.rebase.<name>` for names now resolved in `rebase.py`
  (`detect_base_branch`, `rebase_onto_branch`, `push_changes`,
  `_get_rebase_target_branch`).
- **Test imports:** `test_rebase.py` imports `_get_rebase_target_branch`,
  `_attempt_rebase_and_push` from `...implement.rebase`. These classes do not use
  `_make_llm_response` — do not copy it.
- `run_ruff_fix` to drop now-unused imports in `core.py`/`test_core.py`.

## ALGORITHM

```
1. move_symbol(core.py, [rebase funcs], rebase.py, dry_run=True) → execute.
2. Cut TestGetRebaseTargetBranch + TestRebaseIntegration into test_rebase.py.
3. Add docstring + imports from ...implement.rebase (+ unittest.mock, pathlib).
4. Retarget patch("...core.X") → patch("...rebase.X") in moved tests.
5. Remove now-unused imports (ruff) from core.py and test_core.py.
6. Run all checks; verify compact-diff purity.
```

## DATA

No data changes. `_get_rebase_target_branch` → `Optional[str]` (branch name or
`None`). `_attempt_rebase_and_push` → `bool`.

## Checks (one commit)

Same gate as Step 1: `run_format_code`, `run_ruff_fix`, `run_ruff_check`,
`run_lint_imports_check`, `run_pytest_check`, `run_pylint_check`, `run_mypy_check`.

## LLM prompt

> Implement Step 2 of `pr_info/steps/summary.md` (Issue #1025): move the `rebase`
> group. **Pure move — no logic changes.** Move `_get_rebase_target_branch` and
> `_attempt_rebase_and_push` from `src/mcp_coder/workflows/implement/core.py` into
> a new `src/mcp_coder/workflows/implement/rebase.py` via the MCP refactoring
> tools. Move `TestGetRebaseTargetBranch` and `TestRebaseIntegration` from
> `tests/workflows/implement/test_core.py` into a new
> `tests/workflows/implement/test_rebase.py` with the imports it needs. Retarget
> `patch("mcp_coder.workflows.implement.core.<name>")` strings to
> `...implement.rebase.<name>` where the name now lives in `rebase.py`. Clean
> unused imports with ruff. Run `run_format_code`, `run_ruff_fix`,
> `run_ruff_check`, `run_lint_imports_check`, `run_pytest_check` (fast unit
> markers), `run_pylint_check`, `run_mypy_check` — all green — and verify
> `compact-diff` shows only import/patch-path/header changes. One commit.
