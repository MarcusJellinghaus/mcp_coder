# Implementation Task: Add `CREATE_PR_COMMAND_TEMPLATE` constant

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

Current task from TASK_TRACKER.md: Add `CREATE_PR_COMMAND_TEMPLATE` constant

Please implement this task step by step.

## LLM Response:
Excellent! Task completed successfully. Let me verify what was accomplished:

## Summary

✅ **Task Completed**: Add `CREATE_PR_COMMAND_TEMPLATE` constant

### What Was Done:

1. **Added CREATE_PR_COMMAND_TEMPLATE constant** to `src/mcp_coder/cli/commands/coordinator.py`
   - Added after `IMPLEMENT_COMMAND_TEMPLATE`
   - Template includes git checkout, pull, version checks, and mcp-coder create-pr command
   - Uses placeholders: `{branch_name}` and `{log_level}`

2. **Code Quality Checks - All Passed**:
   - ✅ Pylint: No issues found
   - ✅ Pytest: All 1094 tests passed (fast unit tests)
   - ✅ Mypy: No type errors found

3. **Prepared Git Commit Message**:
   ```
   feat(coordinator): add CREATE_PR_COMMAND_TEMPLATE constant

   Added CREATE_PR_COMMAND_TEMPLATE to complete the set of workflow command templates for the coordinator run feature. This template defines the shell commands for the create-pr workflow.
   ```

4. **Marked Task Complete** in `pr_info/TASK_TRACKER.md`:
   - Changed `- [ ] Add CREATE_PR_COMMAND_TEMPLATE constant` to `- [x] Add CREATE_PR_COMMAND_TEMPLATE constant`

### All CLAUDE.md Requirements Followed:
- ✅ Used MCP filesystem tools exclusively (`mcp__filesystem__edit_file`)
- ✅ Used MCP code checker tools (`mcp__code-checker__run_pylint_check`, `mcp__code-checker__run_pytest_check`, `mcp__code-checker__run_mypy_check`)
- ✅ All code quality checks passed
- ✅ Task marked as complete in TASK_TRACKER.md

The implementation is complete and ready for the next task in the workflow.

---
Generated on: 2025-10-28T11:21:30.398988