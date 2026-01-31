# Implementation Task: Step 3: Update Formatting and Refactor implement/core.py

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

Current task from TASK_TRACKER.md: Step 3: Update Formatting and Refactor implement/core.py

Please implement this task step by step.

## LLM Response:
I have completed Step 3. Here's a summary of what was implemented:

## Step 3 Completed: Update Formatting and Refactor implement/core.py

### Changes Made:

1. **Updated `format_for_human()` method** (`src/mcp_coder/workflow_utils/branch_status.py`):
   - Added branch info as the first lines of the output: `Branch: {branch_name}` and `Base Branch: {base_branch}`
   - The "Branch Status Report" title now comes after the branch info

2. **Updated `format_for_llm()` method** (`src/mcp_coder/workflow_utils/branch_status.py`):
   - Added branch info as the first line: `Branch: {branch_name} | Base: {base_branch}`

3. **Refactored `_get_rebase_target_branch()`** (`src/mcp_coder/workflows/implement/core.py`):
   - Replaced the 40-line implementation with a 2-line version using the shared `detect_base_branch()` function
   - Added import for `detect_base_branch` from `workflow_utils.base_branch`
   - Removed unused `get_default_branch_name` import
   - Removed unused `PullRequestManager` import (replaced with the new function)

4. **Updated format tests** (`tests/workflow_utils/test_branch_status.py`):
   - Added assertions for `test_format_for_human_passed_status()` to verify branch info appears first
   - Added assertions for `test_format_for_llm_basic()` to verify branch info is the first line

### Files Modified:
- `src/mcp_coder/workflow_utils/branch_status.py`
- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflow_utils/test_branch_status.py`
- `pr_info/TASK_TRACKER.md`

### Commit message written to:
- `pr_info/.commit_message.txt`

---
Generated on: 2026-02-01T00:32:34.340733