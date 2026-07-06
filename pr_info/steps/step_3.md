# Step 3 — Move the `task_tracker_prep` group (src + tests)

> Read `pr_info/steps/summary.md` first. **Pure move** — no logic changes.
> This step also auto-repoints the `__init__.py` re-exports.

## WHERE

- **New source:** `src/mcp_coder/workflows/implement/task_tracker_prep.py`
- **New test:** `tests/workflows/implement/test_task_tracker_prep.py`
- **Modified:** `core.py`, `__init__.py` (auto), `test_core.py`

## WHAT (symbols moved verbatim)

```python
def prepare_task_tracker(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    settings_file: str | None = None,
    execution_dir: Optional[Path] = None,
) -> bool: ...

def log_progress_summary(project_dir: Path) -> None: ...
```

Test classes → `test_task_tracker_prep.py`: `TestPrepareTaskTracker`,
`TestPrepareTaskTrackerExecutionDir`, `TestLogProgressSummary`.

## HOW

- `move_symbol(core.py, ["prepare_task_tracker","log_progress_summary"],
  task_tracker_prep.py)`. Both are in `__all__` and re-exported by
  `implement/__init__.py`; **move_symbol repoints those re-exports automatically**
  (`from .task_tracker_prep import log_progress_summary, prepare_task_tracker`).
  Keep `__all__` unchanged. `core.py` calls `prepare_task_tracker` inside
  `run_implement_workflow`, so move_symbol adds a
  `from .task_tracker_prep import prepare_task_tracker` import to `core.py`.
- Module name is `task_tracker_prep` (NOT `task_tracker`) to avoid colliding with
  `workflow_utils/task_tracker.py`. Stays in-package (imports `.constants`,
  `.prerequisites`) — do not move to `workflow_utils`.
- **`patch()` retargeting (manual):** in the moved tests, change
  `patch("mcp_coder.workflows.implement.core.<name>")` →
  `...implement.task_tracker_prep.<name>` for the many patched dependencies
  (`has_implementation_tasks`, `get_prompt`, `prepare_llm_environment`,
  `prompt_llm`, `store_session`, `get_full_status`, `commit_all_changes`,
  `get_branch_name_for_logging`, `get_step_progress`, ...).
- **Test imports + helper:** import `prepare_task_tracker`, `log_progress_summary`
  from `...implement.task_tracker_prep`. These tests **use `_make_llm_response`**
  → copy the 8-line helper into `test_task_tracker_prep.py` (with its
  `Dict[str, Any]` import).
- `run_ruff_fix` to drop now-unused imports in `core.py`/`test_core.py`.

## ALGORITHM

```
1. move_symbol(core.py, [prepare_task_tracker, log_progress_summary],
               task_tracker_prep.py, dry_run=True) → verify __init__ repoint → execute.
2. Cut the 3 test classes into test_task_tracker_prep.py.
3. Add docstring + imports; duplicate _make_llm_response helper.
4. Retarget patch("...core.X") → patch("...task_tracker_prep.X") in moved tests.
5. Confirm __init__.__all__ unchanged; ruff-clean unused imports.
6. Run all checks; verify compact-diff purity.
```

## DATA

No data changes. `prepare_task_tracker` → `bool` (ready/updated vs error);
`log_progress_summary` → `None` (logging side effects only).
`_make_llm_response(text="LLM response text") -> Dict[str, Any]` returns the
standard mock LLM response dict.

## Checks (one commit)

Standard gate. Additionally confirm `implement/__init__.py` `__all__` is byte
-identical to before and re-exports resolve from `task_tracker_prep`.

## LLM prompt

> Implement Step 3 of `pr_info/steps/summary.md` (Issue #1025): move the
> `task_tracker_prep` group. **Pure move — no logic changes.** Move
> `prepare_task_tracker` and `log_progress_summary` from
> `src/mcp_coder/workflows/implement/core.py` into a new
> `src/mcp_coder/workflows/implement/task_tracker_prep.py` via the MCP
> refactoring tools; let it auto-repoint the `implement/__init__.py` re-exports
> and keep `__all__` unchanged. Move `TestPrepareTaskTracker`,
> `TestPrepareTaskTrackerExecutionDir`, and `TestLogProgressSummary` from
> `tests/workflows/implement/test_core.py` into a new
> `tests/workflows/implement/test_task_tracker_prep.py`; copy the 8-line
> `_make_llm_response` helper into it and add the needed imports. Retarget every
> `patch("mcp_coder.workflows.implement.core.<name>")` string to
> `...implement.task_tracker_prep.<name>` for names now resolved in the new
> module. Clean unused imports with ruff. Run `run_format_code`, `run_ruff_fix`,
> `run_ruff_check`, `run_lint_imports_check`, `run_pytest_check` (fast unit
> markers), `run_pylint_check`, `run_mypy_check` — all green — and verify
> `compact-diff` purity. One commit.
