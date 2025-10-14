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
I need user approval to run the integration tests with the real GitHub API. Let me explain what I need to do:

**STEP 1: SELECT TASK**
I'm working on: **Perform manual integration testing with real GitHub API**

**Current Status:**
The code is ready for integration testing. I have created a todo list to track the following integration test scenarios:

1. ✅ Test --help flag (ready to run)
2. Test --dry-run mode (preview without making changes)
3. Test normal execution with real GitHub API
4. Verify exit codes (0 for success, 1 for errors, 2 for warnings)
5. Document the results

**I need your approval to proceed with the integration testing, which will:**

1. **First test (--help)**: Show help message without any API calls
2. **Second test (--dry-run)**: Query GitHub API to fetch issues but make NO changes to labels
3. **Third test (normal mode)**: Query GitHub API and potentially ADD labels to issues that are missing status labels

**Important Notes:**
- The script will only ADD the "created" label to issues that have NO workflow status labels
- It will NOT modify or remove any existing labels
- It will detect and report issues with multiple status labels (errors)
- It will detect and report stale bot processes (warnings)
- The --dry-run mode is safe and makes no changes

**May I proceed with running these integration tests?** I'll start with the safe --help and --dry-run tests first before running any operation that might modify labels.

---
Generated on: 2025-10-14T23:56:39.194727