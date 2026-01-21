# Implementation Task: Implement `_build_set_status_epilog()` helper function

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

Current task from TASK_TRACKER.md: Implement `_build_set_status_epilog()` helper function

Please implement this task step by step.

## LLM Response:
I have successfully completed the sub-task. Here's what was implemented:

## Summary

**Task completed:** Implement `_build_set_status_epilog()` helper function

**Changes made to `src/mcp_coder/cli/main.py`:**

1. **Added imports** for `get_labels_config_path` and `load_labels_config` from `..utils.github_operations.label_config`

2. **Implemented `_build_set_status_epilog()` function** that:
   - Loads labels from the package bundled config using `get_labels_config_path(None)`
   - Builds a formatted epilog showing all available status labels with descriptions
   - Includes usage examples (`mcp-coder set-status status-05:plan-ready` and `mcp-coder set-status status-08:ready-pr --issue 123`)
   - Falls back gracefully with a helpful message if config loading fails
   - Logs failures at debug level (per Decision #9 from the spec)

**Code checks passed:**
- Pylint: No new issues (only pre-existing warnings in other files)
- Mypy: No type errors

The sub-task has been marked as complete in `pr_info/TASK_TRACKER.md`.

---
Generated on: 2026-01-21T10:55:17.434326