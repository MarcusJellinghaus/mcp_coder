# Implementation Task: Write test: `test_dispatch_workflow_missing_branch()`

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

Current task from TASK_TRACKER.md: Write test: `test_dispatch_workflow_missing_branch()`

Please implement this task step by step.

## LLM Response:
## Summary

I have successfully completed the task of writing the test `test_dispatch_workflow_missing_branch()`. Here's what was accomplished:

### Task Completed: Write test `test_dispatch_workflow_missing_branch()`

**What was implemented:**
1. ✅ Added comprehensive test for the missing branch error scenario in `tests/cli/commands/test_coordinator.py`
2. ✅ Test validates that `ValueError` is raised when `get_linked_branches()` returns an empty list for implement/create-pr workflows
3. ✅ Test verifies helpful error message includes issue number
4. ✅ Test confirms no Jenkins job is started and no labels are updated when error occurs

**Test details:**
- Tests the error path for workflows requiring a branch from the issue (implement, create-pr)
- Mocks an issue with `status-05:plan-ready` label
- Mocks `get_linked_branches()` to return empty list `[]`
- Asserts `ValueError` is raised with message containing "No linked branch found for issue" and "#555"
- Verifies branch manager was called but Jenkins and issue manager were not

**Code quality checks:**
- ✅ Pylint: No issues found
- ✅ Mypy: No type errors found  
- ⚠️ Pytest: Tests fail as expected (function not yet implemented - this is TDD)

**Task marked complete in TASK_TRACKER.md:**
- Changed `- [ ] Write test: test_dispatch_workflow_missing_branch()` to `- [x] Write test: test_dispatch_workflow_missing_branch()`

**Note:** The pytest failures are expected behavior for TDD (Test-Driven Development). The test is correctly written and will pass once the `dispatch_workflow()` function is implemented in subsequent tasks. The function currently raises `NotImplementedError` which is the intended state at this stage.

---
Generated on: 2025-10-28T12:00:25.156392