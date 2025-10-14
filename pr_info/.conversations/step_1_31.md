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

**Manual Integration Testing with Real GitHub API**

I need to run the `validate_labels.py` script against the actual GitHub repository to verify it works correctly in production. This is the current task from the TASK_TRACKER.md.

**Test scenarios I need to execute:**

1. **Basic help command**: `python workflows/validate_labels.py --help`
   - Verify the script shows proper help information

2. **Dry-run mode**: `python workflows/validate_labels.py --dry-run`
   - Verify it previews changes without making actual API calls to modify labels
   - Check that it correctly identifies issues needing validation

3. **Normal execution with debug logging**: `python workflows/validate_labels.py --log-level DEBUG`
   - Run against the real repository
   - Verify it can:
     - Detect issues without labels (should initialize with "created")
     - Detect issues with multiple status labels (ERROR condition)
     - Detect stale bot processes (WARNING condition)
     - Respect ignore_labels configuration
     - Display proper summary output

4. **Exit code verification**: After each run, check `echo %ERRORLEVEL%`
   - 0 = success (no errors or warnings)
   - 1 = errors found (multiple status labels)
   - 2 = warnings only (stale bot processes)

**What I need from you:**

Please approve the bash commands so I can run these integration tests. The script will:
- Read the current state of GitHub issues from your repository
- In dry-run mode: only read, no modifications
- In normal mode: may add "created" labels to issues that lack status labels

Should I proceed with these integration tests?

---
Generated on: 2025-10-14T23:57:46.998444