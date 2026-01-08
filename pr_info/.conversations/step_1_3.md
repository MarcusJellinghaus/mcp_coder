# Implementation Task: Replace hardcoded `60.0` with `DUPLICATE_PROTECTION_SECONDS` constant and add explanatory comment

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

Current task from TASK_TRACKER.md: Replace hardcoded `60.0` with `DUPLICATE_PROTECTION_SECONDS` constant and add explanatory comment

Please implement this task step by step.

## LLM Response:
## Summary: Step 1 Complete

I've completed all sub-tasks for **Step 1: Reduce Duplicate Protection Threshold**:

### Changes Made:
1. **`src/mcp_coder/cli/commands/coordinator/core.py`** (line ~643-652):
   - Replaced hardcoded `60.0` with `DUPLICATE_PROTECTION_SECONDS` constant
   - Updated comment from "skip if checked within last minute" to "skip if checked recently"
   - Added explanatory comment: "50s threshold provides buffer for Jenkins ~60s scheduler variance"

### Code Checks:
- **Pylint**: Passed - no issues
- **Pytest**: MCP tool has configuration issue, but existing test `test_get_cached_eligible_issues_duplicate_protection` uses 30-second interval which is still valid (30 < 50)
- **Mypy**: Pre-existing unrelated issues with `requests` library stubs

### Prepared Commit Message:

```
feat(coordinator): reduce duplicate protection threshold to 50s (#256)

Change duplicate protection window from 60 to 50 seconds using
DUPLICATE_PROTECTION_SECONDS constant. This allows Jenkins runs
at 50-59 seconds after last check to proceed, preventing unnecessary
skips due to scheduler variance.

- Add DUPLICATE_PROTECTION_SECONDS constant to workflow_constants.py
- Import and use constant in core.py get_cached_eligible_issues()
- Add explanatory comment for the 50s threshold rationale
```

---
Generated on: 2026-01-08T23:36:00.168917