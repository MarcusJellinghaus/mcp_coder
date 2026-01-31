# Implementation Task: Update `check_prerequisites()` to fail if pr_info/ missing

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

Current task from TASK_TRACKER.md: Update `check_prerequisites()` to fail if pr_info/ missing

Please implement this task step by step.

## LLM Response:
**Step 2 is now complete.** Here's a summary of what was implemented:

## Summary

### Task: Update `check_prerequisites()` to fail if pr_info/ missing

**Changes made to `src/mcp_coder/workflows/implement/prerequisites.py`:**

1. **Added imports** for `TaskTrackerSectionNotFoundError` and `validate_task_tracker` from the task_tracker module

2. **Updated `check_prerequisites()` function** to:
   - Check if `pr_info/` directory exists before checking for TASK_TRACKER.md
   - Log the error message "folder pr_info not found. Run 'create_plan' first." when the directory is missing
   - Validate the existing task tracker structure using `validate_task_tracker()`
   - Log "Task tracker structure validated" on success
   - Log "Invalid task tracker structure: {error}" on validation failure

3. **Updated docstring** to document the new validation behavior

**All sub-tasks in Step 2 are now marked complete:**
- [x] Write tests for failing when pr_info/ folder missing
- [x] Write tests for validation of existing tracker
- [x] Update `check_prerequisites()` to fail if pr_info/ missing
- [x] Update `check_prerequisites()` to validate existing tracker
- [x] Run quality checks and fix any issues

**Quality checks passed:**
- mypy: No type errors
- pylint: No new errors/warnings (one pre-existing warning in unrelated file)

**Commit message written to:** `pr_info/.commit_message.txt`

---
Generated on: 2026-01-31T14:10:08.385122