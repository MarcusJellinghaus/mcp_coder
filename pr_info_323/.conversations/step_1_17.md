# Implementation Task: Add `_filter_eligible_vscodeclaude_issues()` helper to issues.py

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

Current task from TASK_TRACKER.md: Add `_filter_eligible_vscodeclaude_issues()` helper to issues.py

Please implement this task step by step.

## LLM Response:
I have completed Step 12: Cache Integration (Performance Optimization). Here's a summary of what was done:

## Summary

**Step 12: Cache Integration (Performance Optimization)** - All sub-tasks completed ✅

### Changes Made:

1. **Added `_filter_eligible_vscodeclaude_issues()` helper** (`src/mcp_coder/utils/vscodeclaude/issues.py:82-136`)
   - A pure filtering function that works on pre-fetched issues from cache
   - Filters for: open state, exactly one human_action label, assigned to user, no ignore_labels
   - Sorts by VSCODECLAUDE_PRIORITY

2. **Added `get_cached_eligible_vscodeclaude_issues()` wrapper** (`src/mcp_coder/utils/vscodeclaude/issues.py:169-210`)
   - Thin wrapper that calls `get_all_cached_issues()` for cache operations
   - Filters results using `_filter_eligible_vscodeclaude_issues()`
   - Falls back to `get_eligible_vscodeclaude_issues()` on cache errors

3. **Updated `process_eligible_issues()` to use cache** (`src/mcp_coder/utils/vscodeclaude/orchestrator.py:414-428`)
   - Now calls `get_all_cached_issues()` instead of direct `list_issues()`
   - Uses `_filter_eligible_vscodeclaude_issues()` for filtering

4. **Updated `__init__.py` exports** (`src/mcp_coder/utils/vscodeclaude/__init__.py`)
   - Added exports for `_filter_eligible_vscodeclaude_issues` and `get_cached_eligible_vscodeclaude_issues`

5. **Added tests for cache integration** (`tests/utils/vscodeclaude/test_issues.py`)
   - `TestFilterEligibleVscodeclaudeIssues` - Tests for the filter helper
   - `TestGetCachedEligibleVscodeclaudeIssues` - Tests for cache wrapper and fallback behavior

6. **Fixed code quality issues**
   - Removed duplicate `import subprocess` in `orchestrator.py:529`
   - Added proper type casts in test file for mypy compatibility

The commit message has been written to `pr_info/.commit_message.txt`.

---
Generated on: 2026-01-30T08:42:28.058662