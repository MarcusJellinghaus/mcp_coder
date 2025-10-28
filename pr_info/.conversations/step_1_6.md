# Implementation Task: Write tests for error cases (neither, both parameters)

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

Current task from TASK_TRACKER.md: Write tests for error cases (neither, both parameters)

Please implement this task step by step.

## LLM Response:
Perfect! The task has been marked as complete. Let me provide a summary of what was accomplished:

## Summary

✅ **Task Completed: Write tests for error cases (neither, both parameters)**

### What was implemented:

I added a new test class `TestBaseGitHubManagerParameterValidation` to `tests/utils/github_operations/test_base_manager.py` with two comprehensive test methods:

1. **`test_initialization_fails_with_neither_parameter()`** - Tests that calling `BaseGitHubManager()` with no parameters raises a `ValueError` with the message "Exactly one of project_dir or repo_url must be provided"

2. **`test_initialization_fails_with_both_parameters()`** - Tests that calling `BaseGitHubManager(project_dir=..., repo_url=...)` with both parameters raises a `ValueError` with the same error message

### Verification:

✅ **All tests pass**: 1090 tests including the 2 new error case tests  
✅ **Pylint check passes**: No issues found  
✅ **Mypy check passes**: No type errors in the modified file  
✅ **Task marked complete**: Updated `pr_info/TASK_TRACKER.md`

The tests follow the same patterns as the existing test classes in the file, using proper mocking and pytest conventions. All CLAUDE.md requirements were followed - MCP tools were used exclusively for file operations and code quality checks.

---
Generated on: 2025-10-28T09:37:18.994410