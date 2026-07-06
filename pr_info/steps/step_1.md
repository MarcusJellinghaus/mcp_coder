# Step 1 — Move the `failure_reporting` group (src + tests)

> Read `pr_info/steps/summary.md` first. This is a **pure move** — no logic
> changes. Only imports, `patch()` target strings, and file headers may change.

## WHERE

- **New source:** `src/mcp_coder/workflows/implement/failure_reporting.py`
- **New test:** `tests/workflows/implement/test_failure_reporting.py`
- **Modified:** `src/mcp_coder/workflows/implement/core.py`,
  `tests/workflows/implement/test_core.py`

## WHAT (symbols moved verbatim)

Source functions (from `core.py`):

```python
def _format_failure_comment(failure: WorkflowFailure, diff_stat: str) -> str: ...
def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> None: ...
```

Test classes (from `test_core.py`) → `test_failure_reporting.py`:
`TestFormatFailureComment`, `TestHandleWorkflowFailure`,
`TestFormatFailureCommentElapsedAndBuildUrl`, `TestExistingFailuresIncludeNewFields`.

## HOW (integration points)

- Use `mcp__mcp-tools-py__move_symbol` for the two source functions; it creates
  `failure_reporting.py` and updates imports project-wide automatically.
- `core.py` still uses `_handle_workflow_failure` inside `run_implement_workflow`
  → `move_symbol` adds `from .failure_reporting import _handle_workflow_failure`
  to `core.py`. `_format_failure_comment` is called only by
  `_handle_workflow_failure`, so it travels with it.
- These helpers are **not** in `__all__`; no `__init__.py` change.
- **Confirm the import-rewrite form in the dry-run (critical).** Ensure
  `move_symbol(..., dry_run=True)` adds a **direct** import to `core.py`
  (`from .failure_reporting import _handle_workflow_failure`, leaving bare call
  sites) so `core._handle_workflow_failure` / `core._format_failure_comment` stay
  patchable module attributes; **STOP and revisit** if qualified references
  (`from . import failure_reporting` + `failure_reporting._handle_workflow_failure(...)`)
  appear instead (retained orchestrator UNIT tests patch these).
- **`patch()` retargeting (manual):** in the moved test classes, change every
  `patch("mcp_coder.workflows.implement.core.<name>")` to
  `patch("mcp_coder.workflows.implement.failure_reporting.<name>")` — affected
  names include `get_diff_stat`, `handle_workflow_failure` (the shared one),
  `SharedWorkflowFailure`. Leave patches of names still resolved in `core` alone.
- **Test imports:** `test_failure_reporting.py` imports
  `_format_failure_comment`, `_handle_workflow_failure` from
  `mcp_coder.workflows.implement.failure_reporting`, plus `FailureCategory`,
  `WorkflowFailure` from `...implement.constants`. These classes do **not** use
  `_make_llm_response` — do not copy it.
- Run `run_ruff_fix` to drop imports in `core.py`/`test_core.py` that are now
  unused after the move.

## ALGORITHM (mechanical procedure)

```
1. move_symbol(core.py, ["_format_failure_comment","_handle_workflow_failure"],
               failure_reporting.py, dry_run=True) → review, then execute.
2. Cut the 4 test classes from test_core.py into new test_failure_reporting.py.
3. Add the file docstring + imports the classes need (constants + failure_reporting).
4. Retarget patch("...core.X") → patch("...failure_reporting.X") in moved tests.
5. Remove now-unused imports from test_core.py and core.py (ruff).
6. Run all checks; confirm compact-diff shows only imports/patch-paths/headers.
```

## DATA

No data structures change. `_format_failure_comment` returns a formatted
GitHub-comment `str`; `_handle_workflow_failure` returns `None`. Test behaviour
is identical to before the move.

## Checks (must all pass = one commit)

`run_format_code` → `run_ruff_fix` → `run_ruff_check` → `run_lint_imports_check`
→ `run_pytest_check` (unit markers per summary) → `run_pylint_check` →
`run_mypy_check`.

## LLM prompt

> Implement Step 1 of `pr_info/steps/summary.md` (Issue #1025): move the
> `failure_reporting` group. This is a **pure move — do not change any logic**.
> Using the MCP refactoring tools, move `_format_failure_comment` and
> `_handle_workflow_failure` from
> `src/mcp_coder/workflows/implement/core.py` into a new
> `src/mcp_coder/workflows/implement/failure_reporting.py`. Move the test classes
> `TestFormatFailureComment`, `TestHandleWorkflowFailure`,
> `TestFormatFailureCommentElapsedAndBuildUrl`, and
> `TestExistingFailuresIncludeNewFields` from
> `tests/workflows/implement/test_core.py` into a new
> `tests/workflows/implement/test_failure_reporting.py`, giving it the imports it
> needs. In the moved tests, retarget every
> `patch("mcp_coder.workflows.implement.core.<name>")` string to
> `...implement.failure_reporting.<name>` for names now looked up in the new
> module. Clean unused imports with ruff. Then run, in order,
> `run_format_code`, `run_ruff_fix`, `run_ruff_check`, `run_lint_imports_check`,
> `run_pytest_check` (fast unit markers from the summary), `run_pylint_check`,
> `run_mypy_check` — all must pass. Finally confirm `mcp-coder git-tool
> compact-diff` shows only import/patch-path/header changes. Commit as one commit.
