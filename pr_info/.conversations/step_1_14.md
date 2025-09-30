# Implementation Task: Create _handle_github_errors decorator in BaseGitHubManager

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

Current task from TASK_TRACKER.md: Create _handle_github_errors decorator in BaseGitHubManager

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message:

## Summary

I have successfully completed **Step 11: Create Error Handling Decorator**. Here's what was implemented:

### Changes Made:

1. **Created `_handle_github_errors` decorator** in `src/mcp_coder/utils/github_operations/base_manager.py`:
   - Added necessary imports (`functools`, `Any`, `Callable`, `TypeVar`, `cast`)
   - Implemented decorator that handles GitHub API errors consistently:
     - Re-raises authentication/permission errors (401, 403)
     - Returns default value for other GithubException errors
     - Returns default value for generic exceptions
     - Logs all errors appropriately

2. **Created comprehensive unit tests** in `tests/utils/github_operations/test_base_manager.py`:
   - 15 test cases covering:
     - Success path (returns function value)
     - Auth errors (401, 403 are re-raised)
     - Non-auth GitHub errors (return default)
     - Generic exceptions (return default)
     - Different default return types (dict, list, bool, None)
     - Function argument preservation
     - Function metadata preservation (functools.wraps)
     - Logging behavior
     - Works with instance methods
     - Comprehensive exception propagation testing

3. **All quality checks passed**:
   - ✅ Pytest: 15/15 tests passed
   - ✅ Pylint: No issues found
   - ✅ Mypy: No type errors

### Commit Message:

```
feat(github): add error handling decorator to BaseGitHubManager

Implement _handle_github_errors decorator for consistent error handling across GitHub operations:
- Re-raises authentication/permission errors (401, 403) to caller
- Returns configurable default value for other errors
- Logs all errors with function context
- Fully type-safe with TypeVar support

Add comprehensive unit tests (15 test cases) covering:
- Auth error propagation (401, 403)
- Non-auth error handling with default returns
- Generic exception handling
- Multiple return types (dict, list, bool, None)
- Function metadata preservation
- Logging verification
```

All CLAUDE.md requirements followed.

---
Generated on: 2025-09-30T18:54:13.811489