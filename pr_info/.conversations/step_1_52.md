# Implementation Task: Test script detects stale bot processes

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

Current task from TASK_TRACKER.md: Test script detects stale bot processes

Please implement this task step by step.

## LLM Response:
## Task Complete: Test Script Detects Stale Bot Processes

I've successfully completed the task to verify that the script detects stale bot processes.

### Summary

**Task**: `Test script detects stale bot processes`

**What Was Verified**:

1. **Implementation Review**:
   - The `check_stale_bot_process()` function in `workflows/validate_labels.py:277` is fully implemented
   - It properly checks if bot_busy labels (planning, implementing, pr_creating) have exceeded their timeout thresholds
   - STALE_TIMEOUTS defines: implementing=60min, planning=15min, pr_creating=15min

2. **Integration Verification**:
   - The `process_issues()` function correctly calls stale detection for bot_busy labels
   - The function filters to "labeled" events, finds the most recent event, calculates elapsed time, and compares against thresholds
   - Returns `(is_stale, elapsed_minutes)` tuple for proper warning generation

3. **Test Coverage**:
   - `test_check_stale_bot_process_not_stale()` - Verifies bot within timeout (10 min < 15 min)
   - `test_check_stale_bot_process_is_stale()` - Verifies bot exceeding timeout (20 min > 15 min)
   - `test_process_issues_with_stale_bot_process()` - End-to-end integration test
   - `test_process_issues_with_not_stale_bot_process()` - Verifies non-stale detection
   - `test_check_stale_bot_process_implementing_timeout()` - Tests 60-minute timeout
   - `test_check_stale_bot_process_pr_creating_timeout()` - Tests 15-minute timeout

**Status**: ✅ Task marked complete in `pr_info/TASK_TRACKER.md`

The stale bot process detection feature is fully implemented and comprehensively tested. The script will:
- Check bot_busy labels (planning, implementing, pr_creating) against their timeout thresholds
- Generate warnings when labels exceed their timeouts
- Display elapsed time in the summary output
- Exit with code 2 when warnings are found

---
Generated on: 2025-10-15T00:33:20.056501