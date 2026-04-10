# Issue #752: iCoder Busy Indicator with Spinner and Tool Status

## Goal

Add a visible busy indicator to iCoder that shows an animated spinner while the LLM is processing, displays which tool is currently running, shows elapsed time, and resets to `✓ Ready` when idle or on error.

## Architectural / Design Changes

### New Widget: `BusyIndicator`

- **File**: `src/mcp_coder/icoder/ui/widgets/busy_indicator.py`
- **Type**: `Static` subclass (consistent with `#streaming-tail` and `#input-hint` patterns already in the app)
- **Responsibility**: Encapsulates spinner animation, elapsed time tracking, and status text — no external timer management needed
- **Public API**: Two methods only — `show_busy(message: str)` and `show_ready()`
- **Timer strategy**: Single `set_interval(0.15)` created on mount, always running. Callback no-ops when idle. This avoids timer lifecycle complexity (start/stop/leak risks).

### Layout Change

The widget is inserted in `compose()` between `CommandAutocomplete` and `InputArea`:

```
OutputLog
#streaming-tail
CommandAutocomplete
BusyIndicator          ← NEW
InputArea
#input-hint
```

### Wiring in `app.py`

Three call sites in `_handle_stream_event()` and one in the `_stream_llm()` error path:

| Event | Call |
|-------|------|
| `TextChunk` (first text) | `indicator.show_busy("Thinking...")` |
| `ToolStart` | `indicator.show_busy(action.display_name)` |
| `StreamDone` | `indicator.show_ready()` |
| Exception in `_stream_llm` | `indicator.show_ready()` |

`action.display_name` is already formatted by `_format_tool_name` in `stream_renderer.py` (e.g. `workspace > read_file`). No re-formatting needed.

### CSS Addition

4 lines added to `styles.py`: 1-line height, dim color, matching background.

### Snapshot Impact

All 8 existing SVG snapshots in `tests/icoder/__snapshots__/` will change because the new widget adds a row to the layout. Regenerated in the final step.

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/icoder/ui/widgets/busy_indicator.py` | `BusyIndicator` widget |
| `tests/icoder/test_busy_indicator.py` | Unit + integration tests |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/styles.py` | CSS for `BusyIndicator` |
| `src/mcp_coder/icoder/ui/app.py` | Import, compose, wire events |
| `tests/icoder/__snapshots__/*.svg` (8 files) | Regenerated baselines |

## Design Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Spinner chars | `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` | Compact, modern, good Unicode support |
| Timer | Always-running `set_interval(0.15)` | Simplest lifecycle — no start/stop/leak risks |
| Public API | 2 methods: `show_busy`, `show_ready` | KISS — caller passes message string, widget doesn't care about event types |
| Duration | `[3.2s]` while busy only | Useful feedback; no duration shown in idle state |
| Idle text | `✓ Ready` from app launch | Always visible — no layout shift |
| Thread safety | Natural — `call_from_thread()` + UI-thread timer | No extra synchronization needed |
