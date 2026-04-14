# Step 1: MCPManager — Persistent MCP Client

> **Ref:** [summary.md](summary.md) — "New Components → MCPManager"

## LLM Prompt

> Implement Step 1 from `pr_info/steps/step_1.md`. Read `pr_info/steps/summary.md` for full context.
> Create the `MCPManager` class in `src/mcp_coder/llm/mcp_manager.py` with tests in `tests/llm/test_mcp_manager.py`.
> Follow TDD: write tests first, then implement. Run all code quality checks after.

## WHERE

- **New:** `src/mcp_coder/llm/mcp_manager.py`
- **New:** `tests/llm/test_mcp_manager.py`

## WHAT

### `MCPManager` class

```python
from __future__ import annotations

@dataclass(frozen=True)
class MCPServerStatus:
    """Status of a single MCP server connection."""
    name: str
    tool_count: int
    connected: bool

class MCPManager:
    """Persistent MCP client with background event loop.

    Owns MCP server connections for the app's lifetime.
    Lazy: connects on first tools() call, not at construction.
    """

    def __init__(
        self,
        server_config: dict[str, dict[str, object]],
    ) -> None:
        self._server_names = list(server_config.keys())
        ...

    def tools(self) -> list[Any]:
        """Return cached LangChain tools. Connects lazily on first call.
        On failure, recreates client on next call."""
        ...

    def status(self) -> list[MCPServerStatus]:
        """Return connection status for each configured server."""
        ...

    def close(self) -> None:
        """Shut down MCP servers, stop event loop, join thread."""
        ...
```

## HOW

- Uses `_load_mcp_server_config()` and `_sanitize_tool_schema()` from `agent.py` (import them)
- Langchain imports (`MultiServerMCPClient`, `convert_mcp_tool_to_langchain_tool`, etc.) are deferred — only imported inside methods that need them
- Background daemon thread with `asyncio` event loop created in `__init__`
- `asyncio.run_coroutine_threadsafe()` dispatches async work from sync `tools()`/`close()`

## ALGORITHM — `tools()` (core logic)

```
if cached_tools is not None:
    return cached_tools
future = run_coroutine_threadsafe(_connect_and_discover(), loop)
cached_tools = future.result(timeout=60)
return cached_tools
```

## ALGORITHM — `_connect_and_discover()` (async, runs on background loop)

```
client = MultiServerMCPClient(server_config)
all_tools = []
for server_name, connection in client.connections.items():
    async with client.session(server_name) as session:
        raw_tools = await session.list_tools()
        for tool in raw_tools.tools:
            sanitized = _sanitize_tool_schema(tool.inputSchema)
            tool = tool.model_copy(update={"inputSchema": sanitized})
            lc_tool = convert_mcp_tool_to_langchain_tool(None, tool, connection=connection, server_name=server_name)
            all_tools.append(lc_tool)
return all_tools
```

## ALGORITHM — `close()`

```
if client exists:
    run_coroutine_threadsafe(client.__aexit__(), loop).result(timeout=5)
if loop is running:
    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=5)
```

## DATA

- `server_config`: `dict[str, dict[str, object]]` — output of `_load_mcp_server_config()`
- `tools()` returns: `list[Any]` (LangChain `BaseTool` instances)
- `status()` returns: `list[MCPServerStatus]`
- Internal state: `_cached_tools: list[Any] | None`, `_client: MultiServerMCPClient | None`, `_loop: asyncio.AbstractEventLoop`, `_thread: threading.Thread`, `_server_names: list[str]` — initialized from `server_config.keys()` in `__init__` so `status()` can report all configured servers even before connection

## TEST PLAN (`tests/llm/test_mcp_manager.py`)

All tests mock `MultiServerMCPClient` — no real MCP servers.

1. `test_tools_returns_cached_tools` — after first call, second call returns same list without reconnecting
2. `test_tools_lazy_connect` — constructor does NOT connect; connection happens on first `tools()` call
3. `test_status_before_connect` — returns all servers as `connected=False, tool_count=0`
4. `test_status_after_connect` — returns servers as `connected=True` with correct tool counts
5. `test_close_stops_loop` — after `close()`, background thread is no longer alive
6. `test_close_idempotent` — calling `close()` twice does not raise
7. `test_tools_recreates_on_failure` — if `_connect_and_discover` fails, next `tools()` call retries (clears cache)
8. `test_empty_server_config` — empty config returns empty tools list

## COMMIT

```
feat(llm): add MCPManager for persistent MCP connections (#741)
```
