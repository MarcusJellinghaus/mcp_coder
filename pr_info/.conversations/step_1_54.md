# Implementation Task: Write test: `test_end_to_end_fail_fast_on_missing_branch()`

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

Current task from TASK_TRACKER.md: Write test: `test_end_to_end_fail_fast_on_missing_branch()`

Please implement this task step by step.

## LLM Response:
Perfect! Let me provide a summary of what was accomplished:

## ✅ Task Complete: `test_end_to_end_fail_fast_on_missing_branch()`

### What Was Implemented

I successfully wrote the integration test `test_end_to_end_fail_fast_on_missing_branch()` in `tests/cli/commands/test_coordinator.py:3406-3521`.

### Test Purpose

This test verifies the fail-fast behavior when a required branch is missing for workflows that need a branch (implement or create-pr):

1. **Setup**: Mock issue with `status-05:plan-ready` (implement workflow)
2. **Trigger**: `IssueBranchManager.get_linked_branches()` returns empty list (no branches)
3. **Expected**: Processing fails immediately with exit code 1
4. **Verification**:
   - Exit code is 1 (error)
   - `get_linked_branches()` was called with the correct issue number
   - No Jenkins job was started (error before job dispatch)
   - No labels were updated (error before label update)

### Code Quality Results

✅ **All checks passed:**
- **Pytest**: 49/49 tests pass (including the new test)
- **Pylint**: No issues found
- **Mypy**: No type errors found

### Location

- **File**: `tests/cli/commands/test_coordinator.py`
- **Lines**: 3406-3521 (116 lines)
- **Class**: `TestCoordinatorRunIntegration`

### Task Status

✅ Task marked as complete in `pr_info/TASK_TRACKER.md`

---

**All CLAUDE.md requirements followed:**
- ✅ Used MCP filesystem tools exclusively for all file operations
- ✅ Used MCP code-checker tools for all quality checks
- ✅ All code quality checks passed (pylint, pytest, mypy)
- ✅ Task marked as complete in TASK_TRACKER.md

---
Generated on: 2025-10-28T19:09:57.172471