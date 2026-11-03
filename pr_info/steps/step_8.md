# Step 8: Louder progress-summary degradation

See `pr_info/steps/summary.md` (§5 of issue #1093).

## WHERE
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`: `log_progress_summary`
- Tests: `tests/workflows/implement/test_task_tracker_prep.py`

## WHAT
No signature change: `log_progress_summary(project_dir: Path) -> None`.

## HOW
- `logger.debug("No step progress information available")` → `logger.warning(...)`.
- `except Exception as e: logger.debug(f"Could not generate progress summary: {e}")` → `logger.warning(...)`.
- Update the docstring note ("logs debug messages") accordingly.

## ALGORITHM
None.

## DATA
Unchanged.

## Tests (write first)
- `get_step_progress` patched to return `{}` → a WARNING record "No step progress information available" (`caplog`).
- `get_step_progress` patched to raise → a WARNING record "Could not generate progress summary".

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`. Implement step 8 only:
> write the two caplog tests first, then raise both log calls in `log_progress_summary`
> from DEBUG to WARNING. Run pylint, pytest (`-n auto`, unit markers) and mypy.
