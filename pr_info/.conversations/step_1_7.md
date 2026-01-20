# Implementation Task: Fix `commit_sha` field lookup in `_poll_for_ci_completion()`

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

Current task from TASK_TRACKER.md: Fix `commit_sha` field lookup in `_poll_for_ci_completion()`

Please implement this task step by step.

## LLM Response:
I've completed the first sub-task of Step 5: **Fix `commit_sha` field lookup in `_poll_for_ci_completion()`**

**Summary of change:**
- In `src/mcp_coder/workflows/implement/core.py`, line 222
- Changed `run_info.get("head_sha", "unknown")` to `run_info.get("commit_sha", "unknown")`
- This fixes a bug where the wrong field name was being used to retrieve the commit SHA from the CI run info

The sub-task has been marked as complete (`[x]`) in the task tracker. This was a simple field name correction - the `CIStatusData` TypedDict uses `commit_sha` as the field name, not `head_sha`.

---
Generated on: 2026-01-20T09:53:52.456724