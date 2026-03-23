# Decisions — Issue #543 (Extended)

## Original Decisions (Steps 1–4)

See summary.md for the original decision table.

## Code Review Decisions (Round 1–2)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| sqlite3.Error handling | Wrap `query_sqlite_tracking()` in try/except in `verify_mlflow()` | Prevents crash on corrupt DBs |
| Exit code consolidation | `test_prompt_ok` parameter added to `_compute_exit_code()` | Single place for all exit code logic |
| Test prompt exit code scope | `test_prompt_ok=False` → exit 1 regardless of MLflow state | LLM provider failure should never produce exit 0 |
| `since=` in verify | Removed — test prompt doesn't log to MLflow via current path | False negative: `ask_llm()` doesn't trigger `_log_to_mlflow()` |

## Extended Decisions (Steps 5–8)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LangChain text-mode MLflow logging | Add `_log_text_mlflow()` in `_ask_text()`, mirroring `_log_agent_mlflow()` | Text mode is the most common LangChain path; must be visible in MLflow |
| Verify test prompt logging | Use `prompt_llm()` + `_log_to_mlflow()` instead of `ask_llm()` | Need full `LLMResponseDict` to call `_log_to_mlflow()`; confirms logging works end-to-end |
| Restore `since=` in verify | Yes, after test prompt logs to MLflow | DB-level confirmation that logging pipeline works |
| MCP server health check | Per-server connectivity test via `MultiServerMCPClient.session()` + `list_tools()` | Users need to know which server is broken, not just "something failed" |
| MCP server check location | New function in `verification.py` called from `execute_verify()` | Keeps verify orchestration in `verify.py`, domain logic in provider module |
| MCP server check scope | Connect, list tools, disconnect — no agent execution | Fast (~100-500ms/server), no LLM cost, isolates server issues from LLM issues |
| `_log_to_mlflow` reuse | Import from `prompt.py` into `verify.py` | Avoid duplicating MLflow logging logic; single source of truth |

## Plan Update Decisions (Steps 5–8 refinement)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Run lifecycle note (step 5) | Document that `_log_text_mlflow()` starts/ends run, then `_log_to_mlflow()` resumes via `has_session()` | Same lifecycle as agent mode; makes the two-phase pattern explicit |
| Rename `_log_to_mlflow` → `log_to_mlflow` (step 6) | Remove leading underscore, make it a public function | Imported cross-module (from `prompt.py` into `verify.py`); private convention is misleading |
| `project_dir` derivation (step 6) | `Path(args.project_dir).resolve() if args.project_dir else Path.cwd()` | Consistent resolution of project directory |
| E2E test moved to step 6 (from step 8) | Verify/fix `test_verify_llm_integration.py` as part of step 6 | It directly tests the prompt→MLflow pipeline changed in step 6 |
| `verify_mcp_servers` no `env_vars` (step 7) | Pass no `env_vars` — config loader merges with `os.environ` by default | Simpler API; avoid redundant parameter |
| `_compute_exit_code` extended (step 7) | Add `mcp_result: dict[str, Any] | None = None` parameter | MCP failures must affect exit code |
| Hide MCP section when no servers (step 7) | No output at all when no servers configured | Avoid noisy empty sections |
| Step 8 scope reduced | MCP server integration test only (E2E moved to step 6) | Cleaner separation of concerns |
| MCP integration test marker (step 8) | `@pytest.mark.langchain_integration`, skip if no `.mcp.json` | Uses project's own config; skips gracefully in CI |
