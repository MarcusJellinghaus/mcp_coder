# Step 1: Store tool names in `_check_servers()` result

## LLM Prompt

> Implement Step 1 from `pr_info/steps/summary.md` (Issue #550).
> Add `tool_names` list to the `_check_servers()` result dict in `verification.py`.
> Follow TDD: write tests first, then implement. Run all three code quality checks after changes.

## WHERE

| File | Action |
|------|--------|
| `tests/llm/providers/langchain/test_mcp_health_check.py` | Add tests |
| `src/mcp_coder/llm/providers/langchain/verification.py` | Modify `_check_servers()` |

## WHAT

### Modified function

```python
# In _check_servers(), the result dict for successful servers gains tool_names:
async def _check_servers(server_config, timeout) -> dict[str, dict[str, Any]]:
    # existing signature unchanged
```

## HOW

In `_check_servers()`, after `tools = await session.list_tools()`, extract `.name` from each tool object and add to result dict.

## ALGORITHM

```
tools = await session.list_tools()
tool_names = [t.name for t in tools.tools]
results[server_name] = {
    "ok": True,
    "value": f"{len(tools.tools)} tools available",
    "tools": len(tools.tools),
    "tool_names": tool_names,       # <-- NEW
}
```

## DATA

Server result dict changes from:
```python
{"ok": True, "value": "5 tools available", "tools": 5}
```
to:
```python
{"ok": True, "value": "5 tools available", "tools": 5, "tool_names": ["read_file", "save_file", ...]}
```

Failed servers do NOT include `tool_names` (no change to error path).

## TESTS

Add to `TestVerifyMcpServers` in `test_mcp_health_check.py`:

1. **`test_server_success_includes_tool_names`** — Mock tools with `.name` attributes, verify `tool_names` list in result
2. **`test_server_failure_has_no_tool_names`** — Verify failed server result does not contain `tool_names`

### Test pattern

```python
def _make_tools_response_with_names(names: list[str]) -> MagicMock:
    """Create a mock ListToolsResult with named tools."""
    tool_mocks = [MagicMock(name=n) for n in names]
    # Note: MagicMock(name=...) sets the mock's name, not .name attribute
    # Must use configure_mock or set .name explicitly
    for mock, tool_name in zip(tool_mocks, names):
        mock.name = tool_name
    result = MagicMock()
    result.tools = tool_mocks
    return result
```

## COMMIT

```
feat(verify): store tool names in MCP server health check results

Add tool_names list to _check_servers() result dict, extracted from
each tool's .name attribute. This enables downstream formatting to
display individual tool names per server.

Refs #550
```
