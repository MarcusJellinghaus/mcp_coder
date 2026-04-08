# Step 1: Streaming buffer + Static tail widget + basic regression tests (a–e)

> **Context:** See `pr_info/steps/summary.md` for full issue background and design.

## Goal

Fix the token-per-line bug by adding a text buffer to `ICoderApp` and a `Static` "streaming tail" widget. Complete lines flush to `RichLog`; the partial line shows in the `Static`. Write regression tests a–e covering basic buffer behavior.

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md.
Read pr_info/steps/summary.md for context.
Read the current source files before making changes.
Follow TDD: write the tests first (they will fail), then implement the fix.
Run all quality checks after changes.
```

## WHERE — Files to modify

| File | Action |
|---|---|
| `src/mcp_coder/icoder/ui/app.py` | Modify |
| `src/mcp_coder/icoder/ui/styles.py` | Modify |
| `tests/icoder/test_app_pilot.py` | Modify (add tests) |

## WHAT — Changes

### 1. `src/mcp_coder/icoder/ui/styles.py`

Add CSS rule for the streaming tail widget:

```python
# Add to CSS string:
#streaming-tail {
    height: auto;
    background: #1e1e1e;
    color: #d4d4d4;
}
```

### 2. `src/mcp_coder/icoder/ui/app.py`

**New imports:**
```python
from textual.widgets import Static
from mcp_coder.llm.formatting.render_actions import StreamDone  # add to existing import
```

**New instance attribute in `__init__`:**
```python
self._text_buffer: str = ""
```

**Modified `compose()`** — yield `Static` between `OutputLog` and `CommandAutocomplete`:
```python
def compose(self) -> ComposeResult:
    yield OutputLog()
    yield Static(id="streaming-tail")
    yield CommandAutocomplete()
    yield InputArea(registry=self._core.registry, event_log=self._core.event_log)
```

**New method `_flush_buffer()`:**
```python
def _flush_buffer(self) -> None:
    """Flush any buffered text to OutputLog and clear the streaming tail."""
    if self._text_buffer:
        self.query_one(OutputLog).append_text(self._text_buffer)
        self._text_buffer = ""
    self.query_one("#streaming-tail", Static).update("")
```

**Rewritten `_handle_stream_event()`:**

```python
def _handle_stream_event(self, event: StreamEvent) -> None:
    output = self.query_one(OutputLog)
    action = self._renderer.render(event)
    if action is None:
        return

    if isinstance(action, TextChunk):
        self._text_buffer += action.text
        # Split on newlines: flush complete lines, keep partial
        lines = self._text_buffer.split("\n")
        # All but last are complete lines
        for line in lines[:-1]:
            output.append_text(line)
        # Last element is the partial (may be "")
        self._text_buffer = lines[-1]
        self.query_one("#streaming-tail", Static).update(self._text_buffer)
        return

    # Any non-text action: flush buffer first
    self._flush_buffer()

    if isinstance(action, StreamDone):
        output.write("")  # blank line for visual spacing
    elif isinstance(action, ToolStart):
        # ... existing ToolStart logic unchanged ...
    elif isinstance(action, ToolResult):
        # ... existing ToolResult logic unchanged ...
    elif isinstance(action, ErrorMessage):
        output.append_text(f"Error: {action.message}")
```

**Modified `_stream_llm()`** — remove `_append_blank_line` call, add flush before error:
```python
def _stream_llm(self, text: str) -> None:
    try:
        for event in self._core.stream_llm(text):
            self.call_from_thread(self._handle_stream_event, event)
        # StreamDone event handles flush + blank line
    except Exception as exc:
        self.call_from_thread(self._flush_buffer)
        self.call_from_thread(self._show_error, str(exc))
```

**Remove `_append_blank_line` method** — no longer needed.

### ALGORITHM — TextChunk buffer logic (5 lines)

```
buffer += chunk.text
lines = buffer.split("\n")
for each line in lines[:-1]:        # complete lines
    output.append_text(line)
buffer = lines[-1]                   # keep partial
static.update(buffer)                # show partial to user
```

### DATA — Key state

- `self._text_buffer: str` — partial line accumulator, empty string when idle
- `Static#streaming-tail` — displays current partial line, cleared on flush

### 3. `tests/icoder/test_app_pilot.py` — Add tests a–e

All tests use `FakeLLMService(responses=[[...]])` with explicit multi-chunk sequences. Create the app inline with the custom responses (can't use the shared `icoder_app` fixture since it uses default FakeLLMService).

**Helper fixture to add:**
```python
def _make_app(responses: list[list[StreamEvent]], tmp_path: Path) -> ICoderApp:
    fake_llm = FakeLLMService(responses=responses)
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(llm_service=fake_llm, event_log=event_log)
        return ICoderApp(app_core)
```

Note: Since EventLog is a context manager, use a fixture that yields instead. Pattern:

```python
@pytest.fixture
def make_icoder_app(tmp_path: Path) -> Iterator[Callable[[list[list[StreamEvent]]], ICoderApp]]:
    """Factory fixture to create ICoderApp with custom FakeLLM responses."""
    apps: list[tuple[EventLog, ICoderApp]] = []

    def _factory(responses: list[list[StreamEvent]]) -> ICoderApp:
        event_log = EventLog(logs_dir=tmp_path)
        event_log.__enter__()
        fake_llm = FakeLLMService(responses=responses)
        app_core = AppCore(llm_service=fake_llm, event_log=event_log)
        app = ICoderApp(app_core)
        apps.append((event_log, app))
        return app

    yield _factory

    for el, _ in apps:
        el.__exit__(None, None, None)
```

**Test a) Single chunk, no newline — flushed on stream end:**
```python
async def test_streaming_single_chunk_no_newline(make_icoder_app):
    """Single chunk without newline: buffered, flushed to RichLog on stream end."""
    app = make_icoder_app([[
        {"type": "text_delta", "text": "hello"},
        {"type": "done"},
    ]])
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("test")
        await pilot.press("enter")
        await pilot.pause(delay=0.5)
        output = app.query_one(OutputLog)
        assert "hello" in output.recorded_lines
        # Should be a single entry, not split across multiple lines
        hello_entries = [l for l in output.recorded_lines if l == "hello"]
        assert len(hello_entries) == 1
```

**Test b) Multiple chunks, no newlines — combined on stream end:**
```python
async def test_streaming_multi_chunk_no_newlines(make_icoder_app):
    """Multiple chunks without newlines: combined into single line on flush."""
    app = make_icoder_app([[
        {"type": "text_delta", "text": "hello"},
        {"type": "text_delta", "text": " world"},
        {"type": "text_delta", "text": "!"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert "hello world!" in output.recorded_lines
```

**Test c) Mid-stream newline — line flushed, remainder continues:**
```python
async def test_streaming_mid_newline(make_icoder_app):
    """Newline mid-stream flushes completed line, partial continues."""
    app = make_icoder_app([[
        {"type": "text_delta", "text": "line1\nline2"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert "line1" in output.recorded_lines
    assert "line2" in output.recorded_lines
```

**Test d) Chunk with multiple newlines:**
```python
async def test_streaming_multiple_newlines_in_chunk(make_icoder_app):
    """Chunk with multiple newlines: each complete line flushed, partial kept."""
    app = make_icoder_app([[
        {"type": "text_delta", "text": "line1\nline2\nline3"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert "line1" in output.recorded_lines
    assert "line2" in output.recorded_lines
    assert "line3" in output.recorded_lines
```

**Test e) Empty text_delta — no spurious empty line:**
```python
async def test_streaming_empty_text_delta(make_icoder_app):
    """Empty text_delta is a no-op: no spurious empty lines."""
    app = make_icoder_app([[
        {"type": "text_delta", "text": "hello"},
        {"type": "text_delta", "text": ""},
        {"type": "text_delta", "text": " world"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert "hello world" in output.recorded_lines
    # No empty string entries from the empty text_delta
    non_prompt_lines = [l for l in output.recorded_lines if not l.startswith(">")]
    assert "" not in non_prompt_lines or non_prompt_lines == []  # only blank from StreamDone spacing
```

## HOW — Integration points

- `Static` is a standard Textual widget, imported from `textual.widgets`
- `StreamDone` is already defined in `render_actions.py` and returned by `StreamEventRenderer` for `"done"` events — just not handled in `_handle_stream_event` currently
- `_flush_buffer` is called from `_handle_stream_event` (for non-text actions) and from `_stream_llm` except block
- The existing `test_llm_streaming` test should continue to pass (single-chunk default response still works)

## Commit message

```
fix(icoder): buffer streamed tokens into lines instead of one-per-row (#735)

Add Static streaming-tail widget and text buffer to ICoderApp.
Complete lines flush to RichLog on newline; partial lines display
in the Static widget. Any non-text event flushes the buffer first.

Add regression tests a-e for basic buffer behavior:
- single chunk, multi-chunk, mid-stream newline,
  multiple newlines in chunk, empty text_delta.
```
