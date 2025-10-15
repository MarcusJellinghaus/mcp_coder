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
## Integration Testing Approach

Since this task requires **manual integration testing with real GitHub API**, I need your approval to run the commands. Here's what I'll test:

### Test Scenarios

1. **Dry-run mode** - Preview without making changes
2. **Detection of issues without labels** - Check if script identifies and can initialize them
3. **Detection of multiple status labels** - Check error detection
4. **Detection of stale bot processes** - Check warning detection  
5. **Respect for ignore_labels** - Verify issues with "Overview" or other ignore labels are skipped

### Commands to Run

```bash
# Test 1: Dry-run with debug logging
python workflows\validate_labels.py --dry-run --log-level DEBUG

# Test 2: Normal run with INFO level
python workflows\validate_labels.py --log-level INFO

# Test 3: Check exit code
echo %ERRORLEVEL%
```

**Before I proceed, I need your approval to:**
1. Run these commands against the real GitHub repository
2. The script may make API calls to fetch issues and events
3. In dry-run mode, it won't make changes but will read from GitHub
4. In normal mode, it may add "created" labels to issues without status labels

Would you like me to:
- **Option A**: Proceed with running the integration tests (requires approval)
- **Option B**: Document the test plan for you to run manually
- **Option C**: Skip this step and move to the next task

Please let me know how you'd like to proceed!

---
Generated on: 2025-10-14T23:50:38.813992