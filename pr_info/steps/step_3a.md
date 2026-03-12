# Step 3a: Backend Refactor + Chat Model Helper

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Steps 1–2 (agent.py must be complete).
> **Split from**: Step 3 (Decision 26).

## LLM Prompt

```
Implement Step 3a of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: extract model creation from each backend into reusable create_*_model()
functions, and add a _create_chat_model() dispatcher in __init__.py.
Also add _check_agent_dependencies() to agent.py.
Follow TDD — write tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/openai_backend.py` — extract model creation (Decision 9)
- `src/mcp_coder/llm/providers/langchain/gemini_backend.py` — extract model creation (Decision 9)
- `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` — extract model creation (Decision 9)
- `src/mcp_coder/llm/providers/langchain/__init__.py` — add `_create_chat_model()` dispatcher
- `src/mcp_coder/llm/providers/langchain/agent.py` — add `_check_agent_dependencies()` (Decision 18)

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_provider.py` — add tests for `_create_chat_model()` and `_check_agent_dependencies()`

## WHAT

### Backend `create_*_model()` functions (Decision 9 + Decision 16)

Extract model creation from each backend into a reusable function. Signatures:

```python
# openai_backend.py:
def create_openai_model(
    model: str,
    api_key: str | None,
    endpoint: str | None = None,
    api_version: str | None = None,
    timeout: int = 30,
) -> ChatOpenAI | AzureChatOpenAI:
    """Create an OpenAI/Azure chat model without invoking it."""

# gemini_backend.py:
def create_gemini_model(
    model: str,
    api_key: str | None,
    timeout: int = 30,
) -> ChatGoogleGenerativeAI:
    """Create a Gemini chat model without invoking it."""

# anthropic_backend.py:
def create_anthropic_model(
    model: str,
    api_key: str | None,
    timeout: int = 30,
) -> ChatAnthropic:
    """Create an Anthropic chat model without invoking it."""
```

Refactor existing `ask_*()` functions to call their `create_*_model()` internally (no behavior change for text-only path).

### `_create_chat_model()` in `__init__.py`

```python
def _create_chat_model(config: dict[str, str]) -> object:
    """Dispatch to correct backend's create_*_model() based on config."""
```

### `_check_agent_dependencies()` in `agent.py` (Decision 18)

```python
def _check_agent_dependencies() -> None:
    """Runtime import check for langchain-mcp-adapters and langgraph.
    Raises ImportError with clear install instructions if missing."""
```

## HOW

### Backend refactor
- Each backend's `ask_*()` function currently creates the model inline, then invokes it
- Extract the creation logic into `create_*_model()`, then call it from `ask_*()`
- No behavior change — just a code split

### `_create_chat_model()` dispatcher
- Reads `backend` from config, dispatches to the correct `create_*_model()`
- Reads `model`, `api_key`, `endpoint`, `api_version` from config
- Returns the model object (used by agent mode in Step 3b)

## TEST CASES

### `test_langchain_provider.py` — additions

```python
class TestCreateChatModel:
    def test_dispatches_to_openai_backend(self)
        """Config with backend=openai calls create_openai_model."""

    def test_dispatches_to_gemini_backend(self)
        """Config with backend=gemini calls create_gemini_model."""

    def test_dispatches_to_anthropic_backend(self)
        """Config with backend=anthropic calls create_anthropic_model."""

    def test_raises_on_unknown_backend(self)
        """Unknown backend raises ValueError."""

class TestCheckAgentDependencies:
    def test_passes_when_both_installed(self)
        """No error when both packages importable."""

    def test_raises_clear_error_when_mcp_adapters_missing(self)
        """ImportError with install instructions for langchain-mcp-adapters."""

    def test_raises_clear_error_when_langgraph_missing(self)
        """ImportError with install instructions for langgraph."""
```
