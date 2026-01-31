# Implementation Task: Add `check_pr_info_not_exists()` function

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
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Add `check_pr_info_not_exists()` function

Please implement this task step by step.

## LLM Response:
I have completed the sub-task. Here's a summary of what was done:

## Task Completed: Add `check_pr_info_not_exists()` function

**Status:** The function was already implemented in `src/mcp_coder/workflows/create_plan.py` (lines 162-177).

**Implementation details:**
- Function signature: `def check_pr_info_not_exists(project_dir: Path) -> bool`
- Returns `True` if pr_info/ directory does not exist (good state)
- Returns `False` if pr_info/ directory exists (error state)
- Logs clear error message: `"pr_info/ directory already exists. Please clean up before creating a new plan."`

**Tests:** Already written and present in `tests/workflows/create_plan/test_prerequisites.py` in the `TestCheckPrInfoNotExists` class with 5 test cases:
- `test_returns_true_when_pr_info_not_exists`
- `test_returns_false_when_pr_info_exists`
- `test_returns_false_when_pr_info_exists_with_contents`
- `test_logs_error_when_pr_info_exists`
- `test_error_message_mentions_cleanup`

**Actions taken:**
1. ✅ Verified function implementation in source file
2. ✅ Verified tests exist and import the function
3. ✅ Updated `pr_info/TASK_TRACKER.md` to mark sub-task as complete
4. ✅ Wrote commit message to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-31T14:34:35.630176