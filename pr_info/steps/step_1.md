# Step 1: Fix `MultiServerMCPClient` Breaking Change

> **Summary**: [pr_info/steps/summary.md](summary.md)
> **Priority**: 🔴 CRITICAL — blocks all LangChain agent mode usage

## LLM Prompt

```
Implement Step 1 of issue #528: Fix the MultiServerMCPClient breaking change in agent.py.

Read pr_info/steps/summary.md for full context, then read this step file for details.

The `langchain-mcp-adapters>=0.1.0` removed the async context manager from `MultiServerMCPClient`. 
The client is now stateless — plain instantiation, no cleanup needed. `client.session()` manages 
its own lifecycle.

Update src/mcp_coder/llm/providers/langchain/agent.py:
- Remove `async with MultiServerMCPClient(...)` context manager wrapper
- Use plain `client = MultiServerMCPClient(...)`
- Dedent the body that was inside the context manager
- Keep the `async with client.session(server_name)` — that still works

Update tests first (TDD), then the implementation. Run all three code quality checks after.
```

## WHERE

- **Source**: `src/mcp_coder/llm/providers/langchain/agent.py` (function `run_agent()`)
- **Tests**: `tests/llm/providers/langchain/test_langchain_agent.py`

## WHAT

No new functions. Modify existing `run_agent()` signature is unchanged:

```python
async def run_agent(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
```

## HOW

Remove the `async with` wrapper around `MultiServerMCPClient`. The import stays the same.

## ALGORITHM

```
1. Load server config from .mcp.json (unchanged)
2. client = MultiServerMCPClient(server_config)          # was: async with ... as client
3. For each server, async with client.session() to list tools (unchanged)
4. Create ReAct agent, invoke with timeout (unchanged)
5. Extract final text, compute stats (unchanged — was already outside context manager for stats)
```

## DATA

Return type unchanged: `tuple[str, list[dict[str, Any]], dict[str, Any]]`

## Code Change

```python
# BEFORE (broken):
async with MultiServerMCPClient(cast(Any, server_config)) as client:
    all_tools = []
    for server_name, connection in client.connections.items():
        ...
    agent = create_react_agent(chat_model, all_tools)
    ...
    result = await asyncio.wait_for(...)
    output_messages = result["messages"]

# AFTER (fixed):
client = MultiServerMCPClient(cast(Any, server_config))
all_tools = []
for server_name, connection in client.connections.items():
    ...
agent = create_react_agent(chat_model, all_tools)
...
result = await asyncio.wait_for(...)
output_messages = result["messages"]
```

## Test Changes

Update any test mocks that patch `MultiServerMCPClient` as an async context manager to use plain instantiation instead. The mock should return the client directly, not via `__aenter__`.
