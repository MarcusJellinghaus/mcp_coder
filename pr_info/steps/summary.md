# Issue #872 — Reduce redundant `is_session_active` calls in vscodeclaude launch and status

## Goal

Reduce `is_session_active` calls per command from `(N_repos + 3) × N_sessions` (launch) and `N_sessions` per `display_status_table` invocation (status) down to **exactly `N_sessions` per command**.

## Background

The "are you alive?" question is answered identically across cleanup, restart, per-repo capacity checks, and the final summary, even though the truth is a snapshot at command start. `vscodeclaude status` has the same shape on a smaller scale. See issue #872 for the call-trace breakdown.

## Architectural / design changes

### 1. Active-session snapshot threaded as explicit parameter

Each command builds an `active_set: dict[str, bool]` once at entry — keyed by `session["folder"]`, valued by `is_session_active(session)`. The dict is passed as a parameter into:

- `cleanup_stale_sessions`, `get_stale_sessions`
- `restart_closed_sessions`
- `display_status_table`

Inside those functions, `is_session_active(session)` calls become `active_set.get(session["folder"], False)` lookups. **Note:** lookups use `.get(folder, False)` (not `[folder]`) so that sessions removed mid-flow (e.g. by cleanup) are treated as inactive.

**Rationale:** explicit data flow is more maintainable than adding a fourth implicit module-level cache to `sessions.py`.

### 2. New `build_active_session_set` helper

A single helper in `sessions.py` encapsulates "snapshot ceremony": clear caches, log framing line, iterate sessions, opportunistically refresh stored PIDs for active sessions. Used by both command entry points.

### 3. Capacity tracking moved to caller

`process_eligible_issues` no longer calls `get_active_session_count()`. Instead it accepts `current_count: int` as a parameter. The caller in `commands.py` initialises:

```
current_count = sum(active_set.values()) + len(restarted)
```

after `restart_closed_sessions` returns, then increments `current_count += len(started)` after each per-repo `process_eligible_issues` call. The dead local `current_count += 1` increment inside the inner launch loop is dropped (Boy Scout cleanup).

**Rationale:** cross-repo capacity tracking lives in one place and correctly accounts for restarted sessions (which `active_set` records as inactive).

### 4. Cache-clear moved to command entry

`clear_vscode_window_cache()` + `clear_vscode_process_cache()` calls move out of `restart_closed_sessions` and `display_status_table` and into `build_active_session_set` (called at the top of both command entry points), so the snapshot itself is built against fresh caches.

### 5. PID-refresh centralised in snapshot build

The in-loop block at `session_restart.py:264-267` (which only runs in launch, not status) is removed. The same logic — `is_vscode_open_for_folder(folder)` then `update_session_pid` if PID differs — runs once per active session during snapshot build, in **both** `launch` and `status`. Closes today's asymmetry where `status` never refreshes window-title-detected PIDs.

**Status side effect (intentional):** vscodeclaude status now writes updated PIDs to `sessions.json` on window-title detection (intentional — closes today's PID-refresh asymmetry between launch and status).

### 6. `get_active_session_count` removed entirely

Dropped from `sessions.py`, `__init__.py` `__all__`, and the import in `commands.py`. No external callers exist (`mcp_coder.workflows.vscodeclaude` is internal).

### 7. Single INFO framing log line

`build_active_session_set` emits `Checking N session(s)...` at INFO level before the snapshot loop. Matches the existing per-session INFO logs from `is_session_active`, so framing + per-session lines appear together as a coherent block when `--log-level INFO` is set, and stay silent at default level (consistent with current behavior).

## Snapshot key choice

`session["folder"]` matches the existing session-identifier convention used by `update_session_pid`, `remove_session`, `get_session_for_issue`. Using `(repo, issue_number)` tuples would have required rewriting more of the codebase for no functional gain.

## Intervention path

The intervention path (`_handle_intervention_mode`) bypasses the snapshot — it launches a single session directly without checking `is_session_active` and does not need `active_set`.

## Files modified

### Source

| File | Change |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | Add `build_active_session_set`. Remove `get_active_session_count`. |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Export `build_active_session_set`; drop `get_active_session_count`. |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | `cleanup_stale_sessions` and `get_stale_sessions` accept `active_set`. Drop `is_session_active` import. |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | `restart_closed_sessions` accepts `active_set`. Remove cache-clear and in-loop PID-refresh. Drop `clear_vscode_window_cache`, `clear_vscode_process_cache`, `is_session_active`, `is_vscode_open_for_folder`, `update_session_pid` imports as appropriate. |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | `process_eligible_issues` accepts `current_count`. Remove `get_active_session_count` import and call. Drop dead `current_count += 1` increment in inner launch loop. |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | `display_status_table` accepts `active_set`. Remove cache-clear. Drop `clear_vscode_window_cache`, `clear_vscode_process_cache`, `is_session_active` imports. |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Build snapshot at top of `execute_coordinator_vscodeclaude` and `execute_coordinator_vscodeclaude_status`; thread `active_set` and `current_count`. Drop `get_active_session_count` import. |

### Tests modified

| File | Change |
|---|---|
| `tests/workflows/vscodeclaude/test_cleanup.py` | Replace `monkeypatch.setattr(... .is_session_active, ...)` with explicit `active_set=...` argument (~20 sites). |
| `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` | Replace `get_active_session_count` patches with explicit `current_count=...` argument (7 sites). |
| `tests/workflows/vscodeclaude/test_session_restart.py` | Replace `is_session_active` patches with `active_set=...`. |
| `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py` | Same. |
| `tests/workflows/vscodeclaude/test_session_restart_cache.py` | Same. |
| `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py` | Same. |
| `tests/workflows/vscodeclaude/test_status_display.py` | Same. Add explicit assertion that `update_session_pid` is called when stored PID is stale. |
| `tests/workflows/vscodeclaude/test_closed_issues_integration.py` | Same. |
| `tests/workflows/vscodeclaude/test_sessions.py` | Replace `test_get_active_session_count_with_mocked_pid_check` (line 224) with `test_build_active_session_set` (added in step 1); drop the old test in step 4. |

### Tests added

- New invariant test asserting `is_session_active.call_count == N_sessions` for one `launch` and one `status` run with mocked sessions. Added in step 3 once both flows are converted. Location: extend an existing test module under `tests/cli/commands/` if `execute_coordinator_vscodeclaude` is already covered there; otherwise add `tests/workflows/vscodeclaude/test_active_set_invariant.py`. The step 3 author chooses based on what exists.

## Steps

1. **Step 1** — Add `build_active_session_set` helper; thread `active_set` into `cleanup_stale_sessions` / `get_stale_sessions` AND `restart_closed_sessions`; build snapshot at top of `execute_coordinator_vscodeclaude` BEFORE both calls; remove cache-clear and in-loop PID-refresh from `restart_closed_sessions`.
2. **Step 2** — Thread `current_count` into `process_eligible_issues`; remove `get_active_session_count` call; drop dead `current_count += 1` increment.
3. **Step 3** — Thread `active_set` into `display_status_table`; build snapshot at top of `execute_coordinator_vscodeclaude_status`; remove cache-clear from `display_status_table`. Add invariant test (`is_session_active.call_count == N_sessions` for launch and status) and explicit "status refreshes stale stored PID" test.
4. **Step 4** — Remove `get_active_session_count` entirely (dead code after step 2). Deletion-only; no new tests.

Each step is one commit with TDD (test changes first, then implementation, then all checks green).
