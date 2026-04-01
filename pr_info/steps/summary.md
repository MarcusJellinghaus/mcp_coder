# Issue #680: Shared StreamEventRenderer for iCoder and CLI prompt

## Summary

Extract formatting helpers from `formatters.py` into a shared `StreamEventRenderer` class that produces typed dataclasses (`RenderAction`). Both iCoder (primary consumer) and the CLI `prompt` command's "rendered" format (secondary) use the same renderer, each doing `isinstance` dispatch to render to its own target.

## Architecture / Design Changes

### Before
```
StreamEvent → formatters.py (private helpers, print directly to stdout)
StreamEvent → app.py (raw MCP names, no truncation, no JSON expansion)
```
- Formatting logic locked inside `formatters.py` as private functions
- iCoder duplicates event handling with inferior formatting
- `append_tool_use()` in `output_log.py` formats as `⚙ name(args) → result`

### After
```
StreamEvent → StreamEventRenderer.render() → RenderAction (dataclass)
                                                    │
                                       ┌────────────┴────────────┐
                                 iCoder (primary)          CLI prompt (secondary)
                                (Textual widgets)         (print to stdout)
```
- **New module**: `render_actions.py` — 5 frozen dataclasses (TextChunk, ToolStart, ToolResult, ErrorMessage, StreamDone)
- **New module**: `stream_renderer.py` — `StreamEventRenderer` class + private helpers moved from `formatters.py`
- **No UI deps in renderer**: `llm/formatting/` stays stdlib-only
- **Stateless**: `render()` is a pure function on a single event
- **Private internals**: only `StreamEventRenderer` and action types are public

### Key Design Decisions
| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Separate frozen dataclasses | Type-safe isinstance dispatch, mypy exhaustiveness |
| 2 | Module in `llm/formatting/` | Near the renderer that produces them |
| 3 | Helpers private in `stream_renderer.py` | Public API is `render()` only |
| 4 | No `name` field on `ToolResult` | iCoder tracks last ToolStart name itself; uses `└ done` pattern |
| 5 | Class with `render()` method | Room for future constructor-injected config |

## Files Created
| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/formatting/render_actions.py` | 5 frozen dataclasses (~35 lines) |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | StreamEventRenderer + private helpers (~80 lines) |
| `tests/llm/formatting/test_stream_renderer.py` | Tests for renderer and all action types |

## Files Modified
| File | Change |
|------|--------|
| `src/mcp_coder/llm/formatting/formatters.py` | Remove helpers/constants; rewrite "rendered" branch to use renderer |
| `src/mcp_coder/llm/formatting/__init__.py` | Export StreamEventRenderer + 5 action types |
| `src/mcp_coder/icoder/ui/app.py` | Rewrite `_handle_stream_event` to use renderer |
| `src/mcp_coder/icoder/ui/widgets/output_log.py` | Remove `append_tool_use()` (dead code) |
| `tests/llm/formatting/test_formatters.py` | Update imports for moved helpers |

## Implementation Steps
- **Step 1**: Create `render_actions.py` + `stream_renderer.py` with tests
- **Step 2**: Migrate `formatters.py` "rendered" branch to use renderer; fix test imports
- **Step 3**: Migrate iCoder `app.py` + remove `append_tool_use()` from `output_log.py`
- **Step 4**: Update `__init__.py` exports + final verification
