# Step 2: `run_agent_stream()` Accepts Optional Pre-built Tools

> **Ref:** [summary.md](summary.md) — "Modified Components → Langchain agent"

## LLM Prompt

> Implement Step 2 from `pr_info/steps/step_2.md`. Read `pr_info/steps/summary.md` for full context.
> Add optional `tools` parameter to `run_agent_stream()` in `src/mcp_coder/llm/providers/langchain/agent.py`.
> When tools are provided, skip `MultiServerMCPClient` creation. When not provided, behave exactly as today.
> Follow TDD: write/update tests first, then implement. Run all code quality checks after.

## WHERE

- **Modified:** `src/mcp_coder/llm/providers/langchain/agent.py`
- **Modified:** `tests/llm/providers/langchain/test_langchain_agent_streaming.py`

## WHAT

### Signature change for `run_agent_stream()`

```python
async def run_agent_stream(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    session_id: str,
    cancel_event: threading.Event | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    tools: list[Any] | None = None,  # NEW — pre-built tools from MCPManager
) -> AsyncIterator[StreamEvent]:
```

## HOW

- Add `tools: list[Any] | None = None` as last parameter
- At the top of the function, after imports: if `tools is not None`, skip the entire `MultiServerMCPClient` + tool discovery block and use `tools` directly as `all_tools`
- If `tools is None`, execute existing client creation + tool discovery (unchanged)
- No other behavioral changes

## ALGORITHM — modified tool loading section

```
if tools is not None:
    all_tools = tools
else:
    # existing code: _load_mcp_server_config, MultiServerMCPClient, etc.
    server_config = _load_mcp_server_config(mcp_config_path, env_vars)
    client = MultiServerMCPClient(...)
    all_tools = []
    # ... existing tool discovery loop ...
```

## DATA

- `tools` parameter: `list[Any] | None` — LangChain `BaseTool` instances from `MCPManager.tools()`, or `None` for existing behavior
- All other parameters and return values unchanged

## TEST PLAN

Update/add tests in the existing langchain agent test files:

1. `test_run_agent_stream_with_prebuilt_tools` — pass `tools=[mock_tool]`, verify `MultiServerMCPClient` is NOT instantiated, verify agent runs with provided tools
2. `test_run_agent_stream_without_tools_uses_client` — pass `tools=None` (default), verify `MultiServerMCPClient` IS instantiated (existing behavior)
3. Existing tests must continue to pass unchanged (they don't pass `tools`, so they get the default `None` path)

## COMMIT

```
feat(langchain): run_agent_stream accepts pre-built tools (#741)
```
