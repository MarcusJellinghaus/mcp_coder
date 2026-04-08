# Step 2: Regression tests f–h (error/tool mid-line flush, back-to-back streams)

> **Context:** See `pr_info/steps/summary.md` for full issue background and design.
> **Prerequisite:** Step 1 completed — buffer + Static widget + tests a–e in place.

## Goal

Add regression tests for edge cases: stream error mid-line, tool events mid-line, and back-to-back streams. Verify the flush-before-non-text-event behavior works correctly in all paths.

**This step is strictly tests-only.** Step 2 does NOT modify `src/mcp_coder/icoder/ui/app.py`. If any of tests f/g/h reveals a production bug, the fix belongs in Step 1 and MUST be folded back into Step 1 before Step 1 is committed.

## LLM Prompt

```
Implement Step 2 from pr_info/steps/step_2.md.
Read pr_info/steps/summary.md for context.
Read the current state of src/mcp_coder/icoder/ui/app.py and tests/icoder/test_app_pilot.py before making changes.
Step 1 is already implemented — the buffer, Static widget, and tests a-e exist.
Add tests f-h. Step 2 is tests-only — do NOT modify app.py.
If any test reveals a bug, stop, fold the fix into Step 1, then retry Step 2.
Run all quality checks after changes.
```

## WHERE — Files to modify

| File | Action |
|---|---|
| `tests/icoder/test_app_pilot.py` | Modify (add tests f–h) |

**Out of scope:** `src/mcp_coder/icoder/ui/app.py` must NOT be modified in this step. Production fixes belong in Step 1.

## WHAT — Tests to add

All tests reuse the `make_icoder_app` factory fixture from Step 1.

### Test f) Stream error mid-line — partial flushed first, then error rendered

```python
async def test_streaming_error_mid_line(make_icoder_app):
    """Stream error mid-line: partial text flushed before error message."""
```

**Approach:** Need a `FakeLLMService` that raises mid-stream. Two options:
1. Subclass `FakeLLMService` with a raising variant
2. Use a custom responses list where the iterator raises

Simplest: create a small `ErrorLLMService` class inside the test file (or use a generator that raises). The `_stream_llm` method catches `Exception`, calls `_flush_buffer()` then `_show_error()`.

```python
class ErrorAfterChunksLLMService:
    """LLM service that yields some chunks then raises."""

    def __init__(self, chunks: list[StreamEvent], error_msg: str) -> None:
        self._chunks = chunks
        self._error_msg = error_msg

    def stream(self, question: str) -> Iterator[StreamEvent]:
        yield from self._chunks
        raise RuntimeError(self._error_msg)

    @property
    def session_id(self) -> str | None:
        return None
```

**Test logic:**
```python
# Service yields "partial" then raises
# After stream completes:
#   - "partial" should be in recorded_lines (flushed before error)
#   - "Error: boom" should be in recorded_lines (after flush)
#   - "partial" should appear BEFORE "Error: boom" in the list
```

**Factory usage:** The Step 1 `make_icoder_app` factory already accepts an `llm_service` kwarg, so this test just passes the raising service directly:
```python
app = make_icoder_app(llm_service=ErrorAfterChunksLLMService(chunks, "boom"))
```

### Test g) Back-to-back streams — buffer resets cleanly

```python
async def test_streaming_back_to_back_no_leakage(make_icoder_app):
    """Back-to-back streams: buffer resets, no text leaks between streams."""
```

**Approach:** Use `FakeLLMService(responses=[stream1_events, stream2_events])` — it pops responses in order. Submit two messages sequentially.

```python
app = make_icoder_app(responses=[
    [  # First stream
        {"type": "text_delta", "text": "first"},
        {"type": "done"},
    ],
    [  # Second stream
        {"type": "text_delta", "text": "second"},
        {"type": "done"},
    ],
])
# Submit "msg1", wait, submit "msg2", wait
# Verify "first" and "second" are separate entries in recorded_lines
# Verify no "firstsecond" concatenation
```

### Test h) Tool event mid-line — partial flushed first, then tool block

```python
async def test_streaming_tool_event_mid_line(make_icoder_app):
    """Tool event mid-line: partial text flushed before tool block."""
```

**Approach:** Response sequence with text chunks, then tool_use_start, tool_result, more text, done.

```python
app = make_icoder_app(responses=[[
    {"type": "text_delta", "text": "before tool"},
    {"type": "tool_use_start", "name": "mcp__workspace__read_file", "args": {"file_path": "x.py"}},
    {"type": "tool_result", "name": "mcp__workspace__read_file", "output": "content"},
    {"type": "text_delta", "text": "after tool"},
    {"type": "done"},
]])
# Verify recorded_lines ordering:
#   1. the user-input echo line, whatever form it takes
#      (verify the actual echo format against InputArea behavior during implementation)
#   2. "before tool" (flushed partial)
#   3. tool start line (┌ workspace > read_file...)
#   4. tool result lines (│ ... └ done)
#   5. "after tool" (flushed at stream end)
```

## DATA — Assertions pattern

For ordering tests (f, h), check that the flushed partial appears at an earlier index than the subsequent event:

```python
lines = output.recorded_lines
partial_idx = lines.index("partial_text")
error_idx = next(i for i, l in enumerate(lines) if l.startswith("Error:"))
assert partial_idx < error_idx
```

## Commit message

```
test(icoder): add streaming edge-case tests f-h (#735)

- f: stream error mid-line flushes partial before error
- g: back-to-back streams reset buffer cleanly
- h: tool event mid-line flushes partial before tool block
```
