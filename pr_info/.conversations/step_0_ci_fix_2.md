# CI Fix Attempt 2

I have completed the task. Here's a summary of what was done:

## Summary

**Problem:** The CI pipeline unit-tests job was failing because the vscodeclaude module items weren't properly exported from the coordinator package's public API.

**Solution:** Updated `src/mcp_coder/cli/commands/coordinator/__init__.py` to:

1. Added imports from the `.vscodeclaude` module for all key types and functions
2. Added these exports to the `__all__` list to make them part of the public API

**Changes made:**
- Added explicit imports for 20 vscodeclaude items including:
  - Type definitions: `VSCodeClaudeConfig`, `VSCodeClaudeSession`, `VSCodeClaudeSessionStore`, `RepoVSCodeClaudeConfig`
  - Constants: `DEFAULT_MAX_SESSIONS`
  - Session management functions: `load_sessions`, `save_sessions`, `add_session`, `remove_session`, etc.
  - Configuration functions: `load_vscodeclaude_config`, `load_repo_vscodeclaude_config`, `get_github_username`
  - Workflow functions: `get_eligible_vscodeclaude_issues`, `prepare_and_launch_session`, etc.

**Quality checks passed:**
- Pylint: No issues found
- Mypy: No type errors found

**Commit message written to:** `pr_info/.commit_message.txt`