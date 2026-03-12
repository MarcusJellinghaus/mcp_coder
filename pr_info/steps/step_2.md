# Step 2: Agent Execution Core

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 1 (agent.py utilities must exist).

## LLM Prompt

```
Implement Step 2 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: add the core agent execution function `run_agent()` to agent.py.
It uses MultiServerMCPClient + create_react_agent to run an LLM agent with
MCP tools. Follow TDD — write tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/agent.py` — add `run_agent()` async function

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_agent.py` — add agent execution tests

## WHAT

### `agent.py` — add `run_agent()`

```python
async def run_agent(
    question: str,
    chat_model: object,  # BaseChatModel from langchain
    messages: list[dict[str, object]],
    mcp_config_path: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> tuple[str, list[dict[str, object]], dict[str, object]]
    """Run a LangGraph ReAct agent with MCP tools.

    Returns:
        Tuple of (final_text, full_message_history, stats_dict).
        stats_dict contains: agent_steps, total_tool_calls, tool_trace.
    """
```

## HOW

### Imports (deferred, inside function body)
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
```

### Integration with Step 1
- Calls `_load_mcp_server_config()` from Step 1 to get resolved MCP config
- Uses `AGENT_MAX_STEPS` constant from Step 1

### Error handling
- **MCP server startup failure**: any exception from `MultiServerMCPClient.__aenter__` → let it propagate (hard fail per issue requirement)
- **Tool call errors**: handled by the agent itself (LangGraph passes errors back as ToolMessage)
- **Max iterations**: use `recursion_limit=AGENT_MAX_STEPS` in agent invoke config; on limit, return whatever partial output exists

### Message history (Decision 15 — LangChain native serialization)
- Deserialize `messages` (list of dicts) to LangChain message objects using `messages_from_dict()` from `langchain_core.messages`
- This handles all message types natively: HumanMessage, AIMessage (with tool_calls), ToolMessage
- After agent run, serialize full history back to dicts via `.dict()` / `.model_dump()`
- No custom `_to_lc_messages()` extension needed

## ALGORITHM

```
server_config = _load_mcp_server_config(mcp_config_path, env_vars)
async with MultiServerMCPClient(server_config) as client:
    tools = client.get_tools()
    agent = create_react_agent(chat_model, tools)
    input_messages = messages_from_dict(messages) + [HumanMessage(question)]
    result = await agent.ainvoke(
        {"messages": input_messages},
        config={"recursion_limit": AGENT_MAX_STEPS},
    )
    output_messages = result["messages"]
    final_text = extract last AIMessage content from output_messages
    stats = compute agent_steps, total_tool_calls, tool_trace from output_messages
    serialized = [msg.dict() for msg in output_messages]
    return (final_text, serialized, stats)
```

## DATA

### Return tuple

```python
(
    "Here's the plan: ...",           # final_text: str
    [                                  # message_history: list[dict]
        {"type": "human", "content": "Create a plan..."},
        {"type": "ai", "content": "", "tool_calls": [...]},
        {"type": "tool", "name": "read_file", "content": "..."},
        {"type": "ai", "content": "Here's the plan: ..."},
    ],
    {                                  # stats: dict
        "agent_steps": 3,
        "total_tool_calls": 2,
        "tool_trace": [
            {"name": "read_file", "args": {"path": "src/main.py"}, "result": "..."},
        ],
    },
)
```

## TEST CASES

### `test_langchain_agent.py` — additions

```python
class TestRunAgent:
    @pytest.mark.asyncio
    async def test_returns_final_text(self)
        """Agent returns the final AIMessage content as text."""

    @pytest.mark.asyncio
    async def test_returns_message_history(self)
        """Full message history is serialized and returned."""

    @pytest.mark.asyncio
    async def test_returns_stats_with_tool_counts(self)
        """Stats dict contains agent_steps and total_tool_calls."""

    @pytest.mark.asyncio
    async def test_hard_fails_on_mcp_server_error(self)
        """If MultiServerMCPClient fails to start, exception propagates."""

    @pytest.mark.asyncio
    async def test_max_iterations_returns_partial_output(self)
        """When recursion limit reached, returns partial output (no crash)."""

    @pytest.mark.asyncio
    async def test_prepends_session_history(self)
        """Previous message history is prepended to agent input."""

    @pytest.mark.asyncio
    async def test_tool_trace_in_stats(self)
        """Stats contain tool_trace with name, args, result for each tool call."""
```

### Mock strategy
- Mock `MultiServerMCPClient` as async context manager returning mock tools
- Mock `create_react_agent` to return a mock agent
- Mock agent's `ainvoke` to return a canned `{"messages": [...]}` result
- Use `MagicMock` for chat_model (not testing actual LLM calls)
