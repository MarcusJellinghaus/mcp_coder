# Implementation Task: Add private function `_get_rebase_target_branch()` to `src/mcp_coder/workflows/implement/core.py`

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

Current task from TASK_TRACKER.md: Add private function `_get_rebase_target_branch()` to `src/mcp_coder/workflows/implement/core.py`

Please implement this task step by step.

## LLM Response:
I have completed the sub-task. Here's a summary:

## Completed: Add private function `_get_rebase_target_branch()` to core.py

### Changes made:

**File: `src/mcp_coder/workflows/implement/core.py`**

1. **Added new imports** (lines 16-21):
   - `get_current_branch_name` from git_operations
   - `get_default_branch_name` from git_operations
   - `rebase_onto_branch` from git_operations
   - `PullRequestManager` from github_operations

2. **Added new function `_get_rebase_target_branch()`** (lines 46-90):
   - Determines the target branch for rebasing the current feature branch
   - Uses priority-based detection:
     1. GitHub PR base branch (if open PR exists for current branch)
     2. `pr_info/BASE_BRANCH` file content (if file exists)
     3. Default branch (main/master) via `get_default_branch_name()`
   - All errors handled gracefully - returns `None` on any failure
   - Debug logging indicates which detection method was used

### Quality checks:
- **Pylint**: No issues found
- **Mypy**: No type errors found

The function matches the specification in `pr_info/steps/step_2.md` and the tests in `tests/workflows/implement/test_core.py::TestGetRebaseTargetBranch`.

---
Generated on: 2026-01-15T22:20:07.434275