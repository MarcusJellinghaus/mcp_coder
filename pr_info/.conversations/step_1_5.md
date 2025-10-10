# Implementation Task: Implement `manage_branch()` function - Get existing or create new linked branch

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

Current task from TASK_TRACKER.md: Implement `manage_branch()` function - Get existing or create new linked branch

Please implement this task step by step.

## LLM Response:
Perfect! Now let me prepare the commit message as required by Step 5:

## Summary

I have successfully implemented Step 3 of the create_plan workflow. Here's what was completed:

### ✅ Implementation Complete

**Files Modified:**
- `workflows/create_plan.py` (workflows/create_plan.py:125-198)
  - Added `manage_branch()` function - Manages branch linking for GitHub issues
  - Added `verify_steps_directory()` function - Validates pr_info/steps/ is empty
  - Added necessary imports for IssueBranchManager and checkout_branch

**Files Created:**
- `tests/workflows/create_plan/test_branch_management.py` - Comprehensive test suite with 19 test cases

### 🔍 Implementation Details

**manage_branch() function:**
- Uses IssueBranchManager to check for existing linked branches
- If branches exist, uses the first one
- If no branches exist, creates a new branch on GitHub via GraphQL API
- Checks out the branch locally using checkout_branch()
- Returns branch name on success, None on error
- Comprehensive error handling and logging

**verify_steps_directory() function:**
- Checks if pr_info/steps/ directory exists
- Returns True if directory doesn't exist or is empty
- Returns False and logs error with file list if directory contains files
- Strict validation to ensure clean directory before plan generation

### ✅ All Code Quality Checks Passed

- **Pylint**: ✅ No errors or fatal issues
- **Pytest**: ✅ 825 tests passed, 4 skipped
- **Mypy**: ✅ No type errors

### 📋 Prepared Git Commit Message

```
feat(create-plan): implement branch management and directory verification - Step 3

Add manage_branch() and verify_steps_directory() functions to the create_plan workflow.
These functions handle GitHub issue-branch linking and validate the pr_info/steps/ directory
is clean before generating a new implementation plan.
```

### ✅ All CLAUDE.md Requirements Followed

- Used MCP tools exclusively (mcp__filesystem__*, mcp__code-checker__*)
- All code quality checks passed using MCP tools
- No standard Claude tools (Read/Write/Edit) were used for file operations
- All tests pass with proper pytest configuration

The implementation is complete and ready for the next step!

---
Generated on: 2025-10-10T08:52:33.190649