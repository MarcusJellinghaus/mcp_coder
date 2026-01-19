# Implementation Task: Integrate finalisation call into `run_implement_workflow()` after final mypy check

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

Current task from TASK_TRACKER.md: Integrate finalisation call into `run_implement_workflow()` after final mypy check

Please implement this task step by step.

## LLM Response:
I've completed the sub-task:

**Task Completed: Integrate finalisation call into `run_implement_workflow()` after final mypy check**

**Changes Made:**
- Added Step 5.5 in `src/mcp_coder/workflows/implement/core.py:506-518` that calls `run_finalisation()` after the final mypy check
- The integration includes:
  - Conditional execution only when no error occurred (`if not error_occurred:`)
  - Passes all necessary parameters including `auto_push=update_labels` to enable pushing only in workflow mode
  - Logs a warning if finalisation encounters issues but continues anyway (non-blocking)

**Task Tracker Updated:**
- Marked `- [x] Integrate finalisation call into run_implement_workflow() after final mypy check`

The remaining sub-tasks in Step 2 are:
- [ ] Add unit tests to `tests/workflows/implement/test_core.py`
- [ ] Run pylint and fix all issues found
- [ ] Run pytest and fix all issues found
- [ ] Run mypy and fix all issues found
- [ ] Prepare git commit message for Step 2

---
Generated on: 2026-01-19T17:17:19.535812