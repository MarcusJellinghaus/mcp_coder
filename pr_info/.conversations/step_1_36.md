# Implementation Task: Implement test `test_update_workflow_label_removes_different_workflow_label` in `tests/utils/github_operations/test_issue_manager_label_update.py`

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

Current task from TASK_TRACKER.md: Implement test `test_update_workflow_label_removes_different_workflow_label` in `tests/utils/github_operations/test_issue_manager_label_update.py`

Please implement this task step by step.

## LLM Response:
## Summary

I have completed **Step 1: Add Tests for Workflow Label Removal** from the task tracker:

### What was implemented:
- Added test `test_update_workflow_label_removes_different_workflow_label` in `tests/utils/github_operations/test_issue_manager_label_update.py`

### Test Description:
The test verifies that when `update_workflow_label()` is called:
1. If an issue has a **different** workflow label (e.g., `status-03:planning`) instead of the expected source label (`status-06:implementing`)
2. Transitioning to a new state (e.g., `code_review`) should:
   - Add the target label (`status-07:code-review`)
   - **Remove ALL workflow labels** including `status-03:planning` (the key bug being tested)
   - Preserve non-workflow labels like `bug`

### Quality Checks:
- **Pylint**: Passed (only pre-existing W0613 warnings for unused `caplog` fixture)
- **Pytest**: Expected to FAIL (TDD approach - the bug fix is in Step 2)
- **Mypy**: Passed (no type errors)

### Commit Message Prepared:
```
test(issue-manager): Add test for removing all workflow labels during transition

Add test_update_workflow_label_removes_different_workflow_label to verify
that update_workflow_label removes ALL workflow labels (not just the source
label) when transitioning to a new workflow state. This test will fail until
the fix is implemented in Step 2 (TDD approach).

Related to: #193
```

The TASK_TRACKER.md has been updated with all Step 1 tasks marked as `[x]` complete.

---
Generated on: 2025-12-14T19:48:02.224353