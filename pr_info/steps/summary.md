# Issue #905 — `icoder --continue-session`: replay UI history + session picker + `/load`

## Goal

Make `icoder --continue-session` (and a new `/load` slash command) restore the
**UI history** of a prior conversation (commands, slash output, LLM text, tool
blocks, cancelled markers), not just the LLM session_id. Add a session picker
UI for choosing among prior logs.

## Architectural / Design Changes

### 1. Event log gains rotation + path exposure

`EventLog` (`src/mcp_coder/icoder/core/event_log.py`) gets:
- `current_path: Path` — the active JSONL file.
- `rotate() -> Path` — closes current file, opens a fresh
  `icoder_<new_timestamp>.jsonl`, resets the monotonic clock, clears in-memory
  entries. Returns the new path.
- `iter_events(path) -> Iterator[dict]` (module-level) — line-by-line JSONL
  parsing, used by replay + inventory.

### 2. `session_start` event carries `provider`

The picker filters by provider; this is the only piece of metadata that wasn't
already in the payload. CLI emits `provider=<resolved-provider>` alongside
existing fields. The `session_reset` event is **removed** (no longer emitted)
because `/clear` now rotates the log.

### 3. Response JSON gains `metadata.log_file_path`

`store_session()` (`src/mcp_coder/llm/storage/session_storage.py`) accepts a new
optional `log_file_path: str | None` kwarg and writes it under `metadata`. The
caller (`AppCore.stream_llm`) passes `event_log.current_path`. Resume reads
this back to find the JSONL to replay. Legacy response JSONs without this
field — and `.json` paths passed to `--continue-session-from` — produce a
hard error.

### 4. `LLMService.set_session_id(sid)` instead of a `swap_session` abstraction

A small Protocol addition (Real and Fake implementations get a one-line setter)
covers `/load` mid-run. No new abstraction.

### 5. `/clear` rotates the log

`AppCore.handle_input` rotates the event log whenever a command's `Response`
has `reset_session=True`. No new dataclass field — `/clear` is the only command
that resets the session, and the rotation always goes with it. Result: each
post-`/clear` conversation = its own log = its own picker row.

### 6. Self-contained logs across resumes

When a run resumes from a prior log, every replayed event is **also recorded
into the current run's new log file** through the same code paths the live UI
uses. Each log file therefore stands on its own — picker UX never has to walk
chains. (Disk overhead is bounded; acceptable for TUI session sizes.)

### 7. Banner extracted to a reusable helper

`format_runtime_banner(data: Mapping[str, object]) -> list[str]` produces the
mcp-coder/utils/server lines + paths block. The same helper renders the live
banner in `on_mount` and the replayed old banner from a `session_start` event.
Banner-on-resume order: **old banner (from log) → dim
`────── Resumed YYYY-MM-DD HH:MM ──────` divider → new banner (from current
`runtime_info`)**. Drift in env/versions is therefore visible.

### 8. Log inventory = one function

`list_icoder_logs(logs_dir, provider) -> list[LogSummary]` (single function,
returns a list of typed dicts/dataclasses). Globs `*.jsonl`, reads
`session_start` for date+provider filter, scans for `input_received` count and
first-prompt (truncated to 80 chars). Sorted newest first.

### 9. Replay = one dispatcher function

`replay_log(app, path)` on the UI side iterates events and dispatches via the
same primitives the live UI already uses (`OutputLog.append_text`,
`_handle_stream_event`, `format_tool_start`). No new render path. Token
counters are intentionally not updated during replay (a `replay_mode=True` flag
on `_handle_stream_event` skips `_update_token_display()`). A trailing
`llm_request_start` with no matching `llm_request_end` triggers the
`— Cancelled —` marker via the existing helper.

### 10. Picker = `ModalScreen` + Textual `OptionList`

`SessionPickerScreen(ModalScreen[Path | None])` shows rows formatted as
`<YYYY-MM-DD HH:MM> · <provider> · <N turns> · "<first prompt>"`. Up/Down/Enter
selects (returns the path); Esc dismisses (returns `None`). Used both at
startup (`--continue-session`) and via `/load`.

### 11. Single resume code path

`AppCore.prepare_for_resume(path) -> str | None`:
1. reads `session_start` from the log to resolve the recorded `session_id`;
2. calls `llm_service.set_session_id(...)`;
3. rotates the event log so the new conversation gets its own file.

The UI side complements with `ICoderApp.do_resume(path)` which clears the
output, calls `prepare_for_resume`, runs `replay_log`, renders the divider, and
re-renders the current banner. This same method backs both startup-resume and
`/load`.

### 12. CLI changes (`cli/commands/icoder.py`)

Resume resolution is rewritten:
- `--continue-session-from FILE`: must end in `.jsonl`. `.json` is a hard
  error with a clear message.
- `--continue-session` (no file): if any prior log exists for the current
  provider, the picker is shown synchronously **before the main app starts**;
  Esc → fresh session.
- Legacy response-JSON path (`metadata.log_file_path`) is supported but
  refuses to resume when the field is absent or the file is missing.

## Files Created

```
src/mcp_coder/icoder/core/log_inventory.py
src/mcp_coder/icoder/core/commands/load.py
src/mcp_coder/icoder/ui/widgets/session_picker.py
src/mcp_coder/icoder/ui/replay.py
tests/icoder/test_log_inventory.py
tests/icoder/test_session_picker.py
tests/icoder/test_load_command.py
tests/icoder/test_replay.py
pr_info/steps/summary.md
pr_info/steps/step_1.md … step_11.md
```

## Files Modified

```
src/mcp_coder/icoder/core/event_log.py            (rotate + current_path + iter_events)
src/mcp_coder/icoder/core/types.py                (LogSummary dataclass)
src/mcp_coder/icoder/core/app_core.py             (rotate on reset_session, prepare_for_resume)
src/mcp_coder/icoder/core/command_registry.py     (register /load)
src/mcp_coder/icoder/services/llm_service.py      (set_session_id on Protocol + impls)
src/mcp_coder/icoder/ui/app.py                    (extract format_runtime_banner, do_resume, replay_mode flag)
src/mcp_coder/llm/storage/session_storage.py      (log_file_path in metadata)
src/mcp_coder/cli/commands/icoder.py              (provider in session_start; resume rewrite; startup picker)
src/mcp_coder/cli/parsers.py                      (help text update for --continue-session-from)
tests/icoder/test_event_log.py                    (rotation tests)
tests/icoder/test_app_core.py                     (rotation on /clear; prepare_for_resume)
tests/icoder/test_llm_service.py                  (set_session_id)
tests/icoder/test_cli_icoder.py                   (resume resolution: .json error, .jsonl ok, missing log refuse)
tests/icoder/ui/test_app.py                       (do_resume, banner helper, replay integration)
tests/llm/storage/test_session_storage.py         (log_file_path metadata)
docs/icoder/icoder.md                             (document /load + picker)
```

## Step Sequence (each = exactly one commit)

| # | Title | Depends on |
|---|---|---|
| 1 | EventLog: `current_path`, `rotate()`, `iter_events()` | – |
| 2 | `provider` field in `session_start`; remove `session_reset` event | 1 |
| 3 | `log_file_path` in `store_session()` metadata | 1 |
| 4 | `AppCore` rotates log on `reset_session=True` | 1 |
| 5 | `LLMService.set_session_id()` | – |
| 6 | Extract `format_runtime_banner()` helper | – |
| 7 | `list_icoder_logs()` inventory function | 1, 2 |
| 8 | `replay_log()` dispatcher + `replay_mode` flag | 1, 6 |
| 9 | `SessionPickerScreen` (ModalScreen + OptionList) | 7 |
| 10 | `/load` command + `AppCore.prepare_for_resume()` + `ICoderApp.do_resume()` | 5, 8, 9 |
| 11 | CLI resume rewrite + startup picker + docs | 2, 3, 9, 10 |
