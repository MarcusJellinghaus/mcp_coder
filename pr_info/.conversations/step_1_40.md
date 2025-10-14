# Implementation Task: Perform manual integration testing with real GitHub API

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

Current task from TASK_TRACKER.md: Perform manual integration testing with real GitHub API

Please implement this task step by step.

## LLM Response:
I see that running the script requires approval. Let me explain what needs to be tested and ask the user to proceed.

I need to perform manual integration testing with the real GitHub API. The testing involves:

1. **Test --help flag**: `python workflows\validate_labels.py --help`
   - Verifies the script runs and displays help information

2. **Test dry-run mode**: `python workflows\validate_labels.py --dry-run`
   - Shows what changes would be made without actually making them
   - Should process issues and report findings without modifying labels

3. **Test with DEBUG logging**: `python workflows\validate_labels.py --log-level DEBUG`
   - Shows detailed processing information
   - Helps verify the logic is working correctly

4. **Normal execution**: `python workflows\validate_labels.py`
   - Actually processes issues and may make changes
   - Tests the complete workflow

5. **Verify exit codes**: After each run, check `echo %ERRORLEVEL%`
   - Should be 0 for success (no issues found)
   - Should be 1 for errors (issues without labels, multiple labels)
   - Should be 2 for warnings (stale bot processes)

**Would you like me to proceed with these integration tests?** They will:
- Read from your actual GitHub repository
- In dry-run mode, they won't make changes
- In normal mode, they may add/remove labels on issues

Please approve the bash commands so I can run the integration tests, or let me know if you'd like to run them manually and report the results back to me.

---
Generated on: 2025-10-15T00:08:15.015233