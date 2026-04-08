# Issue #735: iCoder token-per-line streaming bug + regression tests

## Problem

Every streamed `text_delta` token from the LLM becomes its own row in the `RichLog`, producing a vertical waterfall instead of readable text. `ICoderApp._handle_stream_event` calls `output.append_text(chunk)` per token, and `OutputLog.append_text` calls `RichLog.write()` which creates a new log row per call.

Existing tests never caught this because `FakeLLMService` defaults to a single `text_delta` chunk.

## Design Changes

### Before (current architecture)

```
StreamEvent → StreamEventRenderer.render() → RenderAction
    → _handle_stream_event: TextChunk → output.append_text(chunk)  [BUG: one row per token]
```

`ICoderApp.compose()` yields: `OutputLog`, `CommandAutocomplete`, `InputArea`.

### After (new architecture)

```
StreamEvent → StreamEventRenderer.render() → RenderAction
    → _handle_stream_event:
        TextChunk → append to _text_buffer, flush complete lines to RichLog,
                     update Static widget with partial line
        Non-text  → _flush_buffer() first, then handle event
```

`ICoderApp.compose()` yields: `OutputLog`, `Static(id="streaming-tail")`, `CommandAutocomplete`, `InputArea`.

### Key design decisions

| Topic | Decision |
|---|---|
| Widget | `Static(id="streaming-tail")` between `OutputLog` and `CommandAutocomplete` |
| Buffer | `self._text_buffer: str` on `ICoderApp`, flushed on any non-text event |
| Flush trigger | `StreamDone`, `ToolStart`, `ToolResult`, `ErrorMessage`, or stream exception |
| `_append_blank_line` | Kept — called from `StreamDone` success path and `except` branch after flush. |
| Error mid-line | Flush partial first, then show error (preserves information) |
| Tool mid-line | Flush partial first, then render tool block (chronological order) |

### What does NOT change

- `OutputLog` widget — unchanged
- `FakeLLMService` default response — unchanged (new tests pass explicit `responses`)
- `ToolStart`/`ToolResult`/`ErrorMessage` rendering logic — already correct (join multi-line into single `append_text`)
- `StreamEventRenderer` — unchanged

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/icoder/ui/app.py` | Add `Static` widget, `_text_buffer`, `_flush_buffer()`, rewrite `_handle_stream_event` TextChunk path, handle `StreamDone`, flush before error |
| `src/mcp_coder/icoder/ui/styles.py` | Add CSS rule for `#streaming-tail` |
| `tests/icoder/test_app_pilot.py` | Add regression tests a–h for streaming buffer behavior |
| `tests/icoder/test_snapshots.py` | Add one snapshot test (i) for multi-chunk streaming layout |
| `tests/icoder/__snapshots__/test_snapshots/*.svg` | Regenerate all baselines (new Static widget changes DOM) |

## Files NOT Modified

- `src/mcp_coder/icoder/ui/widgets/output_log.py`
- `src/mcp_coder/icoder/services/llm_service.py`
- `src/mcp_coder/llm/formatting/render_actions.py`
- `src/mcp_coder/llm/formatting/stream_renderer.py`

## Implementation Steps

1. **Step 1** — Add `Static` streaming-tail widget + CSS + `_text_buffer` + `_flush_buffer()` + rewrite `_handle_stream_event` for buffered streaming. Tests a–e (basic buffer behavior).
2. **Step 2** — Tests f–h (error/tool mid-line flush, back-to-back streams) + ensure error and tool paths flush buffer.
3. **Step 3** — Snapshot test (i) for multi-chunk streaming layout + regenerate all snapshot baselines.
