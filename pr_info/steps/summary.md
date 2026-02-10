# Issue #421: Fix Coordinator VSCodeClaude Session Restart Logic

## Problem Statement

`coordinator vscodeclaude` incorrectly restarts sessions for:
1. Issues at bot statuses (e.g., `status-02:awaiting-planning`, `status-08:ready-pr`)
2. Closed issues
3. PR-created issues (`status-10:pr-created`)

These sessions should be marked as stale and cleaned up, not restarted.

## Root Cause

`restart_closed_sessions()` in `orchestrator.py` only checks if the status label *changed* (via `is_session_stale()`), not whether:
- The current status requires a VSCodeClaude session (has non-null `initial_command`)
- The issue is still open

## Architectural / Design Changes

### New Function: `is_status_eligible_for_session()`

A single helper function that determines if a status label should have a VSCodeClaude session:
- Returns `True` for statuses with non-null `initial_command`: 01, 04, 07
- Returns `False` for bot statuses (02, 03, 05, 06, 08, 09) and pr-created (10)

This function enables consistent eligibility checking across restart, display, and cleanup operations.

### Modified Function Signature: `get_next_action()`

Add optional `stale_reason: str | None` parameter instead of multiple boolean flags:
- Simpler API (one string vs. three booleans)
- More extensible (new reasons just need a new string)
- Enables specific delete messages: `"→ Delete (--cleanup, {reason})"`

### Display Behavior Change

Closed issues are now **shown** in the status table (not hidden) so users can see and clean them up.

### Session Lifecycle Rules (Documented in orchestrator.py)

| Status Category | Examples | Session Needed | On VSCode Close |
|-----------------|----------|----------------|-----------------|
| `human_action` with command | 01, 04, 07 | Yes | Restart |
| `human_action` without command | 10 | No | Delete (--cleanup) |
| `bot_pickup` | 02, 05, 08 | No | Delete (--cleanup) |
| `bot_busy` | 03, 06, 09 | No | Delete (--cleanup) |
| Closed issue | any | No | Delete (--cleanup) |

**Dirty folder protection**: All stale/ineligible sessions with uncommitted changes show `"!! Manual cleanup"`.

## Files to Modify

| File | Purpose |
|------|---------|
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Add `is_status_eligible_for_session()` |
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | Update `restart_closed_sessions()` + add module docstring |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Update `get_next_action()` and `display_status_table()` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Update `get_stale_sessions()` |

## Test Files to Modify

| File | Purpose |
|------|---------|
| `tests/workflows/vscodeclaude/test_issues.py` | Test `is_status_eligible_for_session()` |
| `tests/workflows/vscodeclaude/test_next_action.py` | Test new `stale_reason` parameter |
| `tests/workflows/vscodeclaude/test_status_display.py` | Test closed issues shown in display |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Test expanded stale session detection |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | Test restart logic changes |

## Implementation Steps Overview

1. **Step 1**: Add `is_status_eligible_for_session()` with tests
2. **Step 2**: Update `get_next_action()` with `stale_reason` parameter and tests
3. **Step 3**: Update `display_status_table()` to show closed issues and compute stale reasons
4. **Step 4**: Update `get_stale_sessions()` to include ineligible sessions
5. **Step 5**: Update `restart_closed_sessions()` with eligibility checks + module docstring

## Acceptance Criteria

- [ ] Sessions at `bot_pickup` statuses (02, 05, 08) are NOT restarted
- [ ] Sessions at `bot_busy` statuses (03, 06, 09) are NOT restarted
- [ ] Sessions at `status-10:pr-created` are NOT restarted
- [ ] Sessions for closed issues are NOT restarted
- [ ] Sessions at `human_action` statuses with commands (01, 04, 07) for open issues ARE restarted
- [ ] Bot-status sessions show `→ Delete (--cleanup, now at bot stage)`
- [ ] PR-created sessions show `→ Delete (--cleanup, PR in GitHub)`
- [ ] Closed issue sessions show `→ Delete (--cleanup, issue closed)` and ARE visible in display
- [ ] Dirty folders show `!! Manual cleanup` (same message for all scenarios)
- [ ] All non-restartable sessions are eligible for `--cleanup` (if clean)
- [ ] Session lifecycle rules documented in orchestrator.py module docstring
