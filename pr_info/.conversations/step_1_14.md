# Implementation Task: Add list_issues() method to src/mcp_coder/utils/github_operations/issue_manager.py

## Prompt Sent to LLM:
You are implementing tasks from a task tracker. Follow these steps in order:

**STEP 1: SELECT TASK**
- Read `pr_info/TASK_TRACKER.md`
- Find the FIRST unchecked task (format: `- [ ] Task description`)
- Announce which task you're working on

**STEP 2: IMPLEMENT**
- Read the linked step file in `pr_info/steps/` for detailed requirements
- Implement ONLY what's described - no extra complexity
- If you encounter issues or need decisions, ask immediately

**STEP 3: VERIFY WITH CODE QUALITY CHECKS**
- Run MCP code checker tools (pylint, pytest, mypy)
- See `tests/readme.md` for test execution guidelines (avoid slow integration tests when possible)
- Fix ALL issues found by the checkers
- Repeat checks until everything passes

**STEP 4: VERIFY TASK COMPLETION**
- Re-read the task requirements in `pr_info/TASK_TRACKER.md`
- Confirm ALL requirements are met
- Verify all code quality checks pass

**STEP 5: PREPARE COMMIT MESSAGE** ⚠️ REQUIRED
- Generate a short, concise commit message with step name in the title
- DO NOT actually perform the commit - only prepare the message
- Edit `pr_info/TASK_TRACKER.md` and mark the commit message preparation task as complete
- Change its checkbox from `- [ ] Prepare git commit message` to `- [x] Prepare git commit message`

**STEP 6: MARK MAIN TASK COMPLETE** ⚠️ CRITICAL - DO NOT SKIP THIS STEP
- Edit `pr_info/TASK_TRACKER.md` using the appropriate file editing tool
- Change the main implementation task checkbox from `- [ ]` to `- [x]`
- Example: `- [ ] Implement core.py` becomes `- [x] Implement core.py`
- Verify the file was actually updated
- ⚠️ WARNING: If you skip this step, the workflow will loop infinitely on the same task

**CRITICAL RULES:**
- Work on EXACTLY ONE task per run - do not pick additional tasks
- You MUST complete Step 5 (mark task as `[x]`) before finishing
- The checkbox update is non-negotiable and required for workflow progression

Current task from TASK_TRACKER.md: Add list_issues() method to src/mcp_coder/utils/github_operations/issue_manager.py

Please implement this task step by step.

## LLM Response:
Perfect! Now let me prepare the commit message and mark that task complete:

## Summary

I have successfully completed **Step 2: IssueManager.list_issues() Method**. Here's what was accomplished:

### Implementation Details

1. **Added `list_issues()` method** to `src/mcp_coder/utils/github_operations/issue_manager.py:311-368`
   - Supports state filtering (`open`, `closed`, `all`) with default `open`
   - Filters pull requests by default, with option to include them via `include_pull_requests` parameter
   - Automatic pagination support via PyGithub's PaginatedList
   - Returns `List[IssueData]` with full issue information
   - Proper error handling via `@_handle_github_errors` decorator
   - Logging support via `@log_function_call` decorator

2. **Added comprehensive unit tests** to `tests/utils/github_operations/test_issue_manager.py`
   - `test_list_issues_default_parameters` - Verifies default behavior (open issues, no PRs)
   - `test_list_issues_open_only` - Tests state filtering
   - `test_list_issues_include_pull_requests` - Tests PR inclusion flag
   - `test_list_issues_pagination_handled` - Tests handling of 35+ issues
   - `test_list_issues_empty_repository` - Tests empty results
   - `test_list_issues_github_error_handling` - Tests error handling

3. **All code quality checks passed:**
   - ✅ Pylint: No issues found
   - ✅ Pytest: 960 tests passed, 7 skipped (fast unit tests only)
   - ✅ Mypy: No type errors found

### Commit Message (Prepared)

```
feat(issue_manager): add list_issues() method with pagination support

Implement list_issues() method in IssueManager class to retrieve all issues
from a repository with GitHub API pagination support.

Features:
- State filtering (open/closed/all, default: open)
- Pull request filtering (excluded by default)
- Automatic pagination via PyGithub
- Full issue metadata in IssueData format
- Consistent error handling and logging

Tests:
- 6 comprehensive unit tests with mocked GitHub API
- Test coverage for pagination, PR filtering, and error handling
- All tests pass with fast unit test exclusions

Related to issue #109 - Step 2
```

All CLAUDE.md requirements have been followed - MCP tools were used exclusively, all code quality checks passed, and the task has been marked complete in TASK_TRACKER.md.

---
Generated on: 2025-10-13T08:17:05.176752