# Step 12: Test Coverage Gaps

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 11.
> **Source**: Code review round 2 — decisions 46, 47, 48, 49.

## LLM Prompt

```
Implement Step 12 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: add missing test coverage identified in code review round 2:
(1) empty message list from agent, (2) non-dict server entry skipping in config,
(3) execution_dir and env_vars forwarding from _ask_agent to run_agent,
(4) ImportError tests for all three backend modules.
Do not modify any source files — tests only.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify (tests only)
- `tests/llm/providers/langchain/test_langchain_agent.py` — empty messages + non-dict server entry
- `tests/llm/providers/langchain/test_langchain_agent_mode.py` — execution_dir + env_vars forwarding
- `tests/llm/providers/langchain/test_langchain_openai.py` — ImportError test
- `tests/llm/providers/langchain/test_langchain_gemini.py` — ImportError test
- `tests/llm/providers/langchain/test_langchain_anthropic.py` — ImportError test

## WHAT

### test_langchain_agent.py — empty message list (Decision 46)

```python
class TestRunAgent:
    @pytest.mark.asyncio
    async def test_empty_messages_returns_empty_text(self):
        """Agent returning no messages yields empty final_text."""
        # Mock agent.ainvoke to return {"messages": []}
        # Call run_agent(...)
        # Assert final_text == ""
        # Assert stats["agent_steps"] == 0
        # Assert stats["total_tool_calls"] == 0
```

### test_langchain_agent.py — non-dict server entry (Decision 47)

```python
class TestLoadMcpServerConfig:
    def test_non_dict_server_entry_skipped_with_warning(self):
        """Non-dict server entries are skipped with a warning log."""
        # Write config: {"mcpServers": {"bad": "just a string", "good": {"command": "echo"}}}
        # Call _load_mcp_server_config(path)
        # Assert "bad" is not in result
        # Assert "good" is in result
        # Assert warning was logged mentioning "bad"
```

### test_langchain_agent_mode.py — forwarding tests (Decision 48)

```python
class TestAskLangchainAgentMode:
    def test_execution_dir_forwarded_to_run_agent(self):
        """execution_dir from ask_langchain reaches run_agent."""
        # Call ask_langchain with execution_dir="/some/path"
        # Assert run_agent was called with execution_dir="/some/path"

    def test_env_vars_forwarded_to_run_agent(self):
        """env_vars from ask_langchain reaches run_agent."""
        # Call ask_langchain with env_vars={"FOO": "bar"}
        # Assert run_agent was called with env_vars={"FOO": "bar"}
```

### Backend ImportError tests (Decision 49)

Each backend module has a `try/except ImportError` that raises with install instructions. Test this for each:

```python
# test_langchain_openai.py
class TestCreateOpenaiModel:
    def test_import_error_with_install_hint(self):
        """ImportError raised with pip install hint when langchain-openai missing."""
        # Patch the import to fail
        # Call create_openai_model(...)
        # Assert ImportError with "pip install langchain-openai" in message

# test_langchain_gemini.py
class TestCreateGeminiModel:
    def test_import_error_with_install_hint(self):
        """ImportError raised with pip install hint when langchain-google-genai missing."""

# test_langchain_anthropic.py
class TestCreateAnthropicModel:
    def test_import_error_with_install_hint(self):
        """ImportError raised with pip install hint when langchain-anthropic missing."""
```

## HOW

### Empty message list test
- Mock `create_react_agent` to return an agent whose `ainvoke` returns `{"messages": []}`
- Call `run_agent()` and verify the 3-tuple return

### Non-dict server entry test
- Use `tmp_path` to write a `.mcp.json` with a mix of valid and invalid entries
- Use `caplog` to verify the warning

### Forwarding tests
- Patch `run_agent` and inspect `call_args` for `execution_dir` and `env_vars` kwargs

### Backend ImportError tests
- Use `patch("builtins.__import__")` with a side_effect that raises `ImportError` for the specific vendor package
- Call the `create_*_model()` function
- Assert `ImportError` is raised with install instructions

## ALGORITHM

No algorithmic logic — test-only step.

## DATA

No data structure changes.

## TEST CASES

Summary of all new tests:

| File | Test | Purpose |
|------|------|---------|
| `test_langchain_agent.py` | `test_empty_messages_returns_empty_text` | Agent returns no messages |
| `test_langchain_agent.py` | `test_non_dict_server_entry_skipped_with_warning` | Config robustness |
| `test_langchain_agent_mode.py` | `test_execution_dir_forwarded_to_run_agent` | Parameter forwarding |
| `test_langchain_agent_mode.py` | `test_env_vars_forwarded_to_run_agent` | Parameter forwarding |
| `test_langchain_openai.py` | `test_import_error_with_install_hint` | ImportError path |
| `test_langchain_gemini.py` | `test_import_error_with_install_hint` | ImportError path |
| `test_langchain_anthropic.py` | `test_import_error_with_install_hint` | ImportError path |
