# Implementation Task: Add required imports to `core.py`

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

Current task from TASK_TRACKER.md: Add required imports to `core.py`

Please implement this task step by step.

## LLM Response:
I have completed the sub-task "Add required imports to `core.py`" in Step 3.

## Summary

**Task completed:** Add required imports to `core.py`

**Changes made to `src/mcp_coder/workflows/implement/core.py`:**

1. Added `import time` for sleep functionality needed by the CI polling logic

2. Added `from mcp_coder.utils.git_operations.commits import get_latest_commit_sha` for commit SHA retrieval (used for debug logging)

3. Added `from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager` for CI status management

4. Extended the `.constants` import to include all CI-related constants:
   - `CI_MAX_FIX_ATTEMPTS` (3 attempts)
   - `CI_MAX_POLL_ATTEMPTS` (50 attempts)
   - `CI_NEW_RUN_MAX_POLL_ATTEMPTS` (6 attempts)
   - `CI_NEW_RUN_POLL_INTERVAL_SECONDS` (5 seconds)
   - `CI_POLL_INTERVAL_SECONDS` (15 seconds)
   - `LLM_CI_ANALYSIS_TIMEOUT_SECONDS` (300 seconds)
   - `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` (3600 seconds - reused for CI fix)

**Code quality checks:**
- Pylint: No errors in the modified file (only unrelated warning in `task_processing.py`)
- Mypy: No type errors found

The next sub-task in Step 3 is "Implement `check_and_fix_ci()` main function".

---
Generated on: 2026-01-20T08:57:15.521240