# Implementation Task: Implement check_status_labels() to count workflow labels

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

Current task from TASK_TRACKER.md: Implement check_status_labels() to count workflow labels

Please implement this task step by step.

## LLM Response:
Perfect! 

## Summary

I have successfully completed the task to implement `check_status_labels()` function:

**Implementation Details:**
- Added `check_status_labels()` function in `workflows/validate_labels.py:104-131`
- Function takes an `IssueData` and `workflow_label_names` set as parameters
- Returns a tuple of (count, list_of_status_labels)
- Implementation filters issue labels to only those present in workflow_label_names

**Tests Added:**
- 8 comprehensive test cases covering all scenarios
- Tests for: no labels, one label, multiple labels, empty labels, all workflow labels, three or more labels, and order preservation
- All tests use proper type casting with `cast(IssueData, issue_dict)` for type safety

**Quality Checks:**
- ✅ Pylint: No issues found
- ✅ Pytest: All 23 tests pass (including 8 new tests for check_status_labels)
- ✅ Mypy: No type errors

**Commit Message Prepared:**
```
feat(validate-labels): implement check_status_labels() for step 3.2

Add check_status_labels() function to count workflow status labels on issues.
This function identifies issues with zero, one, or multiple workflow labels,
enabling detection of initialization needs and duplicate label errors.
```

**All CLAUDE.md requirements followed:** Used MCP tools exclusively for all operations.

---
Generated on: 2025-10-14T11:29:14.286388