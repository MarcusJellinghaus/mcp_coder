# Step 3: Thread `tools` Through Provider Stack + LLM Service

> **Ref:** [summary.md](summary.md) — "Modified Components → Langchain provider, LLM interface, LLM service"

## LLM Prompt

> Implement Step 3 from `pr_info/steps/step_3.md`. Read `pr_info/steps/summary.md` for full context.
> Thread the optional `tools` parameter from `RealLLMService` through `prompt_llm_stream()` → `ask_langchain_stream()` → `_ask_agent_stream()` → `run_agent_stream()`.
> Add `mcp_manager` to `RealLLMService`. Each layer just passes `tools` through — no logic changes.
> Follow TDD: write/update tests first, then implement. Run all code quality checks after.

## WHERE

- **Modified:** `src/mcp_coder/llm/providers/langchain/__init__.py`
- **Modified:** `src/mcp_coder/llm/interface.py`
- **Modified:** `src/mcp_coder/icoder/services/llm_service.py`
- **Modified:** relevant test files for each layer

## WHAT

### 3A. `_ask_agent_stream()` — add `tools` parameter

```python
def _ask_agent_stream(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    tools: list[Any] | None = None,  # NEW
) -> Iterator[StreamEvent]:
```

Passes `tools=tools` to `run_agent_stream()` call inside `_run()`.

### 3B. `ask_langchain_stream()` — add `tools` parameter

```python
def ask_langchain_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 600,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    tools: list[Any] | None = None,  # NEW
) -> Iterator[StreamEvent]:
```

Passes `tools=tools` to `_ask_agent_stream()`.

### 3C. `prompt_llm_stream()` — add `tools` parameter

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
    tools: list[Any] | None = None,  # NEW
) -> Iterator[StreamEvent]:
```

Passes `tools=tools` to `ask_langchain_stream()` (langchain path only). Claude path ignores it.

### 3D. `RealLLMService` — add `mcp_manager` parameter

```python
class RealLLMService:
    def __init__(
        self,
        provider: str = "claude",
        session_id: str | None = None,
        execution_dir: str | None = None,
        mcp_config: str | None = None,
        env_vars: dict[str, str] | None = None,
        timeout: int = ICODER_LLM_TIMEOUT_SECONDS,
        mcp_manager: MCPManager | None = None,  # NEW
    ) -> None:
```

In `stream()`, if `self._mcp_manager` is not `None`, call `self._mcp_manager.tools()` and pass result as `tools=` to `prompt_llm_stream()`.

## HOW

- Each function gains `tools: list[Any] | None = None` as last parameter
- Each function passes it through to the next layer with `tools=tools`
- `RealLLMService` imports `MCPManager` under `TYPE_CHECKING` only
- `LLMService` protocol and `FakeLLMService` are NOT changed (they don't know about MCP)
- All existing callers pass nothing for `tools` → `None` → existing behavior

## ALGORITHM — `RealLLMService.stream()` change

```
tools = None
if self._mcp_manager is not None:
    tools = self._mcp_manager.tools()
for event in prompt_llm_stream(..., tools=tools):
    # existing event handling
    yield event
```

## DATA

- `tools` parameter at every layer: `list[Any] | None`
- `mcp_manager` on `RealLLMService`: `MCPManager | None`
- No new return types; all existing return types unchanged

## TEST PLAN

1. `test_real_llm_service_passes_tools` — mock `prompt_llm_stream`, verify `tools=` kwarg is passed when `mcp_manager` is set
2. `test_real_llm_service_no_manager_passes_none` — mock `prompt_llm_stream`, verify `tools=None` when no `mcp_manager`
3. `test_prompt_llm_stream_passes_tools_to_langchain` — mock `ask_langchain_stream`, verify `tools=` kwarg forwarded (langchain provider)
4. `test_prompt_llm_stream_claude_ignores_tools` — verify claude path works fine with `tools` param present
5. All existing tests pass unchanged (no `tools` param = `None` default)

## COMMIT

```
feat(llm): thread persistent MCP tools through provider stack (#741)
```
