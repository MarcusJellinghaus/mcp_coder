# Step 5 — Startup wiring + bypass guard + real-agent integration (D1/D2)

**Reference:** read `pr_info/steps/summary.md` (Decisions D1, D2) first.

Wire everything together at iCoder startup: assert adapter capability early, load the permission
config, construct the gateway, inject its interceptor into `MCPManager`, and pass it to
`RealLLMService`. Add the bypass-guard tests (D1 — covering **both** site 2 and site 3) and one
real-agent integration test that proves the end-to-end path.

## WHERE
- `src/mcp_coder/cli/commands/icoder.py` — `execute_icoder()` component-construction block.
- `tests/icoder/test_icoder_permission_wiring.py` (new) — wiring + bypass-guard.
- `tests/llm/providers/langchain/test_permission_bridge.py` **or**
  `tests/icoder/test_icoder_permission_wiring.py` — the `langchain_integration`-marked integration test.

## WHAT (icoder.py, inside the existing `if provider == "langchain" and mcp_config:` block)
```python
from ...icoder.permissions import load_permission_config           # public API
from ...icoder.permissions.gateway import LangchainEnforcementGateway
from ...llm.providers.langchain.agent import _assert_tool_interceptors_supported

_assert_tool_interceptors_supported()                              # clear error BEFORE first convert(...)
config = load_permission_config(project_dir)                       # D2: once at startup
gateway = LangchainEnforcementGateway(config)
server_config = _load_mcp_server_config(mcp_config, env_vars)
mcp_manager = MCPManager(server_config, tool_interceptors=[gateway.interceptor])
```
Then pass `gateway=gateway` to `RealLLMService(...)`. Keep `gateway = None` outside the langchain branch
and still pass `gateway=gateway` (None) to `RealLLMService`.

## HOW
- **Capability check fires early (ordering fix).** Call the reusable
  `_assert_tool_interceptors_supported()` (Step 1) at the **top** of the langchain branch, before
  constructing `MCPManager` — so a `<0.3.0` adapter yields the clear `ImportError` instead of the raw
  `TypeError: unexpected keyword argument 'tool_interceptors'` raised later when `MCPManager.tools()`
  runs the first `convert_...(tool_interceptors=[gateway.interceptor])`. (`_check_agent_dependencies`
  runs it too, but only inside the agent build, which is *after* the manager builds its tools on the
  iCoder path — hence the explicit early call here.)
- `gateway.interceptor` is a bound async method → valid `ToolCallInterceptor` (`async (request, handler)`).
- `load_permission_config` takes a `Path`; `project_dir` is already a resolved `Path` in this function.
- No change to `AppCore`, `SendToLLM`, or the `LLMService` Protocol.

## ALGORITHM (wiring)
```
mcp_manager = None; gateway = None
if provider == "langchain" and mcp_config:
    _assert_tool_interceptors_supported()          # clear error before first convert(...)
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
- `test_icoder_asserts_adapter_capability_before_manager` (ordering) — with
  `_assert_tool_interceptors_supported` patched to raise `ImportError`, `execute_icoder` raises that
  clear error and `MCPManager` (patched) is **never constructed** — proving the check precedes the
  first `convert_...(tool_interceptors=...)`.

Bypass guard (D1) — must cover **both** un-instrumented `convert_...` sites reachable in principle
(site 2 = non-stream `run_agent`; site 3 = `run_agent_stream` inline `tools is None` loader):
- `test_run_agent_stream_skips_inline_loader_when_tools_provided` (**site 3**) — call
  `run_agent_stream(..., tools=[fake_tool])` with `MultiServerMCPClient` patched to raise; assert it is
  never constructed (the inline loader / site-3 path is not taken).
- `test_icoder_stream_always_provides_manager_tools` — `RealLLMService` with a fake mcp_manager →
  `prompt_llm_stream` always receives non-`None` `tools` (iCoder never hits the site-3 inline loader).
- `test_icoder_path_is_stream_only_never_run_agent` (**site 2**) — iCoder's provider path is
  structurally stream-only: driving a `RealLLMService.stream()` turn routes through `prompt_llm_stream`
  → `run_agent_stream`; with the non-stream `run_agent` (the only caller of site 2's `convert_...`)
  patched to raise, it is **never** invoked. Proves iCoder cannot reach the second un-instrumented
  convert site, completing the AC "no un-instrumented convert site reachable from iCoder".

Integration (`@pytest.mark.langchain_integration`):
- `test_gateway_denies_never_call_through_real_convert` — build a real langchain tool via
  `convert_mcp_tool_to_langchain_tool(None, fake_mcp_tool, connection=..., tool_interceptors=[gate.interceptor])`
  for an in-process/fake MCP tool; a config denying it → invoking the tool yields a
  `ToolMessage(status="error")` and does **not** raise; an `always` tool returns the same result as with
  no gateway. **End-to-end canonical-identity assertion (one line):** capture the `request` the real
  interceptor receives and assert the turn-level stamp (`metadata["mcp_canonical_name"]` /
  `MCPManager.canonical_name(tool)`) equals the interceptor-reconstructed
  `f"mcp__{server}__{request.name}"` — turning the turn/call identity assumption into a guarded fact
  through the real `convert_...` + interceptor path.

## Checks
Full quality gate green. Run the integration test explicitly:
`run_pytest_check(markers=["langchain_integration"])`.

## Commit
`I2.3 step 5: wire permission gateway into iCoder startup + bypass guard + integration`

## LLM prompt
> Implement Step 5 of the I2.3 plan. Read `pr_info/steps/summary.md` (D1, D2) and
> `pr_info/steps/step_5.md`. Following TDD, first add the wiring, bypass-guard (both site 2 and site
> 3), capability-ordering, and integration tests, then in `execute_icoder()` call
> `_assert_tool_interceptors_supported()` at the top of the langchain branch (before `MCPManager`),
> then `load_permission_config(project_dir)` once, construct `LangchainEnforcementGateway(config)`,
> inject `tool_interceptors=[gateway.interceptor]` into `MCPManager`, and pass `gateway=gateway` to
> `RealLLMService` (None outside the langchain branch). Do not touch `AppCore`/`SendToLLM`/the
> Protocol. Use MCP tools only; make all checks pass including the `langchain_integration` test;
> produce one commit.
