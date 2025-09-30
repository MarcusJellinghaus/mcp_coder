# Implementation Task: Apply decorator to all 10 IssueManager methods

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

Current task from TASK_TRACKER.md: Apply decorator to all 10 IssueManager methods

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message as requested:

## Summary

**Task completed:** Step 12 - Apply Decorator to IssueManager Methods

**What was done:**
1. ✅ Applied `@_handle_github_errors` decorator to all 11 IssueManager methods (create_issue, add_comment, get_comments, edit_comment, delete_comment, close_issue, reopen_issue, get_available_labels, add_labels, remove_labels, set_labels)
2. ✅ Removed bare `Exception` catch blocks from all methods
3. ✅ Imported `_handle_github_errors` from base_manager
4. ✅ All quality checks passed:
   - Pylint: ✅ No issues
   - Mypy: ✅ No type errors
   - Pytest: ✅ 595 tests passed

**Changes made:**
- Modified: `src/mcp_coder/utils/github_operations/issue_manager.py`
- Added decorator to 11 methods with appropriate default return values
- Removed 11 bare Exception blocks
- Added import for `_handle_github_errors`

**Commit message:**

```
refactor(github): apply error handling decorator to IssueManager methods

Apply @_handle_github_errors decorator to all IssueManager methods and
remove bare Exception catch blocks. The decorator provides consistent
error handling across all methods while maintaining the same behavior
for authentication errors (re-raise) and other errors (log and return
default value).
```

All CLAUDE.md requirements followed. Task marked as complete in TASK_TRACKER.md.

---
Generated on: 2025-09-30T19:03:35.195090