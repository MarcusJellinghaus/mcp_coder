# Decisions Log — Issue #517

Decisions made during plan review discussion.

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Env var resolution in `_load_mcp_server_config` | Targeted resolution only (`command`, `args`, `env` fields). Log a warning for unknown fields (key + value), then ignore them. | Predictable, covers all real `.mcp.json` fields. No other fields exist in the format. |
| 2 | Session history — mixed text-only / agent mode | Add a mode marker (e.g. `"mode": "agent"` or `"mode": "text"`) in session metadata so deserialization knows which format to expect. | Users could switch modes mid-session; marker prevents format confusion. |
| 3 | `_create_chat_model()` helper | Extract shared helper, reuse in both text-only and agent paths. | DRY — avoids duplicating model creation logic across code paths. |
| 4 | Merge Steps 3 + 4 | Keep separate. | Smaller commits, easier to review individually. |
| 5 | Async strategy in Step 5 smoke tests | Dropped from plan — implementation detail, not plan-level concern. | |
| 6 | `.mcp.json` discovery + verify DRY | Verify calls `ask_llm()` with `mcp_config` for end-to-end testing (same code path as real flow). Reuse `resolve_mcp_config_path()` and `resolve_execution_dir()` from `cli/utils.py` everywhere. Remove `_smoke_test_mcp_server()` and `_verify_mcp_connectivity()` from Step 5. | DRY — verify must follow exactly the same logic as prompt to avoid misleading results. |
| 7 | MLflow logging in Step 3 | Split into a separate sub-step within Step 3 — implement agent routing first, then add MLflow logging as a follow-up commit. | Keeps the largest step manageable. |
| 8 | Tool-error recovery test | Skip — LangGraph handles this internally, not our code to test. |
| 9 | `_create_chat_model()` — backend refactor | Refactor existing backend modules to extract model creation. Update summary.md to allow backend changes. | Enables DRY shared helper properly; trivial model constructors make the refactor low-risk. |
| 10 | Agent history deserialization | Extend `_to_lc_messages()` in `_utils.py` to handle `ToolMessage` and `AIMessage` with `tool_calls`. Single deserialization path, backward compatible. | Avoids silent data loss when reloading agent sessions. |
| 11 | Drop mode marker | Remove Decision 2's mode marker (`"mode": "agent"/"text"`). Extended `_to_lc_messages()` handles all message types — no marker needed. | Simplifies storage; one deserialization path for both modes. |
| 12 | `pytest-asyncio` config | Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in pyproject.toml, in Step 1. | Step 2 uses `@pytest.mark.asyncio` — needs this config to collect async tests. |
| 13 | Verify CLI flags | Just `--mcp-config <path>`. Package checks always run for langchain. Smoke test runs only when path provided. Add `cli/parsers.py` to Step 5 file list. | One flag, simple. No flag = packages only. |
| 14 | Conftest sub-module mocking | Explicitly mock `langchain_mcp_adapters.client` and `langgraph.prebuilt` sub-modules in Step 1's conftest changes. | `agent.py` imports from sub-modules; top-level mocks alone are insufficient. |
| 15 | LangChain native serialization | Use LangChain's native `.dict()` / `messages_from_dict()` for session history storage. Drop Decision 10 (`_to_lc_messages()` extension). Don't migrate old sessions — they start fresh. Leave Claude CLI format untouched. | LangChain already has full-fidelity serialization; no need to maintain custom parsing for tool messages. Supersedes Decisions 2, 10, 11. |
| 16 | `create_model()` signatures in plan | Add explicit `create_model()` function signatures for each backend in Step 3. | More guidance for the implementer; the refactor touches 3 backend files. |
| 17 | No round-trip serialization test | Don't add tests for LangChain's native serialization round-trip. | Trust LangChain's own library tests; less custom code = less custom tests. |
| 18 | `_check_agent_dependencies()` location | Move `_check_agent_dependencies()` to `agent.py` instead of `__init__.py`. | Keeps all agent-related code together; `__init__.py` just calls it. |
| 19 | Full tool results in `tool_trace` | Keep full tool results in `tool_trace` — no truncation. | More useful for debugging. |
