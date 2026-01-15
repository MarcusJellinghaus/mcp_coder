# Implementation Task: Add test class `TestGetRebaseTargetBranch` to `tests/workflows/implement/test_core.py`

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Add test class `TestGetRebaseTargetBranch` to `tests/workflows/implement/test_core.py`

Please implement this task step by step.

## LLM Response:
## Summary

I've completed the first sub-task of Step 2:

**Task completed:** Add test class `TestGetRebaseTargetBranch` to `tests/workflows/implement/test_core.py`

**Changes made:**
1. Added import for `_get_rebase_target_branch` to the test file imports (line 10)
2. Added new test class `TestGetRebaseTargetBranch` with 5 test methods:
   - `test_returns_pr_base_branch` - Tests that the function returns base_branch from an open PR
   - `test_returns_base_branch_file_content` - Tests that it reads from BASE_BRANCH file
   - `test_returns_default_branch_as_fallback` - Tests fallback to default branch (main/master)
   - `test_returns_none_when_no_current_branch` - Tests None return in detached HEAD state
   - `test_pr_takes_priority_over_file` - Tests PR base branch has priority over BASE_BRANCH file

**Note:** The tests are written following TDD (Test-Driven Development). They will fail on import because `_get_rebase_target_branch` doesn't exist yet in `core.py`. This is expected - the function implementation is the next sub-task in the step.

---
Generated on: 2026-01-15T22:11:28.163050