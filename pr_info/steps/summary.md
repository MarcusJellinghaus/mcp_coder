# Issue #413: Fix False 'Dirty' Status in vscodeclaude

## Problem Summary

The `mcp-coder coordinator vscodeclaude status` command incorrectly shows directories as "Dirty" when they are actually clean. The root cause is that `check_folder_dirty()` returns `True` on **any** git command error, without distinguishing between actual uncommitted changes and git failures.

## Architectural / Design Changes

### Current Design
- Single boolean function `check_folder_dirty(folder_path) -> bool`
- Returns `True` on any error (folder missing, not a repo, git error)
- No distinction between error states

### New Design
- Add new function `get_folder_git_status(folder_path) -> str`
- Returns one of: `"Clean"`, `"Dirty"`, `"Missing"`, `"No Git"`, `"Error"`
- Update `check_folder_dirty()` to use new function internally (backward compatible)
- Callers updated to use appropriate status for display and cleanup decisions

### Design Principles Applied
- **KISS**: Single new function in existing module, no new files or enums
- **Backward Compatibility**: Existing `check_folder_dirty()` continues to work
- **Single Responsibility**: New function handles status detection, callers handle display/action

## Status Display Mapping

| Git Status | Display Column | Meaning |
|------------|----------------|---------|
| `Clean` | Clean | No uncommitted changes |
| `Dirty` | Dirty | Has uncommitted changes |
| `Missing` | Missing | Folder doesn't exist |
| `No Git` | No Git | Folder exists but not a git repo |
| `Error` | Error | Git command failed (unknown reason) |

## Cleanup Behavior Mapping

| Git Status | Cleanup Action |
|------------|----------------|
| `Clean` | Delete folder and remove session |
| `Dirty` | Skip (warn about uncommitted changes) |
| `Missing` | Remove session only (folder already gone) |
| `No Git` | Skip (warn - investigate manually) |
| `Error` | Skip (warn - investigate manually) |

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Update | Add `get_folder_git_status()`, update `check_folder_dirty()` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Update | Use new function for cleanup decisions |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Update | Export new function |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Update | Use new function for display |
| `tests/workflows/vscodeclaude/test_status.py` | Update | Add tests for new function |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Update | Update tests for new cleanup behavior |

## Implementation Steps Overview

1. **Step 1**: Add `get_folder_git_status()` function with tests (TDD)
2. **Step 2**: Update `check_folder_dirty()` to use new function + update status display
3. **Step 3**: Update cleanup logic to handle all status cases

## Success Criteria

- [ ] `get_folder_git_status()` correctly identifies all 5 states
- [ ] Status display shows accurate status (not false "Dirty")
- [ ] Cleanup handles missing folders gracefully (removes session)
- [ ] Cleanup skips error states with appropriate warnings
- [ ] All existing tests pass
- [ ] New tests cover all status cases
