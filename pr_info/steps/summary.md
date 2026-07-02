# Summary — iCoder: show log file path in `/info` (Issue #764)

## Goal

Surface the current session's iCoder event-log file and the logs directory in
the `/info` command output, so users can find the active log and browse older
sessions.

New section in `/info`, placed **between** the `MCP_CODER_* env vars` and
`Other env vars` sections:

```
Logs:
  Current: C:\project\logs\icoder_2026-04-17T10-30-00.jsonl
  Directory: C:\project\logs
```

Paths are rendered bare (no trailing separator on the directory), consistent
with how other paths in `/info` are shown.

## Architectural / design changes

The `/info` command is built by `register_info()` (a closure factory) which
delegates rendering to the pure formatter `_format_info()`. To show the log
paths, the command needs one new dependency: the live `EventLog`.

Two small, cohesive changes:

1. **`EventLog.logs_dir` read-only property** — exposes the already-stored
   `self._logs_dir`. The current log file reuses the existing `current_path`
   property (which returns `self._path` and already survives `close()` /
   `__exit__`, since `_path` is never cleared). No new `file_path` alias is
   added — that would duplicate `current_path`.

2. **`register_info()` gains an `event_log` parameter** and its call is moved
   into the `EventLog` `with` block in `icoder.py`, alongside the existing
   `register_color` / `register_display` calls (which already run there and
   already receive live app state). `_format_info()` gains an `event_log`
   argument and renders the new `Logs:` section. `_format_info` stays a pure
   formatter over primitive values so it remains unit-testable in isolation.

### KISS divergence from the issue's design decisions (deliberate)

The issue text proposed routing this through `AppCore` (Decision #2: pass
`AppCore` to `register_info`; add `AppCore.mcp_manager`; Decision #7: assert
`runtime_info is not None` at the boundary). After a simplicity review we
**do not route through `AppCore`**. Rationale:

- `register_info` needs exactly **one** new dependency (`event_log`), and at
  the call site `runtime_info`, `mcp_manager`, and `event_log` are all already
  local variables in scope. Adding one parameter is simpler than adding an
  `AppCore.mcp_manager` property plus a boundary invariant.
- `register_info` already takes `runtime_info: RuntimeInfo` (non-optional) and
  the real caller always passes a non-None value, so the `assert` in Decision
  #7 is unnecessary — it was only needed because reading `app_core.runtime_info`
  yields `RuntimeInfo | None`. Avoiding the routing avoids the invariant.
- Test churn shrinks: existing tests already have an `event_log` fixture in
  `conftest.py`; no bespoke `app_core` fixture is required.

All **user-facing requirements** of the issue are preserved (Decisions
#1, #3, #4, #5, #6, #8). Only the internal wiring choice (#2/#7) is simplified.
If future `/info` additions need broad `AppCore` state, switching
`register_info` to take `app_core` is a localized, mechanical refactor — cheaper
to do when actually needed (YAGNI).

This divergence was **explicitly approved by the repo owner during plan review
(2026-07-02)**: Decisions #2 and #7 are superseded and must **not** be reverted
to the `AppCore` route.

## Folders / modules / files created or modified

### Created
- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md`
- `pr_info/steps/step_2.md`

### Modified — source
- `src/mcp_coder/icoder/core/event_log.py` — add `logs_dir` property (Step 1)
- `src/mcp_coder/icoder/core/commands/info.py` — `event_log` param on
  `register_info`; `Logs:` section in `_format_info` (Step 2)
- `src/mcp_coder/cli/commands/icoder.py` — move `register_info` call into the
  `EventLog` `with` block and pass `event_log` (Step 2)

### Modified — tests
- `tests/icoder/test_event_log.py` — test for `logs_dir` (Step 1)
- `tests/icoder/test_info_command.py` — pass `event_log` at ~12 call sites;
  new test for the `Logs:` section (Step 2)

### Not modified (intentionally)
- `src/mcp_coder/icoder/core/app_core.py` — **unchanged** (no `mcp_manager`
  property, per the KISS divergence above)
- `tests/icoder/conftest.py` — the shared `event_log` fixture is reused as-is
- `tests/icoder/test_cli_icoder.py::test_info_command_registered_in_icoder` —
  stays green unchanged (it only asserts `/info` is registered after
  `execute_icoder`)

## Steps overview

| Step | Scope | Commit |
|------|-------|--------|
| 1 | Add `EventLog.logs_dir` property (+ test) | one commit |
| 2 | `register_info`/`_format_info` `Logs:` section + `icoder.py` wiring + `/info` test updates | one commit |

Step 2 depends on Step 1 (`_format_info` reads `event_log.logs_dir`). The
`register_info` signature change and the `icoder.py` call-site update are in the
**same** step because adding the required `event_log` parameter breaks the
existing call site — they must land together to keep checks green.
