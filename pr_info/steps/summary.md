# Summary — #1407 vscodeclaude: window title authoritative on Windows after grace

## Problem

On Windows the stored `vscode_pid` is either the `cmd.exe` wrapper from `launch_process("code …", shell=True)` or, after the PID refresh in `apply_assessments`, VSCode's single shared main `Code.exe`. Neither tracks one session's window. The main process keeps its original command line, so the session it was cold-started for has `pid_alive=True` and `cmdline_match=True` forever. `assess_liveness` checks title → pid → cmdline, so `rule=pid` wins over a correct `title_match=False`. With the folder gone the result is a permanent `INVESTIGATE_ZOMBIE` (seen for #1342).

Full analysis, decisions and accepted risks: GitHub issue #1407. This plan implements that issue; where they differ, the issue wins — with one deliberate exception: for the workspace file (Step 8) the plan replaces the issue's "JSON-escape each value after truncation" approach with building a dict and writing it with `json.dumps`, and deletes `WORKSPACE_FILE_TEMPLATE`. This removes the escaping problem entirely. Do not revert to the issue's escape-after-truncation approach.

## Architectural / design changes

The detect → assess → decide → render/apply pipeline is unchanged. Changes per stage:

**Detect (`detection.py`)**
- `_get_vscode_window_titles` returns `(titles, ok)`. `DetectionSnapshot` gains `window_enum_ok`. Failures stay uncached.
- `gather_signals` computes two new signals:
  - `window_count`: diagnostic.
  - `title_authoritative = HAS_WIN32GUI and window_enum_ok and repo and not (snapshot.pids and window_count == 0)`.
- On an authoritative title miss, `gather_signals` logs the window titles at DEBUG.
- Session age (and so grace) is measured from the later of `started_at` and the new `restarted_at`.
- Exact matching: a shared helper `_contains_bounded` (regex lookarounds + `re.escape`, any occurrence) rejects a match whose name visibly continues. The issue-number check uses `\[#N(?!\d)`.
- Legacy duplicates `is_vscode_window_open_for_folder` / `is_vscode_open_for_folder` are deleted.

**Assess (`assessment.py`)**
- New rule `LivenessRule.NO_WINDOW`. Past grace with an authoritative title, a title miss is inactive:
  - folder missing → `NO_ARTIFACTS`
  - pid/cmdline alive → `NO_WINDOW`
  - else → `NO_MATCH`
- `Transition` gains `prior_last_active`.
- `decide` is split. The unchanged matrix moves to `_decide_unguarded`. `decide` then applies one shared pure helper, `guard_reason`, only when the result is `DELETE` or `RESTART`:
  - Override guard: `NO_WINDOW` never deletes.
  - Confirmation guard: `DELETE`/`RESTART` only when `prior_last_active is False`.
  - Existing SKIP reasons keep precedence, and `DELETE` stays the single destructive branch.
- The `INVESTIGATE_ZOMBIE` reason names the signal keeping the session alive.
- The PID refresh is removed: `pid_needs_refresh`, the top-level `SessionAssessment.found_pid`, and the refresh in `apply_assessments`. `found_pid` stays in `DetectionSignals` as a diagnostic.

**Apply / render**
- `cleanup._retry_to_be_deleted` calls the same `guard_reason` before `safe_delete_folder`.
- A guard-converted `RESTART` → `SKIP` reaches `cleanup_stale_sessions`' SKIP branch (prints `[WARN] Skipping (just went inactive, confirming next run)`, counted in `skipped`). Intended; `get_stale_sessions` is unchanged.
- `status` shows `Running (zombie: <rule>)`.
- `restart_closed_sessions` records `restarted_at` through `update_session_pid(..., restarted_at=...)`.
- `create_workspace_file` builds a dict and writes `json.dumps` (no string template, so no escaping problem).

**Data**
- `VSCodeClaudeSession.restarted_at: NotRequired[str]` (UTC ISO).
- `DetectionSignals.window_count`, `DetectionSignals.title_authoritative`, `DetectionSnapshot.window_enum_ok`, `Transition.prior_last_active`. No dataclass defaults; every constructor is updated.
- `SessionAssessment.pid_needs_refresh` and `SessionAssessment.found_pid` are removed.
- Audit records and `--explain` pick up the new fields through `_flatten()`.

**Removed**
- `sessions.is_session_active`, `sessions.session_has_artifacts`, the two legacy detection functions, `WORKSPACE_FILE_TEMPLATE`.

## Files to modify

```
src/mcp_coder/workflows/vscodeclaude/
  __init__.py            remove legacy re-exports
  assessment.py          NO_WINDOW liveness, guard_reason, _decide_unguarded, zombie reason, drop PID refresh
  cleanup.py             retry-loop guard, docstring
  detection.py           enum flag, new signals, age from restarted_at, bounded matching, delete legacy
  session_restart.py     restarted_at on restart, zombie wording
  sessions.py            delete legacy, update_session_pid(restarted_at=)
  status.py              zombie rule display, docstrings
  templates.py           remove WORKSPACE_FILE_TEMPLATE
  types.py               new fields/rule, NotRequired restarted_at, drop refresh fields
  workspace.py           create_workspace_file via json.dumps
src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py   comments only
docs/coordinator-vscodeclaude.md                                   Session States
tests/workflows/vscodeclaude/
  conftest.py, test_assessment_layers.py, test_assessment_orchestration.py,
  test_audit.py, test_cleanup.py, test_cleanup_retry.py,
  test_closed_issues_integration.py, test_detection.py, test_detection_probes.py,
  test_explain.py, test_sessions.py, test_sessions_pid_identity.py,
  test_session_restart_closed_sessions.py, test_status_display_assessment_consumer.py,
  test_status_display_delete_actions.py, test_status_display_scenario.py,
  test_status_display_zombie.py, test_types.py, test_workspace.py,
  test_workspace_untrusted.py
tests/cli/commands/coordinator/test_vscodeclaude_cli.py   drop template-format test
```

## Files to delete

```
tests/workflows/vscodeclaude/test_sessions_active_fallback.py
tests/workflows/vscodeclaude/test_sessions_active_grace.py
```

No new source modules.

## Steps (one commit each)

1. Delete legacy detection code (pure deletion).
2. Remove the PID refresh.
3. Restart grace (`restarted_at`).
4. Guards: `LivenessRule.NO_WINDOW` (inert until Step 5), `prior_last_active`, `guard_reason` in `decide` and the retry loop, docs. Lands before Step 5 so no commit can delete a `NO_WINDOW` or unconfirmed session.
5. Title authoritative: enum flag, new signals, `assess_liveness` produces `NO_WINDOW`, DEBUG dump.
6. Zombie visibility: reason, status display, restart warning, docs.
7. Exact matching (negative boundaries).
8. Workspace file via `json.dumps`.

## Checks for every step

Run before every commit; all must pass:
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_format_code`

CI runs on Linux, development on Windows. Tests that reach `gather_signals` / `build_assessments` must pin `HAS_WIN32GUI` explicitly. Windows-path fixtures must not rely on host path semantics.
