# Implementation Task: Refactor `get_config_value()` to use `load_config()` in `src/mcp_coder/utils/user_config.py`

## Prompt Sent to LLM:
You are implementing tasks from a task tracker. Follow these steps in order:

**STEP 1: SELECT TASK**
- Read `pr_info/TASK_TRACKER.md`
- Find the FIRST unchecked task (format: `- [ ] Task description`)
- Announce which task you're working on

**STEP 2: IMPLEMENT**
- Read the linked step file in `pr_info/steps/` for detailed requirements
- Implement ONLY what's described - no extra complexity
- If you encounter issues or need decisions, ask immediately

**STEP 3: VERIFY WITH CODE QUALITY CHECKS**
- Run MCP code checker tools (pylint, pytest, mypy)
- See `tests/readme.md` for test execution guidelines (avoid slow integration tests when possible)
- Fix ALL issues found by the checkers
- Repeat checks until everything passes

**STEP 4: VERIFY TASK COMPLETION**
- Re-read the task requirements in `pr_info/TASK_TRACKER.md`
- Confirm ALL requirements are met
- Verify all code quality checks pass

**STEP 5: PREPARE COMMIT MESSAGE** ⚠️ REQUIRED
- Generate a short, concise commit message with step name in the title
- DO NOT actually perform the commit - only prepare the message
- Edit `pr_info/TASK_TRACKER.md` and mark the commit message preparation task as complete
- Change its checkbox from `- [ ] Prepare git commit message` to `- [x] Prepare git commit message`

**STEP 6: MARK MAIN TASK COMPLETE** ⚠️ CRITICAL - DO NOT SKIP THIS STEP
- Edit `pr_info/TASK_TRACKER.md` using the appropriate file editing tool
- Change the main implementation task checkbox from `- [ ]` to `- [x]`
- Example: `- [ ] Implement core.py` becomes `- [x] Implement core.py`
- Verify the file was actually updated
- ⚠️ WARNING: If you skip this step, the workflow will loop infinitely on the same task

**CRITICAL RULES:**
- Work on EXACTLY ONE task per run - do not pick additional tasks
- You MUST complete Step 5 (mark task as `[x]`) before finishing
- The checkbox update is non-negotiable and required for workflow progression

**Always use the MCP tools**

Current task from TASK_TRACKER.md: Refactor `get_config_value()` to use `load_config()` in `src/mcp_coder/utils/user_config.py`

Please implement this task step by step.

## LLM Response:
I have completed **Step 3: Refactor `get_config_value()` to Use `load_config()`**.

## Summary

### Changes Made

1. **Refactored `get_config_value()` in `src/mcp_coder/utils/user_config.py`:**
   - Replaced direct `tomllib.load()` call with `load_config()`
   - Removed the `try/except` block that caught `tomllib.TOMLDecodeError, OSError, IOError`
   - Let `ValueError` from `load_config()` propagate to caller
   - Updated docstring to document the new `Raises: ValueError` behavior
   - Added type annotation `section_data: Any` for proper type checking

2. **Updated tests in `tests/utils/test_user_config.py`:**
   - Renamed `test_get_config_value_invalid_toml` to `test_get_config_value_invalid_toml_raises` and changed it to expect `ValueError` instead of `None`
   - Renamed `test_get_config_value_io_error` to `test_get_config_value_io_error_raises` and changed it to expect `ValueError` instead of `None`

### Behavior Change

| Scenario | Before | After |
|----------|--------|-------|
| File missing | `None` | `None` |
| Valid TOML, key exists | value | value |
| Valid TOML, key missing | `None` | `None` |
| Invalid TOML | `None` | `ValueError` raised |
| File read error | `None` | `ValueError` raised |

### Quality Checks
- Pylint: Passed (no issues in modified files)
- Mypy: Passed (no type errors)
- Commit message prepared in task tracker

---
Generated on: 2025-12-14T18:47:03.705662