# Implementation Task: Create `func_logger = logging.getLogger(func.__module__)` inside wrapper

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

Current task from TASK_TRACKER.md: Create `func_logger = logging.getLogger(func.__module__)` inside wrapper

Please implement this task step by step.

## LLM Response:
## Step 2 Complete

I have completed all sub-tasks for **Step 2: Fix Logger Name to Use Decorated Function's Module**:

### Summary of Changes Made:

1. **Created `func_logger` inside wrapper** (`src/mcp_coder/utils/log_utils.py:304-305`):
   ```python
   # Get logger for the decorated function's module (not log_utils)
   func_logger = logging.getLogger(module_name)
   ```

2. **Replaced `stdlogger.debug()` calls** with `func_logger.debug()` for:
   - "Calling %s with parameters: %s" log message
   - "%s completed in %sms with result: %s" log message

3. **Replaced `stdlogger.error()` call** with `func_logger.error()` for:
   - "%s failed after %sms with error: %s: %s" log message

4. **structlog already correctly uses `module_name`** - no change needed

5. **Kept `stdlogger` for `setup_logging()` internal logs** - these remain unchanged for logging initialization messages

### Quality Check Results:
- **Pylint**: Only pre-existing "too-many-locals" warning (R0914) - not introduced by these changes
- **Mypy**: No errors in log_utils.py (other files have pre-existing issues unrelated to this change)

### Commit Message Prepared:
```
fix(log_utils): use decorated function's module for logger name

Fix the `@log_function_call` decorator to use the decorated function's module
name for the logger instead of the log_utils module name.

Changes:
- Create `func_logger = logging.getLogger(func.__module__)` inside wrapper
- Replace `stdlogger.debug()` with `func_logger.debug()` for function logs
- Replace `stdlogger.error()` with `func_logger.error()` for error logs
- Keep `stdlogger` for `setup_logging()` internal initialization logs
- structlog already uses `module_name` (func.__module__) correctly

Before:
  2026-01-02 21:32:15 - mcp_coder.utils.log_utils - DEBUG - load_config completed...

After:
  2026-01-02 21:32:15 - mcp_coder.utils.user_config - DEBUG - load_config completed...

This makes log output more useful by showing which module the decorated
function belongs to, enabling better filtering and debugging.
```

---
Generated on: 2026-01-15T15:07:03.681225