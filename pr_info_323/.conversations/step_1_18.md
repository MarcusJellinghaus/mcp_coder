# Implementation Task: Refactor get_issue_current_status() to accept cached_issues parameter

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

Current task from TASK_TRACKER.md: Refactor get_issue_current_status() to accept cached_issues parameter

Please implement this task step by step.

## LLM Response:
**Step 13 is now complete!** Here's a summary of what was accomplished:

## Step 13: Pass Cached Issues to Staleness Checks - COMPLETED

### Changes Made:

1. **`src/mcp_coder/utils/vscodeclaude/status.py`**:
   - Refactored `get_issue_current_status()` to accept `cached_issues` parameter (line 22-61)
   - Refactored `is_issue_closed()` to accept `cached_issues` parameter (line 64-99)
   - Refactored `is_session_stale()` to accept `cached_issues` parameter (line 102-155)
   - Updated `display_status_table()` to accept `cached_issues_by_repo` parameter (line 235-368)

2. **`src/mcp_coder/utils/vscodeclaude/orchestrator.py`**:
   - Refactored `restart_closed_sessions()` to accept `cached_issues_by_repo` parameter (line 615-740)

3. **`src/mcp_coder/cli/commands/coordinator/commands.py`**:
   - Added `_get_repo_full_name_from_url()` helper function (line 350-368)
   - Added `_build_cached_issues_by_repo()` helper function (line 371-420)
   - Updated `execute_coordinator_vscodeclaude()` to build cache once and pass to `restart_closed_sessions()` (line 459-475)

4. **`tests/utils/vscodeclaude/test_status.py`**:
   - Updated existing tests to use new function signatures
   - Added new `TestCacheAwareFunctions` class with 7 new tests:
     - `test_get_issue_current_status_uses_cache`
     - `test_get_issue_current_status_cache_miss_uses_api`
     - `test_get_issue_current_status_raises_without_manager_or_cache`
     - `test_is_session_stale_uses_cache`
     - `test_is_session_stale_with_cache_detects_change`
     - `test_is_issue_closed_uses_cache`
     - `test_is_issue_closed_with_cache_open_issue`

### Performance Improvement:
- **Before**: Multiple `get_issue()` API calls per session (~1s each)
- **After**: Single cache lookup per session (<1ms), with API fallback only when issue not found in cache

### Commit message written to:
`pr_info/.commit_message.txt`

---
Generated on: 2026-01-30T08:51:35.946500