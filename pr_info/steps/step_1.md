# Step 1 — Streaming core additions: `stream_file` + `reason` discriminator

**Reference:** See [summary.md](./summary.md) (Architectural changes 3 & 4). This step makes the
streaming core carry the two pieces the drain-wrapper (Step 2) needs: a `stream_file` value on the
assembled response, and a machine-readable discriminator on the timeout error-event. Purely
additive — no execution-path change yet.

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
    ... existing usage/tool_trace/error ...
```

## DATA
- New event: `{"type": "stream_file", "path": str}` (emitted once, first).
- Error events gain `reason: "inactivity_timeout" | "nonzero_exit"` (plus `timeout` / `return_code`).
- `ResponseAssembler.result()["raw_response"]` gains optional `"stream_file": str`.

## TESTS (write first)
- Assembler: feeding a `stream_file` event puts `stream_file` into `raw_response`; absent event →
  key absent; existing text/usage/error behavior unchanged.
- Stream: first yielded event is `stream_file`; on inactivity the error event has
  `reason == "inactivity_timeout"`; on nonzero exit `reason == "nonzero_exit"`. Update any existing
  test that compares an error event with `==` to expect the new keys.

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md`). TDD: first add
> tests in `tests/llm/test_types.py` and the Claude stream test module for (a) `ResponseAssembler`
> capturing a `stream_file` event into `raw_response["stream_file"]`, and (b)
> `ask_claude_code_cli_stream` emitting a `stream_file` first-event and tagging its timeout /
> nonzero-exit error events with a `reason` discriminator. Then implement the minimal changes in
> `types.py` and `claude_code_cli_streaming.py`. Do not touch the blocking `ask_claude_code_cli`
> yet. Keep it additive; formatters must need no changes. Run pylint, pytest (`-n auto`, unit
> markers excluded), and mypy until green; one commit.
