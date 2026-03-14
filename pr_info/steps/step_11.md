# Step 11: Config Robustness + Transport Warning

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 10.
> **Source**: Code review round 2 — decisions 44, 45.

## LLM Prompt

```
Implement Step 11 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: (1) Wrap json.JSONDecodeError in _load_mcp_server_config() with a
user-friendly message including the file path. (2) Log a warning when a
user-specified transport is being overridden to "stdio". Follow TDD — write
tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/agent.py` — wrap JSONDecodeError, add transport warning

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_agent.py` — add tests for both changes

## WHAT

### agent.py — `json.JSONDecodeError` wrapping (Decision 44)

Wrap the `json.load()` call in `_load_mcp_server_config()`:

```python
try:
    raw_config: dict[str, object] = json.load(fh)
except json.JSONDecodeError as exc:
    raise ValueError(
        f"Invalid JSON in {mcp_config_path}: {exc}"
    ) from exc
```

### agent.py — transport override warning (Decision 45)

Before setting `resolved["transport"] = "stdio"`, check if the user specified a different transport:

```python
user_transport = server_cfg.get("transport")
if user_transport and user_transport != "stdio":
    logger.warning(
        "Server %r specifies transport %r, overriding to 'stdio' "
        "(only stdio is currently supported)",
        server_name,
        user_transport,
    )
resolved["transport"] = "stdio"
```

## HOW

### JSONDecodeError integration
- The `try/except` wraps only the `json.load(fh)` call, not the entire function
- Re-raises as `ValueError` with file path context for better diagnostics
- Chains the original exception via `from exc`

### Transport warning integration
- Check `server_cfg.get("transport")` before the override line
- Only warn if the value is non-None and not already "stdio"
- Use `logger.warning` consistent with existing warning patterns in the function

## ALGORITHM

### JSONDecodeError handling
```
with open(path) as fh:
    try:
        raw_config = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
```

### Transport warning
```
user_transport = server_cfg.get("transport")
if user_transport and user_transport != "stdio":
    logger.warning("overriding transport %r to stdio", user_transport)
resolved["transport"] = "stdio"
```

## DATA

No data structure changes.

## TEST CASES

### test_langchain_agent.py — JSONDecodeError

```python
class TestLoadMcpServerConfig:
    def test_invalid_json_raises_value_error_with_path(self):
        """Malformed JSON produces ValueError mentioning the file path."""
        # Write invalid JSON to a temp file
        # Call _load_mcp_server_config(path)
        # Assert ValueError raised
        # Assert file path appears in the error message
        # Assert "Invalid JSON" appears in the error message
```

### test_langchain_agent.py — transport warning

```python
class TestLoadMcpServerConfig:
    def test_transport_override_logs_warning(self):
        """Warning logged when user transport is overridden to stdio."""
        # Write config with "transport": "sse"
        # Call _load_mcp_server_config(path)
        # Assert warning was logged mentioning "sse" and "stdio"
        # Assert result still has transport = "stdio"

    def test_transport_stdio_no_warning(self):
        """No warning when user already specifies stdio transport."""
        # Write config with "transport": "stdio"
        # Call _load_mcp_server_config(path)
        # Assert no warning logged
```

### Mock strategy
- Use `tmp_path` fixture to create temp config files
- Use `caplog` fixture to capture log warnings
- No mocking needed — these test the actual function with real files
