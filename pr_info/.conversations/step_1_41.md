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
I understand that I cannot execute the bash commands without user approval. Given this constraint, I need to explain to the user what manual integration testing needs to be performed and provide them with the necessary information to do it themselves or approve the commands.

Let me document the integration testing that needs to be performed:

## Manual Integration Testing Required

I've prepared the validation script for manual integration testing, but I need your approval to run the commands that will interact with the real GitHub API. Here's what needs to be tested:

### Test Plan

**1. Test Help Flag**
```bash
workflows\validate_labels.bat --help
```
Expected: Display help message without errors

**2. Test Dry-Run Mode** (Recommended first)
```bash
workflows\validate_labels.bat --dry-run --log-level INFO
```
Expected: Preview what changes would be made without actually making them

**3. Test Debug Logging**
```bash
workflows\validate_labels.bat --dry-run --log-level DEBUG
```
Expected: Show detailed processing information

**4. Test Actual Execution**
```bash
workflows\validate_labels.bat --log-level INFO
```
Expected: Process all open issues and:
- Initialize issues without status labels with "created"
- Detect issues with multiple status labels (ERRORS)
- Detect stale bot_busy processes (WARNINGS)
- Skip issues with ignore labels

**5. Check Exit Code**
```bash
echo %ERRORLEVEL%
```
Expected exit codes:
- `0` = Success (no errors or warnings)
- `1` = Errors found (multiple status labels or API errors)
- `2` = Warnings only (stale bot processes)

### What the Tests Will Verify

According to the step requirements, we need to verify:
- ✅ Script detects issues without labels → Should initialize them with "created"
- ✅ Script detects issues with multiple labels → Should report as ERRORS
- ✅ Script detects stale bot processes → Should report as WARNINGS with elapsed time
- ✅ Script respects ignore_labels → Should skip issues with "Overview" or other ignore labels

### Current Repository State

The script will connect to your GitHub repository and:
1. Fetch all open issues
2. Check each issue's workflow status labels
3. Report any anomalies
4. Initialize missing labels (unless in dry-run mode)

Would you like me to:
1. **Run the tests with your approval** - I'll execute the commands and show you the results
2. **Provide instructions for you to run manually** - You can run the commands yourself and share the results
3. **Skip integration testing and move to next step** - If you're confident the unit tests are sufficient

Please let me know how you'd like to proceed with the manual integration testing.

---
Generated on: 2025-10-15T00:09:36.838225