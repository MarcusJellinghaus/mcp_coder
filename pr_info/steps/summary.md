# Issue #953 — VSCodeClaude Session Detection Improvements

## Problem

On 2026-05-05 the user had two real VSCode sessions open (`#949`, `#937`), but
`vscodeclaude status` listed four "Running" rows and `vscodeclaude launch
--cleanup --max-sessions 5` reported `5/5` sessions — blocking new launches. The
hidden 5th was a closed session `#188` whose folder was already deleted but
whose stored PID `74544` happened to still belong to a live unrelated
`code.exe` process.

Three independent detection bugs combined:

1. Window-title matching produced false positives across unrelated VSCode windows.
2. `check_vscode_running` accepted any live `code.exe` PID, so OS PID reuse was
   indistinguishable from genuine liveness.
3. The status table hid sessions that nonetheless counted toward `max_sessions`.

## Solution Overview

Single PR with seven items shipped in dependency order. Items 1, 2, 5 fix the
reproducer; 8 closes the `.to_be_deleted` retry loop; 4 and 6 surface
diagnostics; 3 is the final tightening that depends on 1+2 being in place;
composition tests cover scenarios that cross item boundaries.

## Architectural / Design Changes

### 1. Window-title detection is now process-scoped

`_vscode_window_cache` changes from `list[str] | None` to
`list[tuple[int, str]] | None`. `is_vscode_window_open_for_folder` first
computes the set of VSCode PIDs whose cmdline references the folder, then
accepts a title match only when the title's owning PID is in that set. This
eliminates the cross-process title-leak that produced the `#946`/`#950` false
positives.

### 2. Process identity is verified via `create_time`, not just PID

`VSCodeClaudeSession` gains an optional `vscode_pid_create_time: float | None`.
**Invariant**: `vscode_pid` and `vscode_pid_create_time` always describe the
same process. The invariant is self-enforcing because `update_session_pid` is
the only populator — it captures both fields atomically. No caller can bypass
it. `build_session` always stores `None`; `update_session_pid` populates the
field on the first cmdline-match refresh after launch (simpler than the
two-path scheme in the issue, since launch-time capture on Windows almost
always returns `None` for the launcher `.cmd` anyway).

No schema migration: all reads use `session.get("vscode_pid_create_time")` so
missing key → `None` → falls back to today's loose name-only check.

### 3. Workspace-file path has a single source of truth

`workspace.py:get_workspace_file_path(workspace_base, folder_name) -> Path`
becomes the only place the `{workspace_base}/{folder_name}.code-workspace`
pattern is constructed. Three existing/new call sites use it.

### 4. `session_has_artifacts` requires the folder

Previously `True` when folder OR workspace file existed. Now: `True` only when
the folder exists. The workspace file is just a launcher referencing the
folder; without the folder it points at nothing.

### 5. Status-table columns each do one job

Git column = on-disk state. VSCode column = liveness. Next Action column =
prescription. Zombie sessions (closed issue + missing folder + still-running
process) appear with `Git: Missing`, `VSCode: Running (zombie)`,
`Next Action: -> Investigate zombie`.

### 6. `.to_be_deleted` retries reconcile against live VSCode

If a folder name in `.to_be_deleted` matches a currently-open VSCode cmdline,
the entry is removed and a reconciliation warning logged — instead of being
retried (and failing) forever.

### 7. Title check is authoritative after a launch grace period

`LAUNCH_GRACE_SECONDS = 60.0`. Once a session is older than the grace window, a
negative title match returns `False` immediately (no PID/cmdline fallback).
During the grace window, fall through to today's PID + cmdline chain — covers
VSCode cold-start + extension install delays.

### 8. At-capacity diagnostic is one log line

Replace the existing "No new sessions started (active: N/M)" tail message
with a single line that always includes the folder basenames consuming the
slots when at capacity. One log site, no coordination between two emissions.

## Files Created or Modified

### Modified

- `src/mcp_coder/workflows/vscodeclaude/types.py`
  Add `vscode_pid_create_time: float | None` to `VSCodeClaudeSession`.
- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
  - New module constant `LAUNCH_GRACE_SECONDS = 60.0`.
  - `_vscode_window_cache` type change to `list[tuple[int, str]] | None`.
  - `_get_vscode_window_titles` returns `(pid, title)` pairs.
  - `is_vscode_window_open_for_folder` filters by owning PID.
  - `check_vscode_running(pid, expected_create_time)` signature change.
  - `update_session_pid` captures `create_time` atomically.
  - `session_has_artifacts` tightened to folder-only.
  - `is_session_active` applies launch-grace logic to the title check.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py`
  New `get_workspace_file_path` helper; `create_workspace_file` uses it.
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
  - `delete_session_folder` uses helper.
  - `cleanup_stale_sessions` reconciliation loop for `.to_be_deleted`.
  - `Missing` branch deletes orphan workspace file via helper.
- `src/mcp_coder/workflows/vscodeclaude/status.py`
  Zombie-row support in `display_status_table`.
- `src/mcp_coder/cli/commands/coordinator/commands.py`
  Single at-capacity diagnostic log replaces the existing tail message.
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
  Drop/downgrade the per-repo "Already at max sessions" log inside
  `process_eligible_issues`.

### Modified (Tests)

- `tests/workflows/vscodeclaude/test_sessions.py`
- `tests/workflows/vscodeclaude/test_cleanup.py`
- `tests/workflows/vscodeclaude/test_status_display.py`
- `tests/workflows/vscodeclaude/test_workspace.py`
- `tests/cli/commands/coordinator/test_commands.py`

### Not modified

- `src/mcp_coder/workflows/vscodeclaude/session_restart.py` —
  unchanged; benefits transparently from the `update_session_pid` invariant.
- `src/mcp_coder/workflows/vscodeclaude/__init__.py` — public re-exports
  unchanged (signatures preserved where possible).

## Implementation Steps

Each step is one commit: tests + implementation + checks passing.

| # | File | Title |
|---|---|---|
| 1 | `step_1.md` | Bind window-title match to owning VSCode process (Item #1) |
| 2 | `step_2.md` | Verify VSCode identity via `create_time` (Item #2) |
| 3 | `step_3.md` | `get_workspace_file_path` helper + auto-clean orphan workspace files (Item #5) |
| 4 | `step_4.md` | Reconcile `.to_be_deleted` against live VSCode (Item #8) |
| 5 | `step_5.md` | Surface zombie sessions in status table (Item #4) |
| 6 | `step_6.md` | Single at-capacity diagnostic log (Item #6) |
| 7 | `step_7.md` | Trust negative title result after launch grace (Item #3) |
| 8 | `step_8.md` | Composition tests (Scenarios A and B) |

## Acceptance Criteria (verified across steps)

- The reproducer state does not block launches: `vscodeclaude launch` reports
  `2` active and starts new sessions.
- `vscodeclaude status` shows every session that counts toward `max_sessions`;
  zombies appear with `VSCode: Running (zombie)` and `Git: Missing`.
- `vscodeclaude launch` at capacity logs the exact folder basenames consuming
  the slots.
- Old `sessions.json` files load unchanged; missing `vscode_pid_create_time`
  treated as `None` and self-populates on first `update_session_pid` call.
- Composition scenario A — orphan workspace file end-to-end: cleanup hits
  `Missing` branch and removes both records in one pass.
- Composition scenario B — false-negative reconciliation: `.to_be_deleted`
  entry removed without delete attempt; reconciliation warning logged.
- Session created within the last 60s with no visible window is not marked
  inactive on Windows (launch grace).
- `{workspace_base}/{folder_name}.code-workspace` is constructed in exactly
  one place (`get_workspace_file_path`).
