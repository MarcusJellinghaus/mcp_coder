# Step 6: Copilot streaming

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 6 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Create `copilot_cli_streaming.py` with `ask_copilot_cli_stream()` that yields `StreamEvent` dicts as Copilot JSONL lines arrive. Map Copilot message types to the project's StreamEvent format. Handle `session.info` unknown-tool warnings with dual surfacing (WARNING log + error StreamEvent). Follow TDD.

## WHERE

### New files
- `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py`
- `tests/llm/providers/copilot/test_copilot_cli_streaming.py`

### Modified files
- `src/mcp_coder/llm/providers/copilot/__init__.py` (add exports)

## WHAT

### `copilot_cli_streaming.py`

```python
def _map_copilot_message_to_event(
    msg: dict[str, Any],
) -> Iterator[StreamEvent]:
    """Map a parsed Copilot JSONL message to StreamEvent(s).

    Mapping:
    - assistant.message → text_delta (for text), tool_use_start (for toolRequests)
    - tool.execution_complete → tool_result
    - result → done (with session_id, usage)
    - session.info with unknown-tool warning → error StreamEvent + WARNING log
    - All other types → skipped (ephemeral)
    """

def ask_copilot_cli_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
    system_prompt: str | None = None,
    execution_dir: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream Copilot CLI responses as events.

    Same parameters as ask_copilot_cli(). Yields StreamEvent dicts
    as each JSONL line arrives from the subprocess.

    Args:
        execution_dir: Directory to read .claude/settings.local.json from

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result,
        done, error, raw_line
    """
```

### `__init__.py` updated exports
```python
from .copilot_cli import ask_copilot_cli
from .copilot_cli_streaming import ask_copilot_cli_stream
```

## HOW

- Imports `stream_subprocess` from `mcp_coder.utils.subprocess_streaming`
- Imports `CommandOptions`, `CommandResult` from subprocess_runner
- Imports `parse_copilot_jsonl_line`, `build_copilot_command`, `convert_settings_to_copilot_tools`, `_read_settings_allow` from `.copilot_cli`
- Imports `find_executable` from `mcp_coder.utils.executable_finder`
- Imports `get_stream_log_path` from `.copilot_cli_log_paths`
- Uses same `raw_line` passthrough pattern as Claude streaming for `json-raw` mode

## ALGORITHM

### Event mapping
```
1. Parse each JSONL line via parse_copilot_jsonl_line()
2. Yield {"type": "raw_line", "line": line} for every line
3. If type == "assistant.message": yield text_delta for each text content block, tool_use_start for each toolRequest
4. If type == "tool.execution_complete": yield tool_result
5. If type == "result": yield done with session_id (from sessionId), usage mapping
6. If type == "session.info" and message contains "unknown tool": log WARNING + yield error event
7. All other types: skip
```

### Stream orchestration
```
1. Find executable, build prompt (prepend system prompt if new session)
2. Read settings_allow via _read_settings_allow(execution_dir), convert via convert_settings_to_copilot_tools(), build command
3. Open log file, start stream_subprocess
4. For each line: write to log, yield raw_line, parse and yield mapped events
5. After stream ends: check result for timeout/error, yield error event if needed
```

## DATA

### StreamEvent mapping table

| Copilot JSONL type | StreamEvent type | Fields |
|---|---|---|
| `assistant.message` (text) | `text_delta` | `{"type": "text_delta", "text": "..."}` |
| `assistant.message` (toolRequest) | `tool_use_start` | `{"type": "tool_use_start", "name": "...", "args": {...}}` |
| `tool.execution_complete` | `tool_result` | `{"type": "tool_result", "name": "...", "output": "..."}` |
| `result` | `done` | `{"type": "done", "session_id": "...", "usage": {...}}` |
| `session.info` (unknown tool) | `error` | `{"type": "error", "message": "..."}` |
| Any line | `raw_line` | `{"type": "raw_line", "line": "..."}` |

## Tests

### `tests/llm/providers/copilot/test_copilot_cli_streaming.py`

#### Event mapping tests (unit, no subprocess)
- `test_map_assistant_message_text` — text content → text_delta event
- `test_map_assistant_message_tool_request` — toolRequests → tool_use_start event
- `test_map_tool_execution_complete` — tool result → tool_result event
- `test_map_result_to_done` — result → done event with session_id and usage
- `test_map_session_info_unknown_tool_warning` — unknown-tool → error event + warning logged
- `test_map_ephemeral_types_skipped` — session.mcp_servers_loaded, assistant.reasoning etc. yield nothing
- `test_map_assistant_message_delta_skipped` — assistant.message_delta yields nothing

#### Stream integration tests (mocked subprocess)
- `test_stream_yields_raw_line_for_each_line` — every line produces raw_line event
- `test_stream_yields_text_and_done` — full JSONL output produces text_delta + done
- `test_stream_timeout_yields_error` — timeout → error event
- `test_stream_nonzero_exit_yields_error` — failed process → error event
- `test_stream_writes_log_file` — verify JSONL written to copilot-sessions/
