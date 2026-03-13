# Step 6: Code Review Fixes — Small Cleanups

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Steps 1–5 (all existing implementation complete).
> **Source**: Code review findings — decisions 30–34.

## LLM Prompt

```
Implement Step 6 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: apply small code review fixes — remove dead code, improve type
annotations, wire unused parameter, and add a missing test. Follow TDD where
applicable.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/agent.py` — remove dead transport branch
- `src/mcp_coder/llm/providers/langchain/__init__.py` — `TYPE_CHECKING` guard for `BaseChatModel` return type
- `src/mcp_coder/llm/providers/langchain/verification.py` — wire `env_vars` through to `ask_llm()`

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_agent.py` — add `_check_agent_dependencies` test

## WHAT

### agent.py — remove dead transport branch (Decision 30)

The `elif key == "transport"` branch in `_load_mcp_server_config` is dead code
because line 139 always overwrites transport to `"stdio"`. Remove the branch.

Before:
```python
            elif key == "transport":
                resolved["transport"] = value
            else:
                resolved[key] = value

        # Always set transport to stdio
        resolved["transport"] = "stdio"
```

After:
```python
            else:
                resolved[key] = value

        # Always set transport to stdio
        resolved["transport"] = "stdio"
```

### __init__.py — `TYPE_CHECKING` guard (Decision 31)

Add `BaseChatModel` as return type for `_create_chat_model()` using a
`TYPE_CHECKING` guard to avoid runtime import when langchain is not installed.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

def _create_chat_model(config: dict[str, str | None]) -> BaseChatModel:
    ...
```

**Note**: `from __future__ import annotations` makes all annotations strings
at runtime, so `BaseChatModel` is never actually resolved unless a type
checker is running.

### verification.py — wire `env_vars` (Decision 32)

Pass `env_vars` through to the `ask_llm()` call in the MCP agent smoke test:

```python
ask_llm(
    "Reply with OK",
    provider="langchain",
    mcp_config=mcp_config_path,
    env_vars=env_vars,  # NEW
    timeout=30,
)
```

### test_langchain_agent.py — `_check_agent_dependencies` test (Decision 34)

```python
class TestCheckAgentDependencies:
    def test_raises_when_packages_missing(self):
        """ImportError raised with install instructions when deps missing."""

    def test_passes_when_packages_installed(self):
        """No exception when both packages importable."""
```

## HOW

### `_check_agent_dependencies` test
- Mock `importlib.import_module` or use `patch.dict(sys.modules)` to simulate missing packages
- Assert `ImportError` message contains package names and install instructions

## ALGORITHM

### Test for `_check_agent_dependencies`
```
# Test missing:
patch builtins.__import__ to raise ImportError for langchain_mcp_adapters
call _check_agent_dependencies()
assert ImportError raised with "langchain-mcp-adapters" in message

# Test present:
with real or mocked imports available
call _check_agent_dependencies()
no exception raised
```

## DATA

No new data structures.

## TEST CASES

### `test_langchain_agent.py` — additions

```python
class TestCheckAgentDependencies:
    def test_raises_when_both_missing(self):
        """Both packages missing → ImportError listing both."""

    def test_raises_when_one_missing(self):
        """Single package missing → ImportError listing that package."""

    def test_passes_when_installed(self):
        """No error when packages are importable (conftest mocks or real)."""
```

### Mock strategy
- Use `patch("builtins.__import__")` with a side_effect that selectively raises
  `ImportError` for target packages while allowing other imports to proceed.
