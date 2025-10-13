# Implementation Task: Run pytest check (fast unit tests) on entire implementation and fix all issues found

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

Current task from TASK_TRACKER.md: Run pytest check (fast unit tests) on entire implementation and fix all issues found

Please implement this task step by step.

## LLM Response:
## ✅ Task Completed Successfully

**Task:** Run pytest check (fast unit tests) on entire implementation and fix all issues found

**Results:**
- ✅ Pytest check completed successfully
- ✅ 994 tests passed
- ✅ 4 tests skipped (integration tests excluded as per CLAUDE.md requirements)
- ✅ 0 failures
- ✅ Task marked complete in TASK_TRACKER.md

**Test Command Used:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
```

**All CLAUDE.md requirements followed:**
- ✅ Used MCP code-checker tool (not Bash)
- ✅ Used fast unit tests with proper marker exclusions
- ✅ All tests passed - no issues to fix
- ✅ Task marked complete in TASK_TRACKER.md
- ✅ Parallel execution enabled with `-n auto`

The entire implementation is now verified with fast unit tests and ready to proceed to the next task: mypy check on entire implementation.

---
Generated on: 2025-10-13T09:14:02.671817