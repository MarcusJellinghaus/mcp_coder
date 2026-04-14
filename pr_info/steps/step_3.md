# Step 3: Langchain Provider — Prepend System Messages

## References
- Summary: `pr_info/steps/summary.md`
- Depends on: Step 2 (interface passes `system_prompt`/`project_prompt` to langchain)

## WHERE

**Modified files:**
- `src/mcp_coder/llm/providers/langchain/__init__.py` — accept + inject SystemMessage objects
- `src/mcp_coder/llm/providers/langchain/agent.py` — accept `system_messages` in `run_agent()` / `run_agent_stream()`
- `tests/llm/providers/langchain/test_langchain_provider.py` — test SystemMessage injection
- `tests/llm/providers/langchain/test_langchain_agent.py` — test agent system messages

## WHAT

### `__init__.py` — entry points gain prompt params

```python
def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    system_prompt: str | None = None,       # NEW
    project_prompt: str | None = None,      # NEW
) -> LLMResponseDict:
```

Same for `ask_langchain_stream()`.

### Internal functions gain `system_messages` param

```python
def _ask_text(
    ...,
    system_messages: list[Any] | None = None,     # NEW — list[SystemMessage]
) -> LLMResponseDict:

def _ask_text_stream(
    ...,
    system_messages: list[Any] | None = None,
) -> Iterator[StreamEvent]:

def _ask_agent(
    ...,
    system_messages: list[Any] | None = None,
) -> LLMResponseDict:

def _ask_agent_stream(
    ...,
    system_messages: list[Any] | None = None,
) -> Iterator[StreamEvent]:
```

### `agent.py` — `run_agent()` and `run_agent_stream()` gain `system_messages`

```python
async def run_agent(
    ...,
    system_messages: list[Any] | None = None,  # NEW
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
```

## HOW

### Building SystemMessage objects (in `ask_langchain` / `ask_langchain_stream`)

```python
from langchain_core.messages import SystemMessage

def _build_system_messages(system_prompt: str | None, project_prompt: str | None) -> list[Any]:
    msgs = []
    if system_prompt:
        msgs.append(SystemMessage(content=system_prompt))
    if project_prompt:
        msgs.append(SystemMessage(content=project_prompt))
    return msgs
```

This helper is defined in `__init__.py` (private, module-level).

### Prepending in internal functions

In `_ask_text()` and `_ask_text_stream()`, change:
```python
# Before:
lc_messages = history_messages + [HumanMessage(content=question)]
# After:
lc_messages = (system_messages or []) + history_messages + [HumanMessage(content=question)]
```

In `_ask_agent()` and `run_agent()`, change:
```python
# Before:
input_messages = messages_from_dict(messages) + [HumanMessage(content=question)]
# After:
input_messages = (system_messages or []) + messages_from_dict(messages) + [HumanMessage(content=question)]
```

Same pattern in `_ask_agent_stream()` and `run_agent_stream()`.

### Pass-through chain

```
ask_langchain(system_prompt, project_prompt)
  → _build_system_messages(system_prompt, project_prompt)
  → _ask_text(system_messages=msgs) or _ask_agent(system_messages=msgs)
    → prepend to lc_messages / input_messages
```

For agent mode, `_ask_agent` passes `system_messages` to `run_agent()` in `agent.py`.

## ALGORITHM

```python
# In ask_langchain():
sys_msgs = _build_system_messages(system_prompt, project_prompt)
if mcp_config:
    return _ask_agent(..., system_messages=sys_msgs)
return _ask_text(..., system_messages=sys_msgs)

# In _ask_text():
lc_messages = (system_messages or []) + history_messages + [HumanMessage(content=question)]
ai_msg = chat_model.invoke(lc_messages)
```

## DATA

No new data structures. `system_messages` is `list[SystemMessage]` (from `langchain_core.messages`), passed as `list[Any]` in type hints to avoid hard import dependency.

## TESTS

### `test_langchain_provider.py`

1. **`test_build_system_messages_both`** — both prompts → 2 SystemMessage objects
2. **`test_build_system_messages_system_only`** — only system prompt → 1 message
3. **`test_build_system_messages_none`** — no prompts → empty list
4. **`test_ask_text_prepends_system_messages`** — mock chat_model.invoke, verify SystemMessage objects appear first in message list
5. **`test_ask_text_stream_prepends_system_messages`** — same for streaming
6. **`test_ask_langchain_passes_system_messages`** — end-to-end mock, verify flow

### `test_langchain_agent.py`

7. **`test_run_agent_prepends_system_messages`** — verify system messages are first in input_messages

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 3.

Implement SystemMessage injection in the langchain provider. In
src/mcp_coder/llm/providers/langchain/__init__.py:
- Add _build_system_messages() helper
- Add system_prompt/project_prompt params to ask_langchain() and ask_langchain_stream()
- Add system_messages param to all 4 internal functions
- Prepend system_messages to message lists in each internal function

In src/mcp_coder/llm/providers/langchain/agent.py:
- Add system_messages param to run_agent() and run_agent_stream()
- Prepend to input_messages

Write tests verifying SystemMessage objects appear first in message lists.
All quality checks must pass.
```
