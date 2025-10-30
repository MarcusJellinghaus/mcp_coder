# Implementation Task: Add `IMPLEMENT_COMMAND_TEMPLATE` constant

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

Current task from TASK_TRACKER.md: Add `IMPLEMENT_COMMAND_TEMPLATE` constant

Please implement this task step by step.

## LLM Response:
## Task Complete ✅

I have successfully completed the task to add `IMPLEMENT_COMMAND_TEMPLATE` constant to `coordinator.py`.

### Summary

**What was done:**
- Added `IMPLEMENT_COMMAND_TEMPLATE` constant to `src/mcp_coder/cli/commands/coordinator.py` (line 87-93)
- The template includes:
  - Git checkout of the branch
  - Git pull to sync with remote
  - Tool version verification (mcp-coder and claude)
  - Dependency sync with `uv sync --extra dev`
  - MCP-coder implement command with proper parameters

**Code quality checks - all passed:**
- ✅ Pylint check: No issues found
- ✅ Pytest check: 1094 tests passed (fast unit tests only)
- ✅ Mypy check: No type errors found

**Commit message prepared:**
```
feat(coordinator): add IMPLEMENT_COMMAND_TEMPLATE constant

Add workflow command template for implement workflow execution.
Template includes git checkout, tool verification, dependency sync,
and mcp-coder implement command with proper parameters.
```

**Task tracker updated:**
- Marked `Add IMPLEMENT_COMMAND_TEMPLATE constant` as complete in `pr_info/TASK_TRACKER.md`

All CLAUDE.md requirements followed: Used MCP tools exclusively, all code quality checks passed, task marked complete in tracker.

---
Generated on: 2025-10-28T11:14:05.440850