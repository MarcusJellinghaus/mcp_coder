# Implementation Task: Step 2: Update BranchStatusReport and collect_branch_status

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

Current task from TASK_TRACKER.md: Step 2: Update BranchStatusReport and collect_branch_status

Please implement this task step by step.

## LLM Response:
**Step 2 is now complete.** Here's a summary of what was implemented:

## Summary of Changes

### Modified Files

1. **`src/mcp_coder/workflow_utils/branch_status.py`**
   - Added `branch_name` and `base_branch` fields to `BranchStatusReport` dataclass
   - Added import for `detect_base_branch` from `base_branch` module
   - Added import for `IssueData` type
   - Updated `create_empty_report()` to include new fields with "unknown" defaults
   - Simplified `_collect_github_label()` to accept `issue_data` parameter directly instead of fetching it
   - Updated `collect_branch_status()` to:
     - Fetch issue data once at the beginning
     - Share issue data between `detect_base_branch()` and `_collect_github_label()`
     - Include `branch_name` and `base_branch` in the returned report

2. **`tests/workflow_utils/test_branch_status.py`**
   - Updated all existing test cases to include `branch_name` and `base_branch` fields
   - Updated `_collect_github_label` tests to use proper `IssueData` TypedDict
   - Added new tests:
     - `test_collect_branch_status_includes_branch_info()`
     - `test_collect_branch_status_shares_issue_data()`

### Verification
- Mypy type checking: **PASSED** (no errors)
- Pylint: **PASSED** (no issues)

### Commit Message
Written to `pr_info/.commit_message.txt` for use in the commit.

---
Generated on: 2026-02-01T00:29:29.556820