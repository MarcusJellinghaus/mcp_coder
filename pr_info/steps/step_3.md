# Step 3: ToolStart Raw Args + `format_tool_start()` + app.py Update

> **Context:** Read `pr_info/steps/summary.md` first. This step changes the ToolStart dataclass, adds the public formatting function, and updates app.py. These are dependent changes that must ship together.

## Goal
1. Change `ToolStart` to carry `args: dict` instead of pre-formatted strings
2. Add `format_tool_start()` public function with inline/block/separator logic
3. Update `StreamEventRenderer.render()` to produce new `ToolStart`
4. Update `app.py` to use `format_tool_start()`
5. Update CLI `formatters.py` to use `format_tool_start()` (rendered format) and `_render_value_compact()` (text format)
6. Remove `_INLINE_ARG_LIMIT` (dead code) and replace `_format_tool_args` (which IS currently used by `formatters.py`) with inline use of `_render_value_compact`

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/formatting/render_actions.py` | Change `ToolStart` dataclass |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | Add `format_tool_start()`, simplify `render()`, remove `_INLINE_ARG_LIMIT` and `_format_tool_args` |
| `src/mcp_coder/llm/formatting/formatters.py` | Rendered format calls `format_tool_start()`; text format calls `_render_value_compact()` inline; drop `_format_tool_args` import |
| `src/mcp_coder/icoder/ui/app.py` | Use `format_tool_start()` for ToolStart rendering |
| `tests/llm/formatting/test_stream_renderer.py` | Rewrite ToolStart tests |
| `tests/llm/formatting/test_formatters.py` | Update tests affected by new rendered/text output (notably `TestRenderedStreamFormat.test_inline_params`, `test_block_params`, `test_json_result_expanded`, `test_blank_line_after_footer`, `TestPrintStreamEvent.test_print_stream_event_tool_use_bordered`); `test_block_params` may need longer args to force block under the new 100-char threshold |

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

### stream_renderer.py — Remove `_INLINE_ARG_LIMIT` (dead code), remove `_format_tool_args()`

`_INLINE_ARG_LIMIT` is truly dead (only referenced by the old `tool_use_start` render branch we are rewriting).

`_format_tool_args()` is NOT dead today — it is imported and called by `formatters.py` text-format branch. We delete it here AND replace its functionality with `_render_value_compact` (see `formatters.py` section below). `_render_value_compact` becomes the module-private helper that `formatters.py` imports.

### formatters.py — Align CLI with iCoder

**Imports (line 13, 15):**
- `ToolStart` still imported, but no longer references `inline_args` / `block_args` (fields removed in this step).
- Remove `_format_tool_args` from the import list.
- Add `_render_value_compact` and `format_tool_start` to the import list.

**Rendered format (lines 315–322, `print_stream_event()` rendered branch):**
Replace the manual reading of `action.inline_args` / `action.block_args` with a single call:

```python
if isinstance(action, ToolStart):
    for line in format_tool_start(action, full=False):
        print(line)
```

This emits the same output as iCoder, including the `├──` separator as the last line when args are present. Single unified rendering path — no CLI-specific branch.

**Text format (around line 344):**
Replace `_format_tool_args(event.get("args"))` with compact inline formatting using `_render_value_compact`:

```python
args = event.get("args") or {}
args_str = ", ".join(f"{k}={_render_value_compact(v)}" for k, v in args.items())
```

This keeps the CLI text format compact (single-line) while using the same value-summarization logic as the rendered/iCoder modes.

### app.py — Note on ToolResult rendering

No changes to ToolResult rendering or footer format.

### render() note

`_render_tool_output()` is called from `render()` with `full=False` implicit (the parameter defaults to `False` per Step 2).

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
- `test_block_preserves_arg_order` — 3 args with distinct keys (e.g., `zebra='x'*200, apple='y'*200, middle='z'*200`) force block format; assert block lines appear in insertion order (zebra, apple, middle), NOT alphabetical

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3: Change ToolStart dataclass to use args: dict, add
format_tool_start() function, simplify render() for tool_use_start,
update app.py to use format_tool_start(), update formatters.py so
both rendered and text CLI paths use the new helpers, and remove
_INLINE_ARG_LIMIT and _format_tool_args. Rewrite ToolStart-related
tests in test_stream_renderer.py and update affected tests in
test_formatters.py.

All files must be updated together — the dataclass change cascades
to its producer (render) and both consumers (app.py, formatters.py).

After implementation, run all three code quality checks.
```
