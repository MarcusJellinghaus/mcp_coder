# Step 1: Update busy indicator after ToolResult

## Summary Reference
See [summary.md](summary.md) for full context on Issue #846.

## Goal
After rendering `ToolResult` output, update the busy indicator to show `"Thinking about {action.name}..."`.

## WHERE
- **Test**: `tests/icoder/ui/test_app.py`
- **Implementation**: `src/mcp_coder/icoder/ui/app.py`

## WHAT

### Test (`tests/icoder/ui/test_app.py`)
Add one async test function:

```python
async def test_busy_indicator_thinking_after_tool_result(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
```

### Implementation (`src/mcp_coder/icoder/ui/app.py`)
No new functions. One line added inside existing `_handle_stream_event()`.

## HOW

### Test
- Uses existing `make_icoder_app` fixture and `pytestmark = pytest.mark.textual_integration`
- Calls `app._handle_stream_event()` with `tool_use_start` then `tool_result` events
- Asserts `BusyIndicator.label_text` contains `"Thinking about workspace > read_file..."`

### Implementation
In `_handle_stream_event()`, in the `isinstance(action, ToolResult)` block, after `output.append_text(body, style=STYLE_TOOL_OUTPUT)`, add:

```python
self.query_one(BusyIndicator).show_busy(f"Thinking about {action.name}...")
```

## ALGORITHM (pseudocode)
```
# In _handle_stream_event, ToolResult branch:
1. Format output lines with "│" prefix
2. Append "└ done" footer (with truncation info if needed)  
3. Write formatted body to OutputLog
4. Update BusyIndicator to "Thinking about {action.name}..."   # NEW
```

## DATA
- **Input**: `action.name` — `str`, e.g. `"workspace > read_file"` (already populated by `StreamEventRenderer`)
- **Output**: Busy indicator displays `"Thinking about workspace > read_file..."`
- **No new data structures**

## LLM Prompt

```
Implement Issue #846 Step 1. See pr_info/steps/summary.md for context and pr_info/steps/step_1.md for details.

TDD approach:
1. Read tests/icoder/ui/test_app.py
2. Add test `test_busy_indicator_thinking_after_tool_result` that:
   - Sends tool_use_start + tool_result events via _handle_stream_event
   - Asserts BusyIndicator.label_text contains "Thinking about workspace > read_file..."
3. Read src/mcp_coder/icoder/ui/app.py
4. In _handle_stream_event(), after the ToolResult output.append_text() call, add:
   self.query_one(BusyIndicator).show_busy(f"Thinking about {action.name}...")
5. Run all code quality checks (pylint, pytest, mypy) and fix any issues.
6. Commit with message: "feat(icoder): show 'Thinking about [tool]...' after tool result (#846)"
```
