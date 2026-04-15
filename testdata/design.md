# Issue #820 — iCoder Tool Output Formatting

## Problem

Tool call outputs in the iCoder TUI are hard to read:
- Diff strings render as escaped walls of `\n` and `\\` on a single line
- Long arg values (edits, file content) are dumped inline in the header
- No visual separation between input args and output
- JSON lists show brackets and quotes unnecessarily
- Hard to tell at a glance whether a tool succeeded or what it did

## Design Decisions

### Generic rendering — no tool-specific logic

All formatting is generic. No special cases for `edit_file`, `search_files`, etc.
Tool-specific field filtering (e.g. hiding `match_results`) can be added later
via a config file, but is not part of this change.

### Two display modes

- **Compact** (default): summarized args + truncated output (16 lines max)
- **Full** (for review): expanded args + full output (no truncation)

### Agreed changes

| # | Change | Description |
|---|--------|-------------|
| 1 | Inline/block args | Inline when total header line ≤120 chars, in both modes. Block otherwise. |
| 2 | Two arg modes | Compact: summarize long values (`(4 items)`, `(425 chars)`). Full: expand with `json.dumps(indent=2)` or splitlines. Both modes use inline for short args — full only differs when values are too long. |
| 3 | Separator | `├──` line between args and output. |
| 4 | Multiline strings | String values containing `\n` are split into actual lines, not escaped. This is the key generic rule that fixes diffs. |
| 5 | No field filtering | All fields from the tool result are shown. Standard JSON pretty-print. |
| 6 | List rendering | Inline JSON if ≤120 chars, `json.dumps(indent=2)` otherwise. |
| 7 | No tool-specific logic | Same renderer for all MCP tools. |
| 8 | Footer unchanged | `└ done` or `└ done (N lines, truncated to M)`. |
| 9 | Separator skipped | No `├──` when the tool has no args. |
| 10 | Truncation per mode | Compact: 10 head + 5 tail = 16 lines max. Full: no truncation. For short tool calls, compact and full produce identical output. |

### Block structure

```
┌ server > tool_name(arg1='short', arg2='short')   ← inline args (compact, fits in 120 chars)
├──                                                  ← separator
│  output line 1                                     ← result body
│  output line 2
└ done

┌ server > tool_name                                 ← block args (too long for inline)
│  arg1: 'value'
│  arg2: (425 chars)                                 ← compact: summarized
├──
│  output line 1
│  ... (N lines skipped)                             ← compact: truncation
│  output line last
└ done (total lines, truncated to 16)

┌ server > tool_name                                 ← full mode
│  arg1: 'value'
│  arg2:                                             ← full: expanded
│    line 1 of value
│    line 2 of value
├──
│  output line 1                                     ← full: no truncation
│  output line 2
│  ...all lines...
│  output line last
└ done
```

## Files

- `render_testdata.py` — renders `_raw.txt` files using current iCoder code
- `render_nice.py` — renders `_nice_compact.txt` and `_nice_full.txt` with target formatting
- `tool_*.json` — raw tool call + result pairs extracted from MLflow artifacts
- `*_raw.txt` — current rendering (before)
- `*_nice_compact.txt` — target compact rendering (after)
- `*_nice_full.txt` — target full rendering (after)

## Implementation scope

The changes affect two places in the codebase:

1. **`src/mcp_coder/llm/formatting/stream_renderer.py`** — `_render_tool_output()` and `StreamEventRenderer.render()` for ToolStart arg formatting
2. **`src/mcp_coder/icoder/ui/app.py`** — `_handle_stream_event()` for the `├──` separator and mode switching

The `render_actions.py` dataclasses may need a `full` flag or the mode can be passed to the renderer at construction time (like the existing `format_tools` flag).
