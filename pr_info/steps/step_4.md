# Step 4 — Agent stream sources persisted history from the graph's final messages

**Goal:** Fix Issue 2. `run_agent_stream` stops persisting a hand-reconstructed,
flattened history that includes the system messages, and instead persists the graph's
own final message list, serialized (and therefore system-stripped) by the shared helper.
This is the single storage site for the agent path.

`run_agent` is **not** touched in this step — it still works as today, stats loop and all.
Step 5 collapses it. The stats loop is **copied** into `_summarize_messages` here and
**deleted** from `run_agent` in step 5, so step 4 leaves both paths working.

## WHERE

* Modify `src/mcp_coder/llm/providers/langchain/agent.py` — `run_agent_stream`
  (~lines 478–698), plus a new module-level `_summarize_messages()`
* Modify `tests/llm/providers/langchain/conftest.py` — add two shared test helpers
* Modify `tests/llm/providers/langchain/test_langchain_agent_streaming.py`
* Modify `tests/llm/providers/langchain/test_langchain_multi_turn.py` (created in step 3)
* Modify `tests/llm/providers/langchain/test_langchain_integration.py` — one
  `langchain_integration` two-turn stream test (see "Required validation gate")

## WHAT

```python
def _summarize_messages(messages: list[Any]) -> tuple[str, dict[str, Any]]:
    """Derive final text and tool stats from a graph's final message list."""
```

`run_agent_stream`'s signature is unchanged.

New test helpers in `tests/llm/providers/langchain/conftest.py` (plain module-level
functions, imported as `from tests.llm.providers.langchain.conftest import ...` — the
same pattern as `tests/icoder/conftest.py`):

```python
def graph_events(
    final_messages: list[Any], inner: Sequence[dict[str, object]] = ()
) -> list[dict[str, object]]: ...

async def async_events(items: list[dict[str, object]]) -> AsyncIterator[dict[str, object]]: ...
```

## HOW

* `agent.py` module-level import: `from ._messages import assemble_messages, serialize_messages`.
* `run_agent_stream` builds its input with
  `assemble_messages(system_messages, messages, question)`.
* Its deferred import block reduces to `from langgraph.prebuilt import create_react_agent`
  — `HumanMessage` / `ToolMessage` / `messages_from_dict` are no longer needed there, and
  `AIMessage` moves into `_summarize_messages`.
* **Delete** the accumulators `accumulated_text`, `tool_calls_by_run_id`,
  `tool_results_list`, the whole reconstruction block after the event loop, and the
  flatten NOTE at lines 659–661. Keep `accumulated_usage` and every `yield` in the event
  loop — user-facing streaming is unchanged.
* `_summarize_messages` receives the stats loop **copied verbatim from** `run_agent`
  (`agent_steps`, `total_tool_calls`, `tool_trace`, `trace_by_id` fill from
  `ToolMessage`s) **minus** its usage accumulation — usage keeps coming from the existing
  `on_chat_model_end` accumulator (see summary; identical values, and usage still reported
  on a cancelled turn).
  **Copy, do not move.** `run_agent` keeps its own copy of the loop through step 4 so it
  still works and its tests stay green; step 5 deletes the original when `run_agent`
  becomes a drainer. The temporary duplication lives for exactly one commit and is the
  price of each step leaving the suite green.
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
           "messages": [], "result": "",
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
`done["usage"]` unchanged (see Tests, item 6). Only `messages` / `result` / `stats` are
empty, because there is nothing safe to persist or summarize.

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
* Cancelled / no-terminal-event turn: `messages: []`, `result: ""`, zeroed stats, and
  **no** storage call — but `session_id` and `usage` are still present and unchanged.

## Tests (write first)

In `test_langchain_agent_streaming.py`:

1. `test_history_stored_before_done` — wrap the events with `graph_events([...])`; assert
   the stored payload equals the serialized final messages.
2. New `test_stored_history_has_no_system_messages` — final messages
   `[SystemMessage, HumanMessage, AIMessage]` → stored has 2 entries, no `"system"` type.
3. New `test_done_event_carries_messages_result_and_stats`.
4. New `test_cancel_persists_nothing` — cancel mid-stream (no terminal event) → store
   **not** called; a `done` event is still emitted.
5. New `test_error_persists_nothing` — `astream_events` raises → store not called; the
   existing `error`-event + re-raise behaviour is unchanged.
6. `test_done_event_emitted_last`, the three `TestRunAgentStreamUsage` tests and the
   tool-output tests keep passing **unchanged** (they emit no terminal event, so they
   simply store nothing — none of them asserts storage).

In `test_langchain_multi_turn.py`:

7. `TestAgentPathMultiTurn::test_two_turns_store_no_systems_and_send_one_system` — call
   `run_agent_stream` twice, feeding turn 2 the `messages` captured from turn 1's store
   call; assert turn 2's `astream_events` input has exactly one `SystemMessage` at index 0
   and the stored history has zero system entries across both turns.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
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
on the done event. Add the private _summarize_messages() helper by COPYING run_agent's
stats loop (leave run_agent's own copy in place — step 5 deletes it). Delete the delta
reconstruction block, the three now-dead accumulators, and the flatten NOTE at
agent.py:659-661.

A cancelled or errored turn must store NOTHING and leave prior history untouched.

Add graph_events() and async_events() to tests/llm/providers/langchain/conftest.py and
use them from the streaming tests. Write the tests listed in the step file first. Also add
the langchain_integration-marked two-turn stream test described under "Required validation
gate" and run it — graph_events() is a fixture we invent, so it cannot on its own prove
real LangGraph emits the terminal event we depend on. If the endpoint is unavailable the
test skips: report the skip, do not call the assumption verified.

Do NOT touch run_agent in this step — step 5 collapses it. Copy its stats loop into
_summarize_messages and leave the original in place.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```
