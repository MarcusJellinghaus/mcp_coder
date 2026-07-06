# Step 5 — Redistribute orchestrator tests; relocate the misplaced `resolve_project_dir` test

> Read `pr_info/steps/summary.md` first. **Test-only step — no source moves, no
> logic changes.** After this step `test_core.py` is under 750 lines.

## WHERE

- **New test:** `tests/workflows/implement/test_core_workflow.py`
- **New test:** `tests/workflows/test_utils.py`
- **Modified:** `tests/workflows/implement/test_core.py`

## WHAT (test classes moved verbatim)

Into `test_core_workflow.py` (second orchestrator test file):
`TestRunImplementWorkflowLabelTransitions`, `TestNoPostErrorProgressDisplay`,
`TestWorkflowSafetyNet`, `TestSigtermHandler`, `TestIntegration`.

Into `test_utils.py` (mirror of `mcp_coder.workflows.utils`):
`TestResolveProjectDir`.

`test_core.py` keeps only: `TestRunImplementWorkflow`. The `_make_llm_response`
helper is **removed** — after this redistribution `TestRunImplementWorkflow` is
the only remaining class and it never references the helper (its prior users
`TestRunFinalisation` and `TestIntegration` left in Steps 4 and 5).

## HOW

- **No source changes** — these classes test `run_implement_workflow` (stays in
  `core.py`) and `resolve_project_dir` (already in `workflows/utils.py`). So the
  orchestrator classes **keep** their existing `patch("...implement.core.<name>")`
  targets unchanged — do **not** retarget them.
- `test_core_workflow.py` imports: `run_implement_workflow` from
  `...implement.core`, `FailureCategory`/`WorkflowFailure` from
  `...implement.constants`, plus stdlib/mock imports as used. It **uses
  `_make_llm_response`** (e.g. `TestIntegration`) → copy the 8-line helper into it.
- `test_utils.py` imports `resolve_project_dir` from
  `mcp_coder.workflows.utils` (+ `pytest`, `pathlib`, `unittest.mock.patch`).
  Does **not** need `_make_llm_response`.
- In `test_core.py`, **remove** the now-unused
  `from mcp_coder.workflows.utils import resolve_project_dir` import (ruff will
  flag it). Also **remove** the `_make_llm_response` helper (and its now-unused
  `Dict[str, Any]` import): `TestRunImplementWorkflow` is the only class left and
  never calls it, so it is dead code here.
- Target directories already exist (`tests/workflows/` has `__init__.py`); no new
  `__init__.py` needed.

## ALGORITHM

```
1. Cut the 5 orchestrator classes from test_core.py into test_core_workflow.py.
2. Add its docstring + imports; duplicate _make_llm_response helper.
3. Cut TestResolveProjectDir into tests/workflows/test_utils.py with its imports.
4. Remove the unused resolve_project_dir import AND the dead _make_llm_response
   helper (+ its Dict[str, Any] import) from test_core.py (ruff).
5. Run all checks incl. check_file_size — confirm test_core.py < 750.
6. Verify compact-diff purity (only headers + import lines differ).
```

## DATA

No data structures change. All assertions and mock setups are identical to their
pre-move form; only the enclosing file and its import block differ.

## Checks (one commit)

Standard gate **plus** `check_file_size(max_lines=750)` — `test_core.py` must now
report under 750 (and `test_core_workflow.py` / `test_utils.py` under 750). Both
files remain in the allowlist until Step 6.

## LLM prompt

> Implement Step 5 of `pr_info/steps/summary.md` (Issue #1025). **Test-only step
> — no source changes, no logic changes.** Move the test classes
> `TestRunImplementWorkflowLabelTransitions`, `TestNoPostErrorProgressDisplay`,
> `TestWorkflowSafetyNet`, `TestSigtermHandler`, and `TestIntegration` from
> `tests/workflows/implement/test_core.py` into a new
> `tests/workflows/implement/test_core_workflow.py`; copy the 8-line
> `_make_llm_response` helper into it and add the needed imports. Move
> `TestResolveProjectDir` from `test_core.py` into a new
> `tests/workflows/test_utils.py` (importing `resolve_project_dir` from
> `mcp_coder.workflows.utils`). Do **not** change any `patch()` targets — the
> orchestrator classes still test code in `implement.core`. Remove the now-unused
> `resolve_project_dir` import from `test_core.py`, and also remove the dead
> `_make_llm_response` helper (and its `Dict[str, Any]` import) — the sole
> remaining class `TestRunImplementWorkflow` never uses it. Run `run_format_code`,
> `run_ruff_fix`, `run_ruff_check`, `run_lint_imports_check`, `run_pytest_check`
> (fast unit markers), `run_pylint_check`, `run_mypy_check`, and `check_file_size`
> (max 750, confirm `test_core.py` is now under 750) — all green — and verify
> `compact-diff` purity. One commit.
