# Implementation Task: Add 4 test scenarios to `tests/utils/git_operations/test_repository.py`

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

Current task from TASK_TRACKER.md: Add 4 test scenarios to `tests/utils/git_operations/test_repository.py`

Please implement this task step by step.

## LLM Response:
## Step 1 Complete

**Summary:** I've completed all sub-tasks for Step 1.

### Changes Made:
- Added 4 test scenarios to `tests/utils/git_operations/test_repository.py`:
  1. `test_is_working_directory_clean_ignore_files_none` - Tests backward compatibility with `ignore_files=None`
  2. `test_is_working_directory_clean_ignore_files_matches_untracked` - Tests that matching untracked file is ignored
  3. `test_is_working_directory_clean_ignore_files_other_untracked` - Tests that non-matching files are still detected
  4. `test_is_working_directory_clean_ignore_files_with_other_changes` - Tests ignore + other real changes

### Code Checks:
- **Pylint**: Reports expected errors (E1123) - `ignore_files` parameter doesn't exist yet (TDD)
- **Mypy**: Reports expected errors (call-arg) - same reason, parameter not implemented yet

### Prepared Commit Message:

```
test(git): add tests for ignore_files parameter in is_working_directory_clean

Add 4 test scenarios for the upcoming ignore_files parameter:
- Test None preserves existing behavior
- Test matching untracked file is filtered
- Test non-matching files are still detected  
- Test ignore_files with other real changes

Tests follow TDD approach - will fail until Step 2 implements the parameter.

Part of #254: Ignore uv.lock in is_working_directory_clean() check
```

---
Generated on: 2026-01-08T23:12:08.317848