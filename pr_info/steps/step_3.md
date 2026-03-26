# Step 3: Claude CLI Streaming Provider

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 3: add `ask_claude_code_cli_stream()` to `src/mcp_coder/llm/providers/claude/claude_code_cli.py`. Follow TDD — write tests first in `tests/llm/providers/claude/test_claude_code_cli.py`, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(claude): add ask_claude_code_cli_stream`.

## WHERE

- **Modify**: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- **Modify**: `tests/llm/providers/claude/test_claude_code_cli.py`

## WHAT

### New function in `claude_code_cli.py`:

```python
def ask_claude_code_cli_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    mcp_config: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream Claude CLI responses as events.

    Same parameters as ask_claude_code_cli(). Instead of returning a single
    LLMResponseDict, yields StreamEvent dicts as each NDJSON line arrives
    from the Claude CLI subprocess.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error, raw_line

    The "done" event includes session_id and usage data from the result message.
    The "raw_line" event wraps each raw NDJSON line for json-raw mode consumers.
    """
```

## HOW

- Import `stream_subprocess`, `StreamResult` from `....utils.subprocess_runner`
- Import `StreamEvent` from `...types`
- Add `Iterator` import from `collections.abc`
- Reuse existing `build_cli_command()`, `format_stream_json_input()`, `parse_stream_json_line()`
- Reuse existing `_find_claude_executable()`, `get_stream_log_path()`
- Each NDJSON line from `stream_subprocess()` is parsed, then mapped to `StreamEvent`:
  - `assistant` message with text content → `text_delta` event
  - `assistant` message with tool_use content → `tool_use_start` event
  - `assistant` message with tool_result content → `tool_result` event
  - `result` message → `done` event (with session_id, usage, cost)
  - Every line also yields a `raw_line` event (for json-raw mode)
- Stream log file is written line-by-line (append) as lines arrive
- Error handling: on subprocess error, yield `error` event then raise

## ALGORITHM

```
def ask_claude_code_cli_stream(question, ...):
    claude_cmd = _find_claude_executable()
    command = build_cli_command(session_id, claude_cmd, mcp_config)
    stream_file = get_stream_log_path(logs_dir, cwd, branch_name)
    input_data = format_stream_json_input(question)
    options = CommandOptions(timeout_seconds=timeout, input_data=input_data, env=env_vars, cwd=cwd)

    stream = StreamResult(stream_subprocess(command, options))
    with open(stream_file, 'w') as log:
        for line in stream:
            log.write(line + '\n'); log.flush()
            yield {"type": "raw_line", "line": line}
            msg = parse_stream_json_line(line)
            if msg: yield _map_stream_message_to_event(msg)

    cmd_result = stream.result
    if cmd_result.timed_out:
        yield {"type": "error", "message": f"Timed out after {timeout}s"}
    if cmd_result.return_code != 0:
        yield {"type": "error", "message": f"CLI failed with code {cmd_result.return_code}"}
```

## DATA

### Input
- Same as `ask_claude_code_cli()` — question, session_id, timeout, etc.

### Output (yielded StreamEvents)
```python
{"type": "raw_line", "line": '{"type":"system","session_id":"abc"}'}
{"type": "text_delta", "text": "Hello "}
{"type": "text_delta", "text": "world"}
{"type": "tool_use_start", "name": "sleep", "args": {"seconds": 2}}
{"type": "tool_result", "name": "sleep", "output": "done"}
{"type": "done", "session_id": "abc123", "usage": {"input_tokens": 100}, "cost_usd": 0.05}
```

### Mapping: StreamMessage → StreamEvent

| StreamMessage type | Content block type | StreamEvent type |
|---|---|---|
| `system` | — | (no event, session_id extracted for done) |
| `assistant` | `text` | `text_delta` |
| `assistant` | `tool_use` | `tool_use_start` |
| `assistant` | `tool_result` | `tool_result` |
| `result` | — | `done` |

## TEST CASES (write first)

1. `test_ask_claude_stream_yields_text_delta` — mock stream_subprocess to yield NDJSON with assistant text, verify text_delta events
2. `test_ask_claude_stream_yields_tool_events` — mock NDJSON with tool_use/tool_result blocks, verify events
3. `test_ask_claude_stream_yields_done` — mock NDJSON with result message, verify done event with session_id/usage
4. `test_ask_claude_stream_yields_raw_lines` — verify every line produces a raw_line event
5. `test_ask_claude_stream_writes_log_file` — verify NDJSON lines written to log file
6. `test_ask_claude_stream_timeout_yields_error` — mock timed-out StreamResult, verify error event
7. `test_ask_claude_stream_nonzero_exit_yields_error` — mock failed StreamResult, verify error event
