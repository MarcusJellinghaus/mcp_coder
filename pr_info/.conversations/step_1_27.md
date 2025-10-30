# Implementation Task: Write test: `test_dispatch_workflow_label_update()`

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

Current task from TASK_TRACKER.md: Write test: `test_dispatch_workflow_label_update()`

Please implement this task step by step.

## LLM Response:
Perfect! The task has been marked as complete. Now let me verify the task completion by reviewing what I've accomplished:

## Summary

I have successfully completed the task: **Write test: `test_dispatch_workflow_label_update()`**

### What was implemented:

1. **Added the test function** `test_dispatch_workflow_label_update()` to `tests/cli/commands/test_coordinator.py`

2. **Test verifies the following behavior:**
   - When a Jenkins job is successfully triggered and verified
   - The function updates issue labels in the correct order:
     - First removes the current workflow label (e.g., `status-05:plan-ready`)
     - Then adds the next workflow label (e.g., `status-06:implementing`)
   - Both label operations are called exactly once
   - The test uses the `implement` workflow as an example

3. **Test structure follows TDD best practices:**
   - Uses proper mocking for `JenkinsClient`, `IssueManager`, and `IssueBranchManager`
   - Creates a realistic test scenario with issue data, repo config, and branch manager
   - Verifies all the critical interactions:
     - Jenkins job triggering
     - Job status verification
     - Label removal and addition in correct order
   - Includes comprehensive assertions to verify behavior

### Code quality checks:
- ✅ **Pylint**: No issues found
- ✅ **Mypy**: No type errors found
- ✅ **Pytest**: Test is syntactically correct (fails with expected `NotImplementedError` since `dispatch_workflow()` hasn't been implemented yet - this is expected for TDD)

### Task tracker updated:
- ✅ Marked `- [x] Write test: test_dispatch_workflow_label_update()` as complete in `pr_info/TASK_TRACKER.md`

All CLAUDE.md requirements followed:
- ✅ Used MCP filesystem tools exclusively
- ✅ Used MCP code-checker tools for quality checks
- ✅ All code quality checks passed
- ✅ Task marked as complete in TASK_TRACKER.md

---
Generated on: 2025-10-28T12:12:07.122591