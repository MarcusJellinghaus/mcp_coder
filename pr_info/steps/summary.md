# Issue #836 — vscodeclaude: `is_session_active` false-negative on Windows enables folder deletion

## Problem

On Windows, `is_session_active()` in `src/mcp_coder/workflows/vscodeclaude/sessions.py` treats the window-title check as authoritative. When the title isn't found (workspace tab closed, folder opened from main repo window), the session is classified inactive even though VSCode still holds file locks on the folder. Cleanup then deletes live folders (observed: `mcp_coder_828-folder2` deleted while open in VSCode).

## Fix

Replace the single-check Windows path with a **fallback chain**: window-title → PID → cmdline → False. Add INFO logging naming the deciding criterion. Refresh stale stored PIDs when cmdline match finds a different PID.

## Architectural / design changes

1. **`is_session_active` becomes side-effecting.** When cmdline fallback finds a PID differing from the stored one, the function calls `update_session_pid()` — mutating `sessions.json`. Callers (`get_active_session_count`) are unaffected but the function is no longer read-only. This is the documented trade-off for self-healing after VSCode close/reopen cycles and for making subsequent calls hit the fast PID path.

2. **Single shared fallback body instead of two branched chains.** The Windows-only title check becomes an early short-circuit in front of one shared `PID → cmdline → False` chain. A local `title_checked` flag toggles INFO wording between the Windows and non-Windows formats. This keeps ~15 lines out of the function versus two parallel chains and ensures future changes to the fallback apply uniformly to both platforms.

3. **INFO-level audit trail of the decision.** Every call (except the artifacts-gone short-circuit, which stays DEBUG) emits exactly one INFO line naming the deciding criterion. Windows fallback paths explicitly carry `window-title not found — potentially stale` so silent degradation of title detection surfaces in logs even when subsequent checks succeed.

4. **Stale WARNING removed.** The `sessions.py:536-541` WARNING (`window title not found but PID alive — treating as inactive`) described the previous trade-off and is incompatible with the new fallback. The new INFO conclusion covers the same signal positively.

5. **Data-loss safety bias.** Where the old code preferred false-negatives (delete live folder), the chain now prefers false-positives (skip cleanup). Loose cmdline matching is kept for the same reason — tightening is explicitly out of scope.

## Files modified

- `src/mcp_coder/workflows/vscodeclaude/sessions.py` — rewrite `is_session_active` (lines 502-549). Remove WARNING at lines 536-541. Update docstring. No new imports; `update_session_pid` is already in the same module.
- `tests/workflows/vscodeclaude/test_sessions.py` — rename class `TestIsSessionActiveWindowPriority` → `TestIsSessionActiveFallbackChain` (line 1066). Rewrite `test_pid_alive_but_window_gone_returns_inactive_with_warning` to expect `True` + INFO line. Add 3 new tests for the fallback paths.

## Files / folders NOT modified

- No new files, no new folders, no new modules.
- `is_vscode_open_for_folder`, `is_vscode_window_open_for_folder`, `check_vscode_running`, `update_session_pid`, `session_has_artifacts` — reused as-is.
- `safe_delete_folder` — separate issue, explicitly out of scope.
- Cmdline-matcher strictness — explicitly out of scope.

## Out of scope

- `safe_delete_folder` destructive-on-failure bug in `src/mcp_coder/utils/folder_deletion.py`.
- Tightening `is_vscode_open_for_folder` to require full-path matches.
