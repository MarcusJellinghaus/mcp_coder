# #1118 — Deny/ask path must carry the real `tool_call_id`

## Problem

The iCoder permission deny path builds a langchain `ToolMessage` with an **empty
`tool_call_id`**. The model's `tool_call` is then left unpaired in the agent's message
history, so `create_react_agent` raises `INVALID_CHAT_HISTORY` on the next turn and the
agent **wedges** — it never continues past a denied tool call.

Live on `main` today for any tool configured `deny` (`Policy.NEVER`) or `ask`
(`Policy.AFTER_APPROVAL`). Regression against I2.3/#1043's shipped AC *"a never/denied call
returns a clean `ToolMessage(status="error")`; agent continues, no raise."*

Found empirically by the I3.1 spike (#1044), Tier C — `spikes/i3-1-approval/FINDINGS.md` §10.

## Root cause (verified against the installed packages)

`build_deny_tool_message` passes `tool_call_id=""` and its docstring claims langgraph's
`ToolNode` overwrites it downstream. **That claim is false.** Verified on
langchain-mcp-adapters 0.3.2 / langgraph 1.2.11 / langchain-core 1.5.5:

| Fact | Where |
|---|---|
| `MCPToolCallRequest` carries `runtime: object \| None` alongside `name`/`args`/`server_name` | `langchain_mcp_adapters.interceptors` |
| `convert_mcp_tool_to_langchain_tool.call_tool` builds the request with `runtime=runtime` | `langchain_mcp_adapters.tools` |
| `ToolNode` injects a `ToolRuntime` (carrying `tool_call_id`) into any tool param **named** `runtime` (`_get_all_injected_args`: `if name == "runtime"`) | `langgraph.prebuilt.tool_node` |
| A `ToolMessage` returned by a tool passes through unchanged (`isinstance(content, ToolOutputMixin) -> return content`) — so neither the empty id nor a correct one is rewritten | `langchain_core.tools.base.BaseTool._format_output` |

So the real id **is** already on the interceptor's request as `request.runtime.tool_call_id`.
No new plumbing is needed — only reading it and passing it along.

## Architectural / design changes

There is **no structural change**: no new module, class, layer, dependency or import
contract. The existing two-part seam is preserved exactly:

```
gateway.interceptor (pure, no langchain_core)
        │  text + name + tool_call_id
        ▼
permission_bridge.build_deny_tool_message (provider package, owns langchain_core)
        ▼
ToolMessage(status="error", tool_call_id=<emitted id>)
```

Three design points, all inherited from the issue's decisions:

1. **The id is sourced, not invented (D1).** The gateway reads
   `request.runtime.tool_call_id` and passes it to the bridge as a new required
   parameter. The bridge stays a dumb shape-builder.
2. **The gateway stays `langchain_core`-free (D2).** It reads the id with plain
   `getattr` chaining — `request` remains typed `Any`, no langgraph/langchain type is
   imported or referenced. This keeps the `langchain_library_isolation` import contract
   intact (it forbids `langchain_core` outside `mcp_coder.llm.providers.langchain.**`).
   The `or ""` fallback preserves today's behaviour outside a graph (`runtime is None`),
   and the outer `getattr` default tolerates an adapter whose request has no `runtime`
   attribute at all.
3. **One shared fix covers both deny branches (D3).** `NEVER` and `AFTER_APPROVAL` reach
   the same call site, so the `NEVER` branch stays correct regardless of what #1045 later
   does to the `AFTER_APPROVAL` branch.

Required (not optional-with-default) third parameter is deliberate: it is what makes the
old 2-arg call a compile-time-visible regression signal, and it avoids a silent default
that could re-introduce the bug.

## Test strategy (D5)

The bug slipped because no test validated tool_call pairing at graph-state level.

* **Unit** — bridge: the deny message carries the id it was given. Gateway: the emitted id
  is carried for **both** `NEVER` and `AFTER_APPROVAL`, plus the `""` fallback when no
  runtime is present.
* **Integration** (`langchain_integration`, deterministic, **no real LLM**) — a scripted
  `BaseChatModel` driven through a real `create_react_agent` / `ToolNode` over a tool built
  by the real `convert_mcp_tool_to_langchain_tool` with the real gateway interceptor.
  Assertions read the **graph state**, not the stream: `run_agent_stream` cosmetically
  masks the empty id in the stream event (it uses `run_id`), so a stream-only assertion
  passes even when the bug is present.

## Files created / modified

| # | Path | Change |
|---|---|---|
| 1 | `src/mcp_coder/llm/providers/langchain/permission_bridge.py` | **modify** — `build_deny_tool_message` gains `tool_call_id: str` and sets it; false docstring claim removed (D4) |
| 1 | `src/mcp_coder/icoder/permissions/gateway.py` | **modify** — `interceptor` sources the id from `request.runtime.tool_call_id` (D2) and passes it on both deny branches |
| 1 | `tests/llm/providers/langchain/test_permission_bridge.py` | **modify** — 3-arg calls, new id assertion, false claim removed from the module docstring (D4) |
| 1 | `tests/icoder/test_permissions_gateway.py` | **modify** — `_request` gains `runtime`, deny-bridge stub widened to 3 args, 3 new tests |
| 1 | `spikes/i3-1-approval/tier_c.py` | **modify** — one-line call-site update (explicit `""`, keeps the frozen spike runnable and its recorded outcome unchanged) |
| 1 | `tests/icoder/test_icoder_permission_wiring.py` | **modify** — one new `langchain_integration` graph test appended (reuses the file's existing fake-`MCPTool` + real-converter scaffolding) |
| 1 | `.github/workflows/langchain-integration.yml` | **modify** — one line: also run this file under the marker, so the regression is guarded in CI |

No new folders or modules. `spikes/i3-1-approval/FINDINGS.md` is **not** edited — it is the
frozen record of the spike run, and #1045 deletes the whole spike directory (D9).

## Steps

| Step | Scope | Commit |
|---|---|---|
| [step_1.md](./step_1.md) | Carry the real `tool_call_id` through both deny branches (unit + graph tests, fix, CI wiring) | 1 |

One step, one commit. The bridge signature change and the gateway call site must land
together (a required third parameter breaks the caller otherwise), and the graph-level
test — the proof that a denied call no longer wedges the agent (AC #3) — is red-first
against that same fix: today it raises `INVALID_CHAT_HISTORY`. Splitting it out would make
it a test written *after* the code it guards, verifiable only by manually reverting the
fix; folded in, it is an ordinary red-then-green test. The CI line that runs it rides along
in the same commit.

## Acceptance criteria (from #1118)

- [ ] `build_deny_tool_message` sets the real `tool_call_id`; the gateway sources it from
      `request.runtime.tool_call_id` with a `""` fallback.
- [ ] Both `NEVER` and `AFTER_APPROVAL` denials return `ToolMessage(status="error")`
      carrying the emitted tool_call id.
- [ ] A denied call no longer wedges the agent — no `INVALID_CHAT_HISTORY`; the agent
      continues past the deny (proven at graph-state level, not just the stream).
- [ ] The false "ToolNode overwrites it" docstring claim is removed (bridge + test docstring).
- [ ] Unit tests (bridge + gateway, both deny branches) and one deterministic
      `langchain_integration` graph test; existing tests updated for the new arity.
- [ ] Passes pylint / mypy(strict) / ruff / pytest; the gateway keeps its
      no-`langchain_core`-import property.

## Verification (all via MCP tools)

```
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/icoder/test_icoder_permission_wiring.py"], markers=["langchain_integration"])
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_ruff_check(extra_args=["--preview"])
mcp__mcp-tools-py__run_lint_imports_check          # gateway stays langchain_core-free
```

The marked run must **pass**, not skip — if it skips, the langchain extras are missing and
the graph test proved nothing.

## Out of scope

* #1045 (I3.2) replaces the `AFTER_APPROVAL` branch with a real approval prompt — this
  issue only fixes the message shape and gives #1045 a clean baseline.
* No change to `run_agent_stream`'s stream events (the `run_id` masking is cosmetic and
  unrelated to history validity).
* `spikes/i3-1-approval/FINDINGS.md` is left untouched.
