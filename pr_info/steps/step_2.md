# Step 2: Migrate formatters.py "rendered" branch to use StreamEventRenderer

## Context
See `pr_info/steps/summary.md` for full issue context and architecture.

Step 1 created the new modules. This step wires the CLI "rendered" format to use the renderer and removes the now-duplicated helpers from `formatters.py`. Existing tests must continue to pass.

## LLM Prompt
> Implement Step 2 of issue #680. Read `pr_info/steps/summary.md` and this step file fully. Migrate the "rendered" branch of `print_stream_event()` in `formatters.py` to use `StreamEventRenderer`, remove the old helpers, and fix test imports. All existing tests must pass.

---

## Part A: Modify formatters.py

### WHERE
`src/mcp_coder/llm/formatting/formatters.py`

### WHAT — Remove
- Delete `_RENDERED_TRUNCATION_LIMIT` constant
- Delete `_RENDERED_INLINE_ARG_LIMIT` constant
- Delete `_render_tool_output()` function
- Delete `_format_tool_name()` function
- Delete `_format_tool_args()` function

### WHAT — Add
```python
from .stream_renderer import StreamEventRenderer
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
- The "text" / "ndjson" / "json-raw" branches remain **completely unchanged**
- `_normalize_event_to_ndjson()` stays in `formatters.py` (not part of this refactor)
- The `__all__` list stays the same (public API unchanged)

### ALGORITHM
The isinstance dispatch matches the old if/elif chain exactly — same print calls, same box-drawing chars, same truncation message format.

---

## Part B: Fix test imports in test_formatters.py

### WHERE
`tests/llm/formatting/test_formatters.py`

### WHAT
Update two import paths:

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

## Verification
- All `TestRenderedStreamFormat` tests pass (exact same output as before)
- All `TestPrintStreamEvent` tests pass
- All `TestFormatToolName` and `TestRenderToolOutput` tests pass (same logic, new import path)
- pylint, mypy, pytest all green

## Commit
One commit: "refactor(formatting): migrate rendered format to use StreamEventRenderer"
