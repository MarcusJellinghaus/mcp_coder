# Issue #846: Show 'Thinking about [tool]...' in busy indicator after tool result

## Problem

After a tool completes (`ToolResult` rendered), the busy indicator still shows the tool's name from the prior `ToolStart`. There's no visual transition indicating the LLM is now processing the result. The indicator stays stale until the next stream event arrives.

## Solution

Add a single line in `_handle_stream_event()` to update the busy indicator immediately after rendering `ToolResult` output.

## Architectural / Design Changes

**None.** This is a one-line behavioral change within the existing event handling flow. No new classes, modules, patterns, or data structures are introduced. The existing `BusyIndicator.show_busy()` API and `ToolResult.name` field are used as-is.

**Flow change (before):**
```
ToolStart → BusyIndicator shows tool name
ToolResult → output rendered (indicator unchanged, still shows tool name)
TextChunk → BusyIndicator shows "Thinking..."
```

**Flow change (after):**
```
ToolStart → BusyIndicator shows tool name
ToolResult → output rendered → BusyIndicator shows "Thinking about workspace > read_file..."
TextChunk → BusyIndicator shows "Thinking..."
```

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | Add `show_busy()` call after `ToolResult` rendering |
| `tests/icoder/ui/test_app.py` | Add test verifying busy indicator text after `ToolResult` |

## Implementation Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | Add test + implementation for busy indicator update after ToolResult |
