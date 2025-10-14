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
I need user approval to run the manual integration tests. Let me explain what I need:

## Manual Integration Testing Required

I need to perform manual integration testing with the real GitHub API. The script is ready and I need to run the following tests:

### Test Plan:

1. **Test --help flag**: Verify the help message displays correctly
   ```
   python workflows\validate_labels.py --help
   ```

2. **Test --dry-run mode**: Preview changes without making actual API calls
   ```
   python workflows\validate_labels.py --dry-run
   ```

3. **Test --log-level DEBUG**: Run with detailed logging
   ```
   python workflows\validate_labels.py --log-level DEBUG
   ```

4. **Test normal execution**: Run the script on the real repository
   ```
   python workflows\validate_labels.py
   ```

5. **Test exit codes**: Verify proper exit codes (0, 1, 2) by checking `echo %ERRORLEVEL%` after each run

### Questions for you:

1. **Do you want me to proceed with these tests?** (They will interact with your actual GitHub repository)

2. **What validation scenarios do you want me to focus on?**
   - Issues without labels
   - Issues with multiple status labels
   - Stale bot processes
   - Ignored labels

3. **Should I use --dry-run first** to preview what changes would be made before actually applying them?

Please approve the tests you'd like me to run, or let me know if you prefer to run these manually yourself and just report the results back to me for documentation.

---
Generated on: 2025-10-14T23:54:26.173672