# Issue #763: iCoder — Improve Tool Display (Formatting, Truncation, Field Filtering)

## Summary

Improve how iCoder displays tool invocations and their results. Currently tool output is shown as raw JSON with escaped newlines, making it hard to read. This issue covers formatting, truncation, field filtering, and a `--no-format-tools` escape hatch.

## Architectural / Design Changes

### Design Philosophy
- **Single chokepoint**: All tool result formatting flows through `_render_tool_output()` in `stream_renderer.py`. Field filtering, truncation, and multiline display changes all land here.
- **No new dataclasses or widgets**: `ToolResult` keeps its existing fields. `OutputLog` keeps its existing interface. The renderer produces final display lines; the UI layer decides presentation (plain text vs Markdown).
- **Flag injection at construction**: `StreamEventRenderer` gains a `format_tools: bool` constructor parameter. When `False`, all new formatting is bypassed — output is identical to today.

### Data Flow (new flag)
```
CLI (--no-format-tools) → execute_icoder() → ICoderApp(format_tools=) → StreamEventRenderer(format_tools=)
                                                  ↓
                                          Markdown rendering decision
```

### Key Design Decisions
| Decision | Rationale |
|----------|-----------|
| No `ToolResult` dataclass changes | Renderer produces final `list[str]`; UI doesn't need field categories |
| No `OutputLog` widget changes | `RichLog.write()` already accepts `rich.markdown.Markdown` objects |
| `_render_tool_output()` does all restructuring | Single function owns field filtering + truncation + multiline display |
| `format_tools` stored on both `ICoderApp` and `StreamEventRenderer` | Renderer handles content logic; app handles Markdown rendering |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Add `--no-format-tools` flag to icoder parser |
| `src/mcp_coder/cli/commands/icoder.py` | Read flag, pass `format_tools` to `ICoderApp` |
| `src/mcp_coder/icoder/ui/app.py` | Accept `format_tools`, pass to renderer, use Markdown rendering |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | `format_tools` on renderer; field filtering; head/tail truncation |
| `src/mcp_coder/icoder/ui/widgets/output_log.py` | Override `write()` to record text for testing |
| `tests/icoder/test_cli_icoder.py` | Test `--no-format-tools` flag parsing and threading |
| `tests/llm/formatting/test_stream_renderer.py` | Test field filtering, head/tail truncation, `format_tools=False` bypass |

## Files NOT Modified

- `src/mcp_coder/llm/formatting/render_actions.py` — `ToolResult` dataclass unchanged
- `.importlinter` — no new cross-layer imports needed

## Implementation Steps

1. **Step 1** — `--no-format-tools` CLI flag + plumbing (parsers → execute_icoder → ICoderApp → StreamEventRenderer)
2. **Step 2** — Field filtering and head/tail truncation in `_render_tool_output()`
3. **Step 3** — Markdown rendering in `ICoderApp._handle_stream_event()`
