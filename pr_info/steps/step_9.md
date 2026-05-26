# Step 9 — `ICoderApp` migrates to `append_unit` flow + orphan cleanup

## Goal

Stop sending tool blocks / user inputs / assistant turns through `append_text()`. Route them through `append_unit()` / `extend_open_unit()` / `finalize_open_unit()` so they become clickable units. Banners, blank spacers, "Resumed" divider, cancelled marker, runtime info, error message, slash-command output stay on `append_text()`.

Also: on stream cancellation AND on `StreamDone`, call `renderer.cleanup_pending()` and render each synthesized cancelled `ToolResult` as a unit.

## WHERE

- `src/mcp_coder/icoder/ui/app.py` — main migration site
- `src/mcp_coder/icoder/ui/replay.py` — verify replay path still works (no source change expected — delegates to `_handle_stream_event` and `append_text`)
- `tests/icoder/test_app_pilot.py` — end-to-end Pilot tests
- `tests/icoder/test_replay.py` — assert replayed sessions get the same unit registrations

## WHAT

App migrations (semantic, not signature changes):

| Call site (today) | Change |
|---|---|
| `on_input_area_input_submitted`: `output.append_text(f"> {text}", style=STYLE_USER_INPUT)` | Build a `ContentUnit(kind="user_input", id=..., timestamp=now, full_text=text)` and `output.append_unit(unit, [f"> {text}"], style=STYLE_USER_INPUT)` |
| `_handle_stream_event` `TextChunk` branch: per-line `output.append_text(line)` | If no current turn unit, build `ContentUnit(kind="assistant_turn", id=..., timestamp=now, full_text="")`, `output.append_unit(turn_unit, [])`, store id in `self._current_turn_id`. For each complete line, append to `self._current_turn_text` and call `output.extend_open_unit(self._current_turn_id, [line])`. |
| `_handle_stream_event` `ToolStart` branch: `output.append_text("\n".join(lines), style=STYLE_TOOL_OUTPUT)` | Build a `ContentUnit(kind="tool", id=..., tool_name=action.display_name, args=dict(action.args), timestamp=now)`. Render compressed-block lines via the helper from step 6 (or the tier-aware path). `output.append_unit(unit, lines, style=STYLE_TOOL_OUTPUT)`. Store id keyed by raw tool name into `self._open_tool_units: dict[str, str]` so `ToolResult` can find the matching unit. **Tool starts do NOT finalize the open turn** — the turn stays multi-range. |
| `_handle_stream_event` `ToolResult` branch | Pop matching tool unit id from `self._open_tool_units` (positional FIFO matching the renderer's). Build an updated `ContentUnit` with `output`, `duration_ms`, `is_error`, `full_text`. **Issue**: `ContentUnit` is frozen — instead, store mutable result fields in a separate dict keyed by unit_id, OR re-register the unit (replace in `_units`). Recommended: use `dataclasses.replace` to build a new `ContentUnit` and write back to `output._units[unit_id]` (private access OK from sibling module; alternatively add `output.update_unit(unit_id, **fields)` helper). Then call `output.extend_open_unit(unit_id, body_lines, style=STYLE_TOOL_OUTPUT)` for the result body. |
| `_handle_stream_event` `StreamDone` | If `self._current_turn_id`: `output.finalize_open_unit(self._current_turn_id)`; clear `_current_turn_id` and `_current_turn_text`. Call `self._renderer.cleanup_pending()` — render each synthesized cancelled `ToolResult` as a unit via `output.append_unit(...)`. |
| `_stream_llm` cancel path (finally block when `_cancel_event.is_set()`) | Same orphan cleanup as `StreamDone` — call `self._renderer.cleanup_pending()` and render the synthesized cancelled tool units BEFORE the cancelled marker. |

Helper added to `OutputLog`:

```python
def update_unit(self, unit_id: str, **fields: Any) -> ContentUnit:
    """Replace the ContentUnit with the given id by applying fields via dataclasses.replace.
    Does NOT trigger rebuild (caller should call rebuild() or extend_open_unit afterwards).
    """
```

App state additions:

```python
self._current_turn_id: str | None = None
self._open_tool_units: deque[str] = deque()      # FIFO of tool unit ids per turn
self._unit_counter: int = 0                       # for id generation
```

Helper:

```python
def _new_unit_id(self, kind: str) -> str:
    self._unit_counter += 1
    return f"{kind}_{self._unit_counter}"
```

## HOW

- **Tool ↔ assistant_turn interleaving**: a tool firing mid-turn does NOT call `finalize_open_unit` on the turn. The turn's `_current_turn_id` stays set. Subsequent text-deltas continue extending the same turn via `extend_open_unit`. Tool units sit between turn's range entries in `_script` and `_ranges`.
- **Turn finalization timing**: turn finalizes on `StreamDone`. On cancel: also finalize (with whatever text accumulated). The cancelled marker stays on `append_text` (it's not a unit).
- **`full_text` for assistant_turn**: accumulate in `self._current_turn_text`. On `StreamDone` / cancel, write final value via `update_unit(turn_id, full_text=accumulated)` BEFORE finalize.
- **Replay**: `replay.py` calls `app._handle_stream_event(payload, replay_mode=True)`. Since `_handle_stream_event` now goes through `append_unit`, replay automatically registers units. **However**, `replay.py` writes user inputs directly with `append_text(f"> {text}", style=STYLE_USER_INPUT)` (line ~41). Migrate that to the same `append_unit(ContentUnit(kind="user_input", ...))` path. Slash-command output (`output_emitted` event → `append_text(text)`) stays on `append_text`.

## ALGORITHM (turn lifecycle)

```
text_chunk arrives:
    if self._current_turn_id is None:
        turn_id = self._new_unit_id("turn")
        unit = ContentUnit(id=turn_id, kind="assistant_turn", timestamp=now(), full_text="")
        output.append_unit(unit, [])
        self._current_turn_id = turn_id
        self._current_turn_text = ""
    self._text_buffer += chunk.text
    lines = self._text_buffer.split("\n")
    for line in lines[:-1]:
        self._current_turn_text += line + "\n"
        output.extend_open_unit(self._current_turn_id, [line])
    self._text_buffer = lines[-1]

stream_done arrives:
    flush_buffer()           # writes any remaining buffer as the last turn line
    if self._current_turn_id:
        output.update_unit(self._current_turn_id, full_text=self._current_turn_text)
        output.finalize_open_unit(self._current_turn_id)
        self._current_turn_id = None
        self._current_turn_text = ""
    for cancelled in self._renderer.cleanup_pending():
        # render as a normal tool result for an orphan unit
        # (the unit was already created at tool_use_start time and never resolved)
        unit_id = self._open_tool_units.popleft() if self._open_tool_units else None
        if unit_id:
            output.update_unit(unit_id, output="(cancelled)", duration_ms=None, is_error=True, full_text="(cancelled)")
            output.extend_open_unit(unit_id, ["│  (cancelled)", "└ cancelled"], style=STYLE_TOOL_OUTPUT)
    self._open_tool_units.clear()
```

## DATA

- `_current_turn_id: str | None` — set when a turn is in progress.
- `_open_tool_units: deque[str]` — FIFO of open tool unit ids matching the renderer's FIFO.
- Synthesized cancelled units share the same `unit_id` as the original `ToolStart` unit (so existing range stays valid).

## TDD

Pilot tests in `tests/icoder/test_app_pilot.py` (extend existing file):

1. `test_user_input_creates_clickable_unit` — type input → output has a `user_input` unit at the input's line.
2. `test_tool_block_creates_clickable_unit` — feed a fake `ToolStart` + `ToolResult` stream event → output has one `tool` unit covering all the tool's lines.
3. `test_assistant_text_creates_clickable_turn` — feed text_delta events → turn unit covers the text lines.
4. `test_tool_inside_turn_keeps_turn_open` — text, tool, text → turn unit has multiple range entries, tool unit sits between them; `last_unit()` returns the tool while inside, then turn after streaming continues, then back to turn after StreamDone (depending on final event order).
5. `test_cancel_synthesizes_cancelled_tool_unit` — start a tool, cancel before result arrives → tool unit's stored output is `(cancelled)`, `is_error=True`, `duration_ms=None`; visible in compressed render as `└ cancelled`.
6. `test_stream_done_clears_renderer_fifo` — after StreamDone, calling renderer.cleanup_pending() again returns `[]`.
7. `test_banner_stays_on_append_text` — startup banner appears in `recorded_lines` but `unit_at_line(0)` returns `None` for banner lines.
8. `test_resumed_divider_is_not_a_unit` — trigger a resume; dim "Resumed" line not registered.

Replay tests in `tests/icoder/test_replay.py`:

9. `test_replay_user_input_creates_unit` — replay a log containing `input_received` → unit registered after replay.
10. `test_replay_tool_creates_unit` — replay a log with stream events → tool unit registered.

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green. Snapshot tests for `test_app_pilot.py` and `test_snapshots.py` may need re-baselining: if rendered output is byte-identical, snapshots pass; otherwise regenerate.

## LLM Prompt

> Implement **Step 9** from `pr_info/steps/step_9.md` (App migration to `append_unit` flow).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Banners, blank spacers, runtime info, "Resumed" divider, cancelled marker, error message, slash-command `OutputText` action — all stay on `append_text()`.
> - Tool blocks, user input, assistant turn streams — migrate to `append_unit` / `extend_open_unit` / `finalize_open_unit`.
> - A tool firing mid-turn does NOT finalize the turn. The turn remains "open" with interleaved tool units inside its range list.
> - `_text_buffer` stays on `ICoderApp` (matches current pattern). Extend turn with complete lines only.
> - Orphan cleanup on cancel AND on `StreamDone`: call `renderer.cleanup_pending()`; for each synthesized `ToolResult`, locate the corresponding open tool unit (FIFO matched) and update its fields + render `(cancelled)` body.
> - `OutputLog.update_unit(unit_id, **fields)` helper added in this step.
> - `replay.py` migration: user-input write goes through `append_unit` (was `append_text`). Slash-command output stays on `append_text`.
> - TDD: 10 Pilot/replay test cases first, then implement.
>
> All three quality gates green after the change. Re-baseline snapshots if and only if rendered content actually changed.
