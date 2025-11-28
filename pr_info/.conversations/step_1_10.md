# Implementation Task: Add `test_execute_coordinator_test_linux_template` test

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

Current task from TASK_TRACKER.md: Add `test_execute_coordinator_test_linux_template` test

Please implement this task step by step.

## LLM Response:
Perfect! I have successfully completed the main task requirement which was to add the `test_execute_coordinator_test_linux_template` test. The test has been:

1. ✅ Added to `tests/cli/commands/test_coordinator.py` 
2. ✅ Marked as completed in `pr_info/TASK_TRACKER.md`

The test validates that when `executor_os = "linux"`, the Linux template is used in the `execute_coordinator_test()` function. It checks that:
- The command contains `source .venv/bin/activate` (Linux-specific)
- The command contains `which mcp-coder` (Linux-specific)
- The command does NOT contain `@echo ON` (Windows-specific)
- The command does NOT contain `VENV_BASE_DIR` (Windows-specific)

This completes the **Part 1** of Step 3 (Write Tests First) from the task requirements. The test file has been successfully modified, and the task tracker has been updated to reflect completion of this specific task.

---
Generated on: 2025-11-23T21:32:23.381491