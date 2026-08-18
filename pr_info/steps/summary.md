# Issue #1116 — LangChain backend: icoder multiple-system-message bug + path convergence

## Goal

Two coupled functional defects plus the agreed convergence refactor:

1. **Issue 1** — `_build_system_messages` emits one `SystemMessage` per prompt, so the
   conversation starts `[System, System, Human, …]`. LiteLLM/Qwen-class single-system
   providers reject this with `system messages must be at the beginning`.
2. **Issue 2** — the agent path stores the prepended system messages as part of the
   history and re-prepends fresh ones every turn, so systems accumulate (+2/turn) and
   the Issue-1 symptom returns on turn 2 even after the merge fix.
3. **Convergence** — the bug existed *because* the text path and the agent path build
   and persist message lists with separate code. Both now route through one pair of
   shared helpers, and the two agent implementations collapse into one execution path.

---

## Architectural / design changes

### 1. New neutral module: `langchain/_messages.py`

Two helpers split by concern, used by **all four** message sites:

| Helper | Responsibility |
|--------|----------------|
| `assemble_messages(system_messages, history, question)` | `systems + messages_from_dict(history minus any "system" entries) + [HumanMessage(question)]` |
| `serialize_messages(messages)` | Drop **leading** `SystemMessage`s, then dump the rest to the stored `{"type","data"}` shape |

The module holds **no intra-package imports**, so it cannot reintroduce the
`__init__` ↔ `agent` cycle that forces `__init__.py` to lazy-import `.agent`.

`serialize_messages` is the spine of the fix: LangGraph's final state list *includes*
the system message that was prepended for the call, so stripping leading systems in the
one shared serializer is what makes stored history system-free on **every** path — no
per-path filtering anywhere.

**Pre-existing histories on resume.** Sessions written by the *current* agent code already
contain `"system"` entries. On `--session-id` / `--continue-session` / icoder resume,
`assemble_messages` puts the fresh merged `SystemMessage` in front of that loaded history,
so the legacy systems end up **non-leading** — `serialize_messages` would not strip them
on the way out, and the provider would still see >1 system message on the first resumed
turn. `assemble_messages` therefore **drops every `SystemMessage` it finds in the loaded
history** before appending it, not just leading ones. This is one line in the one shared
helper, it is what makes "loaded history is system-free" true for old files as well as new
ones, and it needs no migration script or storage-version bump. Covered by a unit test in
step 1 (`test_assemble_drops_system_messages_from_history`).

Note the asymmetry, and keep it: `assemble_messages` drops systems **anywhere** in the
loaded history (that history is untrusted, possibly written by the old code), while
`serialize_messages` strips only **leading** systems (it is handed a list this code just
assembled, where the merged system is always at the front).

### 2. Single merged `SystemMessage`

`_build_system_messages` joins system + project prompt with a blank line (`"\n\n"`) and
returns **at most one** `SystemMessage`. It stays in `__init__.py`: it has only two call
sites (both there), it was never a divergence source, and moving it would churn five
test imports for no benefit. The neutral module holds exactly the two required helpers.

### 3. Agent paths collapse to one execution path

* `run_agent_stream` sources the persisted history from the **graph's final message
  list**, captured from the terminal `on_chain_end` whose `run_id` matches the root
  `on_chain_start` (guarded by a `"messages" in data.output` check). Delta
  reconstruction and the `agent.py:659-661` flatten NOTE are **deleted** — the flattening
  problem disappears by deletion rather than by patching.
* `final_text` and `agent_steps` / `total_tool_calls` / `tool_trace` / `usage` are
  recomputed from that final message list by one private helper, `_summarize_messages()`.
  It is **extracted once** from `run_agent`'s existing loop in step 4 and called from
  **both** `run_agent` and `run_agent_stream` — no copy-then-delete. `run_agent_stream`
  overrides only `usage`, with its `on_chat_model_end` accumulator
  (`{**stats, "usage": accumulated_usage}`). Extracting rather than duplicating also keeps
  `agent.py` near its current 698 lines after step 4 (a temporary copy would have put it
  around 737 against the enforced 750-line limit) before step 5 removes ~100 more.
* `run_agent` becomes a **thin drainer** of `run_agent_stream` (inside its existing
  `asyncio.wait_for` timeout). Its MCP client loading, `ainvoke` call, stats loop and
  serialization are deleted. This satisfies the "all four sites route through the shared
  helpers" criterion by *eliminating* the site rather than converting it.

### 4. Single storage site — the stream owns storage

* `run_agent_stream` stores once internally (unchanged site) and surfaces the final
  serialized `messages`, `result` text and `stats` on the `done` event.
* `run_agent` reads them off `done` and returns them — it does **not** store.
* `_ask_agent` drops its `store_langchain_history` call and only builds `raw_response`.

### 5. Cancel / error persist nothing

Without a terminal `on_chain_end` there is no clean system-free final message list, so
nothing is stored and prior history is untouched. `asyncio.wait_for` cancellation raises
`CancelledError` (a `BaseException`), which `run_agent_stream`'s `except Exception` does
not catch — so no spurious `error` event and no storage, for free.

"Persist nothing" applies to **storage only**. The `done` event still carries
`session_id`, `usage` and — as `result` — the text accumulated from the streamed deltas
(`accumulated_text` survives step 4 for exactly this reason). Emitting `result: ""` there
would mean that any failure to capture the terminal graph event silently turns the
non-stream agent path into an empty answer, because step 5's drainer reads `final_text`
off that key. Bounded degradation: history not stored, text still correct.

### 6. `done` payload and `ResponseAssembler`

The event `run_agent_stream` yields gains `messages` / `result` / `stats` — step 5's
drainer needs all three. Only `result` crosses the provider boundary; `messages` and
`stats` are stripped there. `ResponseAssembler` (`src/mcp_coder/llm/types.py`) already
consumes the name `result`, so its behaviour changes even though its code does not. All
three effects are decided rather than inherited:

* **`result` — kept, with documented semantics.** `add()` reads `done["result"]` and
  `result()` uses it as the response text **only when no `text_delta` event was seen**
  (`types.py:141-143`, `:186-187`). Streaming runs that emit token deltas are unaffected —
  deltas win. Streaming agent runs that emit **no** `text_delta` (a backend or proxy that
  never sends `on_chat_model_stream`) return empty text today and will now return the
  agent's final answer. That is the intended contract: `done["result"]` is the
  authoritative final text, delta accumulation is the preferred rendering. A new
  `tests/llm/test_types.py` case covers the no-`text_delta` path; the existing
  deltas-win cases stay unchanged.
* **`messages` and `stats` — both stripped at the provider boundary, so no consumer
  outside the langchain package ever sees either.** Both keys exist solely for step 5's
  in-process drainer, which consumes `run_agent_stream` **directly**; nothing above the
  boundary reads them. Everything else reaches the `done` event via `_ask_agent_stream`,
  and there are **two** sinks that persist it, not one:
  * `ResponseAssembler.add` appends every non-`raw_line` event to `_raw_events`, which
    `result()` returns as `raw_response["events"]`; icoder persists that per turn via
    `store_session`.
  * `AppCore.stream_llm` emits every non-`raw_line` event to the icoder event log —
    `self._event_log.emit("stream_event", **event)` (`app_core.py:201`) — which keeps the
    payload both in memory (`EventLog._entries`) and as a JSONL line on disk;
    `ui/replay.py:73-81` reads those entries back and re-emits them.

  `done["messages"]` is the *whole* serialized conversation, so leaving it on the event
  makes **both** sinks grow **quadratically** with turn count (turn *n* re-persists all
  *n* turns) — not "roughly doubles". `done["stats"]` adds a constant-factor duplication
  on top: its `tool_trace` repeats the name/args/result of every tool call in the turn,
  content the same sinks already hold as `tool_use_start` / `tool_result` events.

  **Chosen behaviour — one strip site, at the boundary, for both keys.**
  `_ask_agent_stream` removes the `messages` **and** `stats` keys from the `done` event
  (one shallow copy) before putting it on the queue. The drainer still gets them because
  it bypasses that bridge; nothing above the langchain provider does. Filtering the sinks
  individually would instead mean two filters in two modules (`types.py` and
  `app_core.py`) that have to stay in sync as sinks are added — exactly the per-consumer
  drift this issue exists to remove, which is also why both keys are stripped in the same
  place rather than one here and one there. Consequences: **`src/mcp_coder/llm/types.py`
  needs no change** and `app_core.py` is not touched. The ndjson formatter filters `done`
  to `session_id`/`usage`/`cost_usd`, so CLI output is unaffected either way.

### Deliberate non-changes (KISS)

* **`done.usage` keeps its `on_chat_model_end` accumulator** rather than being recomputed
  from the final message list: it needs no new code in the stream path, and usage is still
  reported on a cancelled turn. `_summarize_messages` does compute a `usage` value (it is
  the extracted `run_agent` loop, which `run_agent` still needs in step 4), but
  `run_agent_stream` discards it in favour of the accumulator via
  `{**stats, "usage": accumulated_usage}`.

  **This is not a no-op for the non-stream path, and the two sources are not guaranteed
  equal.** `run_agent` today sums `usage_metadata` off the `AIMessage`s in `ainvoke`'s
  output; after the step-5 collapse it inherits the stream's `on_chat_model_end`
  accumulator instead. Under `astream_events` the model is *streamed*, and the aggregated
  chunk delivered as `on_chat_model_end`'s `data.output` carries `usage_metadata` **only
  when the backend streams usage** — for OpenAI-compatible backends that means
  `stream_usage=True` / `stream_options={"include_usage": True}`; providers or proxies
  that omit it deliver no `usage_metadata` at all. The counts are identical when streamed
  usage is available (one `on_chat_model_end` per state `AIMessage`); when it is not,
  `stats["usage"]` — and therefore `_ask_agent`'s `raw_response["usage"]` for non-stream
  agent mode — degrades to `{}`, where `ainvoke` returned real numbers today.

  **Documented fallback:** `{}` (usage simply unreported), never an error and never a
  wrong number; text, tool stats and stored history are unaffected. This is accepted
  rather than worked around — recomputing usage from the final message list would
  reintroduce a second usage code path — but it must be **verified, not assumed**:
  `tests/llm/providers/langchain/test_langchain_agent_usage.py` (three tests, all mocking
  `ainvoke`) is rewritten in step 5 to feed usage through `on_chat_model_end` events, which
  proves the accumulator arithmetic but **cannot** prove the backend emits it, so step 5
  also gates on a real-endpoint assertion (see step_5.md).
* **`ResponseAssembler` is not modified at all** — deltas still win over `done["result"]`,
  and neither `done["messages"]` nor `done["stats"]` reaches it (both stripped in
  `_ask_agent_stream`, §6). No new assembler state, no format version bump, no code change
  in `types.py`.
* **`prompt` and icoder execution models are not unified** — one `chat_model.invoke()`
  vs a LangGraph ReAct loop. Only the message plumbing converges.

### Net effect

`agent.py` shrinks by roughly 90 lines and `__init__.py` by roughly 15; the "full
convergence" is a **net deletion**. Both files currently sit at 698 / 685 lines against
the 750-line limit, so the extraction also relieves size pressure.

### File-size sweep (750-line CI gate)

The limit is enforced in CI — `.github/workflows/ci.yml` runs
`mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist` as its
own job — so it binds test files exactly as it binds source. Every file any step adds
tests to was measured:

| File | Now | After | Verdict |
|------|-----|-------|---------|
| `test_langchain_agent_streaming.py` | **656** | ~654 | **At risk** — the 7 new step-4 tests (~44 lines each) would reach ~950. Split: they go to the new `test_langchain_agent_stream_history.py`; only the `test_history_stored_before_done` edit stays |
| `test_langchain_agent_run.py` | 493 | ~590 | OK (step 5: `session_id=` at every call site, store patch where storage is reached, plus the parity test) |
| `tests/llm/test_types.py` | 491 | ~511 | OK (one assembler test) |
| `tests/icoder/test_icoder_permission_wiring.py` | 452 | 452 | OK (wording only) |
| `test_langchain_agent_usage.py` | 220 | ~290 | OK |
| `test_langchain_agent_system_messages.py`, `test_langchain_agent_mode.py`, `test_langchain_provider_system_messages.py`, `test_langchain_integration.py`, langchain tests `conftest.py` | all < 300 | < 350 | OK |
| New files (`test_langchain_messages.py`, `test_langchain_multi_turn.py`, `test_langchain_agent_stream_history.py`) | — | ~150 / ~390 / ~320 | OK |

Only one file needed splitting. None of these are in `.large-files-allowlist`, and none
should be added to it.

---

## Files created / modified

### Created

| Path | Purpose |
|------|---------|
| `src/mcp_coder/llm/providers/langchain/_messages.py` | Shared `assemble_messages` + `serialize_messages` |
| `tests/llm/providers/langchain/test_langchain_messages.py` | Unit tests for the two helpers (step 1, ~150 lines) |
| `tests/llm/providers/langchain/test_langchain_multi_turn.py` | Multi-turn text + agent tests; single-system regression tests, incl. one end-to-end through `ask_langchain_stream` + real session-file round trip (steps 3, 4, 6; ~390 lines when complete) |
| `tests/llm/providers/langchain/test_langchain_agent_stream_history.py` | **Step 4** — all seven new tests (step_4 items 3–9): `run_agent_stream` storage / no-system-messages / `done` payload / cancel / error / no-terminal-event, and the `_ask_agent_stream` boundary strip (~320 lines). A separate file because `test_langchain_agent_streaming.py` is already 656 lines against the CI-enforced 750-line gate; it imports `_patch_run_agent_stream` from that file and `graph_events` / `async_events` from the conftest |

### Modified

| Path | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Merged `SystemMessage`; `_ask_text` / `_ask_text_stream` adopt helpers; **step 4** — `_ask_agent_stream` strips `messages` **and** `stats` from the `done` event before queueing it (§6); `_ask_agent` drops its store call and passes `session_id` |
| `src/mcp_coder/llm/providers/langchain/agent.py` | `run_agent_stream` sources history from graph final messages, adopts helpers, stores once, emits `messages`/`result`/`stats` on `done` (`result` falls back to `accumulated_text` when there is no terminal event); new `_summarize_messages` extracted from `run_agent` in step 4 and called from both; `run_agent` becomes a drainer in step 5; flatten NOTE removed; **step 5** also refreshes the two comments that name `run_agent` as a tool-loading caller (`_convert_server_tools` docstring at `:293`, inline comment at `:532`) |
| `tests/llm/test_types.py` | **Step 4** — one assembler case for the new `done["result"]` key: used as the text when no `text_delta` was seen |
| `tests/llm/providers/langchain/conftest.py` | New shared test helpers `graph_events()` + `async_events()`; step 4 anchors the mock-class rule (react-agent mock is `MagicMock()`, never `AsyncMock()`) next to them |
| `tests/llm/providers/langchain/test_langchain_integration.py` | **Step 4** — one `langchain_integration` two-turn stream test; the real-LangGraph gate for the root-`run_id` terminal-event assumption. **Step 5** — `TestAgentModeIntegration::test_agent_simple_prompt` gains a non-empty `raw_response["usage"]` assertion, the real gate for the usage-source change |
| `tests/llm/providers/langchain/test_langchain_provider_system_messages.py` | Merged-`SystemMessage` assertions |
| `tests/llm/providers/langchain/test_langchain_agent_system_messages.py` | **Step 5 only** — `ainvoke` mocks → `astream_events` mocks (`AsyncMock()` → `MagicMock()`, see step 5's mock-class rule) and the two `ainvoke.call_args` assertions retargeted, plus `session_id=` and a `store_langchain_history` patch on all three `run_agent` calls. Its two hand-built `SystemMessage`s are testing prepending, not the merge, so step 2 leaves it alone |
| `tests/llm/providers/langchain/test_langchain_agent_streaming.py` | **Step 4** — `test_history_stored_before_done` wrapped in `graph_events(...)`, and the local `_async_events` helper moved to conftest. **No new tests here** (file-size gate — they go in `test_langchain_agent_stream_history.py`) |
| `tests/llm/providers/langchain/test_langchain_agent_run.py` | **Step 5** — `session_id=` at every `run_agent` call site (including `TestRunAgentLaunchErrorWrap`, which needs nothing else); `ainvoke` mocks → `astream_events` mocks (`AsyncMock()` → `MagicMock()`, see step 5's mock-class rule) + `store_langchain_history` patch for the tests that reach a terminal event; `test_prepends_session_history`'s `ainvoke.call_args` assertion retargeted to `astream_events.call_args` — the single assertion change in this file; new multi-step parity test. 493 → ~590 lines |
| `tests/llm/providers/langchain/test_langchain_agent_usage.py` | **Step 5** — `ainvoke` mocks → `astream_events` mocks (`AsyncMock()` → `MagicMock()`, see step 5's mock-class rule), `session_id=` + `store_langchain_history` patch; usage fed via `on_chat_model_end` events, assertions kept (accumulator arithmetic only — the real-endpoint gate lives in `test_langchain_integration.py`) |
| `tests/llm/providers/langchain/test_langchain_agent_mode.py` | `_ask_agent` no longer stores |
| `tests/icoder/test_icoder_permission_wiring.py` | **Step 5** — wording only, no behaviour change: the two "site 2" docstrings **and** the `AssertionError` message at line 298 (site 2 no longer exists) |
| `docs/architecture/architecture.md` | One bullet: `agent.py` / `_messages.py`, history stored system-free |

### Verified-unchanged (no edit expected)

`src/mcp_coder/llm/types.py` and `src/mcp_coder/icoder/core/app_core.py` (both would need a
`done["messages"]` / `done["stats"]` filter only if those keys crossed the provider
boundary — §6 strips both in `_ask_agent_stream` instead),
`test_langchain_coverage_gaps.py` and `test_langchain_ollama_agent.py` (both mock
`run_agent` wholesale, so the new `session_id` keyword and the dropped store call are
invisible to them), `test_langchain_agent_streaming_tool_output.py` (imports only
`_patch_run_agent_stream`, which stays put), `test_langchain_streaming.py`,
`test_langchain_agent_timeout.py` (drives `_ask_agent_stream` with a stubbed thread and
queue), `test_tool_build_helper.py` (drives `run_agent_stream` but asserts nothing about
storage), `.importlinter` (the `mcp_coder.llm.providers.langchain.**` wildcards
already cover the new module).

---

## Steps

| # | Step | Outcome |
|---|------|---------|
| 1 | [Shared message helpers](step_1.md) | `_messages.py` + unit tests; no callers yet |
| 2 | [Merge system messages](step_2.md) | Issue 1 fixed for turn 1; merge-safety audit |
| 3 | [Text paths adopt the helpers](step_3.md) | `_ask_text` / `_ask_text_stream` converged; multi-turn text test |
| 4 | [Agent stream sources graph final messages](step_4.md) | Issue 2 fixed; single storage site; cancel/error persist nothing |
| 5 | [Collapse `run_agent` into a drainer](step_5.md) | One agent execution path; `_ask_agent` stops storing |
| 6 | [Regression test + docs](step_6.md) | Single-system-provider regression locked in, incl. the end-to-end icoder agent flow |

Each step is exactly one commit: tests + implementation + pylint / pytest / mypy green.

## Verification (after step 6)

Automated: pylint, pytest, mypy per `CLAUDE.md`.

Manual, against the LiteLLM/Qwen endpoint:

* `mcp-coder prompt "..." --add-system-prompts` completes without error.
* A 2+ turn icoder session completes without `system messages must be at the beginning`.

## Acceptance criteria mapping

| Criterion | Step |
|-----------|------|
| Single leading `SystemMessage` | 2 |
| icoder works across multiple turns | 4, 5 |
| `prompt --add-system-prompts` works | 2, 3 |
| Stored history has no system messages | 3, 4 |
| Shared helpers at all four sites | 1, 3, 4, 5 |
| One agent execution path, flatten NOTE removed | 4, 5 |
| Single persistence site, no double-store | 4, 5 |
| Cancelled/errored turn persists nothing | 4 |
| Rejecting-stub regression test | 6 |
| Merge-safety audit | 2 |
