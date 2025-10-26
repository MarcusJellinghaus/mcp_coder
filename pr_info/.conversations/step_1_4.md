# Implementation Task: Add new test: `test_prepare_llm_environment_separate_runner_project`

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

Current task from TASK_TRACKER.md: Add new test: `test_prepare_llm_environment_separate_runner_project`

Please implement this task step by step.

## LLM Response:
Perfect! The task has been successfully marked as complete in the TASK_TRACKER.md file. Now let me prepare a commit message as required by Step 5:

## Summary

I have successfully completed the task to add the new test `test_prepare_llm_environment_separate_runner_project`. Here's what was accomplished:

### ✅ Task Completed

**Added test:** `test_prepare_llm_environment_separate_runner_project` in `tests/llm/test_env.py:74`

This test verifies that:
- The runner environment (where mcp-coder executes) and project directory are independent
- The runner location is obtained from VIRTUAL_ENV environment variable
- The project location is passed as a parameter
- The two paths are completely separate and neither is relative to the other

### ✅ Code Quality Checks - All Passed

- **Pylint**: No issues found
- **Mypy**: No type errors found
- **Pytest**: Test fails as expected (RED phase of TDD) - this is correct behavior since the implementation hasn't been updated yet in Step 2

### 📝 Commit Message (Step 5)

```
test(env): add test for separate runner and project directories

Add test_prepare_llm_environment_separate_runner_project to verify that
runner environment and project directory are independent locations.
```

### ✅ All CLAUDE.md Requirements Followed

- ✅ Used MCP filesystem tools exclusively (`mcp__filesystem__edit_file`)
- ✅ Used MCP code checker tools for all quality checks
- ✅ Test fails as expected in RED phase (implementation comes in Step 2)
- ✅ All code quality checks passed
- ✅ Task marked as complete in TASK_TRACKER.md

The test is now ready and will pass once the implementation is updated in Step 2 of the TDD process.

---
Generated on: 2025-10-26T20:03:30.058523