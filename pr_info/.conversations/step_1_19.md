# Implementation Task: Add `CREATE_PLAN_COMMAND_TEMPLATE` constant

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

Current task from TASK_TRACKER.md: Add `CREATE_PLAN_COMMAND_TEMPLATE` constant

Please implement this task step by step.

## LLM Response:
## Task Complete Summary

I've successfully completed the task to add the `CREATE_PLAN_COMMAND_TEMPLATE` constant to the coordinator module. Here's what was accomplished:

### ✅ Implementation Complete

**File Modified:** `src/mcp_coder/cli/commands/coordinator.py`

**Changes Made:**
- Added `CREATE_PLAN_COMMAND_TEMPLATE` constant after the `WORKFLOW_MAPPING` constant
- The template includes:
  - Git checkout to main branch
  - Git pull to get latest changes
  - Tool version verification (mcp-coder, claude)
  - Environment setup (uv sync)
  - MCP-coder create-plan command with configurable log level and issue number

### ✅ Code Quality Verification

All three code quality checks passed successfully:
- **Pytest**: ✅ 1094 tests collected and passed
- **Pylint**: ✅ No issues found
- **Mypy**: ✅ No type errors found

### ✅ Commit Message Prepared

```
feat(coordinator): add CREATE_PLAN_COMMAND_TEMPLATE constant

Add command template for create-plan workflow with git checkout,
environment verification, and mcp-coder execution steps.
```

### ✅ Task Tracker Updated

The task has been marked as complete in `pr_info/TASK_TRACKER.md` with the checkbox changed from `[ ]` to `[x]`.

**All CLAUDE.md requirements followed:**
- Used MCP filesystem tools exclusively for file operations
- Used MCP code-checker tools for all quality checks
- All code quality checks passed
- Task marked complete in tracker

The constant is now ready to be used in the workflow dispatcher implementation in the next task.

---
Generated on: 2025-10-28T11:08:44.944428