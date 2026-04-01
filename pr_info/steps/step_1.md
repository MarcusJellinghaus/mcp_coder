# Step 1: Create render_actions.py + stream_renderer.py with tests

## Context
See `pr_info/steps/summary.md` for full issue context and architecture.

This step creates the two new modules and their tests. Nothing is modified yet — existing code continues to work as before.

## LLM Prompt
> Implement Step 1 of issue #680. Read `pr_info/steps/summary.md` for context, then read this step file fully. Create the render_actions dataclasses, the StreamEventRenderer class (moving helper logic from formatters.py), and comprehensive tests. Do not modify any existing files in this step.

---

## Part A: render_actions.py

### WHERE
`src/mcp_coder/llm/formatting/render_actions.py` (~35 lines)

### WHAT
Five frozen dataclasses — the renderer's output vocabulary:

```python
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
    output_lines: list[str]  # Truncated display lines
    total_lines: int         # Original line count
    truncated: bool          # total_lines > limit

@dataclass(frozen=True)
class ErrorMessage:
    message: str

@dataclass(frozen=True)
class StreamDone:
    pass
```

### DATA
- `ToolStart.block_args` uses `list[tuple[str, str]]` not `dict` — frozen dataclass can't hold mutable dict
- `ToolStart.inline_args` is `None` when args count > `_INLINE_ARG_LIMIT` (2)
- `ToolResult.output_lines` may be shorter than `total_lines` when truncated

### NOTE
- `ToolResult` has no `name` field — iCoder tracks last `ToolStart.display_name` itself
- All dataclasses are frozen (immutable) for safety

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
- Helpers are **copies** of the logic from `formatters.py` (they'll be removed from formatters in step 2)

### ALGORITHM for `render()`
```
event_type = event.get("type")
if text_delta  → return TextChunk(text)
if tool_use_start → format name/args → return ToolStart(...)
if tool_result → render output lines → return ToolResult(...)
if error → return ErrorMessage(message)
if done → return StreamDone()
else → return None
```

### DATA
- `render()` returns `RenderAction | None` where `RenderAction` is the union type of all 5 dataclasses
- Returns `None` for unknown event types (e.g., `raw_line`)
- `ToolStart`: when args is dict with ≤2 keys → `inline_args` set, `block_args` empty; otherwise → `inline_args` is None, `block_args` populated

---

## Part C: Tests

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

# ToolResult
render({"type": "tool_result", "output": "line1\nline2"})
→ ToolResult(output_lines=["line1", "line2"], total_lines=2, truncated=False)

# ToolResult truncated (>5 lines)
render({"type": "tool_result", "output": "\n".join(f"line {i}" for i in range(10))})
→ ToolResult(output_lines=[5 lines], total_lines=10, truncated=True)

# ErrorMessage
render({"type": "error", "message": "fail"}) → ErrorMessage("fail")

# StreamDone
render({"type": "done"}) → StreamDone()

# Unknown
render({"type": "raw_line", "line": "..."}) → None
```

---

## Commit
One commit: "refactor(formatting): add StreamEventRenderer and render action dataclasses"
