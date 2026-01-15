# Implementation Task: Update `base_manager.py` - 1 call site

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

Current task from TASK_TRACKER.md: Update `base_manager.py` - 1 call site

Please implement this task step by step.

## LLM Response:
## Summary

I completed the first sub-task of **Step 4: Refactor All Callers to Use Batch Config Function**:

### Task: Update `base_manager.py` - 1 call site

**Changes made to `src/mcp_coder/utils/github_operations/base_manager.py`:**

**Before (line 135):**
```python
github_token = user_config.get_config_value("github", "token")
```

**After (lines 135-138):**
```python
config: dict[tuple[str, str], Optional[str]] = user_config.get_config_values(
    [("github", "token", None)]
)
github_token = config[("github", "token")]
```

**Key points:**
- Changed from `get_config_value()` to `get_config_values()` batch API
- Added proper type annotation to satisfy mypy
- The import `from mcp_coder.utils import user_config` was already present (module-level import), so no import change needed
- The behavior remains identical - retrieves the GitHub token from config

The sub-task has been marked complete (`[x]`) in `pr_info/TASK_TRACKER.md`. The remaining sub-tasks in Step 4 are ready for the next run.

---
Generated on: 2026-01-15T15:19:55.636841