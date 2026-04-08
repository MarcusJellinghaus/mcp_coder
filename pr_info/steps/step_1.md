# Step 1: Streaming buffer + Static tail widget + basic regression tests (a–e)

> **Context:** See `pr_info/steps/summary.md` for full issue background and design.

## Goal

Fix the token-per-line bug by adding a text buffer to `ICoderApp` and a `Static` "streaming tail" widget. Complete lines flush to `RichLog`; the partial line shows in the `Static`. Write regression tests a–e covering basic buffer behavior.

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md.
Read pr_info/steps/summary.md for context.
Read the current source files before making changes.
Add the production change and regression tests in the same commit so all checks pass together.
(Strict red->green TDD is not possible here: the new Static widget invalidates existing fixtures and snapshots immediately.)
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

**Keep `_append_blank_line()` helper** — called from BOTH the `StreamDone` success path AND the `except` branch in `_stream_llm`. This preserves the existing trailing-blank visual behavior after every stream (success or error) instead of dropping it on errors.

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
        self._append_blank_line()  # preserve trailing blank line
    elif isinstance(action, ToolStart):
        # ... existing ToolStart logic unchanged ...
    elif isinstance(action, ToolResult):
        # ... existing ToolResult logic unchanged ...
    elif isinstance(action, ErrorMessage):
        output.append_text(f"Error: {action.message}")
```

**Modified `_stream_llm()`** — flush on error, keep `_append_blank_line` on error path too:
```python
def _stream_llm(self, text: str) -> None:
    try:
        for event in self._core.stream_llm(text):
            self.call_from_thread(self._handle_stream_event, event)
        # StreamDone event handles flush + blank line in the success path
    except Exception as exc:
        self.call_from_thread(self._flush_buffer)
        self.call_from_thread(self._show_error, str(exc))
        self.call_from_thread(self._append_blank_line)
```

**Decision — preserve pure blank lines:** The flush loop does NOT guard with `if line:`. Consecutive `\n` characters produce empty lines that are written to `OutputLog` as-is (Option A — simplest, matches LLM intent).

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

**Factory fixture (reuses the existing `event_log` fixture from `tests/icoder/conftest.py`):**

```python
@pytest.fixture
def make_icoder_app(event_log):
    """Factory to create ICoderApp with custom FakeLLM responses or a custom LLM service."""
    def _factory(*, responses=None, llm_service=None):
        llm = llm_service or FakeLLMService(responses=responses or [])
        return ICoderApp(AppCore(llm_service=llm, event_log=event_log))
    return _factory
```

The `llm_service` kwarg lets Step 2 pass a raising service for the error-path test without duplicating the fixture.

### Assertion pattern (applies to all tests a–e and beyond)

Use **strict structural assertions**, not plain `in` checks (which can pass even in the buggy per-token case for single-word lines):

```python
# Exact-count check
assert output.recorded_lines.count("line1") == 1
# Index-ordering check
assert output.recorded_lines.index("line1") < output.recorded_lines.index("line2")
# Streaming tail must be empty after StreamDone
from textual.widgets import Static
assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test a) Single chunk, no newline — flushed on stream end:**
```python
async def test_streaming_single_chunk_no_newline(make_icoder_app):
    """Single chunk without newline: buffered, flushed to RichLog on stream end."""
    app = make_icoder_app(responses=[[
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
        assert output.recorded_lines.count("hello") == 1
        assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test b) Multiple chunks, no newlines — combined on stream end:**
```python
async def test_streaming_multi_chunk_no_newlines(make_icoder_app):
    """Multiple chunks without newlines: combined into single line on flush."""
    app = make_icoder_app(responses=[[
        {"type": "text_delta", "text": "hello"},
        {"type": "text_delta", "text": " world"},
        {"type": "text_delta", "text": "!"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert output.recorded_lines.count("hello world!") == 1
    assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test c) Mid-stream newline — line flushed, remainder continues:**
```python
async def test_streaming_mid_newline(make_icoder_app):
    """Newline mid-stream flushes completed line, partial continues."""
    app = make_icoder_app(responses=[[
        {"type": "text_delta", "text": "line1\nline2"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert output.recorded_lines.count("line1") == 1
    assert output.recorded_lines.count("line2") == 1
    assert output.recorded_lines.index("line1") < output.recorded_lines.index("line2")
    assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test d) Chunk with multiple newlines:**
```python
async def test_streaming_multiple_newlines_in_chunk(make_icoder_app):
    """Chunk with multiple newlines: each complete line flushed, partial kept."""
    app = make_icoder_app(responses=[[
        {"type": "text_delta", "text": "line1\nline2\nline3"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    for ln in ("line1", "line2", "line3"):
        assert output.recorded_lines.count(ln) == 1
    assert output.recorded_lines.index("line1") < output.recorded_lines.index("line2") < output.recorded_lines.index("line3")
    assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test e) Empty text_delta — no spurious empty line:**
```python
async def test_streaming_empty_text_delta(make_icoder_app):
    """Empty text_delta is a no-op: no spurious empty lines."""
    app = make_icoder_app(responses=[[
        {"type": "text_delta", "text": "hello"},
        {"type": "text_delta", "text": ""},
        {"type": "text_delta", "text": " world"},
        {"type": "done"},
    ]])
    # ... submit input, wait ...
    output = app.query_one(OutputLog)
    assert output.recorded_lines.count("hello world") == 1
    assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

### Additional edge-case tests

**Test e2) Chunk ending exactly on `\n`:**
```python
async def test_streaming_chunk_ends_on_newline(make_icoder_app):
    """Chunk ending exactly on newline: line flushed, no trailing empty entry."""
    app = make_icoder_app(responses=[[
        {"type": "text_delta", "text": "line1\n"},
        {"type": "done"},
    ]])
    # ... submit, wait ...
    output = app.query_one(OutputLog)
    assert output.recorded_lines.count("line1") == 1
    assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test e3) Chunk containing only `"\n"` mid-stream:**
```python
async def test_streaming_newline_only_chunk(make_icoder_app):
    """Chunks ['hello', '\\n', 'world']: 'hello' flushes on newline chunk, 'world' on StreamDone."""
    app = make_icoder_app(responses=[[
        {"type": "text_delta", "text": "hello"},
        {"type": "text_delta", "text": "\n"},
        {"type": "text_delta", "text": "world"},
        {"type": "done"},
    ]])
    # ... submit, wait ...
    output = app.query_one(OutputLog)
    assert output.recorded_lines.count("hello") == 1
    assert output.recorded_lines.count("world") == 1
    assert output.recorded_lines.index("hello") < output.recorded_lines.index("world")
    assert str(app.query_one("#streaming-tail", Static).renderable) == ""
```

**Test e4) Mid-stream Static tail assertion:**
At least one test must verify that `Static#streaming-tail` holds the current partial line during streaming (not just after it ends). After a chunk without a newline (and before `StreamDone`), assert:
```python
assert str(app.query_one("#streaming-tail", Static).renderable) == "<expected partial>"
```
and after `StreamDone` assert it is empty. If strict mid-stream pausing is awkward with the Pilot API, drive `_handle_stream_event` directly with a single non-newline chunk event and check the tail state before delivering `StreamDone`.

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
