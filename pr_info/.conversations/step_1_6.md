# Implementation Task: Write tests first (TDD)

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Write tests first (TDD)

Please implement this task step by step.

## LLM Response:
## Summary

I've completed the first sub-task of Step 2: **Write tests first (TDD)**

### What was done:

1. **Read the task tracker** to identify Step 2 as the current step with the first unchecked sub-task "Write tests first (TDD)"

2. **Read the step_2.md details** to understand the requirements for the logger name fix

3. **Added 5 new tests** in `tests/utils/test_log_utils.py` in a new test class `TestLogFunctionCallLoggerName`:
   - `test_log_function_call_uses_correct_logger_name` - Verifies logger name is the decorated function's module
   - `test_log_function_call_logger_not_log_utils_for_func_logs` - Verifies logs don't use `mcp_coder.utils.log_utils` as logger name
   - `test_log_function_call_structlog_uses_correct_module` - Verifies structlog also uses decorated function's module
   - `test_log_function_call_debug_uses_func_logger` - Verifies debug calls use the function-specific logger
   - `test_log_function_call_error_uses_func_logger` - Verifies error calls use the function-specific logger

4. **Updated TASK_TRACKER.md** to mark `- [x] Write tests first (TDD)`

### Next sub-tasks remaining in Step 2:
- `[ ]` Create `func_logger = logging.getLogger(func.__module__)` inside wrapper
- `[ ]` Replace `stdlogger.debug(...)` → `func_logger.debug(...)`
- `[ ]` Replace `stdlogger.error(...)` → `func_logger.error(...)`
- `[ ]` Update structlog call: `structlog.get_logger(module_name)` uses same module
- `[ ]` Keep `stdlogger` for `setup_logging()` internal logs
- `[ ]` Run quality checks (pylint, pytest, mypy) and fix issues
- `[ ]` Prepare git commit message for Step 2

---
Generated on: 2026-01-15T15:00:37.107122