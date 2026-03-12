# Step 4: Update interface.py Routing

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 3 (ask_langchain must accept new params).

## LLM Prompt

```
Implement Step 4 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: update interface.py to pass mcp_config, execution_dir, and env_vars
through to ask_langchain(). This is a minimal change — just add three keyword
arguments to the existing call. Follow TDD — write tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/interface.py` — pass params to `ask_langchain()`

### Files to modify (tests)
- `tests/llm/test_interface.py` — add test for parameter passthrough

## WHAT

### Change in `prompt_llm()`

**Before:**
```python
if provider == "langchain":
    from .providers.langchain import ask_langchain
    return ask_langchain(
        question,
        session_id=session_id,
        timeout=timeout,
    )
```

**After:**
```python
if provider == "langchain":
    from .providers.langchain import ask_langchain
    return ask_langchain(
        question,
        session_id=session_id,
        timeout=timeout,
        mcp_config=mcp_config,
        execution_dir=execution_dir,
        env_vars=env_vars,
    )
```

## HOW

- Single-location change: the `if provider == "langchain"` branch in `prompt_llm()`
- No new imports, no new functions
- Parameters already exist on `prompt_llm()` — they were just not forwarded

## ALGORITHM

```
# In prompt_llm(), langchain branch:
# Before: ask_langchain(question, session_id, timeout)
# After:  ask_langchain(question, session_id, timeout, mcp_config, execution_dir, env_vars)
# That's it — three extra keyword arguments.
```

## DATA

No new data structures. The existing `mcp_config` (str|None), `execution_dir` (str|None), and `env_vars` (dict|None) parameters are simply forwarded.

## TEST CASES

### `test_interface.py` — additions

```python
class TestPromptLlmLangchainRouting:
    def test_passes_mcp_config_to_langchain(self)
        """mcp_config parameter is forwarded to ask_langchain()."""

    def test_passes_execution_dir_to_langchain(self)
        """execution_dir parameter is forwarded to ask_langchain()."""

    def test_passes_env_vars_to_langchain(self)
        """env_vars parameter is forwarded to ask_langchain()."""

    def test_langchain_without_mcp_params_still_works(self)
        """Calling with provider=langchain and no MCP params works (backward compat)."""
```

### Mock strategy
- Mock `ask_langchain` at import path `mcp_coder.llm.interface.ask_langchain` (or patch the lazy import)
- Verify the mock was called with expected keyword arguments
- No real LLM calls needed
