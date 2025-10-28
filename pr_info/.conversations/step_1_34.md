# Implementation Task: Write test: `test_execute_coordinator_run_requires_all_or_repo()`

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

Current task from TASK_TRACKER.md: Write test: `test_execute_coordinator_run_requires_all_or_repo()`

Please implement this task step by step.

## LLM Response:
## ✅ Task Complete

I have successfully implemented the test `test_execute_coordinator_run_requires_all_or_repo()` as specified in the task tracker.

### What was done:

1. **Added the test** to `tests/cli/commands/test_coordinator.py:2177-2220`:
   - Tests that `execute_coordinator_run()` validates that either `--all` or `--repo` must be specified
   - Verifies it returns exit code 1 when neither is provided
   - Confirms appropriate error message is printed to stderr

2. **Test verification**:
   - ✅ Test passes individually
   - ✅ All 1106 unit tests pass
   - ✅ Pylint check passes (no errors/fatal issues)
   - ✅ Mypy check passes (no type errors)

3. **Documentation**:
   - Prepared git commit message
   - Marked task as complete in `pr_info/TASK_TRACKER.md`

### Prepared Commit Message:
```
test: add validation test for coordinator run --all/--repo requirement

Add test_execute_coordinator_run_requires_all_or_repo() to verify that
execute_coordinator_run() properly validates that either --all or --repo
must be specified and returns exit code 1 with appropriate error message
when neither is provided.
```

**All CLAUDE.md requirements followed** - Used MCP tools exclusively for file operations and code quality checks.

---
Generated on: 2025-10-28T13:22:14.257760