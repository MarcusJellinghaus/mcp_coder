# Implementation Task: Implement label configuration loading

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

Current task from TASK_TRACKER.md: Implement label configuration loading

Please implement this task step by step.

## LLM Response:
Perfect! Let me create a summary of what was accomplished:

## Task Completion Summary

**Task:** Implement label configuration loading

**What was implemented:**

1. **Core Functionality in `get_eligible_issues()`:**
   - Load label configuration from `project_dir/workflows/config/labels.json`
   - Extract bot_pickup labels (labels with `category="bot_pickup"`)
   - Extract ignore_labels from configuration
   - Query all open issues via `IssueManager.list_issues(state="open", include_pull_requests=False)`
   - Filter issues to have **exactly one** bot_pickup label
   - Exclude issues with any ignore_labels
   - Sort filtered issues by priority using `PRIORITY_ORDER` (status-08 → 05 → 02)
   - Add debug logging for filtering results

2. **Code Quality:**
   - ✅ All 4 test cases pass (`test_get_eligible_issues_*`)
   - ✅ Pylint check passed with no issues
   - ✅ Pytest check passed (fast unit tests only)
   - ✅ Mypy type check passed with no errors

3. **Files Modified:**
   - `src/mcp_coder/cli/commands/coordinator.py` - Implemented `get_eligible_issues()` function
   - `pr_info/TASK_TRACKER.md` - Marked all Step 2 implementation tasks as complete

**Prepared Commit Message:**
```
feat(coordinator): implement label configuration loading in get_eligible_issues

Implement core issue filtering logic to identify automation-ready issues:
- Load label config from project_dir/workflows/config/labels.json
- Query open issues via IssueManager (exclude pull requests)
- Filter for exactly one bot_pickup label per issue
- Exclude issues with any ignore_labels
- Sort by priority: status-08 → status-05 → status-02
- Add debug logging for filtering results

All tests pass (pylint, pytest, mypy).
```

**All CLAUDE.md requirements followed:**
- ✅ Used MCP filesystem tools for file operations
- ✅ Used MCP code-checker tools for all quality checks
- ✅ All code quality checks passed
- ✅ Task marked as complete in TASK_TRACKER.md

The implementation is complete and ready for the next step!

---
Generated on: 2025-10-28T10:58:33.982863