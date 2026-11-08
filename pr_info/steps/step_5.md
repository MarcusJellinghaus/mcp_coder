# Step 5: Implement's check loop through bindings

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **step 5** as described in
> `pr_info/steps/step_5.md`. Steps 1–4 are done. Update the tests first, then change
> `workflows/implement/`. Run pylint, mypy, pytest (fast unit tests), lint-imports,
> vulture and format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/constants.py` (remove `RUN_MYPY_AFTER_EACH_TASK`)
- Tests: `tests/workflows/implement/test_task_processing_mypy.py`,
  `test_task_processing_branch_name.py`, `test_task_processing.py`,
  `test_core_workflow.py` (plus any other file referencing the removed names)

## WHAT

Replace `_run_mypy_check(project_dir)` with:

```python
def _run_check(project_dir: Path, entry: str) -> str | None
```

Extend the fix loop with the binding entry (keyword with default, so existing calls
keep working):

```python
def check_and_fix_mypy(project_dir, step_num, provider, env_vars=None, mcp_config=None,
                       settings_file=None, entry: str = "implement_final") -> bool
```

The loop body is unchanged except for the two `_run_mypy_check(project_dir)` calls,
which become `_run_check(project_dir, entry)`. The prompt stays
`get_prompt(..., "Mypy Fix Prompt")` with `[mypy_output]` replaced by the returned
text; session names stay `step_{step_num}_mypy_{n}`; log wording stays.

## ALGORITHM

`_run_check`:
```
try: results = run_binding(load_toolkit(project_dir), project_dir, entry)
except Exception as e: raise RuntimeError(f"Failed to run checks: {e}") from e
errors = [f"{req}: {res.summary}" for req, res in results if res.status == "error"]
if errors: raise RuntimeError("Failed to run checks: " + "; ".join(errors))
for req, res in results: if res.status == "skipped": logger.info("%s skipped: %s", req, res.summary)
texts = [res.fix_text or res.summary for _, res in results if res.status == "findings"]
return "\n\n".join(texts) or None
```

The existing outer `except Exception` in `check_and_fix_mypy` already turns that
`RuntimeError` into a logged `False`, and both callers log and continue — today's
"error logs and continues" behaviour (#1389 makes it abort).

Per task (`process_single_task`, Step 7 block):
```
if not check_type_hints: logger.info("Skipping mypy check (check_type_hints disabled)")
elif not get_binding(project_dir, "implement_task"): logger.info("Skipping mypy check (will run after all tasks complete)")
elif not check_and_fix_mypy(..., entry="implement_task"): logger.warning(<unchanged message>)
```

Final (`core.py`, Step 5 block): condition becomes
`progress.completed > 0 and implement_config.check_type_hints and get_binding(project_dir, "implement_final")`;
call `check_and_fix_mypy(..., entry="implement_final")`. Everything inside the block
(LLM error categorisation, formatting, commit, `read_and_clear_blocked`) is unchanged.

## DATA

- `_run_check` → `None` (all `ok`/`skipped`), the joined `fix_text` of `findings`
  results, or raises `RuntimeError` on any `error`.

## HOW

- Imports: `from mcp_coder.utils.toolkit_runner import get_binding, load_toolkit, run_binding`
  in `task_processing.py`; `get_binding` in `core.py`. Remove the
  `from mcp_coder.mcp_tools_py import run_mypy_check` local import and every
  `RUN_MYPY_AFTER_EACH_TASK` import/reference (check `vulture_whitelist.py` too).
- `check_type_hints` remains the gate in front of both implement bindings only.
- The config was already validated by the entry pre-flight (`check_formatter_config`
  always loads it), so `get_binding` needs no extra error handling here.

## Tests (update first)

- `test_task_processing_mypy.py` / `test_task_processing_branch_name.py`: patch target
  `_run_mypy_check` → `_run_check`; `assert_called_once_with(Path(...), "implement_final")`.
- New tests for `_run_check` (patch `task_processing.load_toolkit` and
  `task_processing.run_binding`):
  - all `ok` → `None`; `skipped` → `None` and logged;
  - `findings` with `fix_text="a.py:1: error ..."` → that text; two `findings` results →
    joined with a blank line; `fix_text` empty → falls back to `summary`;
  - `error` result → `RuntimeError` containing the request and summary;
  - `load_toolkit` raising `ValueError` → `RuntimeError`.
- New: `check_and_fix_mypy` with `_run_check` raising `RuntimeError` → `False` (logged).
- `test_task_processing.py`: replace `patch(...RUN_MYPY_AFTER_EACH_TASK, True)` with
  `patch("mcp_coder.workflows.implement.task_processing.get_binding", return_value=("check@quick",))`;
  add a test that an empty `implement_task` binding skips `check_and_fix_mypy`.
- `test_core_workflow.py`: replace `patch(...core.RUN_MYPY_AFTER_EACH_TASK, True)`
  (meaning "no final check") with `patch("mcp_coder.workflows.implement.core.get_binding", return_value=())`.
  Final-check tests that expect the check to run use the default binding.
