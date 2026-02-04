# Issue #400: Fix vscodeclaude Status Display, Cleanup Order, and Blocked Issue Handling

## Summary

This implementation fixes three interrelated problems in the `vscodeclaude` feature:

1. **Status Display Shows Stale Data** - The `status` command shows stored session status instead of current GitHub issue status
2. **Cleanup Runs After Restart** - Cleanup happens after restart, so restarted sessions can't be cleaned up
3. **Blocked Issues Being Restarted** - Issues with `blocked`/`wait` labels are incorrectly auto-restarted

## Architectural Changes

### Data Flow Changes

**Before:**
```
status command → reads session["status"] → displays stored value
vscodeclaude command → restart → cleanup (wrong order)
restart → restarts ALL closed sessions (including blocked)
```

**After:**
```
status command → fetches GitHub status → displays current value → updates session if changed
vscodeclaude command → cleanup → restart (correct order)
restart → skips blocked issues → updates session status when restarting
```

### New Helper Functions

Two new helpers in `issues.py` provide reusable ignore-label logic:
- `get_ignore_labels()` - Returns set of labels from config
- `get_matching_ignore_label()` - Case-insensitive label matching

One new helper in `sessions.py`:
- `update_session_status()` - Updates status field in session store

### Modified Function Signatures

```python
# status.py - Added blocked_label parameter
def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
    blocked_label: str | None = None,  # NEW
) -> str
```

## Files to Modify

| File | Type | Changes |
|------|------|---------|
| `src/mcp_coder/config/labels.json` | Config | Add `blocked`, `wait` to `ignore_labels` |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Source | Add `get_ignore_labels()`, `get_matching_ignore_label()` |
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | Source | Add `update_session_status()` |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Source | Add `blocked_label` param to `get_next_action()` |
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | Source | Skip blocked issues in restart, update status |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Source | Include blocked sessions in cleanup |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Source | Reorder cleanup/restart, fix status command |

## Test Files to Modify

| File | Changes |
|------|---------|
| `tests/workflows/vscodeclaude/test_issues.py` | Add tests for new helpers |
| `tests/workflows/vscodeclaude/test_sessions.py` | Add test for `update_session_status()` |
| `tests/workflows/vscodeclaude/test_status.py` | Add tests for blocked label in `get_next_action()` |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | Add tests for blocked skip logic |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Add tests for blocked session cleanup |
| `tests/cli/commands/coordinator/test_commands.py` | Add tests for status display fixes |

## Design Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Label matching | Case-insensitive | Safety - GitHub labels may vary in case |
| Blocked display | `"Blocked (label-name)"` | Shows which label caused blocking |
| Session update timing | On restart AND status command | Keeps sessions in sync |
| API failure handling | Per-repo `(?)` indicator | Only affected repos show uncertainty |
| Blocked cleanup | Include in cleanup | Blocked + clean sessions should be deletable |
| Cleanup without --cleanup flag | Skip entirely | Only run cleanup when explicitly requested |
| Shared cache builder | Extract `_build_cached_issues_by_repo()` | Avoid code duplication between commands |
| Issue not in cache | Treat as closed/deleted | Current caching is sufficient; missing = stale |
| File locking for sessions | Not needed | Only one vscodeclaude process runs at a time |
| Module `__all__` exports | Skip | Keep consistent with current module style |

## Implementation Order

1. **Step 1**: Config + Helper functions (foundation)
2. **Step 2**: Session status update helper
3. **Step 3**: `get_next_action()` blocked support
4. **Step 4**: Cleanup order fix + blocked session cleanup
5. **Step 5**: Restart blocked-skip logic
6. **Step 6**: Status command display fix

## Acceptance Criteria

- [ ] `blocked` and `wait` added to `ignore_labels` in `labels.json`
- [ ] Helper functions in `issues.py`: `get_ignore_labels()`, `get_matching_ignore_label()`
- [ ] Label matching is case-insensitive
- [ ] Status command shows current GitHub issue status
- [ ] Status command updates session file when status changed
- [ ] On API failure, status shows stored value with `(?)` indicator (per-repo)
- [ ] Cleanup runs before restart in `vscodeclaude` command
- [ ] Issues with ignore_labels are not restarted automatically
- [ ] Status table shows `Blocked (label-name)` in Next Action column
- [ ] Session status updated when restarting
- [ ] Blocked sessions included in cleanup
