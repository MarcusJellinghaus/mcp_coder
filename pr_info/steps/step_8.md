# Step 8 — `replay_log()` dispatcher + `replay_mode` flag

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_8.md`) with strict TDD. Write tests first using a
> Textual `Pilot` to drive `ICoderApp` against fixture JSONL files (mark
> with `textual_integration`). Then implement. Run pylint, pytest, mypy
> via the mandatory MCP tools. Single commit.

## WHERE

- Create: `src/mcp_coder/icoder/ui/replay.py`
- Modify: `src/mcp_coder/icoder/ui/app.py` — add `replay_mode: bool`
  parameter to `_handle_stream_event`; expose `_append_cancelled_marker`
  and `_append_blank_line` for the replay module.
- Create tests: `tests/icoder/test_replay.py` (textual_integration marker)

## WHAT

```python
# src/mcp_coder/icoder/ui/replay.py
def replay_log(app: "ICoderApp", path: Path) -> None:
    """Replay a JSONL event log into app's UI primitives.

    Renders banner, user inputs, slash output, stream events, tool blocks,
    and the cancelled marker (when an LLM turn was interrupted) using the
    same UI methods as the live path. Updates app.command_history. Does
    NOT update token usage. Does NOT emit anything to the current event
    log (that side-effect is handled in Step 11 — replay just renders).
    """
```

In `app.py`:

```python
def _handle_stream_event(
    self, event: StreamEvent, *, replay_mode: bool = False
) -> None:
    ...
    if isinstance(action, StreamDone):
        self.query_one(BusyIndicator).show_ready()
        if not replay_mode:                     # NEW
            self._update_token_display()
        self._append_blank_line()
    ...
```

## HOW

- `replay_log` iterates `iter_events(path)` (Step 1).
- Per-event dispatch:
  - `session_start` → `output.append_text("\n".join(format_runtime_banner(payload)), style="dim")` (Step 6 helper)
  - `input_received` → `app.command_history.add(text)` and
    `output.append_text(f"> {text}", style=STYLE_USER_INPUT)`
  - `output_emitted` → `output.append_text(text)` (slash-command output)
  - `command_matched` → ignored (no visual side-effect today)
  - `llm_request_start` → set local `in_flight = True`
  - `llm_request_end` → set `in_flight = False`
  - `stream_event` → strip the `event` and `t` keys, pass the rest as a
    `StreamEvent` to `app._handle_stream_event(ev, replay_mode=True)`
  - any other event type → ignored (forward-compat)
- After the loop:
  - if `in_flight is True` (turn started, never ended) →
    `app._append_cancelled_marker()` then `app._append_blank_line()`
- `replay_log` is synchronous; UI thread; no workers.

## ALGORITHM

```
replay_log(app, path):
    in_flight = False
    for ev in iter_events(path):
        match ev["event"]:
            case "session_start":
                app.output.append_text("\n".join(format_runtime_banner(ev)), style="dim")
            case "input_received":
                app.command_history.add(ev["text"])
                app.output.append_text(f"> {ev['text']}", style=STYLE_USER_INPUT)
            case "output_emitted":
                app.output.append_text(ev["text"])
            case "llm_request_start":
                in_flight = True
            case "llm_request_end":
                in_flight = False
            case "stream_event":
                payload = {k: v for k, v in ev.items() if k not in ("event", "t")}
                app._handle_stream_event(payload, replay_mode=True)
            case _: pass
    if in_flight:
        app._flush_buffer()
        app._append_cancelled_marker()
        app._append_blank_line()
```

## DATA

- No new types.
- New keyword-only arg `replay_mode: bool = False` on
  `_handle_stream_event`.

## Test Cases

(All marked `@pytest.mark.textual_integration`.)

1. Replay a log containing one `input_received` and a `text_delta` +
   `done` stream → output contains `"> hello"` and the LLM text;
   token-status widget remains hidden / shows zero state.
2. Replay populates `app.core.command_history`: after replay,
   pressing Up in the input area shows the prior input.
3. Replay of a log whose stream included `tool_use_start` + `tool_result`
   → tool block lines are rendered (assert via `output_log.recorded_lines`).
4. Replay of an interrupted turn (`llm_request_start` with no
   `llm_request_end`) → trailing `— Cancelled —` marker present in
   recorded lines.
5. Replay does not call `_update_token_display`'s update path: assert
   `token_usage.has_data is False` after replay even if the log
   contained a `done` event with usage data.
6. Pure-function test (no Textual): construct an `ICoderApp` Pilot with
   a fresh empty log; call `replay_log`; verify no exceptions on an
   empty file.

## Out of Scope

- Re-recording replayed events into the new log — explicitly NOT this
  step. Self-contained-logs requirement is met by Step 11 (CLI level)
  which calls `event_log.emit()` for each event in addition to
  rendering, OR by changing `replay_log` to take an optional
  `event_log` parameter. Decision deferred to Step 11.
