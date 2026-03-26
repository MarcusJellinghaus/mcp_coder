# Issue #586: Streaming Output for LangChain and Claude CLI Providers

## Summary

Add streaming support to `mcp-coder prompt` so tokens/events are displayed as they arrive, for both the LangChain and Claude CLI providers. Introduce new `--output-format` values (`ndjson`, `json-raw`) and remove `--verbosity`.

## Architectural / Design Changes

### Before (current)

```
execute_prompt() → prompt_llm() → provider → [buffers all output] → LLMResponseDict → format → print
```

- `prompt_llm()` is the only entry point — blocking, returns complete `LLMResponseDict`
- `execute_subprocess()` buffers all stdout until process exits
- Claude CLI output is written to NDJSON log files **after** subprocess completes
- LangChain uses `.invoke()` (blocking) and `agent.ainvoke()` (async, blocking)
- `--verbosity` (just-text/verbose/raw) controls post-hoc formatting
- `--output-format` has 3 values: text, json, session-id

### After (new)

```
execute_prompt() → prompt_llm_stream() → provider_stream → yields events → dispatch loop:
                                                              ├─ print to stdout (text/ndjson/json-raw)
                                                              └─ assemble LLMResponseDict
                 → prompt_llm() [unchanged, blocking]
```

- **New `prompt_llm_stream()`** in `interface.py` — returns `Iterator[StreamEvent]`
- **New `stream_subprocess()`** in `subprocess_runner.py` — yields stdout lines in real-time
- **Claude CLI provider**: `ask_claude_code_cli_stream()` uses `stream_subprocess()`, yields parsed NDJSON as stream events
- **LangChain provider**: `ask_langchain_stream()` uses `.stream()` / `agent.stream()` sync APIs
- **Stream events** — simple `dict[str, object]` with `type` key, defined as `StreamEvent` type alias in `types.py`
- **`ResponseAssembler`** — small helper class that accumulates stream events into `LLMResponseDict`
- **Print consumer** — single function in `formatters.py` that writes to stdout based on output format
- **`--verbosity` removed** — replaced by new `--output-format` values
- **`--output-format`** expanded to 5 values: `text`, `ndjson`, `json-raw`, `json`, `session-id`

### Key Design Decisions

1. **No consumer classes or pub/sub** — a simple `for` loop dispatches events to assembler + printer
2. **No new source files** — all source additions go into existing modules (test files may be new)
3. **`prompt_llm()` unchanged** — workflows (implement, create-pr, create-plan) are unaffected
4. **Sync only** — no async APIs for LangChain streaming
5. **Stream events are plain dicts** — no dataclass hierarchy
6. **Agent mode not streamed** — LangChain agent mode falls back to blocking `ask_langchain()` due to async MCP tool complexity. Text mode streams via `chat_model.stream()`.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/types.py` | Add `StreamEvent` type alias, `ResponseAssembler` class |
| `src/mcp_coder/utils/subprocess_runner.py` | Add `stream_subprocess()` generator function |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Add `ask_claude_code_cli_stream()` |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Add `ask_langchain_stream()`, `_ask_text_stream()` (agent mode falls back to blocking) |
| `src/mcp_coder/llm/interface.py` | Add `prompt_llm_stream()` |
| `src/mcp_coder/llm/formatting/formatters.py` | Add `print_stream_event()`, remove verbosity formatters |
| `src/mcp_coder/cli/parsers.py` | Update `--output-format` choices, remove `--verbosity` |
| `src/mcp_coder/cli/commands/prompt.py` | Add streaming path in `execute_prompt()`, remove verbosity logic |

## Test Files Modified / Created

| File | Change |
|------|--------|
| `tests/llm/test_types.py` | Tests for `StreamEvent` and `ResponseAssembler` |
| `tests/utils/test_subprocess_runner.py` | Tests for `stream_subprocess()` |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Tests for `ask_claude_code_cli_stream()` |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Tests for `ask_langchain_stream()` |
| `tests/llm/test_interface.py` | Tests for `prompt_llm_stream()` |
| `tests/llm/formatting/test_formatters.py` | Tests for `print_stream_event()` |
| `tests/cli/commands/test_prompt.py` | Update tests for new output formats, remove verbosity tests |
| `tests/cli/commands/test_prompt_streaming.py` | New: integration tests for streaming prompt command |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Stream event types + ResponseAssembler | `feat(types): add StreamEvent type and ResponseAssembler` |
| 2 | stream_subprocess() in subprocess_runner | `feat(subprocess): add stream_subprocess generator` |
| 3 | Claude CLI streaming provider | `feat(claude): add ask_claude_code_cli_stream` |
| 4 | LangChain streaming provider | `feat(langchain): add ask_langchain_stream` |
| 5 | prompt_llm_stream() interface + stream print formatting | `feat(interface): add prompt_llm_stream and stream formatting` |
| 6 | CLI changes: new output formats, remove verbosity, wire streaming | `feat(cli): add streaming output formats, remove --verbosity` |
