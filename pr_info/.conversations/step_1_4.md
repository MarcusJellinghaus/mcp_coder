# Implementation Task: Implement create_issue, close_issue, reopen_issue methods

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

Current task from TASK_TRACKER.md: Implement create_issue, close_issue, reopen_issue methods

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message as requested:

## Summary

**Step 4: Issue Creation & Lifecycle Operations - Complete**

I successfully implemented the three issue lifecycle methods for the IssueManager class:

### Implementation Details:

**Methods added to `src/mcp_coder/utils/github_operations/issue_manager.py`:**
- `create_issue(title, body, labels)` - Creates new issues with optional labels
- `close_issue(issue_number)` - Closes an existing issue
- `reopen_issue(issue_number)` - Reopens a closed issue

**Features:**
- All methods use `@log_function_call` decorator for consistent logging
- Hybrid error handling: raises exceptions for auth/permission errors (401, 403), returns empty IssueData for other errors
- Input validation with detailed error messages
- Returns fresh IssueData after state changes
- Comprehensive docstrings with examples

**Tests created:**
- `tests/utils/test_issue_manager.py` - 14 unit tests with mocked GitHub API
- `tests/utils/test_issue_manager_integration.py` - Integration test for complete lifecycle

**Quality checks:**
- ✅ Pytest: All 547 unit tests passed
- ✅ Pylint: No errors or fatal issues
- ✅ Mypy: No type errors

### Commit Message:

```
feat: implement issue lifecycle operations (create, close, reopen)

Add create_issue, close_issue, and reopen_issue methods to IssueManager class.
Includes comprehensive unit tests and integration test for complete lifecycle.
```

All CLAUDE.md requirements followed.

---
Generated on: 2025-09-30T05:30:46.022540