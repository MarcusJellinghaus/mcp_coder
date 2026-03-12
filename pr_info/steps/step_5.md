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
- `src/mcp_coder/llm/providers/langchain/verification.py` — add MCP adapter package checks + end-to-end agent test
- `src/mcp_coder/cli/commands/verify.py` — wire new check entries into label map, pass `mcp_config` using shared utils

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_verification.py` — add verification tests
- `tests/cli/commands/test_verify.py` or `test_verify_command.py` — add label map tests

## WHAT

### verification.py — new functions

```python
def _check_mcp_adapter_packages() -> dict[str, dict[str, object]]:
    """Check if langchain-mcp-adapters and langgraph are importable.
    Returns dict with 'mcp_adapters' and 'langgraph' entries."""
```

**Note (Decision 6):** No separate `_smoke_test_mcp_server()` or `_verify_mcp_connectivity()`.
The end-to-end MCP test calls `ask_llm()` with `mcp_config` — same code path as real usage.

### verification.py — extend `verify_langchain()`

Add two new sections to the result dict:
- `mcp_adapters`: package installation check (always run)
- `mcp_agent_test`: end-to-end agent test via `ask_llm()` with `mcp_config` (Decision 6)

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
    "mcp_agent_test": "MCP agent test",
})
```

### verify.py — pass `check_mcp=True` from verify command (Decision 6)

When provider is langchain, also pass `check_mcp=True` and resolve the
`.mcp.json` path using `resolve_mcp_config_path()` from `cli/utils.py` (DRY —
same resolution logic as the main prompt flow).

## HOW

### `_check_mcp_adapter_packages()`
- Uses existing `_check_package_installed()` helper
- Checks `langchain_mcp_adapters` and `langgraph` module names

### End-to-end MCP agent test (Decision 6)
- When `check_mcp=True` and `mcp_config_path` is provided:
  - Call `ask_llm("Reply with OK", provider="langchain", mcp_config=mcp_config_path)` — same code path as real usage
  - This exercises the full agent pipeline: config loading, MCP server startup, tool discovery, agent execution
- Uses `resolve_mcp_config_path()` from `cli/utils.py` for path resolution (DRY)

## ALGORITHM

### `_check_mcp_adapter_packages`
```
mcp_ok = _check_package_installed("langchain_mcp_adapters")
lg_ok = _check_package_installed("langgraph")
return {"mcp_adapters": {"ok": mcp_ok, ...}, "langgraph": {"ok": lg_ok, ...}}
```

### End-to-end MCP agent test
```
if check_mcp and mcp_config_path:
    try:
        from mcp_coder.llm.interface import ask_llm
        ask_llm("Reply with OK", provider="langchain", mcp_config=mcp_config_path, timeout=30)
        result["mcp_agent_test"] = {"ok": True, "value": "agent responded"}
    except Exception as exc:
        result["mcp_agent_test"] = {"ok": False, "value": None, "error": str(exc)}
```

## DATA

### Verification result additions

```python
{
    # ... existing fields ...
    "mcp_adapters": {"ok": True, "value": "langchain-mcp-adapters installed"},
    "langgraph": {"ok": True, "value": "langgraph installed"},
    "mcp_agent_test": {"ok": True, "value": "agent responded"},
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

    def test_mcp_agent_test_skipped_when_check_mcp_false(self)
        """No mcp_agent_test entry when check_mcp=False."""

    def test_mcp_agent_test_calls_ask_llm_end_to_end(self)
        """check_mcp=True calls ask_llm() with mcp_config (Decision 6)."""
```

### `test_verify.py` or `test_verify_command.py` — additions

```python
class TestVerifyLabelMap:
    def test_mcp_adapter_labels_in_map(self)
        """Label map contains entries for MCP adapter checks."""
```

### Mock strategy
- Mock `_check_package_installed` for package checks
- Mock `ask_llm` for end-to-end agent test (verify it's called with correct `mcp_config`)
- No real MCP servers or LLM calls needed
