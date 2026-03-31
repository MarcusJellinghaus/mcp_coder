# Issue #657: Soft-Delete Mechanism for Undeletable Session Folders

## Problem

When `--cleanup` fails to delete a session folder (locked files, permissions), the folder remains visible in `vscodeclaude status` and blocks re-creation of sessions for the same issue.

## Solution

A `.to_be_deleted` file in `workspace_base` acts as a soft-delete registry. One folder name per line. Folders listed there are hidden from status, skipped during session lookup, and retried on next cleanup.

## Architectural / Design Changes

### New concept: soft-delete registry

- **File**: `{workspace_base}/.to_be_deleted` — plain text, one folder name per line (relative to `workspace_base`)
- **Lifecycle**: entries are added on deletion failure (clean folders only), retried on next `--cleanup`, removed on successful retry
- **Chosen over** `.code-workspace` custom properties because workspace files are transient

### Parameter threading: `workspace_base`

All functions that need `.to_be_deleted` access receive `workspace_base` as a parameter, read once at the CLI entry point. This avoids re-reading config in helpers and keeps the dependency explicit.

Affected call chains:
- `execute_coordinator_vscodeclaude()` → `cleanup_stale_sessions(workspace_base=...)` → `delete_session_folder(session, workspace_base=...)`
- `execute_coordinator_vscodeclaude_status()` → loads config → `display_status_table(workspace_base=...)`
- `process_eligible_issues()` → `get_session_for_issue(repo, issue, workspace_base=...)`
- `prepare_and_launch_session()` → `get_working_folder_path(workspace_base, ...)` (already has it)

### Folder naming with suffixes

When the base folder name is occupied (on disk or in `.to_be_deleted`), new sessions use `-folder2` through `-folder9`. This prevents name collisions with undeletable folders.

### Cleanup ordering

`--cleanup` retries `.to_be_deleted` entries **first** (before processing new stale sessions), so previously stuck folders get another chance before new work begins.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | Add `load_to_be_deleted()`, `add_to_be_deleted()`, `remove_from_to_be_deleted()` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Retry `.to_be_deleted` entries, soft-delete on failure, always delete `.code-workspace`, pass `workspace_base` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Suffix-aware `get_working_folder_path()` with `-folder2` to `-folder9` |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Filter `.to_be_deleted` folders from `display_status_table()` |
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | Add `.to_be_deleted` exclusion in `get_session_for_issue()`, add `warn_orphan_folders()` |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Re-export new helpers |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Pass `workspace_base` to `cleanup_stale_sessions()` and `display_status_table()` |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Pass `workspace_base` to `get_session_for_issue()` |

## Files Created

| File | Purpose |
|------|---------|
| `tests/workflows/vscodeclaude/test_soft_delete.py` | Tests for soft-delete helpers |

## Implementation Steps

| Step | Focus | Commit |
|------|-------|--------|
| 1 | `helpers.py` — three soft-delete I/O functions + tests | `feat(vscodeclaude): add soft-delete file helpers` |
| 2 | `cleanup.py` — retry logic + soft-delete on failure + caller update + tests | `feat(vscodeclaude): soft-delete on cleanup failure, retry on next run` |
| 3 | `workspace.py` — suffix-aware folder path + tests | `feat(vscodeclaude): suffix-aware folder naming for soft-deleted folders` |
| 4 | `status.py` — filter soft-deleted from status display + tests | `feat(vscodeclaude): hide soft-deleted folders from status` |
| 5 | `sessions.py` — session lookup exclusion + orphan folder detection + tests | `feat(vscodeclaude): session lookup excludes soft-deleted, detect orphan folders` |

**Note**: Each step must update existing tests to pass the new `workspace_base` parameter to any modified function signatures. When a function gains a required `workspace_base` parameter, all existing test call sites for that function must be updated in the same step.
