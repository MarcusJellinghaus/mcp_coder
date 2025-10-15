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
I need approval to run bash commands. Let me explain what I need to do for manual integration testing:

## Manual Integration Testing Plan

I need to perform manual integration testing with the real GitHub API to verify the script works correctly. The testing checklist from step_5.md includes:

### Test Scenarios Required:
1. **Test script detects issues without labels** - Verify the script initializes issues with 'created' label
2. **Test script detects issues with multiple labels** - Verify ERROR detection
3. **Test script detects stale bot processes** - Verify WARNING detection with timing
4. **Test script respects ignore_labels** - Verify issues with "Overview" label are skipped

### Commands I Need to Run:
1. `python workflows\validate_labels.py --dry-run --log-level DEBUG` - Preview what would happen
2. `python workflows\validate_labels.py --log-level INFO` - Run actual validation
3. Check exit codes with `echo %ERRORLEVEL%` after each run

### Why This is Important:
- This verifies the complete end-to-end workflow with real GitHub API
- Tests all the validation logic we've built in previous steps
- Ensures the script handles actual repository data correctly
- Validates error handling, warnings, and success cases

**Can I proceed with running these bash commands to perform the manual integration testing?** This is a read-only test in dry-run mode first, then we can decide if we want to run the actual validation.

---
Generated on: 2025-10-14T23:46:53.424028