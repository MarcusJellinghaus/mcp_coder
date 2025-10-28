# Implementation Task: Move `build_label_lookups()` from `workflows/validate_labels.py` to `workflows/label_config.py`

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

Current task from TASK_TRACKER.md: Move `build_label_lookups()` from `workflows/validate_labels.py` to `workflows/label_config.py`

Please implement this task step by step.

## LLM Response:
Perfect! Task completed successfully. Let me provide a final summary:

## ✅ Task Complete: Move `build_label_lookups()` to Shared Module

**Implementation Summary:**

I successfully moved the `build_label_lookups()` function and `LabelLookups` TypedDict from `workflows/validate_labels.py` to `workflows/label_config.py` as a shared component.

**Files Modified:**
1. `workflows/label_config.py` - Added `LabelLookups` TypedDict and `build_label_lookups()` function
2. `workflows/validate_labels.py` - Removed duplicates and updated imports
3. `tests/workflows/test_validate_labels.py` - Updated imports to reference new location

**Verification:**
- ✅ All 1065 pytest tests pass
- ✅ Pylint check passes (no errors)
- ✅ Mypy check passes (no type errors)
- ✅ Task marked complete in TASK_TRACKER.md

**Prepared Commit Message:**
```
refactor: Move build_label_lookups to shared label_config module

- Move LabelLookups TypedDict to workflows/label_config.py
- Move build_label_lookups() function to workflows/label_config.py
- Update imports in validate_labels.py
- Update imports in test_validate_labels.py
- All tests pass, no regressions
```

**All CLAUDE.md requirements followed:**
- ✅ Used MCP filesystem tools exclusively
- ✅ Used MCP code-checker tools for all quality checks
- ✅ All code quality checks passed
- ✅ Task marked complete in tracker

The refactoring is complete and ready for the next task in Step 0.

---
Generated on: 2025-10-28T08:56:17.894792