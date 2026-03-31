# Step 7: UI Color Coding with Rich Text Styles

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Color-code different content types using Rich `Text` styles:
- User input: `white on grey23` (dark grey background)
- Tool output: `white on #0a0a2e` (very dark blue background)
- LLM text: default (no background)

## WHERE

- **Modify:** `src/mcp_coder/icoder/ui/widgets/output_log.py`
- **Modify:** `src/mcp_coder/icoder/ui/app.py`
- **Modify:** `tests/icoder/test_widgets.py`

## WHAT

### `output_log.py` — Add optional `style` parameter

```python
from rich.text import Text

class OutputLog(RichLog):
    def append_text(self, text: str, style: str | None = None) -> None:
        """Write text to the output log, optionally styled."""
        self._recorded.append(text)
        if style:
            self.write(Text(text, style=style))
        else:
            self.write(text)

    def append_tool_use(self, name: str, args: str, result: str, style: str | None = None) -> None:
        """Write compact tool use line, optionally styled."""
        line = f"\u2699 {name}({args}) \u2192 {result}"
        self._recorded.append(line)
        if style:
            self.write(Text(line, style=style))
        else:
            self.write(line)
```

### `app.py` — Pass style strings at call sites

Define style constants at module level:

```python
STYLE_USER_INPUT = "white on grey23"
STYLE_TOOL_OUTPUT = "white on #0a0a2e"
```

Apply at call sites:

```python
# User input echo
output.append_text(f"> {text}", style=STYLE_USER_INPUT)

# Tool use start
output.append_tool_use(name, args, "...", style=STYLE_TOOL_OUTPUT)

# Tool result
output.append_tool_use(name, "", "done", style=STYLE_TOOL_OUTPUT)

# LLM text_delta — no style (default)
output.append_text(text)

# Error — no style (default)
output.append_text(f"Error: {msg}")
```

### `test_widgets.py` — Add style tests

New tests:

1. **`test_output_log_append_text_with_style`**: Call `append_text("hello", style="bold")`
   and verify `recorded_lines` still contains `"hello"` (style doesn't affect recording).

2. **`test_output_log_append_tool_use_with_style`**: Call `append_tool_use("read", "x", "ok", style="bold")`
   and verify `recorded_lines` contains the expected formatted line.

3. **`test_output_log_append_text_no_style`**: Call `append_text("hello")` without style
   (backward compatibility). Verify `recorded_lines` contains `"hello"`.

## HOW

- `rich.text.Text` is imported in `output_log.py`.
- `RichLog.write()` accepts both `str` and `Text` (Rich renderables).
- `_recorded` list always stores plain strings (no style info) — keeps testing simple.
- Style constants are plain strings in `app.py` — no enum or config needed.

## ALGORITHM

No algorithm — conditional `Text()` wrapping:

```python
if style:
    self.write(Text(text, style=style))
else:
    self.write(text)
```

## DATA

- `STYLE_USER_INPUT: str = "white on grey23"` — module constant in `app.py`
- `STYLE_TOOL_OUTPUT: str = "white on #0a0a2e"` — module constant in `app.py`
- No new types. `style` parameter is `str | None`.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_7.md for full context.

Implement step 7: Add optional style parameter to OutputLog.append_text() and
append_tool_use() in output_log.py. Define STYLE_USER_INPUT and STYLE_TOOL_OUTPUT
constants in app.py and pass them at call sites. Write tests first in test_widgets.py,
then implement. Run all three MCP code quality checks after changes. Commit message:
"icoder: Rich color coding for user input, tool output, and LLM text"
```
