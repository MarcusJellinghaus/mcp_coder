# Implementation Task: Test script detects issues without labels

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

Current task from TASK_TRACKER.md: Test script detects issues without labels

Please implement this task step by step.

## LLM Response:
I need user approval to run these commands. Let me explain what I'm trying to do:

I'm working on **Step 5: Test script detects issues without labels** from the task tracker. This requires running the `validate_labels.py` script to verify it correctly detects and handles issues that don't have workflow status labels.

To complete this task, I need to:

1. Run the script with `--dry-run` to see what it detects without making changes
2. Verify that it correctly identifies issues without workflow labels
3. Confirm the behavior matches the specification

However, I need your approval to run the following commands:
- `python workflows/validate_labels.py --dry-run --log-level DEBUG` - to test the script
- `gh issue list --state open --limit 20 --json number,title,labels` - to see what issues exist in the repository

**Question**: Should I proceed with running these commands to test the script's ability to detect issues without labels? This is a manual integration test as specified in step_5.md.

---
Generated on: 2025-10-15T00:14:26.347106