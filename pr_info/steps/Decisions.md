# Decisions — issue #1116

Decisions taken during plan review that are **not** already in the issue's own Decisions
table. The issue table remains authoritative for everything it covers (single merged
`SystemMessage`, full convergence, `_messages.py` location, shape-agnostic serialize,
graph-final-messages sourcing, root-`run_id` capture, `run_agent` as drainer, stream owns
storage, cancel/error persist nothing).

Recorded after the plan-review round of 2026-08-18; each entry names who decided it.

| # | Topic | Decision | Decided by |
|---|-------|----------|------------|
| 1 | Step-6 end-to-end test: how to bypass MCP tool loading | Pass **`tools=[]`** through `ask_langchain_stream`. Verified against the source: `ask_langchain_stream` forwards `tools` to `_ask_agent_stream` (`__init__.py:591`) and on to `run_agent_stream` (`:494`), which short-circuits on `if tools is not None` (`agent.py:525`) and never touches `_load_mcp_server_config` or `MultiServerMCPClient`. `mcp_config` still has to be truthy to route to the agent branch, but its value is never read. Reviewer was given the choice between this and explicit MCP patches, with "prefer `tools=[]` if it genuinely works". | Tech lead (choice delegated), reviewer (verified + chose `tools=[]`) |
| 2 | Test isolation for the new single storage site | Every test that reaches `run_agent` or `run_agent_stream` with real internals must pass `session_id=` **and** patch `mcp_coder.llm.storage.session_storage.store_langchain_history`. Applies to `test_langchain_agent_run.py`, `test_langchain_agent_usage.py` and `test_langchain_agent_system_messages.py`. Rationale: storage moves inside `run_agent_stream`, `session_id` becomes a required `run_agent` parameter, and there is no autouse fixture isolating the user app-data directory in `tests/conftest.py` — an unpatched test writes real JSON into `~/.mcp_coder/sessions/langchain/`. | Tech lead ("tests must never write into the user's real `~/.mcp_coder/sessions/`"), with the instruction to sweep the other step-5 test files for the same omission |
| 3 | `_summarize_messages`: extract once vs copy-then-delete | **Extract once, call from both.** Step 4 moves `run_agent`'s final-text + stats loop (including its usage accumulation) into `_summarize_messages` and has `run_agent` call it; `run_agent_stream` calls it too and overrides only `usage` with its `on_chat_model_end` accumulator (`{**stats, "usage": accumulated_usage}`). Replaces the earlier "copy verbatim, delete in step 5" instruction. Every step still leaves the suite green, with no duplicated code and no intermediate size problem (`agent.py` stays near 698 lines instead of ~737 against the enforced 750-line limit). | Tech lead ("duplication avoidance is an explicit repo principle and the agent.py size headroom argument seals it") |
| 4 | `done["stats"]` at the provider boundary | **Strip it too**, in the same shallow copy as `messages`, in `_ask_agent_stream`. Rationale: nothing above the provider boundary reads `stats`; its `tool_trace` duplicates content already emitted as `tool_use_start` / `tool_result` events into both sinks; and one strip site for both keys keeps the "no per-consumer filtering" property this issue exists to establish. `result` is **not** stripped — `ResponseAssembler` consumes it deliberately. `run_agent_stream` still yields all three keys, because the step-5 drainer needs them. | Tech lead (explicit decision, with the rationale to record) |
| 5 | `test_langchain_agent_system_messages.py` in step 2 | It is **not** touched in step 2. Its two hand-built `SystemMessage`s test prepending, not the merge. The summary's Modified table now says "step 5 only", matching `step_2.md`. | Tech lead (accepted the reviewer's finding as written) |

## Review findings applied alongside these decisions

Not decisions in their own right, but the plan edits they produced:

* `step_4.md` now states that `run_agent`'s deferred `AIMessage` / `ToolMessage` imports
  become unused after the extraction and must be dropped (pylint's `unused-import` is
  enabled — only `C` and `R` categories are disabled in `pyproject.toml`).
* `step_4.md` test item 13 pins the extraction's parity contract: the three
  `run_agent` test files must stay green **without edits** in step 4.
* The summary's Verified-unchanged list now also names `test_langchain_ollama_agent.py`
  and `test_langchain_agent_timeout.py`, both confirmed unaffected.
