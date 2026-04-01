# Step 3: Migrate iCoder app.py + remove append_tool_use() from output_log.py

## Context
See `pr_info/steps/summary.md` for full issue context and architecture.

Steps 1-2 created and wired the renderer for the CLI. This step makes iCoder the primary consumer, gaining formatted tool names, truncated output, JSON expansion, and box-drawing characters.

## LLM Prompt
> Implement Step 3 of issue #680. Read `pr_info/steps/summary.md` and this step file fully. Rewrite iCoder's `_handle_stream_event` to use `StreamEventRenderer`, remove `append_tool_use()` from `output_log.py`, and update any tests that reference `append_tool_use`. All tests must pass.

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

### WHAT — Rewrite `_handle_stream_event`
```python
def _handle_stream_event(self, event: StreamEvent) -> None:
    output = self.query_one(OutputLog)
    renderer = StreamEventRenderer()
    action = renderer.render(event)
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

## Part C: Update tests

### WHERE
Check these test files for references to `append_tool_use`:
- `tests/icoder/test_widgets.py`
- `tests/icoder/test_app_pilot.py`
- `tests/icoder/test_snapshots.py`

### WHAT
- Remove or update any tests that call `append_tool_use()` directly
- Update any assertions that expect the `⚙ name(args) → result` format — they should now expect the `┌`/`│`/`└` box-drawing format
- Snapshot tests may need regeneration if they capture tool output

### HOW
- Read each test file first to understand what references `append_tool_use`
- If a test is specifically testing `append_tool_use`, convert it to test `append_text` with the new format
- If a pilot/snapshot test captures tool call rendering, update expected output

---

## Verification
- All iCoder tests pass
- All formatter tests still pass (no regression)
- pylint, mypy, pytest all green
- `append_tool_use` no longer exists anywhere in the codebase (grep to confirm)

## Commit
One commit: "refactor(icoder): use StreamEventRenderer for tool call display"
