# Implementation Task: Add `PRIORITY_ORDER` constant to `coordinator.py`

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

Current task from TASK_TRACKER.md: Add `PRIORITY_ORDER` constant to `coordinator.py`

Please implement this task step by step.

## LLM Response:
Excellent! The task has been marked as complete with `[x]`. Now let me prepare a commit message as required by Step 5 of the workflow:

**Commit Message:**
```
feat(coordinator): add PRIORITY_ORDER constant for issue prioritization

Add PRIORITY_ORDER constant to coordinator.py defining the priority order
for processing issues: status-08:ready-pr (highest), status-05:plan-ready,
status-02:awaiting-planning (lowest). This constant will be used by the
get_eligible_issues() function to sort issues for workflow automation.
```

## Summary

I have successfully completed the task: **Add `PRIORITY_ORDER` constant to `coordinator.py`**

### What was done:
1. ✅ Added the `PRIORITY_ORDER` constant to `src/mcp_coder/cli/commands/coordinator.py`
2. ✅ Positioned it correctly after the `DEFAULT_TEST_COMMAND` constant
3. ✅ Included all three priority labels in the correct order:
   - `"status-08:ready-pr"` (highest priority)
   - `"status-05:plan-ready"`
   - `"status-02:awaiting-planning"` (lowest priority)
4. ✅ Added appropriate comment explaining the constant's purpose
5. ✅ Verified all code quality checks pass:
   - Pylint: No issues
   - Pytest: 1090 tests passed
   - Mypy: No type errors
6. ✅ Marked the task as complete in `pr_info/TASK_TRACKER.md`

### Location:
- Modified file: `src/mcp_coder/cli/commands/coordinator.py:49-54`

### Commit message prepared:
```
feat(coordinator): add PRIORITY_ORDER constant for issue prioritization
```

**All CLAUDE.md requirements followed:**
- Used MCP tools for all file operations
- Ran all required code quality checks (pylint, pytest, mypy)
- All checks passed successfully
- Task marked as complete in tracker

The implementation is ready for the next task in the workflow.

---
Generated on: 2025-10-28T10:04:10.470039