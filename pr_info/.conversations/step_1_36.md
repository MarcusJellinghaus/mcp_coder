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
I need user approval to run the integration tests. Let me explain what I need to do:

## STEP 2: IMPLEMENTATION - Manual Integration Testing

I need to perform manual integration testing with the real GitHub API by running the `validate_labels.bat` script against your actual repository. This testing will verify:

1. **--help flag works** - Shows usage information
2. **--dry-run flag works** - Previews changes without making them
3. **--log-level DEBUG works** - Shows detailed logging
4. **Real GitHub API integration** - Tests against actual repository data
5. **Exit codes** - Verifies correct exit codes (0, 1, 2)

However, I need your approval to run Bash commands. The commands I need to run are:

```bash
# Test 1: Help flag
workflows\validate_labels.bat --help

# Test 2: Dry-run mode (safe - no changes)
workflows\validate_labels.bat --dry-run

# Test 3: Debug logging with dry-run (safe - no changes)
workflows\validate_labels.bat --log-level DEBUG --dry-run

# Test 4: Check exit code
echo %ERRORLEVEL%
```

**These tests are safe because:**
- The `--help` flag just shows documentation
- The `--dry-run` flag previews changes WITHOUT actually making any API modifications
- All tests will use your actual GitHub repository to verify the script works correctly

**Would you like me to proceed with these integration tests?** Please approve the Bash command execution, or if you prefer, I can provide you with the test commands to run manually and you can share the results with me.

Alternatively, if you'd like me to document what SHOULD be tested without actually running the commands, I can do that instead.

---
Generated on: 2025-10-15T00:03:38.588879