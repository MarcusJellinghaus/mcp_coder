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
I see that running the script requires user approval since it involves external operations. Let me document the manual testing plan and ask the user to help with the actual execution:

**Manual Integration Testing Plan**

I've reviewed the implementation and prepared the testing plan. Since running the script requires approval (it will make GitHub API calls), I'll need your help to perform the manual integration tests. Here's what needs to be tested:

## Testing Checklist

### 1. Basic Functionality Tests

**Test 1: Help Flag**
```bash
python workflows/validate_labels.py --help
```
Expected: Display help message with all command-line options

**Test 2: Dry-Run Mode**
```bash
python workflows/validate_labels.py --dry-run
```
Expected: 
- Preview what would happen without making changes
- Should NOT make any API calls to add labels
- Display summary of what would be changed

**Test 3: Debug Logging**
```bash
python workflows/validate_labels.py --log-level DEBUG --dry-run
```
Expected: Show detailed processing information including API call counts

**Test 4: Normal Execution**
```bash
python workflows/validate_labels.py
```
Expected: Run validation and make actual changes if needed

### 2. Validation Detection Tests

The script should detect these scenarios in the repository:

**Test 5: Issues Without Labels**
- Expected: Script identifies issues with no workflow status labels
- Expected: Initializes them with "status-01:created" label
- Verification: Check if any issues in the repo currently lack status labels

**Test 6: Issues with Multiple Labels**
- Expected: Script detects and reports as ERROR
- Expected: Lists conflicting labels in output
- Verification: You may need to manually create a test issue with 2 status labels to verify this

**Test 7: Stale Bot Processes**
- Expected: Script detects bot_busy labels that have exceeded timeout
- Expected: Reports as WARNING with elapsed time
- Verification: Check if any issues have bot_busy labels (planning, implementing, pr_creating)

**Test 8: Ignore Labels**
- Expected: Issues with "Overview" or other ignore labels are skipped
- Verification: Check that issues with ignore labels don't appear in validation results

### 3. Exit Code Tests

After each test above, run:
```bash
echo %ERRORLEVEL%
```

Expected exit codes:
- `0` = Success (no errors or warnings)
- `1` = Errors found (multiple status labels or API errors)
- `2` = Warnings only (stale bot processes)

### 4. Batch File Test

```bash
workflows\validate_labels.bat --dry-run
echo %ERRORLEVEL%
```
Expected: Batch file wrapper works correctly and forwards all arguments

---

Would you like me to proceed with these tests? I'll need your approval to run the commands since they involve GitHub API access. Alternatively, you can run these tests manually and share the results with me so I can:
1. Document the findings
2. Fix any issues discovered
3. Mark the testing tasks as complete

What would you prefer?

---
Generated on: 2025-10-14T23:59:11.265700