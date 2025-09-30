# Implementation Task: Apply decorator to all 4 PullRequestManager methods

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

Current task from TASK_TRACKER.md: Apply decorator to all 4 PullRequestManager methods

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message as requested:

## Task Complete ✅

**Working on:** Step 13 - Apply Decorator to PullRequestManager Methods

**Implementation Summary:**
- Applied `@_handle_github_errors` decorator to all 4 PullRequestManager methods (create_pull_request, get_pull_request, list_pull_requests, close_pull_request)
- Removed debug logging lines (e.status, e.data) from create_pull_request
- Removed all bare `except Exception` blocks
- Kept single-line error logging in GithubException blocks

**Quality Checks:** ✅ All passed
- Pylint: No issues
- Mypy: No type errors  
- Pytest: 595 tests passed (unit tests verified behavior unchanged)

**Commit Message:**
```
refactor(pr): apply error decorator to PullRequestManager methods
```

All CLAUDE.md requirements followed.

---
Generated on: 2025-09-30T19:09:14.280828