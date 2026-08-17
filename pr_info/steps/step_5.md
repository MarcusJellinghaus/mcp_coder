# Step 5 — Collapse `run_agent` into a thin drainer; `_ask_agent` stops storing

**Goal:** One agent execution path. `run_agent` drains `run_agent_stream` and returns what
the `done` event carries, so both agent entry points persist an identical multi-step
structure sourced from the graph's final messages — by construction, not by two
reconstructions that happen to agree.

## WHERE

* Modify `src/mcp_coder/llm/providers/langchain/agent.py` — `run_agent` (~lines 332–475)
* Modify `src/mcp_coder/llm/providers/langchain/__init__.py` — `_ask_agent` (~lines 373–440)
* Modify `tests/llm/providers/langchain/test_langchain_agent_run.py`
* Modify `tests/llm/providers/langchain/test_langchain_agent_usage.py`
* Modify `tests/llm/providers/langchain/test_langchain_agent_system_messages.py`
* Modify `tests/llm/providers/langchain/test_langchain_agent_mode.py`
* Modify `tests/llm/providers/langchain/test_langchain_integration.py` — non-empty
  `raw_response["usage"]` assertion in `TestAgentModeIntegration::test_agent_simple_prompt`
  (the real gate for the usage-source change)
* Modify `tests/icoder/test_icoder_permission_wiring.py` (docstrings only)

## WHAT

```python
async def run_agent(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    session_id: str,                      # NEW — storage now lives in the stream
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    system_messages: list[Any] | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]: ...
```

Return tuple is unchanged: `(final_text, stored_messages, stats)`.

## HOW

* `session_id` is inserted after `mcp_config_path` to mirror `run_agent_stream`'s
  signature. Every caller (production `_ask_agent` and all tests) already uses keyword
  arguments, so this is safe.
* **Delete** from `run_agent`: the deferred langchain/langgraph imports, the
  `MultiServerMCPClient` tool-loading loop, `create_react_agent`, the `ainvoke` call, the
  stats loop (moved to `_summarize_messages` in step 4) and the serialization loop. Keep
  `asyncio` (used by `wait_for`).
* `_load_mcp_server_config`, `_convert_server_tools`, `_format_launch_error`,
  `LLMMCPLaunchError` and `AGENT_MAX_STEPS` stay — `run_agent_stream` and `MCPManager`
  still use them.
* Docstring: state it is a thin drainer and that **storage happens inside
  `run_agent_stream`**, not here.
* `_ask_agent`: pass `session_id=session_id` to `run_agent` and **delete** the
  `store_langchain_history(session_id, messages)` call. `store_langchain_history` stays
  imported — the text paths still use it. `raw_response` construction is unchanged.
* `tests/icoder/test_icoder_permission_wiring.py`: update the module docstring and
  `test_icoder_path_is_stream_only_never_run_agent`'s docstring — "site 2" (the
  `convert_...` call inside `run_agent`) no longer exists, so the guard is now
  structurally trivial. Keep the test; it still pins stream-only behaviour.

## ALGORITHM

```
async def _drain():
    text, stored, stats = "", [], {}
    async for event in run_agent_stream(question=..., session_id=..., ...):
        if event.get("type") == "done":
            text   = str(event.get("result", ""))
            stored = event.get("messages", [])
            stats  = event.get("stats", {})
    return text, stored, stats

return await asyncio.wait_for(_drain(), timeout=float(timeout))
```

`final_text` comes straight off `done["result"]`, which step 4 guarantees is non-empty
whenever the model produced text — including the no-terminal-graph-event case, where it
falls back to the streamed `accumulated_text`. That is what keeps a failed root-`run_id`
capture a history-loss (logged) rather than a silent empty answer on this path.

`wait_for` still raises `asyncio.TimeoutError` on expiry. Its cancellation raises
`CancelledError`, a `BaseException`, so `run_agent_stream`'s `except Exception` does not
catch it — no spurious `error` event and nothing persisted, which is exactly the required
cancel behaviour.

**Intentional behaviour change — the timeout now also covers MCP tool discovery.** Today
`asyncio.wait_for` wraps only `agent.ainvoke` (`agent.py:407`); the MCP client/tool
loading loop above it runs untimed. The drainer wraps the whole `run_agent_stream`
generator, so tool discovery counts against `timeout` too. Accept this (a hung MCP server
should not hang the non-stream agent path forever) rather than splitting the `wait_for`
to exclude tool loading — splitting would require re-plumbing the generator and reinstates
the untimed hang. Note it in the `run_agent` docstring and the commit message.

## DATA

Unchanged for callers: `(final_text: str, stored_messages: list[dict[str, Any]],
stats: dict[str, Any])`, where `stats` carries `agent_steps`, `total_tool_calls`,
`tool_trace` and `usage` — the same keys `_ask_agent` spreads into `raw_response` today.

## Tests (update first)

`test_langchain_agent_run.py` — mechanical conversion using the step-4 conftest helper.
Each test swaps `mock_agent.ainvoke.return_value = {"messages": [...]}` for
`mock_agent.astream_events.return_value = async_events(graph_events([...]))`, adds
`session_id="s1"`, and patches
`mcp_coder.llm.storage.session_storage.store_langchain_history`. **Keep every existing
assertion** — they are the parity contract:

* `test_returns_final_text`, `test_returns_message_history`,
  `test_returns_stats_with_tool_counts`, `test_handles_agent_response_gracefully`,
  `test_prepends_session_history`, `test_tool_trace_in_stats`.
* `test_hard_fails_on_mcp_server_error` — tool loading fails before any event, so the
  `ConnectionError` still propagates; only the mock setup changes.
* `TestRunAgentLaunchErrorWrap::test_run_agent_wraps_launch_errors` (both parametrized
  cases) should pass with **no change at all** — the failure happens during tool loading
  and the drainer propagates `LLMMCPLaunchError` identically. Verify rather than edit.
* New `test_multi_step_structure_matches_stream` — for a
  think→tool→think→tool→answer final message list, assert `run_agent`'s returned history
  equals the payload `run_agent_stream` stored, with all five messages present (no
  flattening).

`test_langchain_agent_usage.py` — **must be rewritten in this step** (all three tests in
`TestRunAgentUsage`). They drive `run_agent` with `mock_agent.ainvoke.return_value =
{"messages": [...]}` and assert `stats["usage"]` summed from each `AIMessage`'s
`usage_metadata`. After the collapse `ainvoke` is never called, and usage no longer comes
from the final message list — it comes from `run_agent_stream`'s `on_chat_model_end`
accumulator. So each test must:

* swap the `ainvoke` mock for
  `mock_agent.astream_events.return_value = async_events(graph_events([...], inner=[...]))`
  and add `session_id="s1"`;
* supply the usage through the `inner` events — one
  `{"event": "on_chat_model_end", "data": {"output": ai_msg}}` per `AIMessage` that
  carries `usage_metadata` — so the accumulator sees it;
* keep the existing assertions verbatim (`input_tokens == 500` / `1300`,
  `output_tokens == 200` / `500`, `cache_read_input_tokens == 100` / `300`, and
  `stats["usage"] == {}` when no message has `usage_metadata`).

If the numbers do not match after the rewrite, stop and report rather than relaxing the
assertions.

**These rewritten tests are not a parity check — they only prove the arithmetic.** They
hand-write the `on_chat_model_end` events *and* the `usage_metadata` on them, so they pass
by construction and cannot detect the actual risk: under `astream_events` the model is
streamed, and the aggregated chunk carries `usage_metadata` **only when the backend streams
usage** (`stream_usage=True` / `stream_options={"include_usage": True}` for
OpenAI-compatible backends). A backend or proxy that omits it makes `stats["usage"]` — and
`_ask_agent`'s `raw_response["usage"]` — silently `{}` where `ainvoke` returned real
numbers today, with a fully green suite.

**Real gate (required, part of this step):** add to
`tests/llm/providers/langchain/test_langchain_integration.py::TestAgentModeIntegration::test_agent_simple_prompt`
(which today asserts only text and `session_id`) an assertion that
`result["raw_response"]["usage"]` is a non-empty dict with a positive `input_tokens`, and
run it against the real endpoint (see Checks). This is the only check that can tell
"accumulator works" from "backend streams usage". If it fails, the configured backend does
not stream usage: report it and record the `{}` fallback as the observed behaviour rather
than deleting the assertion. If it **skips** (no endpoint configured), the usage-source
change is unverified — say so explicitly, exactly as for the root-`run_id` gate.

`test_langchain_agent_system_messages.py`:

* `test_prepends_system_messages` / `test_no_system_messages_when_none` — assert on
  `mock_agent.astream_events.call_args` instead of `ainvoke.call_args`.
* `test_timeout_raises_on_slow_agent` — the slow mock becomes an `astream_events`
  async iterator that sleeps; still expects `asyncio.TimeoutError`.

`test_langchain_agent_mode.py`:

* `test_agent_mode_stores_full_history` → rename to
  `test_agent_mode_does_not_store_history`: patch
  `mcp_coder.llm.providers.langchain.store_langchain_history` and assert it is **not**
  called for the agent path (single storage site, no double-store). The stored-content
  assertions already live in the step-4 stream tests.
* The other tests in that file mock `run_agent` wholesale and stay unchanged.

`test_langchain_coverage_gaps.py` mocks `run_agent` wholesale — expected to need no edit.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Plus the step-4 validation gate, which this step finally routes through the new code on
the non-stream path:

```
mcp__tools-py__run_pytest_check(markers=["langchain_integration"], extra_args=["-n", "auto", "tests/llm/providers/langchain/test_langchain_integration.py"])
```

`TestAgentModeIntegration::test_agent_session_continuity` now runs a real second turn
through the drained `run_agent`, so it is the end-to-end proof of the root-`run_id`
terminal-event capture; `::test_agent_simple_prompt` carries the new non-empty
`raw_response["usage"]` assertion and is the proof for the usage-source change. A skip (no
endpoint configured) is not a pass for either — report both explicitly.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Implement step 5 only: turn run_agent in
src/mcp_coder/llm/providers/langchain/agent.py into a thin drainer of run_agent_stream
(new session_id parameter, asyncio.wait_for preserved, reads text/messages/stats off the
done event, stores nothing), delete its tool loading / ainvoke / stats / serialization
code, and drop the store_langchain_history call from _ask_agent in __init__.py.

Update the tests listed in the step file first, using the graph_events() and
async_events() helpers added to the langchain tests conftest in step 4. Keep the existing
assertions in test_langchain_agent_run.py and test_langchain_agent_usage.py — they are
the parity contract; only the mock setup should change. test_langchain_agent_usage.py
must feed its usage through on_chat_model_end events (see the step file), because
run_agent no longer derives usage from the final message list. Also add the multi-step
structural parity test.

Those usage tests inject usage_metadata by hand and therefore pass by construction, so
they cannot prove the backend actually streams usage. Add the required real gate: an
assertion that raw_response["usage"] is a non-empty dict with a positive input_tokens in
tests/llm/providers/langchain/test_langchain_integration.py::TestAgentModeIntegration::test_agent_simple_prompt,
and run the langchain_integration tests. Report a skip as unverified; report a failure as
"backend does not stream usage" rather than deleting the assertion.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```
