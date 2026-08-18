# Decisions — issue #1116

Decisions taken during plan review that are **not** already in the issue's own Decisions
table. The issue table remains authoritative for everything it covers (single merged
`SystemMessage`, full convergence, `_messages.py` location, shape-agnostic serialize,
graph-final-messages sourcing, root-`run_id` capture, `run_agent` as drainer, stream owns
storage, cancel/error persist nothing).

Recorded after the plan-review rounds of 2026-08-18; each entry names who decided it.
Entries 1–5 come from the first round that day, 6–8 from the follow-up round, 9–11 from
the third.

| # | Topic | Decision | Decided by |
|---|-------|----------|------------|
| 1 | Step-6 end-to-end test: how to bypass MCP tool loading | Pass **`tools=[]`** through `ask_langchain_stream`. Verified against the source: `ask_langchain_stream` forwards `tools` to `_ask_agent_stream` (`__init__.py:591`) and on to `run_agent_stream` (`:494`), which short-circuits on `if tools is not None` (`agent.py:525`) and never touches `_load_mcp_server_config` or `MultiServerMCPClient`. `mcp_config` still has to be truthy to route to the agent branch, but its value is never read. Reviewer was given the choice between this and explicit MCP patches, with "prefer `tools=[]` if it genuinely works". | Tech lead (choice delegated), reviewer (verified + chose `tools=[]`) |
| 2 | Test isolation for the new single storage site | Every test that reaches `run_agent` or `run_agent_stream` with real internals must pass `session_id=` **and** patch `mcp_coder.llm.storage.session_storage.store_langchain_history`. Applies to `test_langchain_agent_run.py`, `test_langchain_agent_usage.py` and `test_langchain_agent_system_messages.py`. Rationale: storage moves inside `run_agent_stream`, `session_id` becomes a required `run_agent` parameter, and there is no autouse fixture isolating the user app-data directory in `tests/conftest.py` — an unpatched test writes real JSON into `~/.mcp_coder/sessions/langchain/`. | Tech lead ("tests must never write into the user's real `~/.mcp_coder/sessions/`"), with the instruction to sweep the other step-5 test files for the same omission |
| 3 | `_summarize_messages`: extract once vs copy-then-delete | **Extract once, call from both.** Step 4 moves `run_agent`'s final-text + stats loop (including its usage accumulation) into `_summarize_messages` and has `run_agent` call it; `run_agent_stream` calls it too and overrides only `usage` with its `on_chat_model_end` accumulator (`{**stats, "usage": accumulated_usage}`). Replaces the earlier "copy verbatim, delete in step 5" instruction. Every step still leaves the suite green, with no duplicated code and no intermediate size problem (`agent.py` stays near 698 lines instead of ~737 against the enforced 750-line limit). | Tech lead ("duplication avoidance is an explicit repo principle and the agent.py size headroom argument seals it") |
| 4 | `done["stats"]` at the provider boundary | **Strip it too**, in the same shallow copy as `messages`, in `_ask_agent_stream`. Rationale: nothing above the provider boundary reads `stats`; its `tool_trace` duplicates content already emitted as `tool_use_start` / `tool_result` events into both sinks; and one strip site for both keys keeps the "no per-consumer filtering" property this issue exists to establish. `result` is **not** stripped — `ResponseAssembler` consumes it deliberately. `run_agent_stream` still yields all three keys, because the step-5 drainer needs them. | Tech lead (explicit decision, with the rationale to record) |
| 5 | `test_langchain_agent_system_messages.py` in step 2 | It is **not** touched in step 2. Its two hand-built `SystemMessage`s test prepending, not the merge. The summary's Modified table now says "step 5 only", matching `step_2.md`. | Tech lead (accepted the reviewer's finding as written) |
| 6 | Step-4 test placement vs the 750-line CI gate | The seven new stream/storage tests go into a **new file**, `tests/llm/providers/langchain/test_langchain_agent_stream_history.py`, not into `test_langchain_agent_streaming.py` (656 lines; ~44 lines/test would put it near 950). The limit is a real CI job — `.github/workflows/ci.yml` runs `mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist`, and that file is not allowlisted. Only the `test_history_stored_before_done` edit and the `_async_events` move stay in the original. Adding the file to `.large-files-allowlist` was **not** chosen. | Tech lead ("accepted, use that filename with the split you proposed") |
| 7 | File-size sweep across every step | Measured **all** files any step adds tests to, not just the one that failed. Result: only `test_langchain_agent_streaming.py` is at risk. `test_langchain_agent_run.py` 493 → ~590, `tests/llm/test_types.py` 491 → ~511, `test_icoder_permission_wiring.py` 452 → unchanged, `test_langchain_agent_usage.py` 220 → ~290; everything else < 300 → < 350; the three new files land at ~150 / ~390 / ~320. No second split needed. Table recorded in `summary.md` § File-size sweep. | Tech lead ("apply the same size check to every other test file any step adds tests to … flag it and split it the same way rather than leaving a second landmine") |
| 8 | `TestRunAgentLaunchErrorWrap` in step 5 | It needs **`session_id="s1"` and nothing else** — the previous "no change at all" instruction was wrong, since `session_id` becomes required and the call at `test_langchain_agent_run.py:404` omits it (`TypeError`, not `LLMMCPLaunchError`). It explicitly does **not** need the `store_langchain_history` patch: tool loading raises before any event, so storage is never reached. The step's storage-patch rule now carries that carve-out (it also covers `test_hard_fails_on_mcp_server_error`). | Tech lead ("accepted as written, including keeping the explicit note that it needs no storage patch") |
| 9 | Mock class for every `astream_events` stub | The react-agent mock must be a **`MagicMock()`, never an `AsyncMock()`**. `run_agent_stream` does `async for event in agent.astream_events(...)`; an `AsyncMock` child call returns a *coroutine*, which `async for` rejects (`TypeError: 'async for' requires an object with __aiter__ method, got coroutine`). Eleven existing call sites build `AsyncMock()` (`test_langchain_agent_run.py` 106/134/173/232/262/320, `test_langchain_agent_usage.py` 119/151/200, `test_langchain_agent_system_messages.py` 80/122) and all must change in step 5. The rule is **anchored once in `step_4.md`** next to the `graph_events()` / `async_events()` conftest helpers and restated where tests hand-roll their own patch set (step 4 test 11, step 5's conversions, both step-6 agent tests). `_patch_run_agent_stream` (`test_langchain_agent_streaming.py:41`) already does it right and is the reference shape. Steps 1–3 need nothing: step 3's multi-turn text test stubs a synchronous `chat_model.stream()`. | Tech lead ("the `AsyncMock` → `MagicMock` catch is the load-bearing one — that would have blocked step 5 outright", with the instruction to sweep the whole plan for the same trap) |
| 10 | Surviving `ainvoke` assertions after the drainer collapse | Swept the whole test tree; the complete list is **three assertion sites plus one substitution**, and `step_5.md` now names each rather than relying on a blanket "keep every existing assertion": `test_langchain_agent_run.py:293` (`test_prepends_session_history` — retarget to `mock_agent.astream_events.call_args`, same `[0][0]["messages"]` indexing; previously uncovered and would have raised `TypeError`, not a parity failure), `test_langchain_agent_system_messages.py:103` and `:138` (already covered), and `mock_agent.ainvoke = _slow_invoke` at `:154`. `test_langchain_agent_usage.py` has **none** — its three `ainvoke` references are `.return_value` setup only. Recorded so later rounds do not re-hunt. | Tech lead ("grep the test files the plan touches for any other surviving `ainvoke` assertion … name them explicitly in the step") |
| 11 | Stale `run_agent` references in `agent.py` | Step 5's wording sweep extends beyond `tests/icoder/test_icoder_permission_wiring.py` to the two source comments the collapse falsifies: the `_convert_server_tools` docstring at `agent.py:293` ("shared by ``run_agent``, ``run_agent_stream`` (else-branch), and ``MCPManager._connect_and_discover``") and the inline comment at `agent.py:532` ("inline, same as run_agent"). Same category, same commit. | Tech lead (accepted the reviewer's task 4 as written) |

## Review findings applied alongside these decisions

Not decisions in their own right, but the plan edits they produced:

* `step_4.md` now states that `run_agent`'s deferred `AIMessage` / `ToolMessage` imports
  become unused after the extraction and must be dropped — as **hygiene, not a gate**.
  (Correction, 2026-08-18: an earlier revision of this line claimed pylint's
  `unused-import` would fail the step and that "only `C` and `R` categories are disabled".
  Both are false — `[tool.pylint.messages_control].disable` in `pyproject.toml` lists
  `W0611 unused-import` alongside W1203/W0621/W0511/W0212/W0613/W0404/W0718/W0706, and
  ruff selects only `["D", "DOC"]`. Nothing catches a leftover import; the instruction
  stands on its own merits.)
* `step_1.md`'s docstring justification was corrected the same way: ruff's `D`/`DOC` rules
  genuinely do require `Args:`/`Returns:` on `src/` functions (`tests/**` is exempt via
  per-file-ignores), but pylint does not — its `C` category is disabled. This was the only
  other "or the linter will fail" claim in the plan; the remaining pylint/ruff/mypy
  mentions are just the per-step check commands.
* `step_4.md` test item 12 pins the extraction's parity contract: the three
  `run_agent` test files must stay green **without edits** in step 4. (Renumbered from 13
  when the test list was made contiguous — it previously skipped 7.)
* The summary's Verified-unchanged list now also names `test_langchain_ollama_agent.py`
  and `test_langchain_agent_timeout.py`, both confirmed unaffected.
* `step_4.md`'s "see Tests, item 6" pointer (in the no-terminal-event `done` discussion)
  was stale after the round-2 renumbering — item 6 is `test_error_persists_nothing`, while
  the item that pins the three `TestRunAgentStreamUsage` tests passing unchanged is
  **item 2**. Corrected. The other renumbered pointers in that file (items 5, 9 and 10 at
  the `test_cancel_done_carries_partial_text`, boundary-strip and `done["result"]`
  references) were re-checked against the current 1–12 list and are correct.
