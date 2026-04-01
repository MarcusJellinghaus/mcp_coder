# Step 1: Create new modules + migrate formatters.py + update exports

## Context
See `pr_info/steps/summary.md` for full issue context and architecture.

This step creates the two new modules, migrates the "rendered" branch in `formatters.py` to use them, updates `__init__.py` exports, and fixes test imports. After this step, all CLI formatter tests pass using the new renderer.

## LLM Prompt
> Implement Step 1 of issue #680. Read `pr_info/steps/summary.md` for context, then read this step file fully. Create the render_actions dataclasses, the StreamEventRenderer class (moving helper logic from formatters.py), migrate the "rendered" branch of `print_stream_event()` to use the renderer, update `__init__.py` exports, and fix test imports. All existing tests must pass.

---

## Part A: render_actions.py

### WHERE
`src/mcp_coder/llm/formatting/render_actions.py` (~40 lines)

### WHAT
Five frozen dataclasses plus a type alias — the renderer's output vocabulary:

```python
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class TextChunk:
    text: str

@dataclass(frozen=True)
class ToolStart:
    display_name: str        # "workspace > read_file"
    raw_name: str            # "mcp__workspace__read_file"
    inline_args: str | None  # "file_path='x.py'" if ≤2 args, else None
    block_args: list[tuple[str, str]]  # [(key, json_value), ...] if >2 args

@dataclass(frozen=True)
class ToolResult:
    name: str                # Tool name for display
    output_lines: list[str]  # Truncated display lines
    total_lines: int         # Original line count
    truncated: bool          # total_lines > limit

@dataclass(frozen=True)
class ErrorMessage:
    message: str

@dataclass(frozen=True)
class StreamDone:
    pass

RenderAction = TextChunk | ToolStart | ToolResult | ErrorMessage | StreamDone
```

### DATA
- `ToolStart.block_args` uses `list[tuple[str, str]]` not `dict` — frozen dataclass can't hold mutable dict
- `ToolStart.inline_args` is `None` when args count > `_INLINE_ARG_LIMIT` (2)
- `ToolResult.output_lines` may be shorter than `total_lines` when truncated
- `ToolResult.name` carries the tool display name so consumers don't need to track ToolStart state
- `RenderAction` is the union type alias of all 5 dataclasses — export it for type annotations

---

## Part B: stream_renderer.py

### WHERE
`src/mcp_coder/llm/formatting/stream_renderer.py` (~80 lines)

### WHAT
```python
# Private constants
_TRUNCATION_LIMIT = 5
_INLINE_ARG_LIMIT = 2

# Private helpers (same logic as current formatters.py)
def _format_tool_name(name: str) -> str: ...
def _format_tool_args(args: object) -> str: ...
def _render_tool_output(output: str) -> tuple[list[str], int]: ...

# Public class
class StreamEventRenderer:
    def render(self, event: StreamEvent) -> RenderAction | None: ...
```

### HOW
- Import `StreamEvent` from `mcp_coder.llm.types`
- Import action types from `.render_actions`
- Helpers are **copies** of the logic from `formatters.py` (they'll be removed from formatters in Part C)

### ALGORITHM for `render()`
```
event_type = event.get("type")
if text_delta  → return TextChunk(text)
if tool_use_start → format name/args → return ToolStart(...)
if tool_result → render output lines → return ToolResult(name=..., ...)
if error → return ErrorMessage(message)
if done → return StreamDone()
else → return None
```

### DATA
- `render()` returns `RenderAction | None`
- Returns `None` for unknown event types (e.g., `raw_line`)
- `ToolStart`: when args is dict with ≤2 keys → `inline_args` set, `block_args` empty; otherwise → `inline_args` is None, `block_args` populated
- `ToolResult`: the `name` field comes from the `tool_result` event's `name` key (passed through from the API); use `_format_tool_name()` on it

---

## Part C: Migrate formatters.py

### WHERE
`src/mcp_coder/llm/formatting/formatters.py`

### WHAT — Remove
- Delete `_RENDERED_TRUNCATION_LIMIT` constant
- Delete `_RENDERED_INLINE_ARG_LIMIT` constant
- Delete `_render_tool_output()` function
- Delete `_format_tool_name()` function

### WHAT — Keep accessible
- **`_format_tool_args` must NOT be deleted** — it is still used by the "text" format branch (around line 419 of formatters.py). Instead, remove the local definition and add an import:
```python
from .stream_renderer import _format_tool_args
```

### WHAT — Add
```python
from .stream_renderer import StreamEventRenderer, _format_tool_args
from .render_actions import ToolStart, ToolResult, TextChunk, ErrorMessage, StreamDone
```

### WHAT — Rewrite
Rewrite the `if output_format == "rendered":` branch to:

```python
if output_format == "rendered":
    renderer = StreamEventRenderer()
    action = renderer.render(event)
    if action is None:
        return
    if isinstance(action, TextChunk):
        print(action.text, end="", file=file, flush=True)
    elif isinstance(action, ToolStart):
        if action.inline_args is not None:
            print(f"┌ {action.display_name}({action.inline_args})", file=file)
        else:
            print(f"┌ {action.display_name}", file=file)
            for key, value in action.block_args:
                print(f"│  {key}: {value}", file=file)
    elif isinstance(action, ToolResult):
        for line in action.output_lines:
            print(f"│  {line}", file=file)
        if action.truncated:
            print(f"└ done ({action.total_lines} lines, truncated to {len(action.output_lines)})", file=file)
        else:
            print("└ done", file=file)
        print(file=file)
    elif isinstance(action, ErrorMessage):
        print(action.message, file=err_file)
    elif isinstance(action, StreamDone):
        print(file=file)
    return
```

### HOW
- Renderer is instantiated per-call to `print_stream_event` — this is acceptable since it's stateless and cheap
- The "text" / "ndjson" / "json-raw" branches remain **completely unchanged**
- `_normalize_event_to_ndjson()` stays in `formatters.py` (not part of this refactor)
- The `__all__` list stays the same (public API unchanged)

---

## Part D: Update __init__.py exports

### WHERE
`src/mcp_coder/llm/formatting/__init__.py`

### WHAT
Add exports for `StreamEventRenderer`, all 5 action types, and `RenderAction`:

```python
from .render_actions import (
    ErrorMessage,
    RenderAction,
    StreamDone,
    TextChunk,
    ToolResult,
    ToolStart,
)
from .stream_renderer import StreamEventRenderer

__all__ = [
    # Existing exports (keep all)
    "format_text_response",
    "format_verbose_response",
    "format_raw_response",
    "print_stream_event",
    "is_sdk_message",
    "get_message_role",
    "get_message_tool_calls",
    "serialize_message_for_json",
    "extract_tool_interactions",
    # New exports
    "StreamEventRenderer",
    "RenderAction",
    "TextChunk",
    "ToolStart",
    "ToolResult",
    "ErrorMessage",
    "StreamDone",
]
```

### HOW
- Do NOT export private helpers (`_format_tool_name`, etc.)
- `RenderAction` type alias is exported so consumers can annotate return types

---

## Part E: Fix test imports in test_formatters.py

### WHERE
`tests/llm/formatting/test_formatters.py`

### WHAT
Update import paths:

```python
# Before
from mcp_coder.llm.formatting.formatters import (
    _format_tool_name,
    _render_tool_output,
    print_stream_event,
)

# After
from mcp_coder.llm.formatting.formatters import print_stream_event
from mcp_coder.llm.formatting.stream_renderer import (
    _format_tool_name,
    _render_tool_output,
)
```

### HOW
- `TestFormatToolName` and `TestRenderToolOutput` classes remain unchanged, just the import source changes
- All `TestRenderedStreamFormat` and `TestPrintStreamEvent` tests pass without modification (output is identical)

---

## Part F: Tests for new modules

### WHERE
`tests/llm/formatting/test_stream_renderer.py`

### WHAT
Test classes:
- `TestStreamEventRenderer` — tests `render()` for all 5 event types + None for unknown
- `TestFormatToolNameRenderer` — tests `_format_tool_name` (same cases as existing tests in test_formatters.py)
- `TestRenderToolOutputRenderer` — tests `_render_tool_output` (same cases as existing tests)

### KEY TEST CASES
```python
# TextChunk
render({"type": "text_delta", "text": "Hello"}) → TextChunk("Hello")

# ToolStart inline (≤2 args)
render({"type": "tool_use_start", "name": "mcp__workspace__read_file", "args": {"file_path": "x.py"}})
→ ToolStart(display_name="workspace > read_file", raw_name="mcp__workspace__read_file",
            inline_args="file_path='x.py'", block_args=[])

# ToolStart block (>2 args)
render({"type": "tool_use_start", "name": "mcp__workspace__edit_file",
        "args": {"file_path": "a.py", "old_text": "foo", "new_text": "bar"}})
→ ToolStart(display_name="workspace > edit_file", ..., inline_args=None,
            block_args=[("file_path", '"a.py"'), ("old_text", '"foo"'), ("new_text", '"bar"')])

# ToolResult (includes name)
render({"type": "tool_result", "name": "mcp__workspace__read_file", "output": "line1\nline2"})
→ ToolResult(name="workspace > read_file", output_lines=["line1", "line2"], total_lines=2, truncated=False)

# ToolResult truncated (>5 lines)
render({"type": "tool_result", "name": "mcp__workspace__read_file", "output": "\n".join(f"line {i}" for i in range(10))})
→ ToolResult(name="workspace > read_file", output_lines=[5 lines], total_lines=10, truncated=True)

# ErrorMessage
render({"type": "error", "message": "fail"}) → ErrorMessage("fail")

# StreamDone
render({"type": "done"}) → StreamDone()

# Unknown
render({"type": "raw_line", "line": "..."}) → None
```

---

## Verification
- All `TestRenderedStreamFormat` tests pass (exact same output as before)
- All `TestPrintStreamEvent` tests pass
- All `TestFormatToolName` and `TestRenderToolOutput` tests pass (same logic, new import path)
- New `test_stream_renderer.py` tests all pass
- pylint, mypy, pytest all green

## Commit
One commit: "refactor(formatting): add StreamEventRenderer and migrate rendered format"
