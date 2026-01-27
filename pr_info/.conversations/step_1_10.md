# Implementation Task: Add configuration and issue filtering functions to vscodeclaude.py

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

Current task from TASK_TRACKER.md: Add configuration and issue filtering functions to vscodeclaude.py

Please implement this task step by step.

## LLM Response:
Step 4 is now complete. Here's a summary of what was implemented:

## Step 4: Issue Selection & Configuration - Complete

### Implementation Summary

**Files modified:**
1. `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` - Added configuration and issue filtering functions
2. `tests/cli/commands/coordinator/test_vscodeclaude.py` - Added comprehensive tests

**New Functions Added:**

Configuration Functions:
- `_load_labels_config()` - Internal helper to load labels from bundled config
- `load_vscodeclaude_config()` - Loads workspace_base and max_sessions from config.toml
- `load_repo_vscodeclaude_config()` - Loads repo-specific setup commands
- `get_github_username()` - Gets authenticated GitHub username via PyGithub
- `sanitize_folder_name()` - Sanitizes strings for safe folder names

Issue Filtering Functions:
- `_is_issue_eligible()` - Internal helper to check issue eligibility
- `get_human_action_labels()` - Extracts human_action labels from labels.json
- `get_eligible_vscodeclaude_issues()` - Filters issues by assignment, labels, and sorts by priority
- `get_linked_branch_for_issue()` - Gets linked branch for issue (errors if multiple)

**Tests Added:**
- `TestConfiguration` class with 6 tests covering config loading and validation
- `TestIssueSelection` class with 7 tests covering issue filtering and branch linking

**Verification:**
- Pylint: No errors or fatal issues
- Mypy: No type errors
- Commit message written to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-27T10:27:13.932545