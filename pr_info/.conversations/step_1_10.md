# Implementation Task: Implement calculate_elapsed_minutes() helper function

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

Current task from TASK_TRACKER.md: Implement calculate_elapsed_minutes() helper function

Please implement this task step by step.

## LLM Response:
Perfect! Task completed successfully. Let me provide a summary:

## Task Completion Summary

✅ **Successfully implemented `calculate_elapsed_minutes()` helper function**

### What was implemented:

**File: `workflows/validate_labels.py`**
- Added `datetime` and `timezone` imports
- Implemented `calculate_elapsed_minutes()` function that:
  - Handles ISO format timestamps with 'Z' suffix or UTC offset
  - Calculates elapsed time from current UTC time
  - Returns integer minutes elapsed

**File: `tests/workflows/test_validate_labels.py`**
- Added 6 comprehensive unit tests covering:
  - Timestamps with 'Z' suffix format
  - Timestamps with '+00:00' UTC offset format
  - Recent timestamps (seconds -> 0 minutes)
  - One hour elapsed (60 minutes)
  - Multiple hours elapsed (150 minutes)
  - Timestamps with microsecond precision

### Code Quality Results:
- ✅ **Pylint**: No issues found
- ✅ **Pytest**: All 6 new tests pass
- ✅ **Mypy**: No type errors

### Commit Message Prepared:
```
feat(validate-labels): implement calculate_elapsed_minutes() helper

Add helper function to calculate elapsed time since ISO timestamps for
bot process timeout validation. Handles both 'Z' suffix and UTC offset
formats, returning integer minutes elapsed.

Includes comprehensive unit tests covering:
- Z suffix and +00:00 offset formats
- Recent timestamps (seconds -> 0 minutes)
- Various time ranges (30min, 45min, 60min, 150min)
- Microsecond precision timestamps
```

### Task Tracker Status:
✅ Marked task as complete in `pr_info/TASK_TRACKER.md`

**All CLAUDE.md requirements followed:**
- Used MCP code-checker tools exclusively for quality checks
- All three checks (pylint, pytest, mypy) passed
- No issues remain unresolved
- Task marked as complete in tracker

The implementation is ready for the next task in Step 3.

---
Generated on: 2025-10-14T11:17:14.655310