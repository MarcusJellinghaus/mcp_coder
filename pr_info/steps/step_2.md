# Step 2 — Unify the three tool-build loops + `MCPManager` interceptor param (D1)

**Reference:** read `pr_info/steps/summary.md` (Decision D1) before starting.

Collapse the three near-duplicate `convert_mcp_tool_to_langchain_tool` build loops into one shared
helper that accepts `tool_interceptors`, and give `MCPManager` a pass-through `tool_interceptors`
constructor parameter. No gateway/policy yet — every site still passes `None` by default. This creates
the single injection point.

## WHERE
- `src/mcp_coder/llm/providers/langchain/agent.py` — new `_convert_server_tools()`; rewire
  `run_agent()` and `run_agent_stream()` (else-branch).
- `src/mcp_coder/llm/providers/langchain/mcp_manager.py` — `MCPManager.__init__` gains
  `tool_interceptors`; `_connect_and_discover` uses the helper.
- `tests/llm/providers/langchain/test_tool_build_helper.py` (new).

## WHAT
```python
# agent.py — one home for the sanitize -> model_copy -> convert inner loop
def _convert_server_tools(
    raw_tools: list[Any],
    connection: Any,
    server_name: str,
    tool_interceptors: list[Any] | None = None,
) -> list[Any]:
    """Convert one server's raw MCP tools to LangChain tools (interceptors optional)."""

# mcp_manager.py
class MCPManager:
    def __init__(
        self,
        server_config: dict[str, dict[str, object]],
        tool_interceptors: list[Any] | None = None,
    ) -> None: ...
```

## HOW
- `_convert_server_tools` does the deferred `from langchain_mcp_adapters.tools import
  convert_mcp_tool_to_langchain_tool`, loops the raw tools, applies `_sanitize_tool_schema` +
  `model_copy`, and passes `tool_interceptors=tool_interceptors` to `convert_...`.
- `run_agent` / `run_agent_stream` (else): keep each **outer** per-server loop, its
  `try/except (FileNotFoundError, PermissionError) -> LLMMCPLaunchError`, then
  `all_tools.extend(_convert_server_tools(raw.tools, connection, server_name))` (interceptors default
  `None`).
- `MCPManager.__init__`: store `self._tool_interceptors = tool_interceptors`.
- `MCPManager._connect_and_discover`: replace its inline loop with
  `_convert_server_tools(raw.tools, connection, server_name, self._tool_interceptors)`, then keep the
  existing canonical-name metadata stamping (`lc_tool.metadata["mcp_canonical_name"] =
  f"mcp__{server_name}__{lc_tool.name}"`) on each returned tool.

## ALGORITHM (`_convert_server_tools`)
```
lc_tools = []
import convert_mcp_tool_to_langchain_tool
for tool in raw_tools:
    tool = tool.model_copy(update={"inputSchema": _sanitize_tool_schema(tool.inputSchema)})
    lc_tools.append(convert_mcp_tool_to_langchain_tool(
        None, tool, connection=connection, server_name=server_name,
        tool_interceptors=tool_interceptors))
return lc_tools
```

## DATA
- `_convert_server_tools` returns `list[Any]` (LangChain tools) — no metadata stamping (caller's job).
- `MCPManager` behaviour unchanged when `tool_interceptors is None`.

## TDD tests (write first)
- `test_convert_server_tools_forwards_interceptors` — patch `convert_mcp_tool_to_langchain_tool`,
  call the helper with a sentinel `tool_interceptors`, assert the sentinel was forwarded per tool.
- `test_convert_server_tools_sanitizes_schema` — a raw tool with a typeless property yields an
  lc tool whose schema property gained `"type": "string"`.
- `test_mcp_manager_stores_and_forwards_interceptors` — construct `MCPManager(cfg, tool_interceptors=[x])`;
  assert stored; (with `_connect_and_discover` patched) assert the helper receives it.
- `test_run_agent_stream_inline_loader_passes_no_interceptors` — the else-branch path uses the helper
  with `tool_interceptors=None`.

## Checks
Full quality gate (pylint / mypy / pytest fast / ruff / lint-imports) green.

## Commit
`I2.3 step 2: unify MCP tool-build loops into one interceptor-aware helper`

## LLM prompt
> Implement Step 2 of the I2.3 plan. Read `pr_info/steps/summary.md` (Decision D1) and
> `pr_info/steps/step_2.md`. Following TDD, first add the tests, then extract `_convert_server_tools`
> in `agent.py`, rewire `run_agent`, `run_agent_stream` (else-branch), and
> `MCPManager._connect_and_discover` onto it, and add a pass-through `tool_interceptors` parameter to
> `MCPManager.__init__`. Preserve the per-server launch-error handling and the canonical-name metadata
> stamping. Every site passes `None` for now. Use MCP tools only; make all checks pass; one commit.
