# Issue #820: Generic Tool Output Rendering with Compact/Full Modes

## Problem
Tool call outputs in the iCoder TUI are hard to read:
- Escaped diffs render as walls of `\n` and `\\` on a single line
- Long arg values (edits arrays, file content) dumped inline create 500+ char header lines
- No separation between input args and result body
- No compact vs full mode switching

## Architectural / Design Changes

### 1. Generic rendering replaces tool-specific field filtering
**Before:** `_render_tool_output()` uses `_ENVELOPE_FIELDS` (type, role, model, etc.) and `_MAIN_CONTENT_KEYS` (result, text, content) to filter and prioritize fields. This is tool-aware logic.
**After:** Only unwrap `{"result": ...}` envelope. All other content rendered generically via `_render_output_value()` — a single recursive function that pretty-prints any JSON structure and splits multiline strings into actual lines. No field filtering, no special-case logic.

### 2. Length-based inline/block decision replaces arg-count heuristic
**Before:** `_INLINE_ARG_LIMIT = 2` — args go inline if ≤2 keys, block otherwise. This causes short 3-arg calls to use block format unnecessarily.
**After:** `_MAX_INLINE_LEN = 100` — args go inline when the full header line fits in 100 chars, block otherwise. Same threshold for both compact and full modes.

### 3. ToolStart carries raw args instead of pre-formatted strings
**Before:** `ToolStart` has `inline_args: str | None` and `block_args: list[tuple[str, str]]` — formatting decisions baked into the dataclass at creation time.
**After:** `ToolStart` has `args: dict` — raw args dict. A new public `format_tool_start(action, full=False) -> list[str]` function formats on demand, enabling future mode toggling without replaying stream events.

### 4. Separator `├──` moves from app.py into format_tool_start()
**Before:** app.py doesn't render a separator between args and output.
**After:** `format_tool_start()` appends `├──` as its last line (when args are present), keeping display logic in the renderer module.

### 5. Compact/full mode support via `full` parameter
**Before:** No mode concept — one rendering path.
**After:** `_render_tool_output(output, full=False)` and `format_tool_start(action, full=False)` accept `full` at call time. Compact mode: summarized args + truncated output (10 head + 5 tail). Full mode: expanded args + no truncation. Initial integration uses compact only.

## Files Modified

| File | Steps | Change |
|------|-------|--------|
| `src/mcp_coder/llm/formatting/stream_renderer.py` | 1, 2, 3 | New helpers, rewritten output rendering, `format_tool_start()` |
| `src/mcp_coder/llm/formatting/render_actions.py` | 3 | `ToolStart` dataclass: `args: dict` replaces inline/block fields |
| `src/mcp_coder/icoder/ui/app.py` | 3 | Use `format_tool_start()`, remove manual inline/block logic |
| `tests/llm/formatting/test_stream_renderer.py` | 1, 2, 3 | Tests added/rewritten for new behavior |

## Files/Folders Deleted

| Path | Step | Reason |
|------|------|--------|
| `testdata/` (entire folder) | 4 | Expectations migrated into unit tests; scripts no longer needed |

## Implementation Steps Overview

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add rendering helper functions + tests | Pure additions, no breaking changes |
| 2 | Rewrite `_render_tool_output()` + tests | Remove field filtering, add `full` param |
| 3 | ToolStart raw args + `format_tool_start()` + app.py | Dataclass change cascades to producer and consumer |
| 4 | Delete `testdata/` folder | Cleanup |
