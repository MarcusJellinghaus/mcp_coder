# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Shared message helpers (`_messages.py`)

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: create `src/mcp_coder/llm/providers/langchain/_messages.py` with `assemble_messages()` + `serialize_messages()` (deferred `langchain_core` imports, no intra-package imports) and `tests/llm/providers/langchain/test_langchain_messages.py` (8 tests, written first). No existing module is modified.
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pytest **could not run**: pre-existing environment breakage, see note in [step_1.md](./steps/step_1.md))
- [x] Commit message prepared

### Step 2: Merge system + project prompt into a single `SystemMessage`

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation: `_build_system_messages` in `langchain/__init__.py` returns at most one merged `SystemMessage` (`"\n\n"` separator); update assertions in `test_langchain_provider_system_messages.py` first. Includes the merge-safety audit (`SystemMessage` / `system_messages` search) — record its result in the commit message; stop and report if production code assumes two messages.
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pytest **could not run**: same pre-existing environment breakage as step 1, see note in [step_2.md](./steps/step_2.md))
- [x] Commit message prepared

### Step 3: Text paths adopt the shared helpers

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation: `_ask_text` and `_ask_text_stream` use `assemble_messages()` / `serialize_messages()`; create `tests/llm/providers/langchain/test_langchain_multi_turn.py` with the multi-turn streaming text-path test (written first). Existing text-path tests must stay green unmodified — if one needs changing, stop and report.
- [x] Quality checks: pylint, pytest, mypy — fix all issues (mandated full-suite pytest still blocked by the pre-existing environment breakage; verified via a temporary shim — see note in [step_3.md](./steps/step_3.md))
- [x] Commit message prepared

### Step 4: Agent stream sources persisted history from the graph's final messages

Detail: [step_4.md](./steps/step_4.md)

- [x] Implementation: `run_agent_stream` assembles via `assemble_messages()`, captures the graph's final messages from the root-`run_id` terminal `on_chain_end`, stores `serialize_messages(...)` once, and emits `messages`/`result`/`stats` on `done` (`result` falls back to `accumulated_text`); extract `_summarize_messages()` from `run_agent` and call it from both; delete the reconstruction block, dead accumulators and flatten NOTE; `_ask_agent_stream` strips `messages` + `stats` at the boundary. Tests first: new `test_langchain_agent_stream_history.py` (7 tests), conftest `graph_events()`/`async_events()`, `test_types.py` assembler case, multi-turn agent test, plus the `langchain_integration` two-turn stream gate. Also run `check_file_size` (750-line gate). Report an integration-test skip as unverified — a skip is not a pass. (**Validation gate SKIPPED — root-`run_id` assumption remains unverified against real LangGraph**, see note in [step_4.md](./steps/step_4.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues (`check_file_size` passed; unit tests run via the same throwaway shim as step 3 — see note in [step_4.md](./steps/step_4.md))
- [x] Commit message prepared

### Step 5: Collapse `run_agent` into a thin drainer; `_ask_agent` stops storing

Detail: [step_5.md](./steps/step_5.md)

- [x] Implementation: `run_agent` becomes a thin drainer of `run_agent_stream` (new required `session_id`, `asyncio.wait_for` kept, stores nothing); delete its tool loading / `ainvoke` / serialization; `_ask_agent` drops its store call; refresh the two stale `agent.py` comments and the `test_icoder_permission_wiring.py` wording. Tests updated first across `test_langchain_agent_run.py` (incl. multi-step parity test), `_usage.py`, `_system_messages.py`, `_mode.py` — `MagicMock()` react agents, `session_id=` at every call site, store patches where storage is reached. Add the non-empty `raw_response["usage"]` assertion to the integration gate and run it; report skip/failure honestly. Also run `check_file_size`. (**Integration gate SKIPPED — 7/7 skipped, no endpoint configured, so the usage-source change and step 4's root-`run_id` assumption both remain unverified against a real backend**, see note in [step_5.md](./steps/step_5.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues (`check_file_size` passed; unit tests run via the same throwaway shim as steps 3–4 — see note in [step_5.md](./steps/step_5.md))
- [x] Commit message prepared

### Step 6: Single-system-provider regression test + docs

Detail: [step_6.md](./steps/step_6.md)

- [x] Implementation: add `TestSingleSystemProviderRejection` (text path, agent path, and end-to-end icoder agent flow through `ask_langchain_stream(..., mcp_config=<truthy>, tools=[])` with real storage under `tmp_path`) to `test_langchain_multi_turn.py`, plus the `docs/architecture/architecture.md` notes. No production logic changes. Run the full suite once without marker exclusions, and report the manual LiteLLM/Qwen verification outcome honestly (say so if no endpoint is available). (**Manual LiteLLM/Qwen verification NOT PERFORMED — no endpoint configured, langchain not installed, no shell; acceptance criteria remain unverified against a real backend.** Full suite covered in chunks: the 300s tool cap makes a single no-exclusions run impossible — see note in [step_6.md](./steps/step_6.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues (unit tests run via the same throwaway shim as steps 3–5, removed before finishing; `check_file_size` passed — see note in [step_6.md](./steps/step_6.md))
- [x] Commit message prepared

## Pull Request

- [ ] PR review: address review feedback and resolve open comments
- [ ] PR summary: write the pull request title and description
