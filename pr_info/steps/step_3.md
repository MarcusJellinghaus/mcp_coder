# Step 3: Extend ask_langchain() with Agent Mode + MLflow

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Steps 1–2 (agent.py must be complete).

## LLM Prompt

```
Implement Step 3 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: extend ask_langchain() in __init__.py to accept mcp_config,
execution_dir, env_vars parameters. When mcp_config is provided, route to
agent mode via asyncio.run(run_agent(...)). Add MLflow logging for agent
interactions. Follow TDD — write tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/__init__.py` — extend `ask_langchain()` signature and logic

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_provider.py` — add agent mode routing tests

## WHAT

### Extended `ask_langchain()` signature

```python
def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    mcp_config: str | None = None,         # NEW — path to .mcp.json
    execution_dir: str | None = None,       # NEW — working directory
    env_vars: dict[str, str] | None = None, # NEW — extra env vars
) -> LLMResponseDict:
```

### New private function

```python
def _check_agent_dependencies() -> None:
    """Runtime import check for langchain-mcp-adapters and langgraph.
    Raises ImportError with clear install instructions if missing."""
```

## HOW

### Routing logic in `ask_langchain()`

```python
if mcp_config:
    _check_agent_dependencies()
    # → agent mode
else:
    # → existing text-only mode (unchanged)
```

### Agent mode branch
1. Runtime import check via `_check_agent_dependencies()`
2. Load config, create chat model (reuse existing backend dispatch to get the model object)
3. Load session history (reuse existing `load_langchain_history()`)
4. Call `asyncio.run(run_agent(question, chat_model, history, mcp_config, execution_dir, env_vars))`
5. Store full message history via `store_langchain_history()` using LangChain native serialization
6. Populate `raw_response` with agent data for MLflow
7. Log to MLflow via `get_mlflow_logger()`

### Chat model creation
- Extract into `_create_chat_model(config)` helper that returns the LangChain chat model instance
- Reuse existing backend logic but return the model object instead of invoking it
- This avoids duplicating model creation across text-only and agent paths

### MLflow logging
- Use existing `get_mlflow_logger()` singleton
- `log_params`: `backend`, `model`, `tool_call_count`
- `log_metrics`: `agent_steps`, `total_tool_calls`
- `log_artifact`: `tool_trace.json` with tool call details

### Session history in agent mode
- Load: `load_langchain_history(session_id)` — returns `list[dict]`
- Agent mode messages include tool_calls and ToolMessage (richer than text-only)
- Store: `store_langchain_history(sid, serialized_messages)` — serialized via `.dict()`

## ALGORITHM

```
if mcp_config is None:
    # existing text-only path — no changes
    dispatch to backend, return LLMResponseDict

_check_agent_dependencies()  # ImportError if missing
config = _load_langchain_config()
chat_model = _create_chat_model(config)
history = load_langchain_history(session_id) if session_id else []
text, messages, stats = asyncio.run(
    run_agent(question, chat_model, history, mcp_config, execution_dir, env_vars)
)
store_langchain_history(sid, messages)
raw_response = {"messages": messages, "backend": config["backend"],
                "model": config["model"], **stats}
log to MLflow (params, metrics, tool_trace.json artifact)
return LLMResponseDict(text=text, raw_response=raw_response, ...)
```

## DATA

### `raw_response` structure (agent mode)

```python
{
    "messages": [
        {"type": "human", "content": "Create a plan for issue #42"},
        {"type": "ai", "tool_calls": [{"name": "read_file", "args": {...}}]},
        {"type": "tool", "name": "read_file", "content": "def main(): ..."},
        {"type": "ai", "content": "Here's the plan: ..."},
    ],
    "backend": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "agent_steps": 3,
    "total_tool_calls": 2,
    "tool_trace": [...],
}
```

### `LLMResponseDict` (agent mode)
```python
{
    "version": "1.0",
    "timestamp": "2026-03-12T...",
    "text": "Here's the plan: ...",       # final agent output only
    "session_id": "uuid-here",
    "method": "api",
    "provider": "langchain",
    "raw_response": { ... }                # full agent data above
}
```

## TEST CASES

### `test_langchain_provider.py` — additions

```python
class TestAskLangchainAgentMode:
    def test_routes_to_agent_when_mcp_config_provided(self)
        """When mcp_config is set, run_agent is called."""

    def test_routes_to_text_mode_when_mcp_config_none(self)
        """When mcp_config is None, existing backend dispatch used."""

    def test_raises_import_error_when_deps_missing(self)
        """Agent mode raises ImportError if langchain-mcp-adapters not installed."""

    def test_agent_mode_stores_full_history(self)
        """Agent mode stores serialized message history including tool calls."""

    def test_agent_mode_populates_raw_response(self)
        """raw_response contains messages, backend, model, agent stats."""

    def test_agent_mode_logs_to_mlflow(self)
        """MLflow logger receives params, metrics, and tool_trace artifact."""

    def test_backward_compatible_text_only(self)
        """Existing text-only tests still pass (regression check)."""

    def test_check_agent_dependencies_raises_clear_error(self)
        """_check_agent_dependencies gives install instructions."""
```
