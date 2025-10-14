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
I need user approval to run commands. Let me explain the situation and what needs to be done:

I need to perform manual integration testing with the real GitHub API. To do this effectively, I need to:

1. **Test the --help flag** to verify basic script functionality
2. **Test --dry-run mode** to preview changes without making API modifications
3. **Run with real API** to verify the script works correctly with GitHub
4. **Test all exit codes** (0 for success, 1 for errors, 2 for warnings)
5. **Verify edge cases** like issues without labels, multiple labels, and stale processes

However, I'm being blocked from running bash commands that would execute the script. 

**Can you approve the bash commands so I can proceed with the integration testing?** Alternatively, you could run the following commands manually and share the results with me:

```bash
# Test 1: Help flag
python workflows\validate_labels.py --help

# Test 2: Dry-run mode
python workflows\validate_labels.py --dry-run

# Test 3: Debug logging with dry-run
python workflows\validate_labels.py --log-level DEBUG --dry-run

# Test 4: Actual run (if you want to test with real API)
python workflows\validate_labels.py

# Test 5: Check exit code after each run
echo %ERRORLEVEL%

# Test 6: Test batch file
workflows\validate_labels.bat --help
workflows\validate_labels.bat --dry-run
```

Would you like to:
1. Approve the bash commands so I can run the tests automatically, or
2. Run the tests manually and provide me with the output so I can verify everything works correctly?

---
Generated on: 2025-10-15T00:10:46.492547