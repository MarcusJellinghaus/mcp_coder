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
I understand that commands require approval. Let me inform you about what I need to do:

## Manual Integration Testing Required

I need to perform manual integration testing of the `validate_labels.py` script with the real GitHub API. This is the current task from the task tracker.

The testing steps are:

1. **Test --help flag** - Verify the script shows proper help
2. **Test --dry-run** - Preview what changes would be made (no actual changes)
3. **Test DEBUG logging** - See detailed processing information
4. **Verify GitHub API access** - Confirm the script can read issue data

### Commands I need to run:

```bash
# 1. Show help message
python workflows/validate_labels.py --help

# 2. Dry-run to preview changes (read-only, no modifications)
python workflows/validate_labels.py --dry-run

# 3. Run with DEBUG logging to see detailed processing
python workflows/validate_labels.py --dry-run --log-level DEBUG

# 4. Check exit code
echo Exit code: %ERRORLEVEL%
```

All of these commands are **read-only operations** during dry-run mode. The script will:
- Read issue data from the GitHub API
- Validate label status
- Show what changes would be made
- NOT make any actual changes (because of --dry-run flag)

**Would you like me to proceed with these integration tests?** If yes, I'll need approval to run the bash commands, or you can run them manually and share the output with me so I can document the results.

Alternatively, if you'd prefer, you can run these commands yourself in your terminal and share the output, and I'll analyze the results and mark the task as complete.

---
Generated on: 2025-10-14T23:52:02.536116