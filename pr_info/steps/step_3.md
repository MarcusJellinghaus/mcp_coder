# Step 3: Markdown Rendering in Tool Output Display

## Context
See [summary.md](summary.md) for overall design. This step adds Rich Markdown rendering for tool output in the UI layer. When `format_tools=True`, tool output lines are rendered as `rich.markdown.Markdown` objects via `OutputLog.write()` (which already supports Rich renderables as a `RichLog` subclass).

## LLM Prompt
> Implement Step 3 of issue #763 (see `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`).
> Add Markdown rendering for tool output in `ICoderApp._handle_stream_event()`.
> When `format_tools=True`, render tool output as `rich.markdown.Markdown`.
> When `format_tools=False`, keep current plain text rendering (identical to today).
> Write tests first (TDD), then implement. Run all three quality checks after changes.

## Part A: Tests

### WHERE
- `tests/icoder/test_app_pilot.py` (Textual pilot integration tests)

### WHAT — New test functions

```python
async def test_tool_result_renders_markdown_by_default(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Tool result output is rendered via Markdown when format_tools=True (default)."""

async def test_tool_result_renders_plain_text_when_no_format(
    event_log: EventLog, fake_llm: FakeLLMService,
) -> None:
    """Tool result output is rendered as plain text when format_tools=False."""
```

### DATA — Test strategy
- Use `FakeLLMService` with `tool_result` events containing markdown-like content (e.g. `"# Header\n**bold**"`)
- For the Markdown test: verify the output is written to `OutputLog` (the exact rendering is Rich's concern — we just verify the code path is reached)
- For the plain text test: verify `format_tools=False` produces plain text output matching today's behavior
- These are `textual_integration` marked tests using the pilot pattern from existing tests

## Part B: Implementation

### WHERE
- `src/mcp_coder/icoder/ui/app.py`

### WHAT — Changes to `_handle_stream_event()`

```python
from rich.markdown import Markdown

# In the ToolResult branch of _handle_stream_event():
elif isinstance(action, ToolResult):
    parts = [f"│  {ln}" for ln in action.output_lines]
    if action.truncated:
        parts.append(
            f"└ done ({action.total_lines} lines, "
            f"truncated to {len(action.output_lines)})"
        )
    else:
        parts.append("└ done")
    body = "\n".join(parts)
    if self._format_tools:
        output.write(Markdown(body))
    else:
        output.append_text(body, style=STYLE_TOOL_OUTPUT)
```

### HOW — Integration
- `rich.markdown.Markdown` is already available (Rich is a dependency of Textual)
- `OutputLog` extends `RichLog` which has `write()` accepting any Rich renderable
- No new imports needed beyond `from rich.markdown import Markdown`
- `self._format_tools` was added in Step 1

### ALGORITHM
```
1. Build tool output body string (same as today: "│  line" per output line + "└ done")
2. If format_tools is True: wrap body in Markdown() and write to OutputLog
3. If format_tools is False: use append_text with STYLE_TOOL_OUTPUT (unchanged behavior)
4. Plain text passes through Markdown safely (no transformation needed)
5. Error messages continue to bypass this — they use ErrorMessage action, not ToolResult
```

### NOTES
- Plain text passes through `Markdown()` safely — Rich renders it as-is
- Accidental markdown syntax (`#`, `*`) in output is acceptable per the issue
- Error messages flow through `ErrorMessage` action, not `ToolResult` — no change needed
- The `recorded_lines` tracking in `OutputLog` only records `append_text` calls; `write()` calls bypass it. This is acceptable since `recorded_lines` is for testing and the Markdown path uses `write()` directly.

## Commit Message
```
feat(icoder): render tool output as Rich Markdown (#763)

When format_tools is enabled (default), tool output is rendered as
rich.markdown.Markdown for proper tables, headers, code blocks, and
bold text. When disabled via --no-format-tools, plain text rendering
is preserved identically to the previous behavior.
```
