# Implementation Task: Update `core.py` load_repo_config() - 4 calls → 1 batch

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

Current task from TASK_TRACKER.md: Update `core.py` load_repo_config() - 4 calls → 1 batch

Please implement this task step by step.

## LLM Response:
I've completed the sub-task:

## Summary

**Completed:** `Update core.py load_repo_config() - 4 calls → 1 batch`

### Changes Made

Refactored `load_repo_config()` in `src/mcp_coder/cli/commands/coordinator/core.py:52-92` to use batch config fetching:

**Before:** 4 individual `get_config_value()` calls:
```python
repo_url = coordinator.get_config_value(section, "repo_url")
executor_job_path = coordinator.get_config_value(section, "executor_job_path")
github_credentials_id = coordinator.get_config_value(section, "github_credentials_id")
executor_os = coordinator.get_config_value(section, "executor_os")
```

**After:** 1 batch `get_config_values()` call:
```python
config = coordinator.get_config_values([
    (section, "repo_url", None),
    (section, "executor_job_path", None),
    (section, "github_credentials_id", None),
    (section, "executor_os", None),
])

repo_url = config[(section, "repo_url")]
executor_job_path = config[(section, "executor_job_path")]
github_credentials_id = config[(section, "github_credentials_id")]
executor_os = config[(section, "executor_os")]
```

This reduces 4 potential disk reads to 1, improving performance.

---
Generated on: 2026-01-15T15:23:02.433464