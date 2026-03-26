# Step 5: prompt_llm_stream() Interface + Stream Print Formatting

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 5: add `prompt_llm_stream()` to `src/mcp_coder/llm/interface.py` and add `print_stream_event()` to `src/mcp_coder/llm/formatting/formatters.py`. Follow TDD — write tests first, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(interface): add prompt_llm_stream and stream formatting`.

## WHERE

- **Modify**: `src/mcp_coder/llm/interface.py`
- **Modify**: `src/mcp_coder/llm/formatting/formatters.py`
- **Modify**: `tests/llm/test_interface.py`
- **Modify**: `tests/llm/formatting/test_formatters.py`

## WHAT

### New function in `interface.py`:

```python
def prompt_llm_stream(
    question: str,
    provider: str = "claude",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    execution_dir: str | None = None,
    mcp_config: str | None = None,
    branch_name: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream LLM responses as events.

    Same parameters as prompt_llm(). Returns an iterator of StreamEvent
    dicts instead of a single LLMResponseDict.

    Does NOT wrap in mlflow_conversation context — the caller should handle
    mlflow logging after assembling the final response (see Step 6 for details
    on how _execute_prompt_streaming logs via mlflow_conversation after assembly).

    Yields:
        StreamEvent dicts from the underlying provider.

    Raises:
        ValueError: If provider is not supported or input validation fails.
    """
```

### New function in `formatters.py`:

```python
def print_stream_event(
    event: StreamEvent,
    output_format: str,
    file: TextIO = sys.stdout,
    err_file: TextIO = sys.stderr,
) -> None:
    """Print a single stream event to stdout based on output format.

    Args:
        event: StreamEvent dict to print
        output_format: One of "text", "ndjson", "json-raw"
        file: Output stream for normal output (default: stdout)
        err_file: Output stream for errors (default: stderr)

    Behavior by format:
        text: Print text_delta content inline (no newline between deltas).
              Tool calls shown with bordered sections.
        ndjson: Print normalized NDJSON line (Claude CLI schema).
        json-raw: Print raw_line content as-is.
    """
```

## HOW

### `prompt_llm_stream()`:
- Import `StreamEvent` from `.types`
- Import `Iterator` from `collections.abc`
- Add to `__all__`
- Input validation: same as `prompt_llm()` (empty question, timeout <= 0, unsupported provider)
- Provider env override: same as `prompt_llm()`
- Routes to:
  - `"claude"` → `ask_claude_code_cli_stream()` (lazy import)
  - `"langchain"` → `ask_langchain_stream()` (lazy import)
- No MLflow wrapping — caller handles that after assembly

### `print_stream_event()`:
- Import `sys`, `json` and `StreamEvent` from `...llm.types`
- Add to `__all__`
- `text` format:
  - `text_delta` → `print(event["text"], end="", flush=True)`
  - `tool_use_start` → print bordered header: `── tool: name(args) ──`
  - `tool_result` → print result text + border close: `──────────────────────────`
  - `error` → `print(event["message"], file=err_file)`
  - `done` → `print()` (final newline)
- `ndjson` format:
  - Map each event to Claude CLI stream-json schema, print as JSON line
  - `text_delta` → `{"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}}`
  - `tool_use_start` → `{"type": "assistant", "message": {"content": [{"type": "tool_use", ...}]}}`
  - `done` → `{"type": "result", ...}`
- `json-raw` format:
  - Only handle `raw_line` events: `print(event["line"])`

## ALGORITHM

### prompt_llm_stream:
```
def prompt_llm_stream(question, provider, ...):
    validate(question, timeout, provider)
    provider = os.environ.get("MCP_CODER_LLM_PROVIDER") or provider
    if provider == "langchain":
        from .providers.langchain import ask_langchain_stream
        yield from ask_langchain_stream(question, session_id, timeout, mcp_config, execution_dir, env_vars)
    else:
        from .providers.claude.claude_code_cli import ask_claude_code_cli_stream
        yield from ask_claude_code_cli_stream(question, session_id, timeout, env_vars, cwd=execution_dir, mcp_config=mcp_config, branch_name=branch_name)
```

### print_stream_event:
```
def print_stream_event(event, output_format, file, err_file):
    event_type = event.get("type")
    if output_format == "json-raw":
        if event_type == "raw_line": print(event["line"], file=file, flush=True)
    elif output_format == "ndjson":
        print(json.dumps(normalize_to_claude_schema(event)), file=file, flush=True)
    else:  # text
        if event_type == "text_delta": print(event["text"], end="", file=file, flush=True)
        elif event_type == "tool_use_start": print(f"\n── tool: {event['name']}({format_args(event.get('args'))}) ──", file=file)
        elif event_type == "tool_result": print(f"{event.get('output', '')}\n{'─' * 26}", file=file)
        elif event_type == "error": print(event["message"], file=err_file)
        elif event_type == "done": print(file=file)  # final newline
```

## DATA

### ndjson normalized schema (Claude CLI stream-json compatible)

```python
# text_delta → assistant message
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Hello"}]}}

# tool_use_start → assistant message with tool_use
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "", "name": "sleep", "input": {"seconds": 2}}]}}

# tool_result → user message with tool_result
{"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "", "content": "done"}]}}

# done → result message
{"type": "result", "session_id": "abc", "usage": {...}, "total_cost_usd": 0.05}
```

## TEST CASES (write first)

### `tests/llm/test_interface.py`:
1. `test_prompt_llm_stream_validates_empty_question` — raises ValueError
2. `test_prompt_llm_stream_validates_timeout` — raises ValueError for timeout <= 0
3. `test_prompt_llm_stream_validates_provider` — raises ValueError for unsupported provider
4. `test_prompt_llm_stream_routes_to_claude` — mock ask_claude_code_cli_stream, verify called
5. `test_prompt_llm_stream_routes_to_langchain` — mock ask_langchain_stream, verify called
6. `test_prompt_llm_stream_env_override` — set MCP_CODER_LLM_PROVIDER env var, verify override

### `tests/llm/formatting/test_formatters.py`:
7. `test_print_stream_event_text_delta` — verify text printed with no newline
8. `test_print_stream_event_tool_use_bordered` — verify bordered section header
9. `test_print_stream_event_tool_result_bordered` — verify result + border close
10. `test_print_stream_event_error_to_stderr` — verify error goes to stderr
11. `test_print_stream_event_done_newline` — verify final newline
12. `test_print_stream_event_ndjson_text` — verify JSON line with Claude schema
13. `test_print_stream_event_json_raw` — verify raw_line passthrough
