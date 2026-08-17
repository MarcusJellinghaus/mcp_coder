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
| `assemble_messages(system_messages, history, question)` | `systems + messages_from_dict(history) + [HumanMessage(question)]` |
| `serialize_messages(messages)` | Drop **leading** `SystemMessage`s, then dump the rest to the stored `{"type","data"}` shape |

The module holds **no intra-package imports**, so it cannot reintroduce the
`__init__` ↔ `agent` cycle that forces `__init__.py` to lazy-import `.agent`.

`serialize_messages` is the spine of the fix: LangGraph's final state list *includes*
the system message that was prepended for the call, so stripping leading systems in the
one shared serializer is what makes stored history system-free on **every** path — no
per-path filtering anywhere.

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
* `final_text` and `agent_steps` / `total_tool_calls` / `tool_trace` are recomputed from
  that final message list by one private helper, `_summarize_messages()`.
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

### Deliberate non-changes (KISS)

* **`done.usage` keeps its `on_chat_model_end` accumulator.** Values are identical in
  practice (one `on_chat_model_end` per state `AIMessage`), no code changes, existing
  usage tests stay green, and usage is still reported on a cancelled turn. Only text and
  tool stats are recomputed from the final messages.
* **`ResponseAssembler` is not touched.** It records the `done` event into
  `raw_response["events"]`, so `messages` on `done` roughly doubles stored session JSON
  for the streaming agent path with `--store-response`. The ndjson formatter filters
  `done` to `session_id`/`usage`/`cost_usd`, so CLI output is unaffected. Size note only,
  out of scope here.
* **`prompt` and icoder execution models are not unified** — one `chat_model.invoke()`
  vs a LangGraph ReAct loop. Only the message plumbing converges.

### Net effect

`agent.py` shrinks by roughly 90 lines and `__init__.py` by roughly 15; the "full
convergence" is a **net deletion**. Both files currently sit at 698 / 685 lines against
the 750-line limit, so the extraction also relieves size pressure.

---

## Files created / modified

### Created

| Path | Purpose |
|------|---------|
| `src/mcp_coder/llm/providers/langchain/_messages.py` | Shared `assemble_messages` + `serialize_messages` |
| `tests/llm/providers/langchain/test_langchain_messages.py` | Unit tests for the two helpers |
| `tests/llm/providers/langchain/test_langchain_multi_turn.py` | Multi-turn text + agent tests, single-system regression test |

### Modified

| Path | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Merged `SystemMessage`; `_ask_text` / `_ask_text_stream` adopt helpers; `_ask_agent` drops its store call and passes `session_id` |
| `src/mcp_coder/llm/providers/langchain/agent.py` | `run_agent_stream` sources history from graph final messages, adopts helpers, stores once, emits `messages`/`result`/`stats` on `done`; new `_summarize_messages`; `run_agent` becomes a drainer; flatten NOTE removed |
| `tests/llm/providers/langchain/conftest.py` | New shared test helpers `graph_events()` + `async_events()` |
| `tests/llm/providers/langchain/test_langchain_provider_system_messages.py` | Merged-`SystemMessage` assertions |
| `tests/llm/providers/langchain/test_langchain_agent_system_messages.py` | Merged assertions; `astream_events` mocks |
| `tests/llm/providers/langchain/test_langchain_agent_streaming.py` | Terminal graph events where storage is asserted; cancel/error-persist-nothing tests |
| `tests/llm/providers/langchain/test_langchain_agent_run.py` | `ainvoke` mocks → `astream_events` mocks; multi-step parity test |
| `tests/llm/providers/langchain/test_langchain_agent_mode.py` | `_ask_agent` no longer stores |
| `tests/icoder/test_icoder_permission_wiring.py` | Docstring update only (site 2 no longer exists) |
| `docs/architecture/architecture.md` | One bullet: `agent.py` / `_messages.py`, history stored system-free |

### Verified-unchanged (no edit expected)

`test_langchain_coverage_gaps.py` (mocks `run_agent` wholesale),
`test_langchain_agent_streaming_tool_output.py`, `test_langchain_streaming.py`,
`test_langchain_agent_usage.py`, `.importlinter` (the
`mcp_coder.llm.providers.langchain.**` wildcards already cover the new module).

---

## Steps

| # | Step | Outcome |
|---|------|---------|
| 1 | [Shared message helpers](step_1.md) | `_messages.py` + unit tests; no callers yet |
| 2 | [Merge system messages](step_2.md) | Issue 1 fixed for turn 1; merge-safety audit |
| 3 | [Text paths adopt the helpers](step_3.md) | `_ask_text` / `_ask_text_stream` converged; multi-turn text test |
| 4 | [Agent stream sources graph final messages](step_4.md) | Issue 2 fixed; single storage site; cancel/error persist nothing |
| 5 | [Collapse `run_agent` into a drainer](step_5.md) | One agent execution path; `_ask_agent` stops storing |
| 6 | [Regression test + docs](step_6.md) | Single-system-provider regression locked in |

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
