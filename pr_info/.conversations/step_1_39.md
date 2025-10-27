# Implementation Task: Fix 4: Standardize test mocking to monkeypatch in test_env.py

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

Current task from TASK_TRACKER.md: Fix 4: Standardize test mocking to monkeypatch in test_env.py

Please implement this task step by step.

## LLM Response:
Perfect! ✅ The task tracker has been updated successfully. All items in Step 5 related to Fix 4 are now marked as complete:

- [x] Fix 4: Standardize test mocking to monkeypatch in test_env.py
- [x] Run pytest - verify all tests pass  
- [x] Run pylint - verify no new issues
- [x] Run mypy - verify no type errors

## Summary

**Task completed successfully:** Fix 4: Standardize test mocking to monkeypatch in test_env.py

**Changes made:**
1. ✅ Replaced `with patch.object(sys, "prefix", system_prefix):` with `monkeypatch.setattr(sys, "prefix", system_prefix)` in two test functions:
   - `test_prepare_llm_environment_uses_sys_prefix_fallback` (tests/llm/test_env.py:70)
   - `test_prepare_llm_environment_all_invalid_uses_sys_prefix` (tests/llm/test_env.py:136)

2. ✅ Removed unused `from unittest.mock import MagicMock, patch` import

**Quality checks - All passed:**
- ✅ Pytest: 1022 tests passed
- ✅ Pylint: No issues found
- ✅ Mypy: No type errors

**Prepared commit message:**
```
refactor(step5): standardize test mocking to monkeypatch in test_env.py

Replace patch.object with monkeypatch.setattr for sys.prefix mocking
to maintain consistency across all tests in test_env.py.
```

**All CLAUDE.md requirements followed:**
- ✅ Used MCP filesystem tools exclusively for file operations
- ✅ Used MCP code-checker tools for all quality checks
- ✅ All code quality checks passed

The task has been marked complete in pr_info/TASK_TRACKER.md and is ready for the next step in the workflow.

---
Generated on: 2025-10-27T02:42:14.908707