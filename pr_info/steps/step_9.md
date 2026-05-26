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
| `_handle_stream_event` `ToolStart` branch: `output.append_text("\n".join(lines), style=STYLE_TOOL_OUTPUT)` | Build a `ContentUnit(kind="tool", id=..., tool_name=action.display_name, args=dict(action.args), timestamp=now)`. `output.append_unit(unit, start_lines, style=STYLE_TOOL_OUTPUT)` where `start_lines` is `format_tool_start(action)` (no body yet — `unit.output` is `None`). Append the new unit_id to `self._open_tool_units.setdefault(raw_name, deque())` so `ToolResult` can find the matching unit by raw name. **Tool starts do NOT finalize the open turn** — the turn stays multi-range. |
| `_handle_stream_event` `ToolResult` branch | Look up the per-name FIFO `self._open_tool_units.get(result.raw_name)` and `popleft()` the matching unit id. Compute the pre-rendered triple via `_render_tool_output(raw_output, format_tools=self._core.format_tools, full=False)` and call `output.update_unit_and_rerender(unit_id, output=raw_output, output_lines=tuple(output_lines), total_lines=total_lines, truncated=truncated, duration_ms=result.duration_ms, is_error=result.is_error)`. The full untruncated `raw_output` is stored on `ContentUnit.output` for the modal; the truncated triple drives tier-2 rendering. The atomic render path (step 6's `_render_unit_atomic`) reads the triple — no separate `extend_open_unit` call. |
| `_handle_stream_event` `StreamDone` | If `self._current_turn_id`: `output.finalize_open_unit(self._current_turn_id)`; clear `_current_turn_id` and `_current_turn_text`. Call `self._renderer.cleanup_pending()` — for each synthesized cancelled `ToolResult`, locate the matching open tool unit_id via the per-name FIFO and call `output.update_unit_and_rerender(unit_id, output="(cancelled)", duration_ms=None, is_error=True, full_text="(cancelled)")`. Then **soft-assert** the deques in `self._open_tool_units`: WARN-log any non-empty remainders before clearing (see "soft-assert" block below). |
| `_stream_llm` cancel path (finally block when `_cancel_event.is_set()`) | Same orphan cleanup as `StreamDone` — call `self._renderer.cleanup_pending()` and update synthesized cancelled tool units BEFORE the cancelled marker. |

`OutputLog.update_unit_and_rerender(unit_id, **fields)` is the helper (defined in step 5) used here for mutating tool result fields and triggering the rerender. No new helper added in this step.

App state additions:

```python
self._current_turn_id: str | None = None
self._open_tool_units: dict[str, deque[str]] = {}   # raw tool name → FIFO of open unit ids
self._unit_counter: int = 0                          # for id generation
```

The per-name FIFO mirrors the renderer's `_pending` FIFO (step 4) — positional matching within a name.

Helper:

```python
def _new_unit_id(self, kind: str) -> str:
    self._unit_counter += 1
    return f"{kind}_{self._unit_counter}"
```

## HOW

- **Tool result pre-rendered triple**: compute once at `tool_result` time and persist on the unit:

  ```python
  output_lines, total_lines, truncated = _render_tool_output(
      raw_output, format_tools=self._core.format_tools, full=False
  )
  output.update_unit_and_rerender(
      unit_id,
      output=raw_output,
      output_lines=tuple(output_lines),
      total_lines=total_lines,
      truncated=truncated,
      duration_ms=result.duration_ms,
      is_error=result.is_error,
  )
  ```

  The full `raw_output` string is preserved on `ContentUnit.output` for the modal (tier 3); the truncated triple is computed once here and read by `_render_unit_atomic` for tier 2. **No `format_tools` plumbing into `OutputLog`** — that flag lives on `AppCore`/`ICoderApp`, accessed only at write time. For the modal (step 7), use `unit.output` directly (full untruncated text), NOT `unit.output_lines`.

- **Tool ↔ assistant_turn interleaving**: a tool firing mid-turn does NOT call `finalize_open_unit` on the turn. The turn's `_current_turn_id` stays set. Subsequent text-deltas continue extending the same turn via `extend_open_unit`. Tool units sit between turn's range entries in `_script` and `_ranges`.
- **Turn finalization timing**: turn finalizes on `StreamDone`. On cancel: also finalize (with whatever text accumulated). The cancelled marker stays on `append_text` (it's not a unit).
- **`full_text` for assistant_turn**: accumulate in `self._current_turn_text`. On `StreamDone` / cancel, write final value via `update_unit_and_rerender(turn_id, full_text=accumulated)` BEFORE finalize. (For turns this triggers a rerender, but only the `full_text` field changed and turn rendering does not use it — accept the harmless extra work, or guard with a `rebuild=False` flag if perf measurement warrants it later.)
- **Per-tool-name FIFO matching**: `self._open_tool_units` is keyed by raw tool name. On `tool_use_start`: `self._open_tool_units.setdefault(name, deque()).append(unit_id)`. On `tool_result`: `self._open_tool_units[name].popleft()`. On orphan cleanup: iterate all deques. This mirrors the renderer's per-name positional matching from step 4.
- **Replay**: `replay.py` calls `app._handle_stream_event(payload, replay_mode=True)`. Since `_handle_stream_event` now goes through `append_unit`, replay automatically registers units. **However**, `replay.py` writes user inputs directly with `append_text(f"> {text}", style=STYLE_USER_INPUT)` (line ~41). Migrate that to the same `append_unit(ContentUnit(kind="user_input", ...))` path. Slash-command output (`output_emitted` event → `append_text(text)`) stays on `append_text`.
- **Replay timestamps**: replayed `ContentUnit.timestamp` is computed as `session_start_time + timedelta(seconds=event["t"])` (using the event's relative timestamp). This is approximate and reflects original event ordering, not wall-clock precision. Document the approximation in `replay.py`.

### Cancel path ordering

Inside `_stream_llm`'s `finally` block on cancellation, the sequence is strict:

1. `_flush_buffer()` (existing) — flushes any pending assistant text in `_text_buffer`.
2. `finalize_turn()` (existing / extend) — closes the current assistant turn unit if any (`update_unit_and_rerender(turn_id, full_text=accumulated)` then `finalize_open_unit`).
3. `cancelled_results = self._renderer.cleanup_pending()` — synthesize cancelled `ToolResult`s for orphans.
4. For each `cancelled` in `cancelled_results`:
   ```
   dq = self._open_tool_units.get(cancelled.raw_name)
   unit_id = dq.popleft() if dq else None
   if unit_id:
       output.update_unit_and_rerender(
           unit_id,
           output="(cancelled)",
           output_lines=("(cancelled)",),
           total_lines=1,
           truncated=False,
           duration_ms=None,
           is_error=True,
       )
   ```
5. `_append_cancelled_marker()` (existing) — writes the "(cancelled)" marker via `append_text`.
6. `reset_busy()` (existing) — clears the busy indicator.
7. blank line (existing).

**Ordering rationale:** the cancelled marker (step 5) comes AFTER orphan-unit updates (step 4) so the user sees "tool block updated to cancelled, then the cancellation marker line" rather than the marker appearing above an in-flight tool block that gets retroactively patched.

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
        output.update_unit_and_rerender(self._current_turn_id, full_text=self._current_turn_text)
        output.finalize_open_unit(self._current_turn_id)
        self._current_turn_id = None
        self._current_turn_text = ""
    for cancelled in self._renderer.cleanup_pending():
        # locate the original open tool unit for this name and update it
        # (the unit was already created at tool_use_start time and never resolved)
        deque_for_name = self._open_tool_units.get(cancelled.raw_name)
        if deque_for_name:
            unit_id = deque_for_name.popleft()
            output.update_unit_and_rerender(
                unit_id,
                output="(cancelled)",
                output_lines=("(cancelled)",),
                total_lines=1,
                truncated=False,
                duration_ms=None,
                is_error=True,
                full_text="(cancelled)",
            )
    # soft-assert: warn (do not silently clear) any orphan deques remaining after cleanup
    import logging
    log = logging.getLogger(__name__)
    for raw_name, dq in self._open_tool_units.items():
        if dq:
            log.warning(
                "FIFO desync: %d open tool units remain for %s after cleanup",
                len(dq), raw_name,
            )
            dq.clear()
```

**Rationale (soft-assert vs. silent sweep):** silently clearing remaining deques can hide FIFO desync bugs (renderer's `_pending` and the app's `_open_tool_units` falling out of sync). A WARN log surfaces those bugs in production while keeping the recovery behavior identical (the deques still get cleared).

## DATA

- `_current_turn_id: str | None` — set when a turn is in progress.
- `_open_tool_units: dict[str, deque[str]]` — keyed by raw tool name; each deque is a FIFO of open tool unit ids for that name. Mirrors the renderer's per-name FIFO.
- Synthesized cancelled units share the same `unit_id` as the original `ToolStart` unit (so existing range stays valid; `update_unit_and_rerender` mutates fields in place).
- Replayed unit timestamps: `session_start_time + timedelta(seconds=event["t"])` — approximate, reflects event ordering, not wall-clock precision.

## TDD

Pilot tests in `tests/icoder/test_app_pilot.py` (extend existing file):

1. `test_user_input_creates_clickable_unit` — type input → output has a `user_input` unit at the input's line.
2. `test_tool_block_creates_clickable_unit` — feed a fake `ToolStart` + `ToolResult` stream event → output has one `tool` unit covering all the tool's lines.
3. `test_assistant_text_creates_clickable_turn` — feed text_delta events → turn unit covers the text lines.
4. `test_last_unit_returns_most_recent_inserted_unit_dict_order` — When an assistant turn streams text, then a tool fires mid-turn, `last_unit()` returns the tool unit. Subsequent `extend_open_unit` calls on the turn do NOT change which unit `last_unit()` returns — dict insertion order is monotonic. Once a new unit is appended, `last_unit()` updates to that. This locks F2 / "most recent content" to the most-recently-registered unit, matching the documented semantics in summary.md. (Also asserts the turn unit has multiple range entries with the tool unit sitting between them.)
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
> - Tools are atomic: `append_unit(tool_unit, start_lines)` on `tool_use_start`; `update_unit_and_rerender(unit_id, output=..., ...)` on `tool_result`. NEVER call `extend_open_unit` on a tool unit (it raises in step 5).
> - A tool firing mid-turn does NOT finalize the turn. The turn remains "open" with interleaved tool units inside its range list.
> - `_text_buffer` stays on `ICoderApp` (matches current pattern). Extend turn with complete lines only.
> - `_open_tool_units` is `dict[str, deque[str]]` (per raw tool name). `setdefault(name, deque()).append(uid)` on start; `popleft()` on result.
> - Orphan cleanup on cancel AND on `StreamDone`: call `renderer.cleanup_pending()`; for each synthesized `ToolResult`, locate the corresponding open tool unit via `self._open_tool_units.get(cancelled.raw_name)` and `update_unit_and_rerender` it with `output="(cancelled)"`, `is_error=True`. The live `tool_result` branch uses `self._open_tool_units.get(result.raw_name)` analogously — both keyed by raw name (not the display name).
> - `OutputLog.update_unit_and_rerender` was added in step 5 — reuse here.
> - `replay.py` migration: user-input write goes through `append_unit` (was `append_text`). Slash-command output stays on `append_text`. Replayed timestamps: `session_start_time + timedelta(seconds=event["t"])` (approximate).
> - TDD: 10 Pilot/replay test cases first, then implement.
>
> All three quality gates green after the change. Re-baseline snapshots if and only if rendered content actually changed.

## Performance note

Every `tool_result` event triggers a full `rebuild()` via `update_unit_and_rerender`. For sessions with many tool calls, this is O(n) re-renders across the lifetime of a turn. **Accepted for v1** — the rebuild walks an in-memory script and writes to a `RichLog` buffer; concrete cost should be measured in practice before optimizing.

If profiling later shows this is hot, `update_unit_and_rerender` can grow a `rerender: bool = True` flag so the cancel path (which updates many units in a tight loop) batches mutations and rebuilds once at the end:

```python
for cancelled in cancelled_results:
    output.update_unit_and_rerender(unit_id, ..., rerender=False)
output.rebuild()
```

No change to the live `tool_result` path required — that's one update per result, which is already the natural rebuild cadence.
