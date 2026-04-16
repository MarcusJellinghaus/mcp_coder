# Step 1 — Rewrite `is_session_active` with fallback chain + INFO logging + PID refresh

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified below. All changes are confined to two files. Follow TDD: write/update the tests in `tests/workflows/vscodeclaude/test_sessions.py` first, confirm they fail for the right reason, then rewrite `is_session_active` in `src/mcp_coder/workflows/vscodeclaude/sessions.py`. Finally run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and `mcp__tools-py__run_pytest_check` with the fast-unit exclusion markers from `CLAUDE.md`. All three must pass before committing.

## WHERE

- **Modify:** `src/mcp_coder/workflows/vscodeclaude/sessions.py` — function `is_session_active` (currently lines 502-549)
- **Modify:** `tests/workflows/vscodeclaude/test_sessions.py` — class `TestIsSessionActiveWindowPriority` (starts line 1066)

No new files, no new imports.

## WHAT

### Production signature (unchanged)

```python
def is_session_active(session: VSCodeClaudeSession) -> bool:
```

Behaviour contract (new):
- Returns `True` when any of: window-title match (Windows only), stored PID is a live VSCode process, or `is_vscode_open_for_folder(folder)` reports the folder open.
- Returns `False` when artifacts are gone (DEBUG-only), or when all of the above miss (INFO).
- Emits exactly one INFO line per call except the artifacts-gone short-circuit (DEBUG).
- On cmdline match where the returned PID differs from the stored `vscode_pid`, calls `update_session_pid(folder, found_pid)` and emits a separate DEBUG replacement line. The INFO conclusion line is not enriched.

### Exact INFO wordings

Windows (HAS_WIN32GUI and issue_num and repo all truthy):

```
active (window-title match)
active (PID {pid} alive, window-title not found — potentially stale)
active (cmdline match PID={pid}, window-title not found — potentially stale)
inactive (no window / PID {pid} gone / no cmdline match)
```

Non-Windows / missing issue_num / missing repo:

```
active (PID {pid} alive)
active (cmdline match PID={pid})
inactive (PID {pid} gone / no cmdline match)
```

All INFO lines are prefixed `is_session_active #{issue_num}: ` via `logger.info(...)`.

### Test changes

- Rename class `TestIsSessionActiveWindowPriority` → `TestIsSessionActiveFallbackChain`.
- Rewrite `test_pid_alive_but_window_gone_returns_inactive_with_warning` → `test_windows_title_miss_pid_alive_returns_active`. Expect `result is True` and that an INFO record contains `"active (PID 28036 alive, window-title not found — potentially stale)"`. Drop the WARNING assertion.
- Add `test_windows_title_miss_cmdline_match_refreshes_pid`: title miss, `check_vscode_running` → False, `is_vscode_open_for_folder` → `(True, 54321)`, stored `vscode_pid=28036`. Expect `True`, `update_session_pid` called with `(folder, 54321)`, INFO record contains `"active (cmdline match PID=54321, window-title not found — potentially stale)"`, DEBUG record mentions `"refreshing stored PID 28036 -> 54321"`.
- Add `test_windows_all_miss_returns_inactive`: title miss, PID dead, cmdline miss. Expect `False`, INFO `"inactive (no window / PID 28036 gone / no cmdline match)"`.
- Add `test_non_windows_pid_alive_info_format`: `HAS_WIN32GUI=False`, PID alive. Expect `True`, INFO `"active (PID 1234 alive)"` — no title wording.

Keep `test_guard_none_falls_through_to_pid_check` and `test_non_windows_uses_pid_fallback` — their asserted `True` return still holds.

## HOW

### Imports

No new imports. `update_session_pid` is already a top-level symbol in the same module (`sessions.py:574`).

### Integration points

- Called by `get_active_session_count` (`sessions.py:552`) — no contract change, still returns `bool`.
- Side effect (`update_session_pid` call) writes `sessions.json`. Acceptable per issue decisions table.

### Test patching

Tests monkeypatch module-level symbols on `mcp_coder.workflows.vscodeclaude.sessions`:
- `HAS_WIN32GUI`
- `session_has_artifacts`
- `is_vscode_window_open_for_folder`
- `check_vscode_running`
- `is_vscode_open_for_folder`
- `update_session_pid` (replace with a `MagicMock()` to assert call args)

Use `caplog.at_level(logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions")` to capture both INFO and DEBUG records in one pass.

## ALGORITHM

```
folder, issue_num, repo = session fields
if not session_has_artifacts(folder):
    logger.debug("#%s: no artifacts -> False"); return False

title_checked = False
if HAS_WIN32GUI and issue_num is not None and repo is not None:
    title_checked = True
    if is_vscode_window_open_for_folder(folder, issue_num, repo):
        logger.info("#%s: active (window-title match)"); return True

stale = ", window-title not found — potentially stale" if title_checked else ""
stored_pid = session.get("vscode_pid")

if check_vscode_running(stored_pid):
    logger.info("#%s: active (PID %s alive%s)", ..., stale); return True

is_open, found_pid = is_vscode_open_for_folder(folder)
if is_open:
    if found_pid is not None and found_pid != stored_pid:
        logger.debug("#%s: refreshing stored PID %s -> %s", ...)
        update_session_pid(folder, found_pid)
    logger.info("#%s: active (cmdline match PID=%s%s)", ..., stale); return True

prefix = "no window / " if title_checked else ""
logger.info("#%s: inactive (%sPID %s gone / no cmdline match)", prefix, stored_pid)
return False
```

## DATA

- **Input:** `session: VSCodeClaudeSession` (TypedDict with `folder: str`, `issue_number: int | None`, `repo: str | None`, `vscode_pid: int | None`, …).
- **Output:** `bool`. Semantics: `True` if any evidence of a live VSCode session for this folder; `False` if no evidence.
- **Side effect:** on cmdline match with `found_pid != stored_pid`, one write to `sessions.json` via `update_session_pid(folder, found_pid)`.
- **Log records emitted per call:**
  - Artifacts gone: 1 DEBUG, no INFO.
  - Any other path: exactly 1 INFO.
  - Cmdline-match-with-PID-refresh: additionally 1 DEBUG before the INFO.

## Acceptance

- All four Windows INFO wordings and all three non-Windows wordings exactly match the issue spec.
- The old WARNING at `sessions.py:536-541` is removed.
- `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, `mcp__tools-py__run_pytest_check` (with fast-unit exclusion markers) all pass.
- One commit: tests + implementation together.
