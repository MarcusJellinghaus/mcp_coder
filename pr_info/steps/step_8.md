# Step 8 — implement: pre-flight, remove old `format_code` plumbing, remove repo key

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md` only.
> TDD: update/write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## Precondition

Step 7 must be done: `grep "\.format_code"` in `src/` must only hit
`implement/core.py` and `task_processing.py`. Otherwise write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/utils/pyproject_config.py`
- `pyproject.toml`
- `tests/workflows/implement/test_core.py`, `tests/workflows/implement/test_task_processing.py`
- `tests/utils/test_pyproject_config.py` (`:123-172, 296-299`), `tests/test_pyproject_config.py:30`

## WHAT

- `ImplementConfig` → only `check_type_hints: bool`; `get_implement_config` docstring updated.
- `process_single_task(...)` and `process_task_with_retry(...)`: remove the `format_code` parameter
  and its docstring line; step 8 becomes `if not run_formatters(project_dir): return TaskOutcome(False, "error")`.
- `implement/core.py`:
  - remove `format_code=implement_config.format_code` (line ~160);
  - line ~280: `if not run_formatters(project_dir):` (gate now inside `run_formatters`);
  - top of `body()`, before `prepare_task_tracker`:

```python
formatter_err = check_formatter_config(project_dir, warn_legacy_key=True)
if formatter_err:
    return fail("general", stage="Formatter configuration", message=formatter_err)
```

- `pyproject.toml`: delete `format_code = true` under `[tool.mcp-coder.implement]`
  (keep the table if `check_type_hints` remains in it).

## HOW

- Import `check_formatter_config` in `implement/core.py` alongside `run_formatters`
  (match how `run_formatters` is imported there).
- Keep `get_implement_config(project_dir)` for `check_type_hints`.

## ALGORITHM

```
body():
    msg = check_formatter_config(project_dir, warn_legacy_key=True)
    if msg: return fail("general", stage="Formatter configuration", message=msg)
    implement_config = get_implement_config(project_dir)
    ... unchanged, minus format_code plumbing ...
```

## DATA

`ImplementConfig(check_type_hints: bool)`.

## Tests

- New: `check_formatter_config` patched (in `mcp_coder.workflows.implement.core`) to a message →
  `fail` with `"general"` / `"Formatter configuration"`; `prepare_task_tracker` not called.
- `test_core.py`: drop `ImplementConfig(format_code=…)` args and `format_code=` kwarg asserts (~`:76, 295, 417`).
- `test_task_processing.py`: remove format_code-parameter tests (~`:359-409, 574-604, 668-750, 844-856, 868-958`);
  keep/adjust one test that `run_formatters` returning False → `TaskOutcome(False, "error")`, and one
  that it is always called (gate is inside it).
- `tests/test_pyproject_config.py:30`: drop the `implement["format_code"]` assertion.
- `tests/utils/test_pyproject_config.py`: drop `format_code` from `get_implement_config` tests.
