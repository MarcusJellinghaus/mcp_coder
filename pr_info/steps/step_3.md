# Step 3: Read config in core.py and pass booleans down

## Context
See `pr_info/steps/summary.md` for full design. This step wires config into the workflow orchestrator and gates the final mypy/formatting in Step 5.

## WHERE
- `src/mcp_coder/workflows/implement/core.py` — read config, pass params, gate Step 5
- `tests/workflows/implement/test_core.py` — add config propagation tests + update existing tests

## WHAT

### In `run_implement_workflow()`:
1. Import and call `get_implement_config(project_dir)` once at the top (after prerequisites)
2. Pass `format_code` and `check_type_hints` to `process_task_with_retry()`
3. Gate Step 5 final mypy block on `check_type_hints`
4. Gate Step 5 `run_formatters()` call on `format_code`

## HOW

### New import
```python
from mcp_coder.utils.pyproject_config import get_implement_config
```

### Config read (after Step 1.5 rebase, before Step 2):
```python
implement_config = get_implement_config(project_dir)
```

### Step 4 loop — pass to process_task_with_retry:
```python
success, reason = process_task_with_retry(
    project_dir, provider, mcp_config, execution_dir,
    format_code=implement_config.format_code,
    check_type_hints=implement_config.check_type_hints,
)
```

### Step 5 — gate final mypy and formatting:
```python
if not RUN_MYPY_AFTER_EACH_TASK and completed_tasks > 0 and implement_config.check_type_hints:
    # existing mypy block...

    if implement_config.format_code:
        if not run_formatters(project_dir):
            # existing error handling...
```

## ALGORITHM
```
# After prerequisites pass:
implement_config = get_implement_config(project_dir)

# In task loop:
process_task_with_retry(..., format_code=implement_config.format_code,
                        check_type_hints=implement_config.check_type_hints)

# Step 5:
if not RUN_MYPY_AFTER_EACH_TASK and completed_tasks > 0 and implement_config.check_type_hints:
    check_and_fix_mypy(...)
    if implement_config.format_code:
        run_formatters(...)
```

## DATA
- `implement_config: ImplementConfig` — read once, used in two places
- No new return values

## TESTS (write first)
Add to `tests/workflows/implement/test_core.py`:
1. `test_run_implement_workflow_reads_config` — verify `get_implement_config` is called with `project_dir`
2. `test_run_implement_workflow_passes_config_to_process_task` — verify `process_task_with_retry` receives the config booleans
3. `test_run_implement_workflow_skips_final_mypy_when_disabled` — `check_type_hints=False` → `check_and_fix_mypy` not called in Step 5
4. `test_run_implement_workflow_skips_final_formatting_when_disabled` — `format_code=False` → `run_formatters` not called in Step 5

Update existing `test_core.py` tests to mock `get_implement_config` where needed.

## LLM PROMPT
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_3.md.

In core.py, import and call get_implement_config() once after prerequisites,
pass format_code and check_type_hints to process_task_with_retry(), and gate
the Step 5 final mypy/formatting blocks. Write tests first, then modify core.py.
Update existing tests to mock the new config call.
```
