# Implementation Task: Create GitHubTestSetup TypedDict and shared github_test_setup fixture

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

Current task from TASK_TRACKER.md: Create GitHubTestSetup TypedDict and shared github_test_setup fixture

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message as requested:

## Task Complete ✅

I have successfully implemented **Step 8: Create Shared GitHub Test Fixture**. Here's what was done:

### Implementation Summary:

1. **Created `GitHubTestSetup` TypedDict** in `tests/conftest.py:166`
   - Defines the structure for GitHub test configuration
   - Contains `github_token`, `test_repo_url`, and `project_dir` fields

2. **Created `github_test_setup` fixture** in `tests/conftest.py:177`
   - Shared fixture that handles GitHub configuration validation
   - Clones test repository once per test
   - Supports environment variables and config file fallback

3. **Created `create_github_manager` helper function** in `tests/conftest.py:249`
   - Generic helper for instantiating any GitHub manager class
   - Eliminates duplicated token mocking logic
   - Uses proper type hints with TypeVar for type safety

4. **Updated test fixtures** in `tests/utils/test_github_operations.py:35,59`
   - Refactored `labels_manager` fixture to use shared setup (reduced from ~70 lines to ~10 lines)
   - Refactored `pr_manager` fixture to use shared setup (reduced from ~105 lines to ~10 lines)
   - Removed ~165 lines of duplicated code

### Quality Checks:
- ✅ **Pylint**: No errors or fatal issues
- ✅ **Pytest**: All 532 unit tests passing
- ✅ **Mypy**: No type errors (strict mode)

### Commit Message:

```
test(fixtures): create shared GitHub test fixture and helper

- Add GitHubTestSetup TypedDict for test configuration structure
- Add github_test_setup fixture with shared repo cloning logic
- Add create_github_manager generic helper function
- Refactor labels_manager and pr_manager fixtures to use shared setup
- Remove ~165 lines of duplicated configuration code
```

All CLAUDE.md requirements followed.

---
Generated on: 2025-09-29T20:46:41.758367