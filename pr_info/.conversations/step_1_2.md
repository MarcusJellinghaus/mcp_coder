# Implementation Task: Add CI check constants to `src/mcp_coder/workflows/implement/constants.py`

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

Current task from TASK_TRACKER.md: Add CI check constants to `src/mcp_coder/workflows/implement/constants.py`

Please implement this task step by step.

## LLM Response:
I have completed **Step 1: Add Constants, Prompts, and .gitignore Entry**. Here's a summary of what was accomplished:

## Step 1 Completed ✓

### Sub-tasks completed:
1. ✅ **Added CI check constants** to `src/mcp_coder/workflows/implement/constants.py`:
   - `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300` (5 minutes)
   - `CI_POLL_INTERVAL_SECONDS = 15`
   - `CI_MAX_POLL_ATTEMPTS = 50`
   - `CI_MAX_FIX_ATTEMPTS = 3`
   - `CI_NEW_RUN_POLL_INTERVAL_SECONDS = 5`
   - `CI_NEW_RUN_MAX_POLL_ATTEMPTS = 6`

2. ✅ **Added CI prompts** to `src/mcp_coder/prompts/prompts.md`:
   - CI Failure Analysis Prompt (with placeholders: `[job_name]`, `[step_name]`, `[other_failed_jobs]`, `[log_excerpt]`)
   - CI Fix Prompt (with placeholder: `[problem_description]`)

3. ✅ **Updated `.gitignore`** with `pr_info/.ci_problem_description.md`

4. ✅ **Added `get_prompt_with_substitutions()`** helper function to `src/mcp_coder/prompt_manager.py`

5. ✅ **Added tests** for `get_prompt_with_substitutions()` in `tests/test_prompt_manager.py`

6. ✅ **Code quality checks passed**:
   - Pylint: No new issues
   - Mypy: No type errors

7. ✅ **Commit message prepared** in `pr_info/.commit_message.txt`

---
Generated on: 2026-01-20T08:47:59.378964