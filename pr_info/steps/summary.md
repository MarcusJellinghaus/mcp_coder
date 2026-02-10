# Issue #422: Status-Aware Branch Handling for VSCodeClaude Coordinator

## Overview

Enhance the vscodeclaude coordinator to handle branches based on issue status during session launch and restart. Currently, the code falls back to `main` for all statuses when no linked branch exists, and session restarts don't properly handle branch switching.

## Problem Statement

**Current Behavior:**
- Falls back to `main` for all statuses when no branch is linked
- Session restarts don't switch branches even when status changes
- No verification of linked branch on restart for status-04/07
- `.vscodeclaude_status.txt` shows `Branch: main` instead of issue branch

**Required Behavior:**
- `status-01:created`: Use linked branch if exists, otherwise `main`
- `status-04:plan-review` / `status-07:code-review`: **Require** linked branch (error if missing)
- Run `git fetch origin` on every restart
- Auto-switch branch if repo is clean and linked branch exists
- Show appropriate indicators in status table for missing branches/errors

---

## Architectural Changes

### Design Principle: Single Skip Reason

Instead of multiple boolean flags, use a single `skip_reason: str | None` pattern throughout:
- `None` = proceed normally
- `"No branch"` = status requires linked branch but none exists
- `"Dirty"` = repo has uncommitted changes, can't switch branch
- `"Git error"` = git operation failed

### New Helper Function

**`status_requires_linked_branch(status: str) -> bool`** in `issues.py`
- Simple predicate: returns `True` for `status-04:plan-review` and `status-07:code-review`
- Used by both launch and restart logic

### New Branch Preparation Helper

**`_prepare_restart_branch(...) -> BranchPrepResult`** in `orchestrator.py`
- Encapsulates all git operations for restart
- Returns `BranchPrepResult` NamedTuple with `(should_proceed, skip_reason, branch_name)`
- Handles: fetch (fatal if fails), dirty check, checkout, pull
- Catches `ValueError` for multiple branches → `skip_reason="Multi-branch"`

### Modified Status Display

**`get_next_action(..., skip_reason: str | None)`** in `status.py`
- Single new parameter replaces multiple booleans
- Cleaner interface, easier to extend

---

## Files to Modify

| File | Type | Changes |
|------|------|---------|
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | MODIFY | Add `status_requires_linked_branch()` helper |
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | MODIFY | Add `BranchPrepResult` NamedTuple, `_prepare_restart_branch()`, modify `process_eligible_issues()`, `restart_closed_sessions()`, update module docstring |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | MODIFY | Add `skip_reason` to `get_next_action()`, update `display_status_table()` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | REFACTOR | Refactor `execute_coordinator_vscodeclaude_status()` to call `display_status_table()` |
| `tests/workflows/vscodeclaude/test_issues.py` | MODIFY | Add tests for `status_requires_linked_branch()` |
| `tests/workflows/vscodeclaude/test_next_action.py` | MODIFY | Add tests for `skip_reason` parameter |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | MODIFY | Add tests for branch handling in restart |
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | MODIFY | Add tests for branch requirement on launch |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Session Launch Flow                          │
├─────────────────────────────────────────────────────────────────┤
│  process_eligible_issues()                                      │
│    │                                                            │
│    ├─► Get issue status                                         │
│    ├─► Get linked branch from GitHub API                        │
│    ├─► status_requires_linked_branch(status)?                   │
│    │     ├─► YES + no branch → skip, log error                  │
│    │     └─► NO or has branch → prepare_and_launch_session()    │
│    └─► Return started sessions + skipped issues                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Session Restart Flow                          │
├─────────────────────────────────────────────────────────────────┤
│  restart_closed_sessions()                                      │
│    │                                                            │
│    ├─► For each closed session:                                 │
│    │     ├─► Validate folder, repo config, issue state          │
│    │     ├─► _prepare_restart_branch()                          │
│    │     │     ├─► git fetch origin (always)                    │
│    │     │     ├─► If status-04/07:                             │
│    │     │     │     ├─► Get linked branch                      │
│    │     │     │     ├─► Check dirty → skip if dirty            │
│    │     │     │     ├─► git checkout + git pull                │
│    │     │     │     └─► Return (success, None) or (fail, reason)│
│    │     │     └─► If status-01: Return (True, None)            │
│    │     ├─► If skip_reason → don't restart, log indicator      │
│    │     ├─► regenerate_session_files()                         │
│    │     └─► launch_vscode()                                    │
│    └─► Return restarted sessions                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Status Table Indicators

| Condition | Indicator | Location |
|-----------|-----------|----------|
| VSCode running | `(active)` | Next Action column |
| No linked branch for status-04/07 | `!! No branch` | Next Action column |
| Multiple branches linked | `!! Multi-branch` | Next Action column |
| Dirty repo + needs branch switch | `!! Dirty` | Next Action column |
| Git operation failed (incl. fetch) | `!! Git error` | Next Action column |
| Eligible issue without linked branch | `→ Needs branch` | Next Action column |
| Blocked by label | `Blocked (label)` | Next Action column |
| Stale (status changed) | `→ Delete (with --cleanup)` | Next Action column |
| Normal restart needed | `→ Restart` | Next Action column |

---

## Implementation Steps

### Core Implementation (Completed)
1. **Step 1**: Add `status_requires_linked_branch()` helper with tests ✅
2. **Step 2**: Add `skip_reason` parameter to `get_next_action()` with tests ✅
3. **Step 3**: Add `_prepare_restart_branch()` helper with tests ✅
4. **Step 4**: Modify `process_eligible_issues()` for branch-aware launch ✅
5. **Step 5**: Modify `restart_closed_sessions()` for branch-aware restart ✅
6. **Step 6**: Update `display_status_table()` for new indicators ✅
7. **Step 7**: Update module docstring and final integration testing ✅

### Code Review Follow-ups (New)
8. **Step 8**: Extract CLI logic to `build_eligible_issues_with_branch_check()` helper
9. **Step 9**: Remove redundant status file write in `restart_closed_sessions()`
10. **Step 10**: Add comprehensive decision matrix to `orchestrator.py` module docstring

---

## Acceptance Criteria Mapping

### Core Feature Requirements
| Criteria | Step | Status |
|----------|------|--------|
| `status-01:created` sessions launch on `main` (or linked branch if exists) | Step 4 | ✅ |
| `status-04:plan-review` sessions require linked branch or don't start | Step 4 | ✅ |
| `status-07:code-review` sessions require linked branch or don't start | Step 4 | ✅ |
| New sessions without linked branch show `→ Needs branch` in status table | Step 6 | ✅ |
| `git fetch origin` runs on every restart (all statuses) | Step 3, 5 | ✅ |
| Restart verifies linked branch exists for status-04/07 | Step 3, 5 | ✅ |
| Session restart runs: `git fetch` → `git checkout` → `git pull` | Step 3, 5 | ✅ |
| Session restart detects status change and auto-switches branch | Step 5 | ✅ |
| Dirty repos show `!! Dirty`, VSCode not restarted | Step 2, 5 | ✅ |
| Missing branch shows `!! No branch`, VSCode not restarted | Step 2, 5 | ✅ |
| Git errors show `!! Git error`, VSCode not restarted | Step 2, 5 | ✅ |
| Status file updated after successful branch switch | Step 5 | ✅ |
| Intervention sessions follow same branch rules | Step 4, 5 | ✅ |
| `orchestrator.py` module docstring documents branch handling | Step 7 | ✅ |

### Code Quality Improvements
| Criteria | Step | Status |
|----------|------|--------|
| CLI eligible issues logic extracted to reusable helper | Step 8 | ⏳ |
| Redundant status file write removed from restart | Step 9 | ⏳ |
| Comprehensive decision matrix documented in module docstring | Step 10 | ⏳ |
