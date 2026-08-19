# Step 1 — Carry the real `tool_call_id` through both deny branches

**Goal:** the deny `ToolMessage` returned for `NEVER` and `AFTER_APPROVAL` carries the
tool_call id the model emitted, sourced from the langgraph runtime already present on the
adapter request — proven both in unit tests and at **graph-state level** (a denied call no
longer wedges `create_react_agent`).

**One commit:** tests + implementation + CI line, all checks green. The bridge signature
change and its two call sites must land together (a required third parameter breaks the
caller otherwise), and the graph-level test is red-first against the same fix — so unit
tests, graph test and production change are one step.

---

## WHERE

| Path | Role |
|---|---|
| `tests/llm/providers/langchain/test_permission_bridge.py` | unit — bridge shape (write first) |
| `tests/icoder/test_permissions_gateway.py` | unit — gateway sourcing (write first) |
| `tests/icoder/test_icoder_permission_wiring.py` | integration — graph-state proof (write first) |
| `src/mcp_coder/llm/providers/langchain/permission_bridge.py` | production — the langchain shape |
| `src/mcp_coder/icoder/permissions/gateway.py` | production — the pure enforcement seam |
| `spikes/i3-1-approval/tier_c.py` | call-site follow-through (one line) |
| `.github/workflows/langchain-integration.yml` | CI — run the graph test under the marker |

---

## WHAT — signatures

```python
# src/mcp_coder/llm/providers/langchain/permission_bridge.py
def build_deny_tool_message(text: str, name: str, tool_call_id: str) -> Any: ...

# src/mcp_coder/icoder/permissions/gateway.py  (unchanged signature)
async def interceptor(self, request: Any, handler: Callable[[Any], Awaitable[Any]]) -> Any: ...
```

Only `build_deny_tool_message` changes shape: a third **required** positional parameter.
Required — not defaulted to `""` — so the old 2-arg call is a visible regression signal.

---

## HOW — integration points

* No new imports in either production module. The gateway must **not** import
  `langchain_core`, `langgraph` or `langchain_mcp_adapters`; it reads the id with plain
  `getattr` chaining and `request` stays typed `Any`. The
  `langchain_library_isolation` import contract enforces this — `run_lint_imports_check`
  must stay green.
* The bridge keeps its function-local `from langchain_core.messages import ToolMessage`.
* `tests/icoder/test_permissions_gateway.py` stubs the bridge via the existing autouse
  `_fake_deny_bridge` monkeypatch fixture; widen that stub to 3 args so the gateway tests
  still need no `langchain_core`.

---

## ALGORITHM — gateway deny path

```
policy = resolve(canonical, request.args, frame, config).policy
if policy is ALWAYS:            return await handler(request)
text = _DENY_ASK if policy is AFTER_APPROVAL else _DENY_NEVER
runtime = getattr(request, "runtime", None)          # absent on non-graph/old adapters
tool_call_id = getattr(runtime, "tool_call_id", None) or ""   # None outside a graph
return build_deny_tool_message(text, request.name, tool_call_id)
```

Written as one expression to match the module's style (black wraps it):

```python
        tool_call_id = (
            getattr(getattr(request, "runtime", None), "tool_call_id", None) or ""
        )
        return build_deny_tool_message(text, request.name, tool_call_id)
```

---

## DATA — return values

* `build_deny_tool_message(...)` -> `ToolMessage(content=text, status="error",
  tool_call_id=tool_call_id, name=name)`.
* `interceptor(...)` -> unchanged contract: the real handler result for `ALWAYS`, else that
  deny `ToolMessage`.
* Fallback: no `runtime` attribute, `runtime is None`, or `tool_call_id is None` -> `""`
  (exactly today's behaviour outside a graph).

---

## TDD order

### 1. `tests/llm/providers/langchain/test_permission_bridge.py` (red)

* **Module docstring (D4):** delete the false parenthetical *"(langgraph's `ToolNode` fills
  in the real `tool_call_id` downstream)"*; replace with a statement that the deny message
  carries the id of the tool call it denies.
* Update both existing tests to the 3-arg call:
  `build_deny_tool_message("x", "t", "call_1")`.
* Add:

```python
def test_build_deny_tool_message_carries_tool_call_id() -> None:
    """The deny message keeps the tool_call id it was given (history stays paired)."""
    msg = build_deny_tool_message("denied", "some_tool", "call_1")

    assert msg.tool_call_id == "call_1"
```

### 2. `tests/icoder/test_permissions_gateway.py` (red)

* `_request` gains a runtime carrying the id:

```python
def _request(
    server_name: str,
    name: str,
    args: dict[str, Any] | None = None,
    tool_call_id: str = "call_1",
) -> Any:
    """Build a fake adapter request, incl. the langgraph runtime ToolNode injects."""
    return SimpleNamespace(
        server_name=server_name,
        name=name,
        args=args or {},
        runtime=SimpleNamespace(tool_call_id=tool_call_id),
    )
```

* Widen the autouse `_fake_deny_bridge` stub and let it mirror the id back, so no separate
  capture list is needed (update its docstring: the gateway must hand the bridge the
  correct text **and** tool_call id):

```python
    def _fake(text: str, name: str, tool_call_id: str) -> Any:
        return SimpleNamespace(
            content=text,
            status="error",
            name=name,
            tool_call_id=tool_call_id,
            type="tool",
        )
```

* Add three tests (the first two fail against today's 2-arg call — the regression signal):

```python
async def test_interceptor_never_carries_tool_call_id() -> None:
    """A ``never`` denial carries the emitted tool_call id (history stays paired)."""
    # config NEVER -> await interceptor(_request("s", "t", tool_call_id="call_7"), handler)
    # assert result.tool_call_id == "call_7"

async def test_interceptor_ask_carries_tool_call_id() -> None:
    """An ``ask`` denial carries the emitted id too (same shared bridge call)."""

async def test_interceptor_deny_without_runtime_uses_empty_id() -> None:
    """No ``runtime`` on the request (outside a graph) -> the id falls back to ``""``."""
    # request built inline WITHOUT a runtime attribute:
    #   SimpleNamespace(server_name="s", name="t", args={})
    # assert result.tool_call_id == ""
```

The existing `test_interceptor_never_*` / `test_interceptor_ask_*` tests keep working
through the widened stub; no other change to them.

### 3. `tests/icoder/test_icoder_permission_wiring.py` — graph-state test (red)

Proves AC #3: a denied tool call leaves the history **paired**, so `create_react_agent`
does not raise `INVALID_CHAT_HISTORY` and the agent continues past the deny. Red-first
against the unfixed gateway: today the run raises `ValueError` (`INVALID_CHAT_HISTORY`,
naming the unpaired `call_1`) before any assertion is reached. It is
`langchain_integration`-marked, so run it under its marker (see **Checks**) to see the red
— the default unit run does not collect it.

Appended to this file because it already holds the sibling `langchain_integration` deny
test (`test_gateway_denies_never_call_through_real_convert`) and its fake-`MCPTool` +
real-converter scaffolding — no new file, no duplicated setup. Also add one module-docstring
line noting the graph-level deny test alongside the existing wiring/ordering/bypass
concerns.

```python
@pytest.mark.langchain_integration
@pytest.mark.asyncio
async def test_denied_call_keeps_history_paired_and_agent_continues() -> None: ...
```

* Function-local imports (matching the existing integration test's style), guarded by
  `pytest.importorskip("langchain_mcp_adapters")`, `("langgraph")`, `("mcp")` so selecting
  the marker on a base install is a clean skip, not an error:

```python
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool
    from langgraph.prebuilt import create_react_agent
    from mcp.types import Tool as MCPTool

    from mcp_coder.icoder.permissions import Matcher, PermissionConfig, Policy, Rule
    from mcp_coder.icoder.permissions.gateway import _DENY_NEVER  # deny text, asserted
    from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
```

* A local scripted model inside the test (~15 lines). Both overrides carry
  `# type: ignore[no-untyped-def]` (or full annotations) — `run_mypy_check` runs strict and
  rejects untyped defs in `tests/`; this mirrors `spikes/i3-1-approval/_common.py:91`.
  The **class statement itself** additionally needs `# type: ignore[misc]`: `pyproject.toml`
  sets `follow_imports = "skip"` for `langchain_core.*`, so `BaseChatModel` resolves to
  `Any` and strict mypy's `disallow_subclassing_any` errors with
  *Class cannot subclass "BaseChatModel" (has type "Any")* `[misc]`. Without it the
  required `run_mypy_check` fails on the class line even when both methods are annotated.
  (`spikes/` is outside the mypy target dirs, which is why `_common.py` carries no such
  ignore.)

```python
    class _ScriptedModel(BaseChatModel):  # type: ignore[misc]
        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> "_ScriptedModel":
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            raise NotImplementedError("scripted model implements _agenerate")

        async def _agenerate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            ...

        @property
        def _llm_type(self) -> str:
            return "scripted"
```

`bind_tools` must be overridden (`BaseChatModel.bind_tools` raises `NotImplementedError`
and `create_react_agent` calls it). Only the **async** `_agenerate` is implemented: the
agent path is async, and `BaseChatModel`'s default `_agenerate` would hand `_generate` to a
thread-pool. `invoke_count` doubles as the script index — no extra counter.

* The tool is built by the **real** converter with the **real** gateway interceptor,
  wrapped in a capturing shim (same pattern as the sibling test) so the assertions can
  prove the interceptor actually ran — that is what proves the adapter really hands
  `runtime` to the interceptor:

```python
    captured: dict[str, Any] = {}

    async def _capturing_interceptor(request: Any, handler: Any) -> Any:
        captured["request"] = request
        return await gateway.interceptor(request, handler)

    tool = convert_mcp_tool_to_langchain_tool(
        None,                                   # no session needed: deny never calls the handler
        fake_tool,
        connection={"transport": "stdio"},
        server_name="srv",
        tool_interceptors=[_capturing_interceptor],
    )
```

* `fake_tool = MCPTool.model_validate({"name": "do_it", "description": "",
  "inputSchema": {"type": "object", "properties": {}}})` — an empty-object schema so
  `args={}` passes `ToolNode`'s schema validation (which runs **before** the tool coroutine,
  hence before the interceptor; a schema mismatch would silently skip the interceptor —
  the deny-text and captured-request assertions below are what catch that).
* Config: `PermissionConfig(rules=(Rule(matcher=Matcher(server="srv", tool="do_it"),
  policy=Policy.NEVER, layer="user"),))`. One policy is enough — `NEVER` and
  `AFTER_APPROVAL` reach the identical call site, and the unit tests above cover both.

Flow:

```
script: invoke 1 -> AIMessage(tool_calls=[{name:"do_it", args:{}, id:"call_1"}])
        invoke 2 -> AIMessage("done")
tool  = real converter(fake MCPTool, interceptors=[capturing NEVER gateway.interceptor])
agent = create_react_agent(scripted_model, [tool])
result = await agent.ainvoke({"messages": [HumanMessage("go")]})   # raises today: INVALID_CHAT_HISTORY
```

Assertions read the **graph state**, never the stream:

```python
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].content == _DENY_NEVER     # the GATEWAY denied it, not ToolNode
    assert captured["request"].name == "do_it"     # the interceptor really ran
    assert tool_msgs[0].status == "error"
    assert tool_msgs[0].tool_call_id == "call_1"   # THE fix, at graph-state level
    assert model.invoke_count == 2                 # agent continued past the deny
    assert result["messages"][-1].content == "done"
```

The deny-text and captured-request assertions are load-bearing: `ToolNode`'s own
tool-invocation / unknown-tool error also yields a `ToolMessage(status="error")` carrying
the correct `tool_call_id`, and the agent still loops back for a 2nd invoke — so without
them the test would pass green even if the interceptor was never reached.

`await agent.ainvoke(...)` returns the final state dict (`{"messages": [...]}`) — no
threads, no `run_agent_stream`, no session-history writes. Assert on this state and never
on stream events: `run_agent_stream` masks the empty id in the deny `tool_result` event via
`run_id`, so a stream-only assertion passes even with the bug present.

### 4. Production (green)

* `permission_bridge.py`: add the parameter, set it on the `ToolMessage`, and rewrite the
  `Args:`/`Returns:` docstring — **the "ToolNode overwrites it downstream" sentence must be
  gone** (D4). Document `tool_call_id` as *the id of the model's tool call being denied, so
  the deny message stays paired with it in the agent's history*.
* `gateway.py`: apply the ALGORITHM above. Extend the `interceptor` docstring's `Args:`
  entry for `request` to mention `.runtime` (carrying the emitted `tool_call_id` inside a
  langgraph run). Leave the module docstring alone — it stays accurate.

### 5. `spikes/i3-1-approval/tier_c.py` (call-site follow-through)

One line in `InterceptorGate.interceptor`:

```python
            return build_deny_tool_message(_DENY_TEXT, request.name, "")
```

Replace the two stale comment lines above it (*"request exposes only .server_name / .name /
.args, so there is no tool_call_id to derive"* — now known false) with a single accurate
note: the explicit `""` keeps this frozen spike run byte-identical to the pre-#1118
behaviour it recorded. Do **not** touch `FINDINGS.md`.

### 6. `.github/workflows/langchain-integration.yml` (CI wiring)

The marker run currently covers only
`tests/llm/providers/langchain/test_langchain_integration.py`, so nothing would guard this
regression in CI. Add the file:

```yaml
          pytest tests/llm/providers/langchain/test_langchain_integration.py \
            tests/icoder/test_icoder_permission_wiring.py \
            -m langchain_integration \
```

The workflow installs `.[dev,langchain]` and `textual` is a **core** dependency, so
`tests/icoder/` collects there; the new test needs no API credentials. This also brings the
pre-existing icoder integration test into CI — intended.

---

## Checks (all via MCP tools, all must pass)

```
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/icoder/test_icoder_permission_wiring.py"], markers=["langchain_integration"])
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_ruff_check(extra_args=["--preview"])
mcp__mcp-tools-py__run_lint_imports_check
```

The marked run must **pass**, not skip — if it skips, the langchain extras are missing and
the graph test proved nothing.

Ruff runs the `D`/`DOC` rules in preview mode: the new `tool_call_id` parameter needs an
`Args:` entry in the bridge docstring or `DOC` fails. Run `./tools/format_all.sh` before
committing.

---

## Done when

* `build_deny_tool_message` sets a caller-supplied `tool_call_id`; no docstring anywhere
  claims `ToolNode` fills it in.
* Both deny branches pass the id sourced from `request.runtime.tool_call_id`, `""` when
  absent.
* The graph test passes under its marker: the state `ToolMessage` carries the deny text and
  `tool_call_id == "call_1"`, and the agent continues past the deny.
* All five checks green; `lint-imports` confirms the gateway still imports no
  `langchain_core`.
* The CI workflow runs `tests/icoder/test_icoder_permission_wiring.py` under the
  `langchain_integration` marker.

---

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`, then implement step 1.
>
> Use MCP tools exclusively for file access and checks (see `.claude/CLAUDE.md`) — never
> `Read`/`Write`/`Edit`, never `Bash` for pylint/pytest/mypy.
>
> Work TDD: first write all three test changes exactly as the step describes —
> `tests/llm/providers/langchain/test_permission_bridge.py`,
> `tests/icoder/test_permissions_gateway.py`, and the new graph-state test appended to
> `tests/icoder/test_icoder_permission_wiring.py`. Confirm they fail before the fix: the
> new gateway tests fail against the current 2-arg `build_deny_tool_message` call, and the
> graph test (run it under `markers=["langchain_integration"]`) fails with langgraph's
> `INVALID_CHAT_HISTORY`. Those failures are the regression signal. Then apply the
> production change to `permission_bridge.py` and `gateway.py`, plus the one-line call-site
> update in `spikes/i3-1-approval/tier_c.py` and the workflow line in
> `.github/workflows/langchain-integration.yml`.
>
> Constraints: `gateway.py` must not import `langchain_core`, `langgraph` or
> `langchain_mcp_adapters` — read the id with plain `getattr` chaining and keep `request`
> typed `Any`. The third bridge parameter is required, not defaulted. The graph test must
> assert the deny text (`_DENY_NEVER`) and the captured interceptor request, not only
> `status`/`tool_call_id` — a `ToolNode` error message would satisfy those alone. Annotate
> the scripted model's `_generate`/`_agenerate` or carry
> `# type: ignore[no-untyped-def]`, **and** put `# type: ignore[misc]` on the
> `class _ScriptedModel(BaseChatModel):` line — `langchain_core.*` is
> `follow_imports = "skip"`, so `BaseChatModel` is `Any` and strict mypy's
> `disallow_subclassing_any` rejects the subclass otherwise. Assert on the state returned by
> `await agent.ainvoke(...)`, never on stream events. Delete the false "ToolNode overwrites
> it downstream" claim from both the bridge docstring and the bridge test-module docstring.
> Do not edit `spikes/i3-1-approval/FINDINGS.md`.
>
> Run all the checks listed in the step — the marked run must pass, not skip — and fix
> everything they report. Then `./tools/format_all.sh` and make exactly one commit.
