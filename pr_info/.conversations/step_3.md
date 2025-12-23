# Implementation Task: Implement Step 3: Extract shared utility function (step_3.md)

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

Current task from TASK_TRACKER.md: Implement Step 3: Extract shared utility function (step_3.md)

Please implement this task step by step.

## LLM Response:
## Step 3 Complete! 

I have successfully implemented Step 3 from the task tracker: **Extract `extract_issue_number_from_branch()` Utility Function**.

### Summary of what was accomplished:

1. ✅ **Added comprehensive tests** for the new function in `tests/utils/git_operations/test_branches.py`
2. ✅ **Implemented `extract_issue_number_from_branch()`** function in `src/mcp_coder/utils/git_operations/branches.py` 
3. ✅ **Exported the function** in `src/mcp_coder/utils/git_operations/__init__.py`
4. ✅ **Refactored `issue_manager.py`** to use the shared function and removed unused `re` import
5. ✅ **Refactored `core.py`** to use the shared function and removed unused `re` import 
6. ✅ **Fixed all mypy type issues** by properly handling Optional return types
7. ✅ **Passed all code quality checks** (pylint and mypy)
8. ✅ **Updated TASK_TRACKER.md** to mark Step 3 as complete

### Key Changes Made:

- **New shared function**: `extract_issue_number_from_branch(branch_name: str) -> Optional[int]` that extracts issue numbers from branch names following the `{issue_number}-title` pattern
- **Eliminated code duplication**: Both `issue_manager.py` and `core.py` now use the shared function instead of duplicating regex logic
- **Improved maintainability**: Any future changes to branch name parsing logic only need to be made in one place
- **Type safety**: All type issues resolved with proper handling of Optional return values

The implementation follows TDD principles (tests first, then implementation) and maintains backward compatibility while reducing code duplication across the codebase.

---
Generated on: 2025-12-23T21:39:37.102582