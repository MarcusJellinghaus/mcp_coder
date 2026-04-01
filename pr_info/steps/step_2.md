# Step 2: Migrate iCoder app.py + remove append_tool_use() from output_log.py

## Context
See `pr_info/steps/summary.md` for full issue context and architecture.

Step 1 created the new modules and wired the CLI "rendered" format. This step makes iCoder the primary consumer, gaining formatted tool names, truncated output, JSON expansion, and box-drawing characters.

## LLM Prompt
> Implement Step 2 of issue #680. Read `pr_info/steps/summary.md` and this step file fully. Rewrite iCoder's `_handle_stream_event` to use `StreamEventRenderer`, remove `append_tool_use()` from `output_log.py`, and apply specific test updates listed below. All tests must pass.

---

## Part A: Modify app.py

### WHERE
`src/mcp_coder/icoder/ui/app.py`

### WHAT — Add imports
```python
from mcp_coder.llm.formatting.stream_renderer import StreamEventRenderer
from mcp_coder.llm.formatting.render_actions import (
    TextChunk, ToolStart, ToolResult, ErrorMessage, StreamDone,
)
```

### WHAT — Store renderer instance
In `__init__` or `on_mount`, add:
```python
self._renderer = StreamEventRenderer()
```
This reuses a single instance since the renderer is stateless but avoids per-event allocation.

### WHAT — Rewrite `_handle_stream_event`
```python
def _handle_stream_event(self, event: StreamEvent) -> None:
    output = self.query_one(OutputLog)
    action = self._renderer.render(event)
    if action is None:
        return
    if isinstance(action, TextChunk):
        output.append_text(action.text)
    elif isinstance(action, ToolStart):
        if action.inline_args is not None:
            line = f"┌ {action.display_name}({action.inline_args})"
        else:
            parts = [f"┌ {action.display_name}"]
            for key, value in action.block_args:
                parts.append(f"│  {key}: {value}")
            line = "\n".join(parts)
        output.append_text(line, style=STYLE_TOOL_OUTPUT)
    elif isinstance(action, ToolResult):
        parts = [f"│  {ln}" for ln in action.output_lines]
        if action.truncated:
            parts.append(f"└ done ({action.total_lines} lines, truncated to {len(action.output_lines)})")
        else:
            parts.append("└ done")
        output.append_text("\n".join(parts), style=STYLE_TOOL_OUTPUT)
    elif isinstance(action, ErrorMessage):
        output.append_text(f"Error: {action.message}")
```

### WHAT — Remove unused import
- Remove `StreamEvent` import if no longer used directly (check — it's still used as type hint for the method parameter, so keep it)

### HOW
- `StreamDone` is intentionally not handled — `_append_blank_line()` already runs after the stream loop in `_stream_llm`
- iCoder now shows: `┌ workspace > read_file(file_path='x.py')` instead of `⚙ mcp__workspace__read_file({...}) → ...`
- `action.name` is available on `ToolResult` for consumers that need the tool name at result time

### BEFORE vs AFTER (iCoder output)
| Before | After |
|--------|-------|
| `⚙ mcp__workspace__read_file({'file_path': 'x.py'}) → ...` | `┌ workspace > read_file(file_path='x.py')` |
| `⚙ mcp__workspace__read_file() → done` | `└ done` |
| Raw output, unlimited | JSON-expanded, truncated to 5 lines |

---

## Part B: Remove append_tool_use() from output_log.py

### WHERE
`src/mcp_coder/icoder/ui/widgets/output_log.py`

### WHAT
Delete the entire `append_tool_use()` method (~18 lines). No other code calls it after Part A.

---

## Part C: Update tests (specific changes)

### WHERE
`tests/icoder/test_widgets.py`

### WHAT — Delete these tests
- `test_output_log_append_tool_use` — tests the removed method directly
- `test_output_log_append_tool_use_with_style` — tests the removed method with style arg

### WHAT — Update this test
- `test_output_log_recorded_lines_property` — if it calls `append_tool_use`, change the call to use `append_text` instead with equivalent text content

### WHAT — No changes needed
- Do NOT touch `tests/icoder/test_app_pilot.py` — it does not reference `append_tool_use`
- Do NOT touch `tests/icoder/test_snapshots.py` — it does not reference `append_tool_use`

---

## Verification
- All iCoder tests pass
- All formatter tests still pass (no regression)
- pylint, mypy, pytest all green
- `append_tool_use` no longer exists anywhere in the codebase (grep to confirm)

## Commit
One commit: "refactor(icoder): use StreamEventRenderer for tool call display"
