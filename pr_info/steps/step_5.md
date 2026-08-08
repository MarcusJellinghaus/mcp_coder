# Step 5 — Tier C: real MCP + real tool_interceptors, end-to-end

**Commit:** `spike(i3.1): Tier C — real interceptor fired, resume + deny end-to-end`

Read `pr_info/steps/summary.md` first. This is the heaviest tier and the end-to-end proof: a
throwaway FastMCP **stdio server inside the spike dir** (D4) plus a real
`tool_interceptors=[gate]` on a real `MCPManager`. It proves the **real interceptor coroutine
actually fired** even with the model stubbed, that on resolve the agent proceeds past the gated
call, and that deny returns `ToolMessage(status="error")` and the agent continues (**#5**).

## WHERE

- Create `spikes/i3-1-approval/server.py` — minimal FastMCP stdio server, one tool.
  **Template: `tests/llm/providers/claude/_mcp_stub_server.py`** — an existing, working minimal
  `mcp.server.fastmcp.FastMCP` stdio server launched via `sys.executable`, already proven on this
  platform (and `pyproject.toml:235` already carries an `mcp.server.fastmcp` mypy override, which
  independently confirms D4's "no new dependency"). Copy its shape; don't invent one.
- Create `spikes/i3-1-approval/tier_c.py` — the driver + gate + assertions. Imports `FakeChatModel`
  from `spikes/i3-1-approval/_common.py` (created in Step 2) rather than restating it.

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
class InterceptorGate:
    """Real async tool_interceptors hook: (request, handler) -> Any.

    Named InterceptorGate, not Gate, so it cannot be confused with
    `_common.Gate` (the blocking-tool cross-thread handoff) — different
    mechanism, different file.
    """
    fired: bool = False
    loop_id: int | None = None
    loop: asyncio.AbstractEventLoop | None = None    # captured inside the coroutine (D6)
    future: asyncio.Future[str] | None = None        # the pending approval the resolver thread hits
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
- Drive with the shared `FakeChatModel` from `_common.py` (first invoke → tool_call to `ping`,
  second → `AIMessage("done")`), via real `run_agent_stream(..., tools=manager.tools())`. It
  records, per invoke, both the running-loop id and the **`messages` list it was handed**; the
  second invoke's list contains the post-`ToolNode` `ToolMessage` from state, which the deny
  scenario asserts on (below).
- Inside `InterceptorGate.interceptor`, set `self.fired = True`,
  `self.loop = asyncio.get_running_loop()`, `self.loop_id = id(self.loop)` and
  `self.future = self.loop.create_future()` **before** awaiting — this is the D6 fact on the
  *real* adapter path, the flag is the "interceptor really fired" assertion, and `loop`/`future`
  are what the resolver thread targets with `call_soon_threadsafe`.
- **Capture two independent loop references for the D6 identity check (the go/no-go):**
  - `agent_loop_id` — an **independent** reference to the agent loop, recorded *not* by the
    interceptor (that would be circular). Have `FakeChatModel` record
    `id(asyncio.get_running_loop())` when the agent invokes it (the model runs on the same
    `asyncio.run(_run())` agent loop as the ToolNode await), and expose it (e.g. `model.loop_id`).
  - `daemon_loop_id` — the MCPManager daemon-loop id, read from the manager's own loop handle
    (`mcp_manager.py:52-59`; e.g. `id(manager._loop)`) captured after construction.
  These give the two poles the interceptor's `loop_id` is compared against below.
- Approve path resolves the Future from a bare thread via `call_soon_threadsafe`; deny path reuses
  the shipped `permission_bridge.build_deny_tool_message(text, request.name)`, which returns
  `ToolMessage(content=text, status="error", tool_call_id="", name=name)` — `permission_bridge.py:28`
  really does hardcode the empty id, and the real interceptor `request` exposes only `.server_name`,
  `.name`, and `.args`, so there is **no** `request.tool_call_id` to derive from. The shape stays
  as shipped; the spike does not change it.
- **But the claim that langgraph's `ToolNode` overwrites the empty id downstream is an inherited
  docstring assumption that nothing currently verifies** — and `scenario_deny` cannot notice it
  being wrong, because `FakeChatModel` never validates the `ToolMessage.tool_call_id` ↔
  `AIMessage.tool_calls[].id` pairing that a real provider API rejects. So turn it into an
  **observed fact**: compare the `tool_call_id` of the `ToolMessage` in the fake's **second-invoke**
  `messages` list against the id of the tool_call the fake emitted on invoke 1.
- This one is a **recorded probe, not a gating assert** — the only exception in Step 5; every other
  assertion here stays gating. Print `PASS: deny-tool-call-id-filled` when the ids match, and
  `OBSERVED: deny-tool-call-id-empty (finding for I3.2 / latent I2.3 bug)` when they do not;
  **exit 0 either way**. Both outcomes are valid deliverables under §10.3's "demonstrated working
  **or** documented-impossible with rationale", and Step 6 §10 records whichever occurred — the run
  cannot both fail and be the deliverable. A negative is not hypothetical:
  `langchain_core.BaseTool._format_output` returns `ToolOutputMixin` instances unchanged and
  `ToolMessage` **is** a `ToolOutputMixin`, so the empty id may well survive `ToolNode`.
- `close()` the manager in a `finally` to stop its daemon loop/subprocess.

## ALGORITHM — resume (scenario_resume)

```
gate = InterceptorGate()
manager = MCPManager(cfg, tool_interceptors=[gate.interceptor]); tools = manager.tools()
daemon_loop_id = id(manager._loop)            # MCPManager daemon loop (mcp_manager.py:52-59)
run real agent with FakeChatModel over `tools`; resolver thread approves the pending Future via
  gate.loop.call_soon_threadsafe(gate.future.set_result, "approve")
drain events to completion
assert gate.fired is True                     # real coroutine executed (even with stub model)
# D6 identity — the go/no-go, proven on the REAL adapter path (not just Tier A's single loop):
assert gate.loop_id == model.loop_id          # interceptor ran on the AGENT loop (independent ref)
assert gate.loop_id != daemon_loop_id         # ...and NOT on the MCPManager daemon loop
assert a tool_result event AND the fake's final assistant text (the AIMessage("done") returned on
  invoke 2) appear                            # agent proceeded PAST the gate
# NOT the {"type": "done"} StreamEvent: agent.py:698 yields that unconditionally once the
# astream_events loop ends, so it cannot distinguish "proceeded past the gate" from "stopped early".
```

## ALGORITHM — deny (scenario_deny)

```
gate configured to DENY -> returns build_deny_tool_message(text, request.name); run the agent
assert the returned ToolMessage has status == "error"   # shipped deny shape (tool_call_id="")
assert the agent still reaches its final message   # #5: deny does not wedge
# RECORDED PROBE (not a gating assert — the only one in this step): observe whether ToolNode
# filled the empty id. The fake never validates the pairing a real provider API would reject,
# so without this the assumption stays untested; but a negative is a valid recorded finding,
# not a run failure (Step 6 §10 writes up whichever occurred).
emitted_id = id of the tool_call FakeChatModel emitted on invoke 1
tm = the ToolMessage in FakeChatModel's SECOND-invoke messages list (post-ToolNode, from state)
if tm.tool_call_id == emitted_id: print("PASS: deny-tool-call-id-filled")
else: print("OBSERVED: deny-tool-call-id-empty (finding for I3.2 / latent I2.3 bug)")
# no raise, no non-zero exit, either way
```

## DATA

- `build_server_config()` returns the stdio server dict (`command=sys.executable`,
  `args=[<abs path to server.py>]`, `transport="stdio"`).
- Prints `PASS: interceptor-fired`, `PASS: loop-identity-real-path`, `PASS: resume-past-gate`,
  `PASS: deny-shape-and-continue`; then **either** `PASS: deny-tool-call-id-filled` **or**
  `OBSERVED: deny-tool-call-id-empty (finding for I3.2 / latent I2.3 bug)`. Exits 0 in both cases.
  The LLM call is stubbed/faked; only the *mechanics* are asserted (non-determinism of a real model
  must not gate these asserts).

## Notes

- Windows/stdio: launching a Python subprocess as the MCP server needs the Proactor loop (default
  on Windows) — `MCPManager` already runs its own daemon loop, so this is handled. Use the absolute
  path to `server.py` and `sys.executable` so the spike is CWD-independent.

## Definition of done

- `python spikes/i3-1-approval/tier_c.py` exits 0, all PASS lines, repeatable (mechanic asserts
  deterministic; only real-LLM latency/output — if ever swapped in — is best-effort).
- **Explicit exception to "all PASS lines":** the deny-`tool_call_id` probe is a *recorded* probe,
  not a gating assert. A run that prints `OBSERVED: deny-tool-call-id-empty (finding for I3.2 /
  latent I2.3 bug)` instead of `PASS: deny-tool-call-id-filled` still exits 0 and still satisfies
  this DoD — that line is a recorded finding, not a failure. Every other assertion in Step 5 is
  gating.
- Standard `src`/`tests` fast unit suite still green.
