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
| 8 | Tool-error recovery test | Skip — LangGraph handles this internally, not our code to test. | |
