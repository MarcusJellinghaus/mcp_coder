# Step 5: Verification Extensions

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Steps 1–2 (agent.py must exist for MCP config loading).

## LLM Prompt

```
Implement Step 5 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: extend the verification system to check MCP adapter packages and
test MCP server connectivity via a stdio smoke test. Follow TDD — write tests
first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/verification.py` — add MCP adapter checks + smoke test
- `src/mcp_coder/cli/commands/verify.py` — wire new check entries into label map and formatting

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_verification.py` — add verification tests
- `tests/cli/commands/test_verify.py` or `test_verify_command.py` — add label map tests

## WHAT

### verification.py — new functions

```python
def _check_mcp_adapter_packages() -> dict[str, dict[str, object]]:
    """Check if langchain-mcp-adapters and langgraph are importable.
    Returns dict with 'mcp_adapters' and 'langgraph' entries."""

async def _smoke_test_mcp_server(
    server_name: str,
    server_config: dict[str, object],
) -> dict[str, object]:
    """Start an MCP server via stdio, list tools, shut down.
    Returns dict with ok, value, tool_count, error."""

def _verify_mcp_connectivity(
    mcp_config_path: str | None,
    env_vars: dict[str, str] | None = None,
) -> dict[str, dict[str, object]]:
    """Verify each MCP server in .mcp.json can start and respond.
    Returns dict keyed by server name with smoke test results."""
```

### verification.py — extend `verify_langchain()`

Add two new sections to the result dict:
- `mcp_adapters`: package installation check (always run)
- `mcp_servers`: per-server connectivity check (only in verify command, when .mcp.json exists)

```python
def verify_langchain(
    check_models: bool = False,
    check_mcp: bool = False,         # NEW — triggers smoke test
    mcp_config_path: str | None = None,  # NEW — path to .mcp.json
    env_vars: dict[str, str] | None = None,  # NEW — for var substitution
) -> dict[str, Any]:
```

### verify.py — label map additions

```python
_LABEL_MAP.update({
    "mcp_adapters": "MCP adapters",
    "langgraph": "LangGraph",
    "mcp_servers": "MCP servers",
})
```

### verify.py — pass `check_mcp=True` from verify command

When provider is langchain, also pass `check_mcp=True` and resolve the
`.mcp.json` path from the current working directory.

## HOW

### `_check_mcp_adapter_packages()`
- Uses existing `_check_package_installed()` helper
- Checks `langchain_mcp_adapters` and `langgraph` module names

### `_smoke_test_mcp_server()`
- Async function using `MultiServerMCPClient` with a single server
- Opens connection, calls `client.get_tools()`, counts tools, closes
- Wrapped in try/except for clean error reporting
- Timeout: 10 seconds (reasonable for local stdio servers)

### `_verify_mcp_connectivity()`
- Loads MCP config via `_load_mcp_server_config()` from agent.py
- Runs `_smoke_test_mcp_server()` for each server sequentially
- Uses `asyncio.run()` wrapper
- Only called when `check_mcp=True`

## ALGORITHM

### `_check_mcp_adapter_packages`
```
mcp_ok = _check_package_installed("langchain_mcp_adapters")
lg_ok = _check_package_installed("langgraph")
return {"mcp_adapters": {"ok": mcp_ok, ...}, "langgraph": {"ok": lg_ok, ...}}
```

### `_smoke_test_mcp_server`
```
try:
    async with MultiServerMCPClient({name: config}) as client:
        tools = client.get_tools()
        return {"ok": True, "value": f"{len(tools)} tools", "tool_count": len(tools)}
except Exception as exc:
    return {"ok": False, "value": None, "error": str(exc)}
```

### `_verify_mcp_connectivity`
```
server_config = _load_mcp_server_config(mcp_config_path, None, env_vars)
results = {}
for name, config in server_config.items():
    results[name] = asyncio.run(_smoke_test_mcp_server(name, config))
return results
```

## DATA

### Verification result additions

```python
{
    # ... existing fields ...
    "mcp_adapters": {"ok": True, "value": "langchain-mcp-adapters installed"},
    "langgraph": {"ok": True, "value": "langgraph installed"},
    "mcp_servers": {
        "ok": True,
        "value": "all servers responding",
        "details": {
            "code-checker": {"ok": True, "value": "12 tools", "tool_count": 12},
            "filesystem": {"ok": True, "value": "8 tools", "tool_count": 8},
        }
    },
}
```

## TEST CASES

### `test_langchain_verification.py` — additions

```python
class TestCheckMcpAdapterPackages:
    def test_both_installed(self)
    def test_mcp_adapters_missing(self)
    def test_langgraph_missing(self)

class TestVerifyLangchainMcpSection:
    def test_includes_mcp_adapter_check(self)
        """verify_langchain() result includes mcp_adapters entry."""

    def test_mcp_servers_skipped_when_check_mcp_false(self)
        """No mcp_servers entry when check_mcp=False."""

    def test_mcp_servers_included_when_check_mcp_true(self)
        """mcp_servers entry present when check_mcp=True."""
```

### `test_verify.py` or `test_verify_command.py` — additions

```python
class TestVerifyLabelMap:
    def test_mcp_adapter_labels_in_map(self)
        """Label map contains entries for MCP adapter checks."""
```

### Mock strategy
- Mock `_check_package_installed` for package checks
- Mock `MultiServerMCPClient` for smoke test (async context manager)
- Mock `_load_mcp_server_config` for connectivity test
- No real MCP servers needed
