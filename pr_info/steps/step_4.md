# Step 4 — Move the `finalisation` group (src + tests)

> Read `pr_info/steps/summary.md` first. **Pure move** — no logic changes.
> `core.py` is already under 750 after Step 3 (~654); this step further reduces
> it to ~500.

## WHERE

- **New source:** `src/mcp_coder/workflows/implement/finalisation.py`
- **New test:** `tests/workflows/implement/test_finalisation.py`
- **Modified:** `core.py`, `test_core.py`

## WHAT (symbol moved verbatim)

```python
def run_finalisation(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    settings_file: str | None = None,
    execution_dir: Optional[Path] = None,
) -> bool: ...
```

Test class → `test_finalisation.py`: `TestRunFinalisation`.

## HOW

- `move_symbol(core.py, ["run_finalisation"], finalisation.py)`. `core.py` calls
  `run_finalisation` inside `run_implement_workflow`, so move_symbol adds
  `from .finalisation import run_finalisation` to `core.py`. `run_finalisation`
  imports `generate_commit_message_with_llm`, `prompt_llm`, `store_session`,
  `get_full_status`, `commit_all_changes`, `push_changes`, `has_incomplete_work`,
  `get_prompt_with_substitutions`, `prepare_llm_environment`, constants, etc. —
  move_symbol carries these imports into `finalisation.py`.
- `run_finalisation` is **not** in `__all__`; no `__init__.py` change.
- **Confirm the import-rewrite form in the dry-run (critical).** Ensure
  `move_symbol(..., dry_run=True)` adds a **direct** import to `core.py`
  (`from .finalisation import run_finalisation`, leaving bare call sites) so
  `core.run_finalisation` stays a patchable module attribute; **STOP and revisit**
  if qualified references (`from . import finalisation` +
  `finalisation.run_finalisation(...)`) appear instead (retained orchestrator UNIT
  tests patch this).
- **`patch()` retargeting (manual):** in `TestRunFinalisation`, change
  `patch("mcp_coder.workflows.implement.core.<name>")` →
  `...implement.finalisation.<name>` for its patched dependencies
  (`has_incomplete_work`, `prompt_llm`, `store_session`, `get_full_status`,
  `generate_commit_message_with_llm`, `commit_all_changes`, `push_changes`,
  `prepare_llm_environment`, `get_prompt_with_substitutions`, ...).
- **Test imports + helper:** import `run_finalisation` from
  `...implement.finalisation`. `TestRunFinalisation` **uses `_make_llm_response`**
  → copy the helper into `test_finalisation.py`.
- `run_ruff_fix` to drop now-unused imports in `core.py`/`test_core.py`.

## ALGORITHM

```
1. move_symbol(core.py, ["run_finalisation"], finalisation.py, dry_run=True) → execute.
2. Cut TestRunFinalisation into test_finalisation.py.
3. Add docstring + imports; duplicate _make_llm_response helper.
4. Retarget patch("...core.X") → patch("...finalisation.X") in moved tests.
5. Ruff-clean unused imports (core.py now ~500 lines).
6. Run all checks incl. check_file_size — confirm core.py < 750.
```

## DATA

No data changes. `run_finalisation` → `bool` (succeeded/skipped vs error).

## Checks (one commit)

Standard gate **plus** `mcp__mcp-workspace__check_file_size(max_lines=750)` —
`core.py` (already under 750 since Step 3) must report under 750, now ~500. (It
stays in `.large-files-allowlist` until
Step 6; allowlist is a maximum, so this is fine.)

## LLM prompt

> Implement Step 4 of `pr_info/steps/summary.md` (Issue #1025): move the
> `finalisation` group. **Pure move — no logic changes.** Move `run_finalisation`
> from `src/mcp_coder/workflows/implement/core.py` into a new
> `src/mcp_coder/workflows/implement/finalisation.py` via the MCP refactoring
> tools. Move `TestRunFinalisation` from
> `tests/workflows/implement/test_core.py` into a new
> `tests/workflows/implement/test_finalisation.py`; copy the 8-line
> `_make_llm_response` helper into it and add the needed imports. Retarget every
> `patch("mcp_coder.workflows.implement.core.<name>")` string to
> `...implement.finalisation.<name>` for names now resolved in the new module.
> Clean unused imports with ruff. Run `run_format_code`, `run_ruff_fix`,
> `run_ruff_check`, `run_lint_imports_check`, `run_pytest_check` (fast unit
> markers), `run_pylint_check`, `run_mypy_check`, and `check_file_size`
> (max 750, confirm `core.py` is now under 750) — all green — and verify
> `compact-diff` purity. One commit.
