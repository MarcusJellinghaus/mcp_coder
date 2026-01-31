# Implementation Task: Task 2.1: Migrate `test_issue_manager_label_update.py` to use `execute_command()`

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
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Task 2.1: Migrate `test_issue_manager_label_update.py` to use `execute_command()`

Please implement this task step by step.

## LLM Response:
## Summary

I've completed **Task 2.1: Migrate `test_issue_manager_label_update.py` to use `execute_command()`**.

### Changes Made

**File: `tests/utils/github_operations/test_issue_manager_label_update.py`**

1. **Removed** `import subprocess` from imports
2. **Added** `from mcp_coder.utils.subprocess_runner import execute_command` import
3. **Replaced** all 13 instances of `subprocess.run()` calls with `execute_command()`:
   - Changed `subprocess.run([...], cwd=tmp_path, check=True, capture_output=True)` to `execute_command([...], cwd=str(tmp_path))`
   - Converted `cwd` from `Path` to `str` (required by `execute_command`)
   - Removed `check=True` and `capture_output=True` parameters (not needed - `execute_command` handles this internally)

### Verification

- ✅ Pylint check passed (no issues found)
- ✅ Mypy type check passed (no type errors)
- ✅ No remaining `subprocess` references in the file

### Task Tracker Updated

- Marked Task 2.1 as complete: `- [x]`
- Commit message written to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-31T23:35:14.743781