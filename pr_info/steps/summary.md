# Summary: Add Clean Working Directory Check to set-status Command

## Issue Reference
- **Issue #326**: mcp-coder set-status: Add clean working directory check

## Overview
Add a git working directory cleanliness check to the `mcp-coder set-status` command to prevent status label updates when uncommitted changes exist. This aligns `set-status` with other workflow commands (`create_plan`, `create_pr`, `implement`) that already perform this validation.

## Architectural / Design Changes

### No New Architecture Required
This change follows existing patterns in the codebase:
- Reuses `is_working_directory_clean()` from `utils.git_operations.repository`
- Reuses `DEFAULT_IGNORED_BUILD_ARTIFACTS` constant from `constants.py`
- Follows the same check pattern used in `create_plan.py` and other workflows

### Design Decisions
1. **Check Position**: After `resolve_project_dir()`, before label validation - ensures valid project directory exists before git operations
2. **Force Flag**: `--force` bypasses the check for edge cases (consistent with Git CLI conventions)
3. **Ignored Files**: Uses `DEFAULT_IGNORED_BUILD_ARTIFACTS` (currently `["uv.lock"]`) to allow auto-generated files
4. **Error Message**: Clear, actionable message with solution hint

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/cli/main.py` | Modify | Add `--force` CLI argument |
| `src/mcp_coder/cli/commands/set_status.py` | Modify | Add imports + working directory check |
| `.claude/commands/plan_approve.md` | Modify | Add error handling note |
| `.claude/commands/implementation_needs_rework.md` | Modify | Add error handling note |
| `.claude/commands/implementation_approve.md` | Modify | Add error handling note |
| `tests/cli/commands/test_set_status.py` | Modify | Add tests for new functionality |

## Implementation Summary

### Step 1: Add Tests (TDD)
- Add unit tests for clean directory check behavior
- Add tests for `--force` flag bypass
- Add tests for error scenarios

### Step 2: Implement Core Functionality
- Add `--force` argument to CLI parser
- Add imports and working directory check to `execute_set_status()`

### Step 3: Update Slash Commands
- Add error handling notes to 3 slash command files

## Success Criteria
1. `mcp-coder set-status` fails with clear error when working directory is dirty
2. `mcp-coder set-status --force` bypasses the check
3. Files in `DEFAULT_IGNORED_BUILD_ARTIFACTS` (e.g., `uv.lock`) are ignored
4. All existing tests continue to pass
5. New tests cover the added functionality
