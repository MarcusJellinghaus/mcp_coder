# Step 4 — Agent stream sources persisted history from the graph's final messages

**Goal:** Fix Issue 2. `run_agent_stream` stops persisting a hand-reconstructed,
flattened history that includes the system messages, and instead persists the graph's
own final message list, serialized (and therefore system-stripped) by the shared helper.
This is the single storage site for the agent path.

`run_agent` keeps its own execution path in this step — step 5 collapses it. The stats
loop is **extracted once** into `_summarize_messages` and **called from both**
`run_agent` and `run_agent_stream`, so step 4 leaves both paths working with no
duplicated code. Step 5 then deletes `run_agent`'s call along with the rest of its body.

## WHERE

* Modify `src/mcp_coder/llm/providers/langchain/agent.py` — `run_agent_stream`
  (~lines 478–698), plus a new module-level `_summarize_messages()`; `run_agent`
  (~lines 417–462) loses its inline final-text/stats loop and **calls the new helper**
  instead (its `ainvoke`, tool loading and serialization stay until step 5)
* Modify `src/mcp_coder/llm/providers/langchain/__init__.py` — `_ask_agent_stream`
  (~lines 438–540): strip `messages` **and** `stats` from the `done` event before
  queueing it (see "`done` payload contract"). `src/mcp_coder/llm/types.py` and
  `src/mcp_coder/icoder/core/app_core.py` are **not** touched.
* Modify `tests/llm/test_types.py` — assembler test for the new `done["result"]` key
* Modify `tests/llm/providers/langchain/conftest.py` — add two shared test helpers
* **Create** `tests/llm/providers/langchain/test_langchain_agent_stream_history.py` — all
  seven new stream/storage tests live here, **not** in
  `test_langchain_agent_streaming.py`, which is already 656 lines against the CI-enforced
  750-line limit (see "Tests")
* Modify `tests/llm/providers/langchain/test_langchain_agent_streaming.py` — one existing
  test edited; no new tests added
* Modify `tests/llm/providers/langchain/test_langchain_multi_turn.py` (created in step 3)
* Modify `tests/llm/providers/langchain/test_langchain_integration.py` — one
  `langchain_integration` two-turn stream test (see "Required validation gate")

## WHAT

```python
def _summarize_messages(messages: list[Any]) -> tuple[str, dict[str, Any]]:
    """Derive final text and stats (incl. usage) from a graph's final message list."""
```

The returned `stats` dict carries `agent_steps`, `total_tool_calls`, `tool_trace` **and**
`usage` — exactly the four keys `run_agent` builds today. `run_agent` uses the returned
`usage` as-is; `run_agent_stream` overrides it with its own `on_chat_model_end`
accumulator (`{**stats, "usage": accumulated_usage}`), which is also reported on a
cancelled turn. One helper, two usage sources, no duplicated loop.

`run_agent_stream`'s and `run_agent`'s signatures are unchanged.

New test helpers in `tests/llm/providers/langchain/conftest.py` (plain module-level
functions, imported as `from tests.llm.providers.langchain.conftest import ...` — the
same pattern as `tests/icoder/conftest.py`):

```python
def graph_events(
    final_messages: list[Any], inner: Sequence[dict[str, object]] = ()
) -> list[dict[str, object]]: ...

async def async_events(items: list[dict[str, object]]) -> AsyncIterator[dict[str, object]]: ...
```

**Mock-class rule wherever these helpers are used.** The mocked react agent whose
`astream_events` returns `async_events(...)` must be a `MagicMock()`, **never** an
`AsyncMock()`: `run_agent_stream` does `async for event in agent.astream_events(...)`, and
an `AsyncMock` child call returns a *coroutine*, which `async for` rejects with
`TypeError: 'async for' requires an object with __aiter__ method, got coroutine`.
`_patch_run_agent_stream` (`test_langchain_agent_streaming.py:41`) already builds
`MagicMock()` and is the reference shape — tests 1 and 3–8 below get this for free by using
it, and test 9 is exempt because it patches `run_agent_stream` wholesale rather than
stubbing a react agent. Any test that hand-rolls its own patch set (test 11, and the
step-6 agent tests) must follow the rule explicitly. Step 5 restates it for the
`ainvoke` → `astream_events` conversions.

## HOW

* `agent.py` module-level import: `from ._messages import assemble_messages, serialize_messages`.
* `run_agent_stream` builds its input with
  `assemble_messages(system_messages, messages, question)`.
* Its deferred import block reduces to `from langgraph.prebuilt import create_react_agent`
  — `HumanMessage` / `messages_from_dict` are no longer needed there, and `AIMessage` /
  `ToolMessage` move into `_summarize_messages`'s own deferred import (it needs both:
  `AIMessage` for the final text and tool-call counting, `ToolMessage` for the
  `trace_by_id` result fill).
* **Delete** the accumulators `tool_calls_by_run_id` and `tool_results_list`, the whole
  reconstruction block after the event loop, and the flatten NOTE at lines 659–661. Keep
  `accumulated_usage` and every `yield` in the event loop — user-facing streaming is
  unchanged.
* **Keep `accumulated_text`.** It no longer feeds history reconstruction, but it is the
  `result` fallback when no terminal graph event was captured. Without it the
  no-terminal-event branch would emit `result: ""`, and step 5's drainer reads
  `final_text` straight off that key — so a failed root-`run_id` capture would silently
  turn the non-stream agent path (`_ask_agent` → `run_agent`) into an **empty-text
  response** instead of merely skipping storage. Document in the code why the
  accumulator survives.
* `_summarize_messages` is the **moved** (not copied) body of `run_agent`'s final-text +
  stats loop (`agent_steps`, `total_tool_calls`, `tool_trace`, `trace_by_id` fill from
  `ToolMessage`s, plus the `_extract_usage` / `_sum_usage` accumulation) — `agent.py:417-462`
  becomes `final_text, stats = _summarize_messages(output_messages)`.
  **Extract once, call from both.** `run_agent` calls the helper in this step (so it and
  its tests stay green), and `run_agent_stream` calls it on the graph's final messages,
  overriding only `usage`. This keeps every step green *without* duplicating ~45 lines
  for a commit, and it keeps the intermediate file size down: `agent.py` is 698 lines
  against the enforced 750-line limit, so a temporary copy would land it near ~737 with
  almost no headroom; extracting instead leaves it near ~700 after step 4, before step 5
  removes ~100 more.
* After the extraction `run_agent`'s deferred import block no longer uses `AIMessage` or
  `ToolMessage` (only `HumanMessage` / `messages_from_dict` for its input assembly, which
  step 5 removes) — drop them. Hygiene, not a gate: **nothing will flag them if you
  don't.** `pyproject.toml` disables `W0611 unused-import` in
  `[tool.pylint.messages_control]`, and ruff selects only `["D", "DOC"]`, so neither check
  catches a leftover import. Delete them anyway rather than relying on a tool to notice.
* `graph_events()` emits a root `on_chain_start` / `on_chain_end` pair with the same
  `run_id` (`"root"`) and `data.output == {"messages": final_messages}`; move the local
  `_async_events` out of `test_langchain_agent_streaming.py` into conftest as
  `async_events` and import it there.

## ALGORITHM

Two new branches in the existing `event_kind` chain:

```
elif event_kind == "on_chain_start":
    if root_run_id is None:                       # first on_chain_start == outermost run
        root_run_id = event.get("run_id")
elif event_kind == "on_chain_end" and event.get("run_id") == root_run_id:
    output = event.get("data", {}).get("output")
    if isinstance(output, dict) and "messages" in output:   # defensive fallback guard
        final_messages = list(output["messages"])
    else:
        logger.warning("Terminal graph event carried no 'messages'; history not stored")
```

Finalization after the loop:

```
if final_messages is None:            # cancelled, or no terminal event -> persist nothing
    yield {"type": "done", "session_id": session_id, "usage": accumulated_usage,
           "messages": [], "result": accumulated_text,
           "stats": {"agent_steps": 0, "total_tool_calls": 0, "tool_trace": [],
                     "usage": accumulated_usage}}
    return
stored = serialize_messages(final_messages)          # strips the leading SystemMessage
_store_history(session_id, stored)                   # the single storage site
final_text, stats = _summarize_messages(final_messages)
yield {"type": "done", "session_id": session_id, "usage": accumulated_usage,
       "messages": stored, "result": final_text, "stats": {**stats, "usage": accumulated_usage}}
```

Both branches carry `session_id` **and** `usage` at the top level — the no-terminal-event
branch is not a stripped-down event. The three `TestRunAgentStreamUsage` tests emit no
terminal graph event, so they take exactly this branch, and they must keep asserting
`done["usage"]` unchanged (see Tests, item 2).

`result` falls back to `accumulated_text` in that branch — **not** `""`. Only `messages`
and `stats` are empty, because there is nothing safe to persist or summarize; the answer
text, however, was already streamed and must survive. Step 5's drainer takes
`final_text = done["result"]`, so `""` here would make `mcp-coder prompt` in agent mode
return an empty answer whenever the root-`run_id` capture fails — a silent, user-visible
regression on top of the (logged) history loss. Degrading to "history not stored, text
still correct" keeps the failure mode bounded.

Matching by root `run_id` (not by event name) is deliberate: `astream_events` emits one
`on_chain_end` per node/sub-chain, and event names are version-specific LangGraph
internals.

## DATA

* `done` event gains three keys: `messages: list[dict[str,Any]]` (serialized, system-free),
  `result: str`, `stats: {"agent_steps": int, "total_tool_calls": int, "tool_trace":
  list[dict], "usage": UsageInfo}`. `session_id` and `usage` keep their current meaning.
  `stats` is nested so it cannot collide with the top-level keys, and it carries `usage`
  so step 5's drainer can hand `_ask_agent` the exact dict it builds `raw_response` from
  today.
* Cancelled / no-terminal-event turn: `messages: []`, `result: accumulated_text`, zeroed
  stats, and **no** storage call — `session_id` and `usage` are present and unchanged.
* All three keys are on the event `run_agent_stream` **yields** — step 5's drainer needs
  all three. Only `messages` and `stats` are removed again at the `_ask_agent_stream`
  boundary; `result` crosses it deliberately (see below).

## `done` payload contract (consumers)

Of the three new `done` keys, only `result` reaches consumers outside this package, and
that is a deliberate semantic change, not a no-op. All three effects are decided here:

* **`result` — intended semantics, kept.** `ResponseAssembler.add` already reads
  `done["result"]` and `result()` uses it as the response text **only when no `text_delta`
  event was seen** (`types.py:141-143`, `:186-187`). Runs that stream tokens are therefore
  unaffected (deltas win). Runs that produce no `text_delta` — a backend or proxy that
  does not emit `on_chat_model_stream` — today yield empty text and will now yield the
  agent's final answer. That is the intended semantics: `done["result"]` is the
  authoritative final text, `text_delta` accumulation is the preferred rendering. Covered
  by Tests item 10.
* **`messages` and `stats` — both stripped in `_ask_agent_stream`, the provider
  boundary.** `done["messages"]` is the *whole* serialized conversation; `done["stats"]`
  carries `tool_trace`, i.e. the full name/args/result of every tool call in the turn.
  Both exist solely for step 5's in-process drainer, which consumes `run_agent_stream`
  **directly** — nothing above the provider boundary reads either key, and `tool_trace`
  duplicates content already emitted as `tool_use_start` / `tool_result` events. Every
  other consumer reaches the event through `_ask_agent_stream`, and **two** of them
  persist it per turn:
  * `ResponseAssembler.add` appends every non-`raw_line` event to `_raw_events`, which
    `result()` returns as `raw_response["events"]`; icoder persists that via
    `store_session`.
  * `AppCore.stream_llm` writes every non-`raw_line` event to the icoder event log —
    `self._event_log.emit("stream_event", **event)` (`app_core.py:201`) — keeping it in
    memory (`EventLog._entries`) and as a JSONL line on disk; `ui/replay.py:73-81` reads
    those entries back and re-emits them.

  Left on the event, `messages` makes both sinks grow **quadratically** with turn count
  (turn *n* re-persists all *n* turns); `stats` adds a constant-factor duplication of the
  turn's tool payloads on top.

  **Chosen behaviour — one strip site for both keys.** `_ask_agent_stream` puts a shallow
  copy of the `done` event **without** the `messages` and `stats` keys on its queue; every
  other event is queued unchanged. `run_agent_stream` still yields both keys, so the
  step-5 drainer (which bypasses the bridge) gets them. Stripping both in the same shallow
  copy is what preserves the "no per-consumer filtering" property this issue exists to
  establish. Consequence: **`types.py` and `app_core.py` need no filter** —
  filtering them individually would be two filters in two modules that must stay in sync
  as sinks are added, which is exactly the per-consumer drift this issue removes. The
  ndjson formatter filters `done` to `session_id`/`usage`/`cost_usd`, so CLI output is
  unaffected either way. Covered by Tests item 9.

## Tests (write first)

**File-size constraint — the new tests go in a new file.**
`test_langchain_agent_streaming.py` is **656 lines** against the CI-enforced 750-line gate
(`.github/workflows/ci.yml` runs
`mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist`, and
that file is **not** allowlisted). At the file's current density (~44 lines per test) the
seven new tests below would land it near 950 lines and fail the `file-size` CI job. So
only the edit to the existing test stays there; every new test goes into a new sibling
file, leaving the original at ~654 lines (the `_async_events` helper moves out to
conftest, which is a small net reduction).

In `test_langchain_agent_streaming.py` (edit + verify only, no new tests):

1. `test_history_stored_before_done` — wrap the events with `graph_events([...])`; assert
   the stored payload equals the serialized final messages.
2. `test_done_event_emitted_last`, the three `TestRunAgentStreamUsage` tests and the
   tool-output tests keep passing **unchanged** (they emit no terminal event, so they
   simply store nothing — none of them asserts storage).

In the **new** `tests/llm/providers/langchain/test_langchain_agent_stream_history.py`
(~320 lines expected). It imports `_patch_run_agent_stream` from
`tests.llm.providers.langchain.test_langchain_agent_streaming` — the same cross-file
pattern `test_langchain_agent_streaming_tool_output.py:5` already uses — and
`graph_events` / `async_events` from `tests.llm.providers.langchain.conftest`:

3. New `test_stored_history_has_no_system_messages` — final messages
   `[SystemMessage, HumanMessage, AIMessage]` → stored has 2 entries, no `"system"` type.
4. New `test_done_event_carries_messages_result_and_stats`.
5. New `test_cancel_persists_nothing` — cancel mid-stream (no terminal event) → store
   **not** called; a `done` event is still emitted.
6. New `test_error_persists_nothing` — `astream_events` raises → store not called; the
   existing `error`-event + re-raise behaviour is unchanged.
7. New `test_no_terminal_event_done_carries_streamed_text` — feed `on_chat_model_stream`
   deltas but **no** terminal graph event; assert `done["result"]` equals the accumulated
   text (not `""`), `done["messages"] == []` and store was not called. This is the guard
   against step 5's drainer returning an empty answer when the root-`run_id` capture
   fails.
8. New `test_cancel_done_carries_partial_text` — same shape as item 5, plus
   `done["result"]` holds the text streamed before the cancel.
9. New `test_ask_agent_stream_strips_messages_and_stats_from_done` — drive
   `_ask_agent_stream` with a patched `run_agent_stream` whose `done` carries `messages`
   and `stats`; assert the yielded `done` has **neither** key while `session_id` /
   `usage` / `result` survive, and that non-`done` events pass through unchanged. This is
   what keeps the whole conversation and the tool trace out of both
   `raw_response["events"]` and the icoder event log. It drives `_ask_agent_stream` rather
   than `run_agent_stream`, but the strip is a langchain-boundary behaviour and belongs
   with the storage/`done`-payload tests it protects.

In `tests/llm/test_types.py` (491 lines; one ~20-line test keeps it well clear of 750):

10. New `test_done_result_used_when_no_text_delta` — feed `ResponseAssembler` a `done`
    event with `result` and no `text_delta`; assert the assembled `text` is the `result`
    value. With a `text_delta` present, the deltas still win (existing tests cover that
    direction — keep them unchanged).

In `test_langchain_multi_turn.py`:

11. `TestAgentPathMultiTurn::test_two_turns_store_no_systems_and_send_one_system` — call
   `run_agent_stream` twice, feeding turn 2 the `messages` captured from turn 1's store
   call; assert turn 2's `astream_events` input has exactly one `SystemMessage` at index 0
   and the stored history has zero system entries across both turns. Patch
   `mcp_coder.llm.storage.session_storage.store_langchain_history` with a mock (as
   `_patch_run_agent_stream` does) — `run_agent_stream` imports it lazily from that module
   and would otherwise write into the user's real `~/.mcp_coder/sessions/langchain/`.
   This test hand-rolls its own patch set, so apply the mock-class rule explicitly: the
   react-agent mock is a `MagicMock()`, not an `AsyncMock()`.

Unchanged, and the parity contract for the extraction:

12. `test_langchain_agent_run.py`, `test_langchain_agent_usage.py` and
    `test_langchain_agent_system_messages.py` must stay green **without any edit** in this
    step. `run_agent` still calls `ainvoke` and still returns the same
    `(final_text, serialized, stats)` — only the loop that computes text and stats moved
    into `_summarize_messages`. If any of them needs changing, the extraction was not
    behaviour-preserving: stop and report. (Step 5 is where these files are rewritten.)

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
mcp__mcp-workspace__check_file_size          # 750-line CI gate — see "Tests"
```

## Required validation gate — real LangGraph events

Every unit test above feeds `graph_events()`, a fixture **this plan invents**. It proves
the code reacts correctly to the assumed event shape; it cannot prove real LangGraph emits
that shape. If the assumption is wrong the guard just logs a warning and stores nothing —
icoder would silently lose multi-turn history with a green suite. So the assumption must
be validated against a real graph before step 4 is considered done:

```
mcp__tools-py__run_pytest_check(markers=["langchain_integration"], extra_args=["-n", "auto", "tests/llm/providers/langchain/test_langchain_integration.py"])
```

`TestAgentModeIntegration::test_agent_simple_prompt` and
`::test_agent_session_continuity` are the gate — the latter runs a real second turn
against the stored history, which is exactly what the root-`run_id` capture must get
right. They reach `run_agent` (non-stream) and therefore only exercise the new code path
**after step 5**; in step 4, drive the same check through the stream path instead — add a
`langchain_integration`-marked test that calls `ask_langchain_stream` with an `mcp_config`
for two turns and asserts the stored history is non-empty and system-free after each.

If no endpoint is configured these tests skip. **A skip is not a pass** — report it
explicitly and treat the root-`run_id` assumption as unverified until step 6's manual
run against the LiteLLM/Qwen endpoint covers it. Do not silently rely on the mocks.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement step 4 only: in src/mcp_coder/llm/providers/langchain/agent.py, make
run_agent_stream assemble its input via assemble_messages(), capture the graph's final
message list from the terminal on_chain_end that matches the root on_chain_start's
run_id, persist serialize_messages(final_messages) once, and emit messages/result/stats
on the done event. EXTRACT run_agent's final-text + stats loop (agent.py:417-462,
including its usage accumulation) into a new private _summarize_messages() and call it
from BOTH run_agent and run_agent_stream — do not copy it. run_agent uses the returned
stats as-is; run_agent_stream overrides only usage with its on_chat_model_end accumulator
via {**stats, "usage": accumulated_usage}. Drop AIMessage/ToolMessage from run_agent's
now-unused deferred imports. Delete the delta reconstruction block, the two now-dead
accumulators (tool_calls_by_run_id, tool_results_list) and the flatten NOTE at
agent.py:659-661.

KEEP accumulated_text: when no terminal graph event is captured, the done event must
carry it as `result` (never ""), otherwise step 5's drainer silently returns an empty
answer on the non-stream agent path.

A cancelled or errored turn must store NOTHING and leave prior history untouched.

Also make _ask_agent_stream in src/mcp_coder/llm/providers/langchain/__init__.py queue a
shallow copy of the done event WITHOUT its `messages` and `stats` keys. Both are only for
step 5's drainer, which consumes run_agent_stream directly; nothing above the bridge reads
either, yet every consumer above it persists the whole event twice per turn — into
raw_response["events"] via ResponseAssembler/store_session, and into the icoder JSONL
event log via AppCore.stream_llm's `self._event_log.emit("stream_event", **event)`
(app_core.py:201). Leaving `messages` in grows both sinks quadratically with turn count;
`stats["tool_trace"]` duplicates content already emitted as tool_use_start/tool_result
events. Strip both once at the boundary: do NOT add filters to
src/mcp_coder/llm/types.py or src/mcp_coder/icoder/core/app_core.py. `result` is NOT
stripped — ResponseAssembler consumes it deliberately. Add the tests/llm/test_types.py
case for done["result"] and the boundary-strip test from the step file.

Add graph_events() and async_events() to tests/llm/providers/langchain/conftest.py and
use them from the streaming tests. Write the tests listed in the step file first.

MOCK CLASS: any react-agent mock whose astream_events returns async_events(...) must be a
MagicMock(), NOT an AsyncMock() — run_agent_stream does
`async for event in agent.astream_events(...)`, and an AsyncMock child call returns a
coroutine, which async for rejects ("TypeError: 'async for' requires an object with
__aiter__ method, got coroutine"). _patch_run_agent_stream already does this correctly, so
the tests that use it inherit the rule; test 11 in test_langchain_multi_turn.py builds its
own patch set and must follow it explicitly.

Put ALL seven new stream/storage tests in a NEW file,
tests/llm/providers/langchain/test_langchain_agent_stream_history.py — do NOT add them to
test_langchain_agent_streaming.py, which is already 656 lines against the CI-enforced
750-line file-size gate (.github/workflows/ci.yml runs `mcp-coder check file-size
--max-lines 750 --allowlist-file .large-files-allowlist` and that file is not
allowlisted); seven more tests there would fail CI. The new file imports
_patch_run_agent_stream from
tests.llm.providers.langchain.test_langchain_agent_streaming (same pattern as
test_langchain_agent_streaming_tool_output.py) and graph_events/async_events from the
conftest. The only change to test_langchain_agent_streaming.py is wrapping
test_history_stored_before_done's events with graph_events(...) and moving _async_events
out to conftest. Run mcp__mcp-workspace__check_file_size before committing.

Also add
the langchain_integration-marked two-turn stream test described under "Required validation
gate" and run it — graph_events() is a fixture we invent, so it cannot on its own prove
real LangGraph emits the terminal event we depend on. If the endpoint is unavailable the
test skips: report the skip, do not call the assumption verified.

Do NOT otherwise touch run_agent in this step — step 5 collapses it. The only change to
run_agent here is that its stats loop becomes a call to _summarize_messages; its tool
loading, ainvoke call and serialization stay. test_langchain_agent_run.py,
test_langchain_agent_usage.py and test_langchain_agent_system_messages.py must stay green
with NO edits — if they don't, the extraction was not behaviour-preserving: stop and
report.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```
