# Step 7: Add per-server MCP health check to verify

## Context
See [summary.md](./summary.md) and [Decisions.md](./Decisions.md).

Users need to know whether their configured MCP servers actually start and respond. Currently `verify_langchain()` has an optional `mcp_agent_test` that runs a full agent prompt — expensive, slow (300s timeout), and doesn't isolate server issues from LLM issues.

This step adds a fast per-server connectivity check: load config, start each server, call `list_tools()`, report results. No LLM call needed.

---

## LLM Prompt

```
Read pr_info/steps/summary.md, pr_info/steps/Decisions.md, and pr_info/steps/step_7.md.

Implement step 7: add per-server MCP health check to the verify command.

1. Write tests first in tests/llm/providers/langchain/test_mcp_health_check.py
2. Add verify_mcp_servers() to src/mcp_coder/llm/providers/langchain/verification.py
3. Integrate into execute_verify() in src/mcp_coder/cli/commands/verify.py
4. Run pytest, pylint, mypy, ruff to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| Modified source | `src/mcp_coder/llm/providers/langchain/verification.py` |
| Modified source | `src/mcp_coder/cli/commands/verify.py` |
| New tests | `tests/llm/providers/langchain/test_mcp_health_check.py` |
| Modified tests | `tests/cli/commands/test_verify_orchestration.py` |

---

## WHAT

### New function: `verify_mcp_servers()`

```python
def verify_mcp_servers(
    mcp_config_path: str,
    timeout: int = 15,
) -> dict[str, Any]:
    """Check each configured MCP server by connecting and listing tools.

    Returns:
        Dict with per-server results and overall_ok.
        Keys: "servers" (dict of server_name -> result), "overall_ok" (bool).
        Each server result: {"ok": bool, "value": str, "tools": int | None, "error": str | None}.
    """
```

### Integration in `execute_verify()`

After the LangChain verification section, if `mcp_config_resolved` is not None:

```python
# 3a. MCP server health check
if mcp_config_resolved:
    mcp_results = verify_mcp_servers(mcp_config_resolved)
    print(_format_mcp_section(mcp_results, symbols))
```

The `=== MCP SERVERS ===` section should be hidden entirely when no servers are configured (no output at all).

### New helper: `_format_mcp_section()`

In `verify.py`, format the per-server results:

```python
def _format_mcp_section(mcp_results: dict, symbols: dict) -> str:
    """Format MCP server health check results."""
```

---

## HOW

### Server connectivity check (async internals)

```python
async def _check_servers(server_config, timeout):
    results = {}
    for server_name in server_config:
        client = MultiServerMCPClient({server_name: server_config[server_name]})
        try:
            async with asyncio.timeout(timeout):
                async with client.session(server_name) as session:
                    tools = await session.list_tools()
                    results[server_name] = {
                        "ok": True,
                        "value": f"{len(tools.tools)} tools available",
                        "tools": len(tools.tools),
                    }
        except Exception as exc:
            results[server_name] = {
                "ok": False,
                "value": str(exc),
                "error": type(exc).__name__,
            }
    return results
```

### Import chain

- `verification.py` already imports from `.agent` indirectly (via `ask_llm`). Adding `from .agent import _load_mcp_server_config` is a within-package import.
- `MultiServerMCPClient` is a deferred import inside the async function (only when called).
- `asyncio.run()` wraps the async internals (same pattern as `_ask_agent`).
- No `env_vars` parameter needed — the config loader merges with `os.environ` by default.

### Timeout

- 15 seconds per server by default (generous for subprocess startup)
- Each server checked independently — one slow server doesn't block others

---

## ALGORITHM

```
def verify_mcp_servers(mcp_config_path, timeout=15):
    server_config = _load_mcp_server_config(mcp_config_path)
    if not server_config:
        return {"servers": {}, "overall_ok": True, "value": "no servers configured"}
    results = asyncio.run(_check_servers(server_config, timeout))
    overall_ok = all(r["ok"] for r in results.values())
    return {"servers": results, "overall_ok": overall_ok}
```

---

## DATA

### Return structure

```python
{
    "servers": {
        "tools-py": {"ok": True, "value": "12 tools available", "tools": 12},
        "workspace": {"ok": True, "value": "8 tools available", "tools": 8},
        "broken-one": {"ok": False, "value": "FileNotFoundError: ...", "error": "FileNotFoundError"},
    },
    "overall_ok": False,  # any server failed
}
```

### Verify output format

```
=== MCP SERVERS ===
  tools-py             ✓ 12 tools available
  workspace            ✓ 8 tools available
  broken-one           ✗ FileNotFoundError: executable not found
```

### Exit code impact

`_compute_exit_code()` signature must be extended with `mcp_result: dict[str, Any] | None = None` parameter. Update all call sites (there's one in `execute_verify()`).

MCP server failures should affect exit code when `active_provider == "langchain"`. Add to `_compute_exit_code()`:

```python
if active_provider == "langchain" and mcp_result and not mcp_result.get("overall_ok"):
    return 1
```

---

## TESTS

### `test_mcp_health_check.py`

```python
class TestVerifyMcpServers:
    def test_no_config_returns_ok(self):
        """No servers configured → overall_ok True."""

    def test_server_success(self):
        """Server responds with tools → ok True, tool count reported."""

    def test_server_failure(self):
        """Server fails to start → ok False, error message."""

    def test_mixed_servers(self):
        """One ok, one broken → overall_ok False, per-server details correct."""

    def test_timeout_handling(self):
        """Slow server → timeout error reported."""
```

### `test_verify_orchestration.py` updates

- Add mock for `verify_mcp_servers` in tests that provide `mcp_config`
- Add test: `test_mcp_servers_displayed_when_config_present`
- Add test: `test_mcp_servers_skipped_when_no_config`
