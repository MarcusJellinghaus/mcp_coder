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
The command requires approval. Let me ask the user to help run this test:

I need to test if the script detects stale bot processes by running it against the real GitHub API. However, the command requires approval.

Could you please approve running the following command to test stale bot process detection?

```bash
workflows\validate_labels.bat --log-level DEBUG --dry-run
```

This will:
1. Fetch all open issues from GitHub
2. Check each issue for workflow labels
3. For issues with bot_busy labels (like "planning", "implementing", "pr_creating"), it will check if the label has been there longer than the timeout threshold
4. Report any stale bot processes as warnings

The `--dry-run` flag ensures no changes are made to GitHub - it only reads and reports.

Alternatively, would you like me to:
- Run it without dry-run mode (which would make API calls to check events)?
- Create a unit test to verify the stale detection logic instead?
- Document the manual testing steps for you to run?

---
Generated on: 2025-10-15T00:30:55.600562