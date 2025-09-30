# Implementation Task: Implement remove_labels and set_labels methods

## Prompt Sent to LLM:
Please look at `pr_info/TASK_TRACKER.md` and pick the next task that should be done.
Please let me know on which task you are working on.
Please implement!
Please verify your implementation running the various checks of the MCP server and by solving potential issues (and repeat).
Please do not invent extra complexity not mentioned in the project plan.
Please let me know in case you encounter any issues or need a decision.
Please provide a short concise commit message stating the step name in the title. Do NOT perform a commit!

Once you are done, please check again that task description on `pr_info/TASK_TRACKER.md` to ensure that everything is done.
Once everything is done, please mark the task as done.
Please work only on one task. Do not pick further tasks.

Please also take a look at the tests\readme.md and only run those tests that are required in your context -i.e. avoid slow integration tests.

Current task from TASK_TRACKER.md: Implement remove_labels and set_labels methods

Please implement this task step by step.

## LLM Response:
## Task Complete ✅

I've successfully implemented **Step 6: Remove & Set Labels Operations**. Here's what was done:

### Implementation Summary

**1. Added `remove_labels` method** (src/mcp_coder/utils/github_operations/issue_manager.py:650-781)
- Removes specified labels from an issue
- Validates issue number and ensures labels are provided
- Returns updated IssueData with fresh label information
- Proper error handling for auth/permission errors

**2. Added `set_labels` method** (src/mcp_coder/utils/github_operations/issue_manager.py:783-903)
- Sets labels on an issue, replacing all existing labels
- Allows empty argument list to clear all labels
- Validates issue number
- Returns updated IssueData with fresh label information
- Proper error handling for auth/permission errors

**3. Added comprehensive unit tests** (tests/utils/test_issue_manager.py)
- 5 tests for `remove_labels`: success, single label, invalid issue number, no labels provided, auth error
- 5 tests for `set_labels`: success, empty to clear all, single label, invalid issue number, auth error

**4. Enhanced integration test** (tests/utils/test_issue_manager_integration.py:114-168)
- Added label operations workflow: add labels → remove labels → set labels
- Verifies proper label manipulation throughout the lifecycle

**5. All quality checks passed**
- ✅ Pytest: 32 tests passed
- ✅ Pylint: No issues found
- ✅ Mypy: No type errors

### Commit Message

```
feat(issue-manager): implement remove_labels and set_labels methods
```

**All CLAUDE.md requirements followed**

---
Generated on: 2025-09-30T07:43:59.077509