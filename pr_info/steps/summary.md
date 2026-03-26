# Issue #602: NOTICE log level should not be used for logging

## Summary

The NOTICE log level (25) was introduced as a **filter threshold** for non-workflow CLI commands.
When a CLI command defaults to `--log-level NOTICE`, all `logger.info()` messages (level 20) are silenced, giving cleaner terminal output.

However, ~72 `logger.info()` calls were simultaneously promoted to `logger.log(NOTICE, ...)`, defeating the purpose — those messages now always show regardless of threshold.

**Goal**: Revert NOTICE from being used as a logging level back to being threshold-only.

## Architectural / Design Changes

- **No architectural changes.** This is a behavioral revert: messages that were promoted to NOTICE go back to INFO.
- **Design clarification**: `NOTICE = 25` remains as a threshold constant used by `_resolve_log_level()` in `cli/main.py`. It is never used as a level to emit logs at.
- **Removed pattern**: The `Logger.notice()` monkey-patch on `logging.Logger` is removed (it was never called anywhere).
- **Import cleanup**: `NOTICE` is no longer imported in files that only used it for `logger.log(NOTICE, ...)` calls.

## Files Modified

### Source files (log call reverts + import removal)

| File | Changes |
|------|---------|
| `src/mcp_coder/utils/log_utils.py` | Remove `_notice` monkey-patch, add threshold-only comment |
| `src/mcp_coder/cli/commands/check_branch_status.py` | 7 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/cli/commands/define_labels.py` | 4 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/cli/commands/prompt.py` | 3 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/cli/commands/set_status.py` | 1 call → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | 2 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/cli/commands/coordinator/core.py` | 4 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | 1 call → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/create_plan.py` | 18 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/create_pr/core.py` | 8 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/implement/core.py` | 18 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/implement/prerequisites.py` | 1 call → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/implement/task_processing.py` | 4 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | 2 calls → `logger.info()`, remove NOTICE import |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | 3 calls → `logger.info()`, remove NOTICE import |

### Source files (unused import removal only)

| File | Changes |
|------|---------|
| `src/mcp_coder/utils/github_operations/issues/branch_manager.py` | Remove unused NOTICE import |
| `src/mcp_coder/utils/github_operations/issues/manager.py` | Remove unused NOTICE import |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Remove unused NOTICE import |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Remove unused NOTICE import |

### Test files

| File | Changes |
|------|---------|
| `tests/utils/test_log_utils.py` | Remove `test_logger_notice_method_exists` test |

### Files NOT modified (unchanged)

- `src/mcp_coder/utils/log_utils.py` — `NOTICE = 25` constant and `logging.addLevelName()` stay
- `src/mcp_coder/utils/__init__.py` — `NOTICE` re-export stays (valid as threshold constant)
- `src/mcp_coder/cli/main.py` — `_resolve_log_level()` stays as-is
- `tests/cli/test_main.py` — All assertions are about threshold resolution, not log emission

## Implementation Steps

- **Step 1**: Update `log_utils.py` (remove monkey-patch, add comment) + update test
- **Step 2**: Revert CLI command files (7 files) — log calls + import cleanup
- **Step 3**: Revert workflow files (8 files) + unused import cleanup (4 files) — log calls + import cleanup

## Risk

**Low** — purely changes which log level messages are emitted at. No logic, API, or behavioral changes.
