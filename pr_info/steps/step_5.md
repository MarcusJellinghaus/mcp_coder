# Step 5 — Tier C: real MCP + real tool_interceptors, end-to-end

**Commit:** `spike(i3.1): Tier C — real interceptor fired, resume + deny end-to-end`

Read `pr_info/steps/summary.md` first. This is the heaviest tier and the end-to-end proof: a
throwaway FastMCP **stdio server inside the spike dir** (D4) plus a real
`tool_interceptors=[gate]` on a real `MCPManager`. It proves the **real interceptor coroutine
actually fired** even with the model stubbed, that on resolve the agent proceeds past the gated
call, and that deny returns `ToolMessage(status="error")` and the agent continues (**#5**).

## WHERE

- Create `spikes/i3-1-approval/server.py` — minimal FastMCP stdio server, one tool.
- Create `spikes/i3-1-approval/tier_c.py` — the driver + gate + assertions.

## WHAT — functions / signatures

`server.py`:
```python
from mcp.server.fastmcp import FastMCP     # arrives transitively via langchain-mcp-adapters (D4)
mcp = FastMCP("spike")

@mcp.tool()
def ping(text: str) -> str:
    """Return text unchanged — the single gated tool."""
    return text

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

`tier_c.py`:
```python
class Gate:
    """Real async tool_interceptors hook: (request, handler) -> Any."""
    fired: bool = False
    loop_id: int | None = None
    async def interceptor(self, request, handler):
        """Record fire + loop identity; approve -> await Future -> handler; deny -> ToolMessage."""

def build_server_config() -> dict:   # {"spike": {"command": sys.executable, "args":[server.py], "transport":"stdio"}}
def scenario_resume() -> None:       # approve path: interceptor fired + agent proceeds past gate
def scenario_deny() -> None:         # deny path: ToolMessage(status="error") + agent continues
```

## HOW — integration points

- `MCPManager(build_server_config(), tool_interceptors=[gate.interceptor])` from
  `mcp_coder.llm.providers.langchain.mcp_manager`; call `.tools()` to discover the real
  interceptor-wrapped `ping`.
- Drive with the same `FakeChatModel` pattern as Tier B (first invoke → tool_call to `ping`,
  second → `AIMessage("done")`), via real `run_agent_stream(..., tools=manager.tools())`.
- Inside `Gate.interceptor`, set `self.fired = True` and
  `self.loop_id = id(asyncio.get_running_loop())` **before** awaiting — this is the D6 fact on the
  *real* adapter path, and the flag is the "interceptor really fired" assertion.
- Approve path resolves the Future from a bare thread via `call_soon_threadsafe`; deny path returns
  `ToolMessage(content=..., status="error", tool_call_id=request.tool_call_id, name=request.name)`
  — the `tool_call_id` is **derived from the request** (as `permission_bridge.build_deny_tool_message`
  does), never `""`, so the `ToolMessage` matches the pending tool call in the AI message and the
  agent can continue (a mismatched/empty id would leave the tool call unanswered and wedge the turn).
- `close()` the manager in a `finally` to stop its daemon loop/subprocess.

## ALGORITHM — resume (scenario_resume)

```
manager = MCPManager(cfg, tool_interceptors=[gate.interceptor]); tools = manager.tools()
run real agent with FakeChatModel over `tools`; resolver thread approves the pending Future
drain events to completion
assert gate.fired is True                     # real coroutine executed (even with stub model)
assert a tool_result / final 'done' event appears   # agent proceeded PAST the gate
```

## ALGORITHM — deny (scenario_deny)

```
gate configured to DENY; run the agent
assert the returned ToolMessage has status == "error"
assert the returned ToolMessage.tool_call_id == request.tool_call_id   # matches the pending call
assert the agent still reaches its final message   # #5: deny does not wedge the turn
```

## DATA

- `build_server_config()` returns the stdio server dict (`command=sys.executable`,
  `args=[<abs path to server.py>]`, `transport="stdio"`).
- Prints `PASS: interceptor-fired`, `PASS: resume-past-gate`, `PASS: deny-shape-and-continue`;
  exits 0. The LLM call is stubbed/faked; only the *mechanics* are asserted (non-determinism of a
  real model must not gate these asserts).

## Notes

- Windows/stdio: launching a Python subprocess as the MCP server needs the Proactor loop (default
  on Windows) — `MCPManager` already runs its own daemon loop, so this is handled. Use the absolute
  path to `server.py` and `sys.executable` so the spike is CWD-independent.

## Definition of done

- `python spikes/i3-1-approval/tier_c.py` exits 0, all PASS lines, repeatable (mechanic asserts
  deterministic; only real-LLM latency/output — if ever swapped in — is best-effort).
- Standard `src`/`tests` fast unit suite still green.
