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

"Persist nothing" applies to **storage only**. The `done` event still carries
`session_id`, `usage` and — as `result` — the text accumulated from the streamed deltas
(`accumulated_text` survives step 4 for exactly this reason). Emitting `result: ""` there
would mean that any failure to capture the terminal graph event silently turns the
non-stream agent path into an empty answer, because step 5's drainer reads `final_text`
off that key. Bounded degradation: history not stored, text still correct.

### 6. `done` payload and `ResponseAssembler`

The `done` event gains `messages` / `result` / `stats`, and `ResponseAssembler`
(`src/mcp_coder/llm/types.py`) already consumes two of those key names — so it **is**
touched, in step 4, and both effects are decided rather than inherited:

* **`result` — kept, with documented semantics.** `add()` reads `done["result"]` and
  `result()` uses it as the response text **only when no `text_delta` event was seen**
  (`types.py:141-143`, `:186-187`). Streaming runs that emit token deltas are unaffected —
  deltas win. Streaming agent runs that emit **no** `text_delta` (a backend or proxy that
  never sends `on_chat_model_stream`) return empty text today and will now return the
  agent's final answer. That is the intended contract: `done["result"]` is the
  authoritative final text, delta accumulation is the preferred rendering. A new
  `tests/llm/test_types.py` case covers the no-`text_delta` path; the existing
  deltas-win cases stay unchanged.
* **`messages` — excluded from the persisted `raw_response["events"]`.** `add()` appends
  every non-`raw_line` event to `_raw_events`, which `result()` returns as
  `raw_response["events"]`, and icoder persists that **per turn** via `store_session`.
  `done["messages"]` is the *whole* serialized conversation, so leaving it in would grow
  stored session JSON **quadratically** with turn count (turn *n* re-persists all *n*
  turns) — not "roughly doubles". The payload exists solely for step 5's in-process
  drainer, which reads it off the live event, so nothing needs it after assembly.
  **Chosen behaviour:** `ResponseAssembler.add` records a shallow copy of the `done` event
  with the `messages` key removed; the event yielded to consumers keeps it. The ndjson
  formatter filters `done` to `session_id`/`usage`/`cost_usd`, so CLI output is unaffected
  either way.

### Deliberate non-changes (KISS)

* **`done.usage` keeps its `on_chat_model_end` accumulator** rather than being recomputed
  from the final message list. Values are identical in practice (one
  `on_chat_model_end` per state `AIMessage`), it needs no new code in the stream path, and
  usage is still reported on a cancelled turn. Only text and tool stats are recomputed
  from the final messages.

  **This is not a no-op for the non-stream path.** `run_agent` today sums `usage_metadata`
  off the `AIMessage`s in `ainvoke`'s output; after the step-5 collapse it inherits the
  stream's `on_chat_model_end` accumulator instead. That is a real change of usage source
  for `run_agent`, and `tests/llm/providers/langchain/test_langchain_agent_usage.py`
  (three tests, all mocking `ainvoke`) must be rewritten in step 5 to emit
  `on_chat_model_end` events — keeping their numeric assertions verbatim as the parity
  check. Only the stream path's usage code is unchanged.
* **`ResponseAssembler`'s text-assembly rules are not touched** beyond §6 — deltas still
  win over `done["result"]`, and the only structural change is dropping `done["messages"]`
  from the recorded event. No new assembler state, no format version bump.
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
| `tests/llm/providers/langchain/test_langchain_multi_turn.py` | Multi-turn text + agent tests; single-system regression tests, incl. one end-to-end through `ask_langchain_stream` + real session-file round trip |

### Modified

| Path | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Merged `SystemMessage`; `_ask_text` / `_ask_text_stream` adopt helpers; `_ask_agent` drops its store call and passes `session_id` |
| `src/mcp_coder/llm/providers/langchain/agent.py` | `run_agent_stream` sources history from graph final messages, adopts helpers, stores once, emits `messages`/`result`/`stats` on `done` (`result` falls back to `accumulated_text` when there is no terminal event); new `_summarize_messages`; `run_agent` becomes a drainer; flatten NOTE removed |
| `src/mcp_coder/llm/types.py` | **Step 4** — `ResponseAssembler.add` records the `done` event without its `messages` key (see §6) |
| `tests/llm/test_types.py` | **Step 4** — assembler cases for the two new `done` keys: `result` used when no `text_delta`, `messages` absent from `raw_response["events"]` |
| `tests/llm/providers/langchain/conftest.py` | New shared test helpers `graph_events()` + `async_events()` |
| `tests/llm/providers/langchain/test_langchain_integration.py` | **Step 4** — one `langchain_integration` two-turn stream test; the real-LangGraph gate for the root-`run_id` terminal-event assumption |
| `tests/llm/providers/langchain/test_langchain_provider_system_messages.py` | Merged-`SystemMessage` assertions |
| `tests/llm/providers/langchain/test_langchain_agent_system_messages.py` | Merged assertions; `astream_events` mocks |
| `tests/llm/providers/langchain/test_langchain_agent_streaming.py` | Terminal graph events where storage is asserted; cancel/error-persist-nothing tests |
| `tests/llm/providers/langchain/test_langchain_agent_run.py` | `ainvoke` mocks → `astream_events` mocks; multi-step parity test |
| `tests/llm/providers/langchain/test_langchain_agent_usage.py` | **Step 5** — `ainvoke` mocks → `astream_events` mocks; usage fed via `on_chat_model_end` events, assertions kept |
| `tests/llm/providers/langchain/test_langchain_agent_mode.py` | `_ask_agent` no longer stores |
| `tests/icoder/test_icoder_permission_wiring.py` | Docstring update only (site 2 no longer exists) |
| `docs/architecture/architecture.md` | One bullet: `agent.py` / `_messages.py`, history stored system-free |

### Verified-unchanged (no edit expected)

`test_langchain_coverage_gaps.py` (mocks `run_agent` wholesale),
`test_langchain_agent_streaming_tool_output.py` (imports only
`_patch_run_agent_stream`, which stays put), `test_langchain_streaming.py`,
`test_tool_build_helper.py` (drives `run_agent_stream` but asserts nothing about
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
