# Step 1 — Streaming core additions: `stream_file` + `reason` discriminator + text parity

**Reference:** See [summary.md](./summary.md) (Architectural changes 3 & 4). This step makes the
streaming core carry the pieces the drain-wrapper (Step 2) needs: a `stream_file` value on the
assembled response, a machine-readable discriminator on the timeout error-event, and **byte-identical
top-level `text`** (AC3) so the assembler matches today's blocking `_parse_stream_lines` output.
Purely additive — no execution-path change yet.

## WHERE
- `src/mcp_coder/llm/types.py` — `ResponseAssembler`.
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — `ask_claude_code_cli_stream`.
- Tests: `tests/llm/test_types.py`, `tests/llm/providers/claude/test_claude_cli_stream_parsing.py`
  (or the closest existing stream test module).

## WHAT
- `ResponseAssembler.add(self, event)` — additionally capture a `stream_file` event:
  when `event["type"] == "stream_file"`, store `self._stream_file: str | None`.
- `ResponseAssembler.result(self) -> LLMResponseDict` — include `raw_response["stream_file"]`
  when captured.
- `ResponseAssembler` — **text parity** (AC3): the assembled top-level `text` must be
  byte-identical to today's blocking `_parse_stream_lines` output. Two behaviors to add:
  (a) `.strip()` the concatenated `text_delta` text; and (b) when **no** `text_delta` /
  assistant-text event was seen, fall back to the final result message's `result` value
  (`_parse_stream_lines` only uses the result field when there were zero assistant text blocks).
- `ask_claude_code_cli_stream(...)` — yield one new event **before** iterating the subprocess,
  and tag the two terminal error events with a structured `reason`.

## HOW
- No signature changes. `StreamEvent` stays `dict[str, object]`; new keys are additive.
- `print_stream_event` and `StreamEventRenderer` already ignore unknown event types
  (renderer returns `None`), so **no formatter changes** are required.

## ALGORITHM
Streaming module (`ask_claude_code_cli_stream`), around existing `stream_file` computation:
```
stream_file = get_stream_log_path(logs_dir, cwd, branch_name)   # existing
yield {"type": "stream_file", "path": str(stream_file)}         # NEW: first event
... existing subprocess iteration + MCP guard unchanged ...
if cmd_result.timed_out:
    yield {"type": "error", "reason": "inactivity_timeout",     # NEW key
           "timeout": timeout, "message": "LLM inactivity timeout (claude): ..."}
elif cmd_result.return_code != 0:
    yield {"type": "error", "reason": "nonzero_exit",           # NEW key
           "return_code": cmd_result.return_code, "message": "CLI failed with code ..."}
```
Assembler:
```
def add(self, event):
    self._raw_events.append(event)
    t = event.get("type")
    if t == "stream_file":
        p = event.get("path")
        if isinstance(p, str): self._stream_file = p
    ... existing branches ...
def result(self):
    raw = {"events": list(self._raw_events)}
    if self._stream_file is not None: raw["stream_file"] = self._stream_file
    # text parity (AC3): strip assembled text; fall back to result-message
    # `result` only when no text_delta/assistant-text was seen.
    text = self._text.strip()
    if not self._saw_assistant_text and self._result_text is not None:
        text = self._result_text.strip()
    ... existing usage/tool_trace/error ...
```

## DATA
- New event: `{"type": "stream_file", "path": str}` (emitted once, first).
- Error events gain `reason: "inactivity_timeout" | "nonzero_exit"` (plus `timeout` / `return_code`).
- `ResponseAssembler.result()["raw_response"]` gains optional `"stream_file": str`.

## TESTS (write first)
- Assembler: feeding a `stream_file` event puts `stream_file` into `raw_response`; absent event →
  key absent; existing text/usage/error behavior unchanged.
- Assembler **text parity** (AC3): assembled `text` is `.strip()`-ed (leading/trailing whitespace
  removed to match `_parse_stream_lines`); and when no `text_delta`/assistant-text event is fed
  but a result message carries a `result` value, `text` falls back to that stripped `result`.
- Stream: first yielded event is `stream_file`; on inactivity the error event has
  `reason == "inactivity_timeout"`; on nonzero exit `reason == "nonzero_exit"`. Update any existing
  test that compares an error event with `==` to expect the new keys.

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md`). TDD: first add
> tests in `tests/llm/test_types.py` and the Claude stream test module for (a) `ResponseAssembler`
> capturing a `stream_file` event into `raw_response["stream_file"]`, (b) `ResponseAssembler` text
> parity (AC3): stripping the assembled text and falling back to the result-message `result` when no
> assistant text was seen, and (c) `ask_claude_code_cli_stream` emitting a `stream_file` first-event
> and tagging its timeout / nonzero-exit error events with a `reason` discriminator. Then implement
> the minimal changes in
> `types.py` and `claude_code_cli_streaming.py`. Do not touch the blocking `ask_claude_code_cli`
> yet. Keep it additive; formatters must need no changes. Run pylint, pytest (`-n auto`, unit
> markers excluded), and mypy until green; one commit.
