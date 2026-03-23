# Step 8: Add MCP server integration test

## Context
See [summary.md](./summary.md) and [Decisions.md](./Decisions.md).

After step 7 adds `verify_mcp_servers()`, this step adds a real integration test that calls it with an actual `.mcp.json` config.

---

## LLM Prompt

```
Read pr_info/steps/summary.md, pr_info/steps/Decisions.md, and pr_info/steps/step_8.md.

Implement step 8: add MCP server integration test.

1. Add integration test in tests/llm/providers/langchain/test_mcp_health_check.py
2. Run pytest, pylint, mypy, ruff to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| New/modified tests | `tests/llm/providers/langchain/test_mcp_health_check.py` (add integration marker test) |

---

## WHAT

### MCP server integration test

```python
@pytest.mark.langchain_integration
class TestMcpServerIntegration:
    def test_verify_mcp_servers_with_real_config(self):
        """verify_mcp_servers() with a real .mcp.json reports per-server results."""
```

- Use `@pytest.mark.langchain_integration` marker (skipped in CI).
- Use the project's own `.mcp.json` if present, otherwise skip with `pytest.skip("No .mcp.json found")`.
- Keep it simple: call `verify_mcp_servers()` with a real config, assert per-server results.

---

## ALGORITHM

### MCP integration test flow

```
1. Look for .mcp.json in the project root
2. If not found, pytest.skip("No .mcp.json found")
3. Call verify_mcp_servers(config_path)
4. Assert "servers" in result
5. Assert per-server results contain expected keys (ok, value)
6. Assert overall_ok reflects actual server status
```

---

## DATA

No new data structures. Uses existing `verify_mcp_servers()` return dict.

---

## TESTS

### MCP integration test assertions

```python
result = verify_mcp_servers(str(config_path))
assert "servers" in result
assert isinstance(result["overall_ok"], bool)
for name, server_result in result["servers"].items():
    assert "ok" in server_result
    assert "value" in server_result
```
