# Step 5 — Startup wiring + bypass guard + real-agent integration (D1/D2)

**Reference:** read `pr_info/steps/summary.md` (Decisions D1, D2) first.

Wire everything together at iCoder startup: load the permission config, construct the gateway, inject
its interceptor into `MCPManager`, and pass it to `RealLLMService`. Add the bypass-guard test (D1) and
one real-agent integration test that proves the end-to-end path.

## WHERE
- `src/mcp_coder/cli/commands/icoder.py` — `execute_icoder()` component-construction block.
- `tests/icoder/test_icoder_permission_wiring.py` (new) — wiring + bypass-guard.
- `tests/llm/providers/langchain/test_permission_bridge.py` **or**
  `tests/icoder/test_icoder_permission_wiring.py` — the `langchain_integration`-marked integration test.

## WHAT (icoder.py, inside the existing `if provider == "langchain" and mcp_config:` block)
```python
from ...icoder.permissions import load_permission_config           # public API
from ...icoder.permissions.gateway import LangchainEnforcementGateway

config = load_permission_config(project_dir)                       # D2: once at startup
gateway = LangchainEnforcementGateway(config)
server_config = _load_mcp_server_config(mcp_config, env_vars)
mcp_manager = MCPManager(server_config, tool_interceptors=[gateway.interceptor])
```
Then pass `gateway=gateway` to `RealLLMService(...)`. Keep `gateway = None` outside the langchain branch
and still pass `gateway=gateway` (None) to `RealLLMService`.

## HOW
- `gateway.interceptor` is a bound async method → valid `ToolCallInterceptor` (`async (request, handler)`).
- `load_permission_config` takes a `Path`; `project_dir` is already a resolved `Path` in this function.
- No change to `AppCore`, `SendToLLM`, or the `LLMService` Protocol.

## ALGORITHM (wiring)
```
mcp_manager = None; gateway = None
if provider == "langchain" and mcp_config:
    config  = load_permission_config(project_dir)
    gateway = LangchainEnforcementGateway(config)
    mcp_manager = MCPManager(_load_mcp_server_config(mcp_config, env_vars),
                             tool_interceptors=[gateway.interceptor])
llm_service = RealLLMService(..., mcp_manager=mcp_manager, gateway=gateway, enforce_skill_tools=False)
```

## DATA
- One `PermissionConfig` snapshot per session; one gateway shared by the interceptor (call level) and
  `RealLLMService` (turn level) → guaranteed same canonical identity + same config.
- No-config case: `load_permission_config` returns an empty `PermissionConfig` (`default_policy=None`)
  → resolver answers `ALWAYS` → no behaviour change vs today.

## TDD tests (write first)
Wiring (unit; patch `MCPManager`, `RealLLMService`, `load_permission_config`, TUI run):
- `test_icoder_loads_permission_config_once` — `load_permission_config` called exactly once with
  `project_dir` when provider is langchain + mcp_config present.
- `test_icoder_injects_interceptor_into_manager` — `MCPManager` constructed with
  `tool_interceptors=[gateway.interceptor]`; same gateway instance passed to `RealLLMService`.
- `test_icoder_no_gateway_without_langchain` — non-langchain provider → `gateway=None`,
  `load_permission_config` not called.

Bypass guard (D1):
- `test_run_agent_stream_skips_inline_loader_when_tools_provided` — call `run_agent_stream(...,
  tools=[fake_tool])` with `MultiServerMCPClient` patched to raise; assert it is never constructed
  (the inline loader / site-3 path is not taken).
- `test_icoder_stream_always_provides_manager_tools` — `RealLLMService` with a fake mcp_manager →
  `prompt_llm_stream` always receives non-`None` `tools` (iCoder never hits the inline loader).

Integration (`@pytest.mark.langchain_integration`):
- `test_gateway_denies_never_call_through_real_convert` — build a real langchain tool via
  `convert_mcp_tool_to_langchain_tool(None, fake_mcp_tool, connection=..., tool_interceptors=[gate.interceptor])`
  for an in-process/fake MCP tool; a config denying it → invoking the tool yields a
  `ToolMessage(status="error")` and does **not** raise; an `always` tool returns the same result as with
  no gateway.

## Checks
Full quality gate green. Run the integration test explicitly:
`run_pytest_check(markers=["langchain_integration"])`.

## Commit
`I2.3 step 5: wire permission gateway into iCoder startup + bypass guard + integration`

## LLM prompt
> Implement Step 5 of the I2.3 plan. Read `pr_info/steps/summary.md` (D1, D2) and
> `pr_info/steps/step_5.md`. Following TDD, first add the wiring, bypass-guard, and integration tests,
> then in `execute_icoder()` call `load_permission_config(project_dir)` once, construct
> `LangchainEnforcementGateway(config)`, inject `tool_interceptors=[gateway.interceptor]` into
> `MCPManager`, and pass `gateway=gateway` to `RealLLMService` (None outside the langchain branch). Do
> not touch `AppCore`/`SendToLLM`/the Protocol. Use MCP tools only; make all checks pass including the
> `langchain_integration` test; produce one commit.
