# Implementation Task: Implement `load_config()` function in `src/mcp_coder/utils/user_config.py`

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

Current task from TASK_TRACKER.md: Implement `load_config()` function in `src/mcp_coder/utils/user_config.py`

Please implement this task step by step.

## LLM Response:
## Summary

I have completed **Step 2: Add `load_config()` Function**. Here's what was done:

### Implementation (`src/mcp_coder/utils/user_config.py`):
- Added `Any` to typing imports
- Added the `load_config()` function with `@log_function_call` decorator that:
  - Returns `dict[str, Any]` containing the full configuration
  - Returns an empty dict `{}` if the config file doesn't exist
  - Raises `ValueError` with formatted error message (using `_format_toml_error()`) on TOML parse errors
  - Raises `ValueError` on file read (OSError) errors

### Tests (`tests/utils/test_user_config.py`):
- Added `load_config` to imports
- Added `TestLoadConfig` class with 6 comprehensive tests:
  - `test_load_config_returns_dict` - Verifies successful loading of valid TOML config
  - `test_load_config_returns_empty_dict_if_missing` - Verifies empty dict returned when file doesn't exist
  - `test_load_config_raises_on_invalid_toml` - Verifies ValueError raised on parse errors
  - `test_load_config_error_includes_file_path` - Verifies error message includes file path
  - `test_load_config_error_includes_line_content` - Verifies error message includes line content
  - `test_load_config_preserves_nested_structure` - Verifies nested TOML structures are preserved

### Quality Checks:
- Pylint: ✅ No issues found
- Mypy: ✅ No type errors found

### Prepared Commit Message:
```
Step 2: Add load_config() function for TOML config loading

Add load_config() function to user_config.py that provides centralized
config file loading with proper error handling. The function returns
an empty dict if the config file doesn't exist, and raises ValueError
with formatted error messages on parse failures.

- Add load_config() function with @log_function_call decorator
- Return empty dict {} when config file is missing
- Raise ValueError with _format_toml_error() formatted message on TOML errors
- Raise ValueError on file read (OSError) errors
- Add comprehensive tests for all load_config() scenarios

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---
Generated on: 2025-12-14T18:42:07.368901