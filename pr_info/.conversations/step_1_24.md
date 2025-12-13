# Implementation Task: Update `CREATE_PLAN_COMMAND_WINDOWS` template (add DISABLE_AUTOUPDATER, --update-labels flag, archive listing)

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

Current task from TASK_TRACKER.md: Update `CREATE_PLAN_COMMAND_WINDOWS` template (add DISABLE_AUTOUPDATER, --update-labels flag, archive listing)

Please implement this task step by step.

## LLM Response:
Task completed successfully.

## Summary

I have completed the task: **Update `CREATE_PLAN_COMMAND_WINDOWS` template**

### Changes Made to `src/mcp_coder/cli/commands/coordinator.py`:

1. **Added `set DISABLE_AUTOUPDATER=1`** after the virtual environment activation block
2. **Added `--update-labels` flag** to the mcp-coder create-plan command
3. **Added archive listing** at the end of the template:
   - `echo archive after execution =======================================`
   - `dir .mcp-coder\create_plan_sessions`
   - `dir logs`

### Code Quality Verification:
- **Pylint**: No issues found
- **Mypy**: No type errors found

### Task Tracker Updated:
- Marked the task checkbox as `[x]` in `pr_info/TASK_TRACKER.md`

---
Generated on: 2025-12-13T11:02:31.140336