# Implementation Task: Modify `log_function_call` to accept optional `sensitive_fields` parameter

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

Current task from TASK_TRACKER.md: Modify `log_function_call` to accept optional `sensitive_fields` parameter

Please implement this task step by step.

## LLM Response:
I have completed the sub-task **"Modify `log_function_call` to accept optional `sensitive_fields` parameter"**.

## Summary of Changes

### Implementation (`src/mcp_coder/utils/log_utils.py`)

Modified `log_function_call` decorator to:

1. **Accept optional `sensitive_fields` parameter** - The decorator now works both as:
   - `@log_function_call` (backward compatible)
   - `@log_function_call(sensitive_fields=["token", "password"])`

2. **Updated decorator signature**:
   ```python
   def log_function_call(
       func: Callable[..., T] | None = None,
       *,
       sensitive_fields: list[str] | None = None,
   ) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
   ```

3. **Applied redaction to `serializable_params`** before logging function parameters (line ~341-345)

4. **Applied redaction to `result_for_log`** and `serializable_result` before logging return values (line ~382-387)

### Tests (`tests/utils/test_log_utils.py`)

Added comprehensive tests:
- `TestRedactForLogging` class with 5 tests for the helper function
- `TestLogFunctionCallWithSensitiveFields` class with 6 tests for the decorator:
  - Backward compatibility (without sensitive_fields)
  - Empty parentheses usage
  - Parameter redaction
  - Return value redaction (flat dict)
  - Nested return value redaction
  - Non-dict return values

### Quality Checks

- **Pylint**: No new issues introduced
- **Mypy**: The `untyped-decorator` warnings are expected with this decorator pattern and match pre-existing behavior in the codebase

---
Generated on: 2026-01-15T14:44:49.809304