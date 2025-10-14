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
The user needs to approve the script execution for GitHub API access. Let me explain what I need and what the test will verify:

## Test Plan for Stale Bot Process Detection

I need to test whether the `validate_labels.py` script correctly detects when an issue has been stuck in a `bot_busy` status for too long. Here's what I need to verify:

### What the Script Should Detect:

The script checks for three bot_busy labels with these timeout thresholds:
- **status-03:planning** - timeout: 15 minutes
- **status-06:implementing** - timeout: 60 minutes  
- **status-09:pr-creating** - timeout: 15 minutes

If an issue has one of these labels and it was applied more than the timeout threshold ago, the script should:
1. Detect it as a "stale bot process"
2. Add it to the warnings section
3. Display the issue number, label name, and elapsed time
4. Exit with code 2 (warnings only) if no errors exist

### Test Procedure:

I need to run the script and verify:

```bash
workflows\validate_labels.bat --log-level DEBUG
```

The DEBUG output should show:
- For each issue with a bot_busy label, whether it's stale or not
- API calls to `get_issue_events()` for checking staleness
- Warnings logged for any stale processes

### Expected Output:

If a stale bot process is detected, the summary should include:
```
Warnings (stale bot processes): 1
  - Issue #XX: planning (20 minutes)
```

And the script should exit with code 2.

**May I have approval to run the GitHub API integration test?** The script will:
1. Fetch open issues from the repository
2. Check which ones have bot_busy labels
3. Query GitHub Events API to determine when those labels were applied
4. Report any that exceed the timeout thresholds

This is a read-only operation that will help verify the stale bot process detection feature works correctly.

---
Generated on: 2025-10-15T00:29:50.209657