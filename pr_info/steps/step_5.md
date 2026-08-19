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
* Modify `tests/icoder/test_icoder_permission_wiring.py` (wording only — two docstrings
  plus the `AssertionError` message at line 298)

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
  `MultiServerMCPClient` tool-loading loop, `create_react_agent`, the `ainvoke` call, its
  `_summarize_messages(...)` call (step 4 already replaced the inline stats loop with it;
  the helper itself stays — `run_agent_stream` is now its only caller) and the
  serialization loop. Keep `asyncio` (used by `wait_for`).
* `_load_mcp_server_config`, `_convert_server_tools`, `_format_launch_error`,
  `LLMMCPLaunchError` and `AGENT_MAX_STEPS` stay — `run_agent_stream` and `MCPManager`
  still use them. Two comments in `agent.py` name `run_agent` as a tool-loading caller and
  become false once its loading loop is deleted — **update both**: the
  `_convert_server_tools` docstring at `agent.py:293` (drop `run_agent` from
  "shared by ``run_agent``, ``run_agent_stream`` (else-branch), and
  ``MCPManager._connect_and_discover``") and the inline comment at `agent.py:532`
  ("Load tools with schema sanitization (inline, same as run_agent)"). Same wording-sweep
  category as the `test_icoder_permission_wiring.py` edit below.
* Docstring: state it is a thin drainer and that **storage happens inside
  `run_agent_stream`**, not here.
* `_ask_agent`: pass `session_id=session_id` to `run_agent` and **delete** the
  `store_langchain_history(session_id, messages)` call. `store_langchain_history` stays
  imported — the text paths still use it. `raw_response` construction is unchanged.
* `tests/icoder/test_icoder_permission_wiring.py`: **wording only, no behaviour change** —
  "site 2" (the `convert_...` call inside `run_agent`) no longer exists, so the guard is
  now structurally trivial. Update all three places the phrase appears: the module
  docstring, `test_icoder_path_is_stream_only_never_run_agent`'s docstring, **and the
  `AssertionError` message at line 298** (`"run_agent (site 2) must be unreachable from
  iCoder"`) — that one is a string in the test body, not a docstring. Keep the test; it
  still pins stream-only behaviour.

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

**Mock-class rule for this step — the mocked react agent must be a `MagicMock()`, never an
`AsyncMock()`.** `run_agent_stream` consumes the graph with
`async for event in agent.astream_events(...)`. An `AsyncMock` child call returns a
*coroutine*, which `async for` rejects outright
(`TypeError: 'async for' requires an object with __aiter__ method, got coroutine`), so the
`ainvoke` → `astream_events` swap is **not** complete without also changing the class.
Eleven tests currently build `mock_agent = AsyncMock()`: six in
`test_langchain_agent_run.py` (lines 106, 134, 173, 232, 262, 320), all three in
`test_langchain_agent_usage.py` (119, 151, 200) and two in
`test_langchain_agent_system_messages.py` (80, 122). Change every one to `MagicMock()`.
The step-4 helper `_patch_run_agent_stream`
(`test_langchain_agent_streaming.py:41`) already does exactly this and is the reference
shape; `test_timeout_raises_on_slow_agent` (`:153`) is already `MagicMock()` and needs no
class change. Tests that never build a react-agent mock — `test_hard_fails_on_mcp_server_error`
and `TestRunAgentLaunchErrorWrap` — are unaffected.

**Surviving `ainvoke` assertions — the full list, already swept.** Only three places
*assert* on `mock_agent.ainvoke` (as opposed to setting `.return_value`), and all three are
named explicitly below: `test_langchain_agent_run.py:293`,
`test_langchain_agent_system_messages.py:103` and `:138`, plus the
`mock_agent.ainvoke = _slow_invoke` substitution at `:154`. `test_langchain_agent_usage.py`
has none — its three `ainvoke` references are `.return_value` setup only. Nothing else in
the tree needs hunting.

`test_langchain_agent_run.py` — mechanical conversion using the step-4 conftest helper.
`session_id="s1"` is added at **every** `run_agent(...)` call site; the tests that reach a
terminal graph event also swap `mock_agent = AsyncMock()` for `MagicMock()` and
`mock_agent.ainvoke.return_value = {"messages": [...]}` for
`mock_agent.astream_events.return_value = async_events(graph_events([...]))`, and patch
`mcp_coder.llm.storage.session_storage.store_langchain_history`. **Keep every existing
assertion** — they are the parity contract — with the one explicit exception called out
below, which asserts on a mock that no longer exists:

* `test_returns_final_text`, `test_returns_message_history`,
  `test_returns_stats_with_tool_counts`, `test_handles_agent_response_gracefully`,
  `test_tool_trace_in_stats` — the full treatment: `session_id=`, mock swap, store patch.
  Their assertions are untouched.
* `test_prepends_session_history` — the full treatment **plus one assertion change**: line
  293 reads `call_args = mock_agent.ainvoke.call_args`, and after the collapse `ainvoke` is
  never called, so `call_args` is `None` and the test fails with `TypeError` rather than a
  parity failure. Retarget it to `mock_agent.astream_events.call_args`; the indexing is
  unchanged (`call_args[0][0]["messages"]`), because `run_agent_stream` calls
  `agent.astream_events({"messages": input_messages}, version="v2", config=...)`. The
  `mock_messages_from_dict.assert_called_once_with([...])` assertion above it stays as-is:
  `assemble_messages` passes a filtered **copy** of the history, which compares equal.
* `test_hard_fails_on_mcp_server_error` — tool loading fails before any event, so the
  `ConnectionError` still propagates; add `session_id=` and adjust the mock setup, but
  **no store patch** (storage is never reached).
* `TestRunAgentLaunchErrorWrap::test_run_agent_wraps_launch_errors` (both parametrized
  cases) needs **exactly one change: add `session_id="s1"`.** The call at
  `test_langchain_agent_run.py:404` passes no `session_id`, which is now a required
  parameter, so without it the test raises `TypeError` instead of `LLMMCPLaunchError` and
  fails. It needs **no** `store_langchain_history` patch — tool loading raises before any
  event is produced, so storage is never reached. Beyond that keyword the behaviour is
  unchanged: the drainer propagates `LLMMCPLaunchError` identically, so no mock swap and
  no assertion change.
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

* swap `mock_agent = AsyncMock()` for `MagicMock()` (mock-class rule above) and the
  `ainvoke` mock for
  `mock_agent.astream_events.return_value = async_events(graph_events([...], inner=[...]))`,
  add `session_id="s1"` **and patch
  `mcp_coder.llm.storage.session_storage.store_langchain_history`** — storage now happens
  inside `run_agent_stream`, so an unpatched test writes real files into the user's
  `~/.mcp_coder/sessions/langchain/`;
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

`test_langchain_agent_system_messages.py` — all three tests in
`TestRunAgentSystemMessages` call `run_agent(...)` and so need the **same two mechanical
changes as `test_langchain_agent_run.py`**: add `session_id="s1"` (it becomes a required
parameter — omitting it is a `TypeError`) and patch
`mcp_coder.llm.storage.session_storage.store_langchain_history` (otherwise the first two
tests, which now reach a terminal graph event, write real session JSON into the user's
`~/.mcp_coder/sessions/langchain/`). On top of that:

* `test_prepends_system_messages` / `test_no_system_messages_when_none` — swap
  `mock_agent = AsyncMock()` for `MagicMock()` (mock-class rule above) and
  `mock_agent.ainvoke.return_value` for
  `mock_agent.astream_events.return_value = async_events(graph_events([...]))`, and assert
  on `mock_agent.astream_events.call_args` instead of `ainvoke.call_args` (lines 103, 138).
  Note the merge from step 2 does not apply here: these two tests hand-build their own
  `SystemMessage` list, so `test_prepends_system_messages` still expects **2** systems +
  1 human in the input.
* `test_timeout_raises_on_slow_agent` — already a `MagicMock()`, so no class change; the
  slow mock becomes `mock_agent.astream_events = <async generator that sleeps>` instead of
  `mock_agent.ainvoke = _slow_invoke` (line 154); still expects `asyncio.TimeoutError`.

**Storage-patch rule for this step:** every test that reaches `run_agent` or
`run_agent_stream` with real (unmocked) internals must patch
`mcp_coder.llm.storage.session_storage.store_langchain_history` — `run_agent_stream`
imports it lazily from that module at `agent.py:692-694`, and there is no autouse fixture
isolating the user app-data directory in `tests/conftest.py`. Tests that mock `run_agent` /
`run_agent_stream` wholesale (`test_langchain_agent_mode.py`,
`test_langchain_coverage_gaps.py`, `test_langchain_ollama_agent.py`) are unaffected. So
are the tests that raise during **tool loading**, before any event exists
(`test_hard_fails_on_mcp_server_error`, `TestRunAgentLaunchErrorWrap`) — they never reach
the storage call, so they need `session_id=` but no store patch.

**`session_id=` is the broader rule:** it is a required parameter now, so *every*
`run_agent(...)` call site needs it, including the ones exempt from the store patch above.

`test_langchain_agent_mode.py`:

* `test_agent_mode_stores_full_history` → rename to
  `test_agent_mode_does_not_store_history`: patch
  `mcp_coder.llm.providers.langchain.store_langchain_history` and assert it is **not**
  called for the agent path (single storage site, no double-store). The stored-content
  assertions already live in the step-4 stream tests.
* The other tests in that file mock `run_agent` wholesale and stay unchanged.

`test_langchain_coverage_gaps.py` mocks `run_agent` wholesale — expected to need no edit.

**File sizes.** The biggest grower here is `test_langchain_agent_run.py`: 493 lines today,
plus `session_id=` and a store patch at each call site and the new multi-step parity test
≈ 590 — comfortably inside the 750-line CI gate, so no split is needed. Every other file
this step touches is under 300 lines. Run `mcp__mcp-workspace__check_file_size` before
committing anyway; if the parity test pushes the file past 750, split it rather than
allowlisting.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
mcp__mcp-workspace__check_file_size          # 750-line CI gate — see "File sizes" above
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
the parity contract; only the mock setup should change, with ONE named exception (below).
test_langchain_agent_usage.py must feed its usage through on_chat_model_end events (see
the step file), because run_agent no longer derives usage from the final message list.
Also add the multi-step structural parity test.

MOCK CLASS: every converted test must build the react-agent mock as MagicMock(), NOT
AsyncMock(). run_agent_stream does `async for event in agent.astream_events(...)`, and an
AsyncMock child call returns a coroutine, which async for rejects
("TypeError: 'async for' requires an object with __aiter__ method, got coroutine").
Eleven call sites currently use AsyncMock(): test_langchain_agent_run.py lines
106/134/173/232/262/320, test_langchain_agent_usage.py 119/151/200,
test_langchain_agent_system_messages.py 80/122. Copy the shape from
_patch_run_agent_stream in test_langchain_agent_streaming.py, which already uses
MagicMock().

THE ONE ASSERTION EXCEPTION: test_prepends_session_history in test_langchain_agent_run.py
asserts on mock_agent.ainvoke.call_args at line 293. ainvoke is never called after the
collapse, so that is None and the test raises TypeError. Retarget it to
mock_agent.astream_events.call_args (same [0][0]["messages"] indexing). The step file
lists every surviving ainvoke assertion in the tree — that one plus
test_langchain_agent_system_messages.py:103/138/154 — so do not go hunting for more.

Also update the two stale comments in agent.py that name run_agent as a tool-loading
caller: the _convert_server_tools docstring at agent.py:293 and the inline comment at
agent.py:532.

EVERY run_agent(...) call site in the tests needs session_id="s1" — it is now a required
parameter, so omitting it is a TypeError. That includes
TestRunAgentLaunchErrorWrap::test_run_agent_wraps_launch_errors, which the step file
previously (and wrongly) said needed no change at all.

Call sites that actually reach the storage call ALSO need a patch of
mcp_coder.llm.storage.session_storage.store_langchain_history — storage now lives inside
run_agent_stream and there is no autouse fixture isolating the user app-data directory, so
an unpatched test writes real JSON into ~/.mcp_coder/sessions/langchain/. That applies
across the three files that call run_agent directly — test_langchain_agent_run.py,
test_langchain_agent_usage.py and test_langchain_agent_system_messages.py. Two exceptions
need session_id but NOT the store patch, because they raise during tool loading before any
event exists: test_hard_fails_on_mcp_server_error and TestRunAgentLaunchErrorWrap. Tests
that mock run_agent / run_agent_stream wholesale need neither.

Those usage tests inject usage_metadata by hand and therefore pass by construction, so
they cannot prove the backend actually streams usage. Add the required real gate: an
assertion that raw_response["usage"] is a non-empty dict with a positive input_tokens in
tests/llm/providers/langchain/test_langchain_integration.py::TestAgentModeIntegration::test_agent_simple_prompt,
and run the langchain_integration tests. Report a skip as unverified; report a failure as
"backend does not stream usage" rather than deleting the assertion.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```

---

## Outcome (implementation notes)

### ⚠️ Validation gate SKIPPED — usage source still unverified

`mcp__tools-py__run_pytest_check(markers=["langchain_integration"], ...)` on
`test_langchain_integration.py` collected **7 tests and skipped all 7** —
`_require_langchain_config()` found no configured backend/credentials in this
environment. Therefore:

* The new non-empty `raw_response["usage"]` assertion in
  `TestAgentModeIntegration::test_agent_simple_prompt` **never ran**. Whether the
  configured backend actually streams usage (`stream_usage=True` /
  `stream_options={"include_usage": True}`) is **unknown**. The three rewritten
  unit tests in `test_langchain_agent_usage.py` inject `usage_metadata` by hand
  and pass by construction, so they cannot substitute for this.
* `TestAgentModeIntegration::test_agent_session_continuity` — which would have
  been the end-to-end proof of step 4's root-`run_id` terminal-event capture now
  that it routes through the drained `run_agent` — also never ran. Step 4's
  assumption remains unvalidated.

**A skip is not a pass.** Both must be cleared by step 6's manual run against the
LiteLLM/Qwen endpoint before either is treated as validated.

### Implementation

* `run_agent` is now a `_drain()` coroutine inside the existing
  `asyncio.wait_for`; its imports, tool-loading loop, `create_react_agent`,
  `ainvoke`, `_summarize_messages` call and serialization loop are deleted.
  `agent.py` went from 727 to **706 lines** (~90 lines of logic removed, partly
  offset by the larger drainer docstring).
* `_ask_agent` passes `session_id=` and no longer stores.
* Both stale comments refreshed. The `get_tools()` rationale that lived only in
  `run_agent`'s deleted loader was moved onto `run_agent_stream`'s inline loader
  comment rather than dropped.

### Tests

* One deviation from the plan, for a pylint reason:
  `test_timeout_raises_on_slow_agent` uses a module-level `_SlowAsyncIter` class
  assigned to `mock_agent.astream_events.return_value`, **not** an async-generator
  function assigned to `mock_agent.astream_events` itself. Assigning a plain
  function to that attribute made astroid infer `.astream_events` as that
  function project-wide, producing four new
  `E1101: Function '_slow_events' has no 'call_args' member` errors — including
  in `test_langchain_multi_turn.py`, which this step does not touch. Keeping the
  attribute a `MagicMock` avoids that entirely; behaviour (a run that outlives
  the 1s timeout) is identical.
* `test_langchain_agent_run.py` is **554 lines** after the conversion (under the
  750-line gate; the plan estimated ~590, so no split was needed).

### Checks

* **`check_file_size`**: passed — all 813 files within 750 lines.
* **pylint** (`src` + `tests`): no issues attributable to this change. What
  remains is the pre-existing stale-`mcp-workspace` skew (`E0401`/`E0611` on
  `mcp_workspace.checks.branch_status_rendering`, `E1101`/`E1123` on
  `pr_feedback_undeterminable` / `fail_on_reviews` / `add_assignees`) and the
  `langchain_core` / `httpx` / `mcp.server.fastmcp` optional-import errors that
  predate the step.
* **mypy** (`src` + `tests`): 8 errors, **all pre-existing** — the same
  mcp-workspace skew plus `tests/llm/providers/claude/_mcp_stub_server.py`'s
  untyped decorator. None in any file this step touched.
* **pytest**: the step-1..4 environment breakage is still present (the venv's
  `mcp-workspace` has no `mcp_workspace.checks.branch_status_rendering`, which
  `src/mcp_coder/checks/branch_status.py:17` imports at `import mcp_coder` time,
  so every test module fails at collection). The same throwaway root
  `conftest.py` shim was used and **deleted afterwards — it is not part of this
  commit**. Results with the shim:
  * `tests/llm/providers/langchain/` + `tests/icoder/test_icoder_permission_wiring.py`:
    green except the pre-existing `httpx`-absent
    `test_connection_errors_contains_httpx_connect_error`.
  * `tests/llm` + `tests/icoder`: additionally the pre-existing copilot CLI
    subprocess integration failures and `tests/icoder/test_snapshots.py`
    (`snap_compare` fixture not installed).
  * `tests/cli` + `tests/workflows` + `tests/utils`: only the pre-existing
    `AttributeError: NOT_CONFIGURED` / `UNAVAILABLE` branch-status failures from
    the same mcp-workspace skew (the shim unmasks them; without it they fail at
    collection). Unrelated to this change.
  * A single full-suite run without path arguments exceeds the tool's 300s
    timeout, so it was run in three directory batches instead.
