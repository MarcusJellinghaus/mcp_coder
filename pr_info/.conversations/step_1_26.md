# Implementation Task: Write test: `test_dispatch_workflow_jenkins_failure()`

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

Current task from TASK_TRACKER.md: Write test: `test_dispatch_workflow_jenkins_failure()`

Please implement this task step by step.

## LLM Response:
Perfect! Now let me prepare a git commit message as specified in Step 5 of the instructions:

## Summary

I have successfully completed the task of writing the test `test_dispatch_workflow_jenkins_failure()`. Here's what was accomplished:

### ✅ Task Complete

**Test Written:** `test_dispatch_workflow_jenkins_failure()` in `tests/cli/commands/test_coordinator.py:1491-1568`

**What the test verifies:**
1. When `JenkinsClient.start_job()` raises a `JenkinsError`, the exception bubbles up from `dispatch_workflow()`
2. The error message contains useful debugging information (job path, error details)
3. `start_job()` was called with expected parameters
4. `get_job_status()` was NOT called (error occurred before that step)
5. Issue labels were NOT updated (job never started successfully)

**Test structure:**
- Mocks all dependencies (JenkinsClient, IssueManager, IssueBranchManager)
- Creates a realistic test issue with `status-02:awaiting-planning` label
- Configures Jenkins mock to raise `JenkinsError` on `start_job()` call
- Uses `pytest.raises()` to verify exception is raised and contains expected message
- Verifies all method calls (and non-calls) with assertions

**Code quality checks:**
- ✅ Pylint: No issues found
- ✅ Mypy: No type errors
- ⚠️ Pytest: Test correctly fails with `NotImplementedError` (expected for TDD - test written before implementation)

### 📝 Commit Message

```
test(coordinator): add test for Jenkins failure in dispatch_workflow

Add test_dispatch_workflow_jenkins_failure() to verify error handling when
Jenkins job fails to start. Test ensures JenkinsError bubbles up correctly
and that labels are not updated when job triggering fails.

This is part of TDD for Step 3 (Workflow Dispatcher). The test will pass
once dispatch_workflow() implementation is complete in a future task.
```

### ✅ All CLAUDE.md Requirements Followed

1. ✅ Used MCP tools exclusively for file operations (`mcp__filesystem__*`)
2. ✅ Used MCP code checker tools (`mcp__code-checker__run_pylint_check`, `mcp__code-checker__run_mypy_check`)
3. ✅ Pylint check passed
4. ✅ Mypy check passed
5. ✅ Task tracker updated (marked task as complete)

The task is now complete and ready for the next step in the workflow!

---
Generated on: 2025-10-28T12:07:52.181280