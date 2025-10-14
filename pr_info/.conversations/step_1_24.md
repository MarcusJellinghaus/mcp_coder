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
Now let me provide a summary document for the user with the exact commands to run for manual integration testing:

## **STEP 2: MANUAL INTEGRATION TESTING**

I've prepared comprehensive integration testing documentation. Since bash commands require your approval, here are the **exact commands you need to run** to complete the manual integration testing:

### Test Commands to Execute

**1. Test help flag:**
```cmd
workflows\validate_labels.bat --help
```
Expected: Help message displayed, exit code 0

**2. Test dry-run mode:**
```cmd
workflows\validate_labels.bat --dry-run
```
Expected: Shows what would be done WITHOUT making changes, displays summary

**3. Test normal run (makes real GitHub API changes):**
```cmd
workflows\validate_labels.bat
```
Expected: Connects to GitHub, processes issues, adds labels if needed

**4. Test debug logging:**
```cmd
workflows\validate_labels.bat --log-level DEBUG
```
Expected: Detailed logging output with API call counts

**5. Check exit code after each run:**
```cmd
echo %ERRORLEVEL%
```
Expected: 
- 0 = success (no errors/warnings)
- 1 = errors found (multiple status labels)
- 2 = warnings only (stale bot processes)

### What the Script Should Do

The script validates GitHub issue labels and:
- **Detects issues without status labels** → Adds "status-01:created" label
- **Detects issues with multiple status labels** → Reports as ERROR
- **Detects stale bot_busy processes** → Reports as WARNING (if label exceeds timeout)
- **Respects ignore_labels** → Skips issues with ignore labels from config

### Integration Testing Documentation

I've created a comprehensive testing guide at:
- `pr_info/steps/step_5_integration_testing.md`

This document includes:
- All test scenarios with expected results
- Troubleshooting guidance
- Success criteria checklist
- Section to document your testing results

---

Since I cannot execute the bash commands directly (they require your approval), **please run the above commands** and verify:

1. ✅ All command-line flags work correctly
2. ✅ Dry-run mode prevents API changes
3. ✅ Normal mode successfully modifies GitHub labels
4. ✅ Exit codes match validation results
5. ✅ Error handling works gracefully

Once you've completed the manual testing, I can proceed to mark this task as complete in the task tracker. Would you like me to:

**Option A:** Assume the manual testing will pass and proceed to mark the task complete now?

**Option B:** Wait for you to run the tests and report back the results?

Let me know which approach you prefer!

---
Generated on: 2025-10-14T23:49:19.796193