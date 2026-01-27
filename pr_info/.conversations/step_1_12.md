# Implementation Task: Add launch and orchestration functions to vscodeclaude.py

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

Current task from TASK_TRACKER.md: Add launch and orchestration functions to vscodeclaude.py

Please implement this task step by step.

## LLM Response:
I have completed **Step 6: VSCode Launch & Session Orchestration**. Here's a summary of what was implemented:

## Summary

### Files Modified:
1. **`src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`** - Added launch and orchestration functions
2. **`tests/cli/commands/coordinator/test_vscodeclaude.py`** - Added TestLaunch and TestOrchestration test classes

### Functions Added:

**Launch Functions:**
- `launch_vscode()` - Non-blocking VSCode launch using subprocess.Popen
- `get_stage_display_name()` - Returns human-readable stage names (e.g., "CODE REVIEW")
- `truncate_title()` - Truncates titles with ellipsis if over max length

**Orchestration Functions:**
- `prepare_and_launch_session()` - Full session preparation including git setup, workspace creation, VSCode launch, and cleanup on failure
- `process_eligible_issues()` - Processes eligible issues for a repo with max session enforcement
- `restart_closed_sessions()` - Relaunches VSCode for sessions where it was closed
- `handle_pr_created_issues()` - Displays issue URLs for pr-created status issues

**Helper Functions:**
- `_get_repo_short_name()` - Extracts repo name from URL
- `_get_repo_full_name()` - Extracts owner/repo from URL
- `_get_issue_status()` - Gets status label from an issue
- `_build_session()` - Builds a VSCodeClaudeSession dictionary

### Tests Added:
- `TestLaunch` class with 7 tests covering launch functions
- `TestOrchestration` class with 9 tests covering session orchestration

### Quality Checks:
- ✅ Pylint: No errors
- ✅ Mypy: No type errors

The commit message has been written to `pr_info/.commit_message.txt`.

---
Generated on: 2026-01-27T10:43:33.100443