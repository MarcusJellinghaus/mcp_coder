# Implementation Task: Create CLI command module at `src/mcp_coder/cli/commands/define_labels.py`

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

Current task from TASK_TRACKER.md: Create CLI command module at `src/mcp_coder/cli/commands/define_labels.py`

Please implement this task step by step.

## LLM Response:
## Step 1 Complete

I have completed **Step 1: Create CLI Command Module and Refactor Error Handling**. Here's what was done:

### Summary of Changes

1. **Created** `src/mcp_coder/cli/commands/define_labels.py` with:
   - `_log_dry_run_changes()` - Helper function for dry-run logging
   - `calculate_label_changes()` - Pure function to compare existing vs target labels
   - `apply_labels()` - Orchestrator that raises `RuntimeError` on API errors (instead of `sys.exit`)
   - `execute_define_labels()` - CLI entry point with proper exception handling (returns exit codes)

2. **Code quality verified:**
   - Pylint: No errors or fatal issues
   - Mypy: No type errors (strict mode)
   - Pytest: Tests for this module will be created in Step 3

### Prepared Git Commit Message

```
feat(cli): add define-labels command module

Create CLI command module for label synchronization workflow.
Refactored from workflow script to integrate with mcp-coder CLI.

Changes:
- Add src/mcp_coder/cli/commands/define_labels.py with:
  - calculate_label_changes(): pure function for label comparison
  - apply_labels(): raises RuntimeError instead of sys.exit(1)
  - execute_define_labels(): CLI entry point with exception handling
- Import resolve_project_dir from workflows.utils (not copied)
- Use exception-based error handling pattern

Part of CLI integration for define-labels command.
```

### Files Modified/Created
- **Created**: `src/mcp_coder/cli/commands/define_labels.py`
- **Updated**: `pr_info/TASK_TRACKER.md` (marked sub-tasks complete)

**Note**: The remaining sub-tasks from Step 1 (refactoring `resolve_project_dir` and updating `validate_labels.py`) were already completed in previous runs as indicated by the task tracker.

---
Generated on: 2026-01-08T21:59:03.285467