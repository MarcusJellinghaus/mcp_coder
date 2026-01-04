# Implementation Task: Analyze existing coordinator.py public interface

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

Current task from TASK_TRACKER.md: Analyze existing coordinator.py public interface

Please implement this task step by step.

## LLM Response:
Based on my analysis of `src/mcp_coder/cli/commands/coordinator.py`, I've identified the complete public interface. The file contains the following publicly accessible functions and classes:

## Public Interface Analysis

### **Entry Points (CLI Commands)**
- `execute_coordinator_test(args)` - CLI entry point for test command
- `execute_coordinator_run(args)` - CLI entry point for run command

### **Core Business Logic Functions**
- `dispatch_workflow()` - Triggers Jenkins jobs and updates issue labels
- `get_cached_eligible_issues()` - Main function for getting eligible issues with caching
- `get_eligible_issues()` - Direct API function for getting eligible issues
- `load_repo_config()` - Loads repository configuration from config file
- `validate_repo_config()` - Validates repository configuration
- `get_jenkins_credentials()` - Gets Jenkins credentials from env/config
- `get_cache_refresh_minutes()` - Gets cache refresh threshold from config

### **Utility Functions**
- `format_job_output()` - Formats Jenkins job trigger output

### **Type Definitions**
- `CacheData` - TypedDict for cache structure

### **Constants/Templates**
- Various command templates (`DEFAULT_TEST_COMMAND`, `CREATE_PLAN_COMMAND_TEMPLATE`, etc.)
- `WORKFLOW_MAPPING` - Workflow configuration
- `PRIORITY_ORDER` - Issue priority order

The task of analyzing the existing coordinator.py public interface is now complete. This analysis will be used in the next sub-task to create the `__init__.py` file with complete public API re-exports.

---
Generated on: 2026-01-04T14:20:40.273937