# Step 2 — Graph-level regression test: a denied call no longer wedges the agent

**Goal:** prove AC #3 — a denied tool call leaves the history **paired**, so
`create_react_agent` does not raise `INVALID_CHAT_HISTORY` and the agent continues past the
deny. Proven on the **graph state**, not the stream.

**One commit:** the new test + the CI line. No production code changes in this step.

> **Why the test comes after the fix:** every step must commit green, so a red-first test
> cannot be its own commit here. Verify it is a real regression test by temporarily
> reverting step 1's gateway line locally (pass `""`), confirming the test fails, then
> restoring the fix.

---

## WHERE

| Path | Change |
|---|---|
| `tests/icoder/test_icoder_permission_wiring.py` | append one test + one module-docstring line |
| `.github/workflows/langchain-integration.yml` | add this file to the marker run |

The test goes in this file because it already holds the sibling `langchain_integration`
deny test (`test_gateway_denies_never_call_through_real_convert`) and its fake-`MCPTool` +
real-converter scaffolding — no new file, no duplicated setup. (`tests/icoder` and
`tests.llm` stay import-independent: the test imports only production modules.)

---

## WHAT — the new test

```python
@pytest.mark.langchain_integration
@pytest.mark.asyncio
async def test_denied_call_keeps_history_paired_and_agent_continues() -> None: ...
```

Plus a local scripted model inside the test (~15 lines):

```python
    class _ScriptedModel(BaseChatModel):
        invoke_count: int = 0
        def bind_tools(self, tools: Any, **kw: Any) -> "_ScriptedModel": return self
        def _generate(self, messages, stop=None, run_manager=None, **kw): raise NotImplementedError
        async def _agenerate(self, messages, stop=None, run_manager=None, **kw): ...
        @property
        def _llm_type(self) -> str: return "scripted"
```

`bind_tools` must be overridden (`BaseChatModel.bind_tools` raises `NotImplementedError`
and `create_react_agent` calls it). Only the **async** `_agenerate` is implemented: the
agent path is async, and `BaseChatModel`'s default `_agenerate` would hand `_generate` to a
thread-pool. `invoke_count` doubles as the script index — no extra counter.

---

## HOW — integration points

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
    from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
```

* The tool is built by the **real** converter with the **real** gateway interceptor —
  that is what proves the adapter really hands `runtime` to the interceptor:

```python
    tool = convert_mcp_tool_to_langchain_tool(
        None,                                   # no session needed: deny never calls the handler
        fake_tool,
        connection={"transport": "stdio"},
        server_name="srv",
        tool_interceptors=[gateway.interceptor],
    )
```

* `fake_tool = MCPTool.model_validate({"name": "do_it", "description": "",
  "inputSchema": {"type": "object", "properties": {}}})` — an empty-object schema so
  `args={}` passes `ToolNode`'s schema validation (which runs **before** the tool coroutine,
  hence before the interceptor; a schema mismatch would silently skip the interceptor).
* Config: `PermissionConfig(rules=(Rule(matcher=Matcher(server="srv", tool="do_it"),
  policy=Policy.NEVER, layer="user"),))`. One policy is enough — `NEVER` and
  `AFTER_APPROVAL` reach the identical call site, and step 1's unit tests cover both.

---

## ALGORITHM

```
script: invoke 1 -> AIMessage(tool_calls=[{name:"do_it", args:{}, id:"call_1"}])
        invoke 2 -> AIMessage("done")
tool  = real converter(fake MCPTool, interceptors=[NEVER gateway.interceptor])
agent = create_react_agent(scripted_model, [tool])
result = await agent.ainvoke({"messages": [HumanMessage("go")]})   # raises today: INVALID_CHAT_HISTORY
assert the state ToolMessage is status="error" AND tool_call_id == "call_1"
assert model.invoke_count == 2 and the last message content == "done"
```

---

## DATA — assertions (graph state, not the stream)

```python
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].status == "error"
    assert tool_msgs[0].tool_call_id == "call_1"   # THE fix, at graph-state level
    assert model.invoke_count == 2                 # agent continued past the deny
    assert result["messages"][-1].content == "done"
```

`await agent.ainvoke(...)` returns the final state dict (`{"messages": [...]}`) — no
threads, no `run_agent_stream`, no session-history writes. Assert on this state and never
on stream events: `run_agent_stream` masks the empty id in the deny `tool_result` event via
`run_id`, so a stream-only assertion passes even with the bug present.

Two independent failure signals against unfixed code: `create_react_agent` raises
`ValueError` (`INVALID_CHAT_HISTORY`, naming the unpaired `call_1`) before the asserts are
reached, and the `tool_call_id` assert catches it if a future langgraph tolerates the
unpaired history.

---

## Also in this commit

* One line in the module docstring of `tests/icoder/test_icoder_permission_wiring.py`
  noting the graph-level deny test alongside the existing wiring/ordering/bypass concerns.
* `.github/workflows/langchain-integration.yml` — the marker run currently covers only
  `tests/llm/providers/langchain/test_langchain_integration.py`, so nothing would guard
  this regression in CI. Add the file:

```yaml
          pytest tests/llm/providers/langchain/test_langchain_integration.py \
            tests/icoder/test_icoder_permission_wiring.py \
            -m langchain_integration \
```

The workflow installs `.[dev,langchain]` and `textual` is a **core** dependency, so
`tests/icoder/` collects there; the new test needs no API credentials. This also brings the
pre-existing icoder integration test into CI — intended.

---

## Checks

```
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/icoder/test_icoder_permission_wiring.py"], markers=["langchain_integration"])
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_ruff_check(extra_args=["--preview"])
mcp__mcp-tools-py__run_lint_imports_check
```

The marked run must **pass**, not skip — if it skips, the langchain extras are missing and
the test proved nothing. Run `./tools/format_all.sh` before committing.

---

## Done when

* The new test passes with step 1's fix and **fails** with it reverted (verify locally,
  then restore).
* The unit suite, pylint, mypy(strict), ruff and lint-imports are all green.
* The CI workflow runs the file under the `langchain_integration` marker.

---

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`, then implement step 2.
> Step 1 must already be committed.
>
> Use MCP tools exclusively for file access and checks (see `.claude/CLAUDE.md`).
>
> Append one `langchain_integration` + `asyncio` test to
> `tests/icoder/test_icoder_permission_wiring.py` exactly as the step describes: a scripted
> `BaseChatModel` (async `_agenerate` only, `bind_tools` returning `self`) driven through a
> real `create_react_agent` over a tool built by the real
> `convert_mcp_tool_to_langchain_tool` with the real `LangchainEnforcementGateway`
> interceptor and a `NEVER` rule. Assert on the state returned by `await agent.ainvoke(...)`
> — never on stream events. Guard the third-party imports with `pytest.importorskip`. Add
> the workflow line to `.github/workflows/langchain-integration.yml`.
>
> Prove the test is a real regression test: temporarily change `gateway.py` to pass `""` as
> the `tool_call_id`, confirm the new test fails, then restore the fix and confirm it
> passes. Report both outcomes.
>
> Run the marked test plus all the checks listed in the step — the marked run must pass,
> not skip. Then `./tools/format_all.sh` and make exactly one commit.
