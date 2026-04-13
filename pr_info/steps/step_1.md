# Step 1: Fix tool result rendering + add pipeline tests

**Ref:** [summary.md](summary.md) | Issue #778

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Implement the fix and tests described below. After all edits, run pylint, pytest, and mypy checks. All must pass before committing.

## Overview

Fix the bug where tool result output is invisible in iCoder due to `Markdown()` rendering, then add end-to-end pipeline tests and update the existing test that asserts Markdown behavior.

---

## Part A: Fix `src/mcp_coder/icoder/ui/app.py`

### WHERE
- `src/mcp_coder/icoder/ui/app.py`

### WHAT
1. **Remove import** `from rich.markdown import Markdown` (line 7) — no longer used.
2. **Replace lines 237–240** (the `if self._format_tools` / `else` branch in the `ToolResult` handler) with a single line:

### HOW
In `_handle_stream_event`, the `elif isinstance(action, ToolResult):` block currently ends with:
```python
if self._format_tools:
    output.write(Markdown(body))
else:
    output.append_text(body, style=STYLE_TOOL_OUTPUT)
```
Replace with:
```python
output.append_text(body, style=STYLE_TOOL_OUTPUT)
```

### ALGORITHM
```
1. Build body string from action.output_lines with "│" prefix (existing code, unchanged)
2. Append "└ done" or "└ done (N lines, truncated to M)" (existing code, unchanged)
3. Always render via append_text with STYLE_TOOL_OUTPUT  ← THE FIX
```

### DATA
- No changes to data structures or return values.
- `append_text` records text in `OutputLog._recorded` (used by tests).

---

## Part B: Update existing test in `tests/icoder/test_app_pilot.py`

### WHERE
- `tests/icoder/test_app_pilot.py`

### WHAT
Update `test_tool_result_renders_markdown_by_default` (line ~676):
1. **Rename** to `test_tool_result_renders_plain_text_by_default`
2. **Update docstring** to reflect plain text rendering
3. **Update comment** on line ~704 from "goes through write() as Markdown" to "goes through append_text (plain text)"

The assertions themselves (`"│" in joined`, `"# Header" in joined`, `"done" in lines`) already work for plain text output — they don't assert Markdown-specific behavior. Only the name, docstring, and comment need updating.

---

## Part C: Create `tests/icoder/ui/test_app.py`

### WHERE
- `tests/icoder/ui/test_app.py` (new file)

### WHAT
Four async test functions using `_handle_stream_event` directly (same pattern as `test_streaming_tail_shows_partial_during_stream` in `test_app_pilot.py`):

```python
async def test_tool_output_list_directory(make_icoder_app) -> None:
async def test_tool_output_read_file(make_icoder_app) -> None:
async def test_tool_output_truncated(make_icoder_app) -> None:
async def test_tool_output_empty(make_icoder_app) -> None:
```

### HOW
- Import `ICoderApp` from `mcp_coder.icoder.ui.app`
- Import `OutputLog` from `mcp_coder.icoder.ui.widgets.output_log`
- Use `make_icoder_app` fixture from `tests/icoder/conftest.py` (via `test_app_pilot.py` pattern)
- Mark with `pytestmark = pytest.mark.textual_integration`
- Each test: mount app via `run_test()`, call `_handle_stream_event` directly, assert on `recorded_lines`

### ALGORITHM (per test)
```
1. Create app via make_icoder_app(responses=[])
2. async with app.run_test() as pilot: await pilot.pause()
3. app._handle_stream_event({"type": "tool_use_start", ...})
4. app._handle_stream_event({"type": "tool_result", "output": <json_string>, ...})
5. lines = app.query_one(OutputLog).recorded_lines
6. Assert expected content is present in lines
```

### DATA — Test inputs and expected assertions

**Test 1: `test_tool_output_list_directory`**
- Input: `{"type": "tool_result", "name": "mcp__workspace__list_directory", "output": '{"result": ["file1.py", "file2.py", "src/"]}'}`
- Assert: `"file1.py"`, `"file2.py"`, `"src/"` appear in recorded lines (inside `│`-prefixed lines)
- Assert: `"└ done"` appears in recorded lines

**Test 2: `test_tool_output_read_file`**
- Input: `{"type": "tool_result", "name": "mcp__workspace__read_file", "output": '{"result": "line1\\nline2\\nline3"}'}`
- Assert: `"line1"`, `"line2"`, `"line3"` appear in joined recorded output
- Assert: `"└ done"` appears

**Test 3: `test_tool_output_truncated`**
- Input: `{"type": "tool_result", "name": "...", "output": '{"result": "' + '\\n'.join(f'line{i}' for i in range(30)) + '"}'}`
- Assert: `"truncated"` appears in the `└ done (...)` line
- Assert: `"skipped"` appears (from the `... (N lines skipped)` marker)

**Test 4: `test_tool_output_empty`**
- Input: `{"type": "tool_result", "name": "...", "output": ""}`
- Assert: `"└ done"` appears (no output lines, just the footer)

### Fixture
Reuse the `make_icoder_app` fixture — copy the fixture definition from `test_app_pilot.py` into this file (it depends on `event_log` from `conftest.py`). This avoids cross-file fixture dependencies.

---

## Commit

```
fix(icoder): render tool results as plain text instead of Markdown

Rich's Markdown parser interprets box-drawing characters (│, └) as
table syntax, making tool output invisible in iCoder.

Replace Markdown(body) with append_text(body) for tool results.
The format_tools flag continues to control JSON filtering/truncation
in StreamEventRenderer.

Add end-to-end pipeline tests for tool output visibility.

Closes #778
```
