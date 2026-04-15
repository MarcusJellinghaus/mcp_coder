# Step 3: ToolStart Raw Args + `format_tool_start()` + app.py Update

> **Context:** Read `pr_info/steps/summary.md` first. This step changes the ToolStart dataclass, adds the public formatting function, and updates app.py. These are dependent changes that must ship together.

## Goal
1. Change `ToolStart` to carry `args: dict` instead of pre-formatted strings
2. Add `format_tool_start()` public function with inline/block/separator logic
3. Update `StreamEventRenderer.render()` to produce new `ToolStart`
4. Update `app.py` to use `format_tool_start()`
5. Remove dead code: `_INLINE_ARG_LIMIT`, `_format_tool_args`

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/formatting/render_actions.py` | Change `ToolStart` dataclass |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | Add `format_tool_start()`, simplify `render()`, remove dead code |
| `src/mcp_coder/icoder/ui/app.py` | Use `format_tool_start()` for ToolStart rendering |
| `tests/llm/formatting/test_stream_renderer.py` | Rewrite ToolStart tests |

## WHAT

### render_actions.py — `ToolStart` dataclass change

**Before:**
```python
@dataclass(frozen=True)
class ToolStart:
    display_name: str
    raw_name: str
    inline_args: str | None
    block_args: list[tuple[str, str]]
```

**After:**
```python
@dataclass(frozen=True)
class ToolStart:
    display_name: str
    raw_name: str
    args: dict  # raw args from stream event
```

### stream_renderer.py — Add `format_tool_start()`

**Signature:** `format_tool_start(action: ToolStart, full: bool = False) -> list[str]`

**Algorithm:**
```
if no args: return ["┌ {display_name}"]
build inline attempt: "┌ {name}({k}={compact(v)}, ...)"
if len(inline) <= _MAX_INLINE_LEN: lines = [inline]
else: lines = ["┌ {name}"] + block args (compact or full per mode)
append "├──" separator as last line
return lines
```

**Block args rendering:**
- Compact mode (`full=False`): `│  key: {_render_value_compact(value)}`
- Full mode (`full=True`): `│  key: {_render_value_full(value)}` — if multi-line, key on its own line + indented value lines with `│    ` prefix

### stream_renderer.py — Simplify `render()` for `tool_use_start`

**Before:** Complex branch deciding inline vs block based on `_INLINE_ARG_LIMIT`, building formatted strings.
**After:**
```python
if event_type == "tool_use_start":
    name = str(event.get("name", ""))
    args = event.get("args", {})
    if not isinstance(args, dict):
        args = {}
    return ToolStart(
        display_name=_format_tool_name(name),
        raw_name=name,
        args=args,
    )
```

### stream_renderer.py — Remove dead code
- `_INLINE_ARG_LIMIT = 2`
- `_format_tool_args()` function

### app.py — Use `format_tool_start()`

**Add import:** `from mcp_coder.llm.formatting.stream_renderer import format_tool_start`

**Before (ToolStart handling in `_handle_stream_event`):**
```python
elif isinstance(action, ToolStart):
    self.query_one(BusyIndicator).show_busy(action.display_name)
    if action.inline_args is not None:
        line = f"┌ {action.display_name}({action.inline_args})"
    else:
        parts = [f"┌ {action.display_name}"]
        for key, value in action.block_args:
            parts.append(f"│  {key}: {value}")
        line = "\n".join(parts)
    output.append_text(line, style=STYLE_TOOL_OUTPUT)
```

**After:**
```python
elif isinstance(action, ToolStart):
    self.query_one(BusyIndicator).show_busy(action.display_name)
    lines = format_tool_start(action, full=False)
    output.append_text("\n".join(lines), style=STYLE_TOOL_OUTPUT)
```

### app.py — ToolResult footer update

**Before:**
```python
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
    output.append_text(body, style=STYLE_TOOL_OUTPUT)
```

**After (same logic, just update the truncation message to match compact format):**
```python
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
    output.append_text(body, style=STYLE_TOOL_OUTPUT)
```

(ToolResult rendering stays the same — no changes needed here.)

## HOW — Test changes in `test_stream_renderer.py`

### Add import
```python
from mcp_coder.llm.formatting.stream_renderer import format_tool_start
```

### Rewrite `TestStreamEventRenderer` ToolStart tests

**Replace `test_tool_use_start_inline`:**
```python
def test_tool_use_start_short_args(self) -> None:
    action = _RENDERER.render({
        "type": "tool_use_start",
        "name": "mcp__workspace__read_file",
        "args": {"file_path": "x.py"},
    })
    assert isinstance(action, ToolStart)
    assert action.display_name == "workspace > read_file"
    assert action.raw_name == "mcp__workspace__read_file"
    assert action.args == {"file_path": "x.py"}
```

**Replace `test_tool_use_start_block`:**
```python
def test_tool_use_start_many_args(self) -> None:
    action = _RENDERER.render({
        "type": "tool_use_start",
        "name": "mcp__workspace__edit_file",
        "args": {"file_path": "a.py", "old_text": "foo", "new_text": "bar"},
    })
    assert isinstance(action, ToolStart)
    assert action.args == {"file_path": "a.py", "old_text": "foo", "new_text": "bar"}
```

### Add `TestFormatToolStart` class

- `test_no_args` — empty dict → `["┌ workspace > read_file"]` (no separator)
- `test_inline_short_args` — fits in 100 chars → `["┌ name(k='v')", "├──"]`
- `test_block_long_args` — exceeds 100 chars → `["┌ name", "│  key: (N chars)", "├──"]`
- `test_inline_threshold_boundary` — exactly 100 chars → inline; 101 chars → block
- `test_compact_value_summaries` — large list arg → `"(N items)"` in compact mode
- `test_full_mode_expands_values` — same arg with `full=True` → multiline expansion
- `test_full_mode_still_inlines_short` — short args + `full=True` → still inline (full doesn't force block)
- `test_separator_present_with_args` — last line is always `"├──"` when args present
- `test_separator_absent_without_args` — no `"├──"` in output when no args

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3: Change ToolStart dataclass to use args: dict, add
format_tool_start() function, simplify render() for tool_use_start,
update app.py to use format_tool_start(), remove _INLINE_ARG_LIMIT
and _format_tool_args. Rewrite ToolStart-related tests.

All four files must be updated together — the dataclass change cascades
to its producer (render) and consumer (app.py).

After implementation, run all three code quality checks.
```
