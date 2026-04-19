# Step 2: Gate formatting and mypy in task_processing.py

## Context
See `pr_info/steps/summary.md` for full design. This step adds `format_code` and `check_type_hints` parameters to task processing functions and gates Steps 7-8.

## WHERE
- `src/mcp_coder/workflows/implement/task_processing.py` — modify function signatures + add gates
- `tests/workflows/implement/test_task_processing.py` — add gating tests + update existing tests

## WHAT

### Modified signatures
```python
def process_single_task(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    attempt: int = 1,
    format_code: bool = False,      # NEW
    check_type_hints: bool = False,  # NEW
) -> tuple[bool, str]:

def process_task_with_retry(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    format_code: bool = False,      # NEW
    check_type_hints: bool = False,  # NEW
) -> tuple[bool, str]:
```

## HOW

### In `process_single_task()`:
- **Step 7** (mypy): Change condition from `if RUN_MYPY_AFTER_EACH_TASK:` to `if check_type_hints and RUN_MYPY_AFTER_EACH_TASK:`
- **Step 8** (formatters): Wrap `run_formatters()` call in `if format_code:`

### In `process_task_with_retry()`:
- Pass `format_code` and `check_type_hints` through to `process_single_task()`

## ALGORITHM
```
# Step 7 in process_single_task:
if check_type_hints and RUN_MYPY_AFTER_EACH_TASK:
    check_and_fix_mypy(...)

# Step 8 in process_single_task:
if format_code:
    if not run_formatters(project_dir):
        return False, "error"
```

## DATA
- New params: `format_code: bool = False`, `check_type_hints: bool = False`
- Return values unchanged: `tuple[bool, str]`

## TESTS (write first)
Add to `tests/workflows/implement/test_task_processing.py`:
1. `test_process_single_task_skips_formatters_when_format_code_false` — verify `run_formatters` not called
2. `test_process_single_task_runs_formatters_when_format_code_true` — verify `run_formatters` called
3. `test_process_single_task_skips_mypy_when_check_type_hints_false` — verify `check_and_fix_mypy` not called
4. `test_process_single_task_runs_mypy_when_check_type_hints_true` — verify `check_and_fix_mypy` called (with `RUN_MYPY_AFTER_EACH_TASK=True` patched)

Update all existing tests that call `process_single_task()` or `process_task_with_retry()` to pass the new params (or rely on defaults).

## LLM PROMPT
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_2.md.

Add format_code and check_type_hints parameters to process_single_task() and
process_task_with_retry() in task_processing.py. Gate Step 7 (mypy) on
check_type_hints and Step 8 (formatters) on format_code. Write tests first,
then modify the functions. Update existing tests as needed for the new params.
```
