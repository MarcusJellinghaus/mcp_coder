# Task Tracker — Issue #999

Restore the ToolSearch wait-bridge to fix the headless MCP cold-start race.
Branch: `999-restore-toolsearch-wait-bridge`.

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder
- TDD per D-TDD: record red→green observation when ticking a task.

---

## Tasks

- [x] Step 1 — Emit `--tools "ToolSearch"` ([steps/step_1.md](steps/step_1.md)) — red: 4 flag tests + mcp_config test asserted `--tools ''` (`'' != 'ToolSearch'`); green: flipped `CLAUDE_BUILTIN_TOOLS` to `"ToolSearch"`, all pass
- [x] Step 2 — Guard module: `find_fatal_mcp_servers`, dict types, drop retry machinery ([steps/step_2.md](steps/step_2.md)) — red: guard tests `ImportError: cannot import name 'find_fatal_mcp_servers'`; green: added `find_fatal_mcp_servers`, switched both finders + `McpServersUnavailableError` to `dict[str, str]`, removed retry machinery (constants/`_MCP_RETRYABLE_STATUSES`/`mcp_failure_is_retryable`). Call sites kept importable via `.items()` + single-attempt fatal stopgap (TODO step-3); deleted obsolete `TestMcpFailureIsRetryable`/`TestMcpRetryInAskClaude`. 19 guard tests + full unit suite pass
- [x] Step 3 — Blocking path: single attempt, fatal-only guard ([steps/step_3.md](steps/step_3.md)) — red: `test_pending_only_succeeds_single_attempt` failed (stopgap aborted on pending-only init with `McpServersUnavailableError`); green: collapsed `while True` retry loop to a single attempt, switched guard to `find_fatal_mcp_servers` (abort only on fatal), info-log pending via `find_unavailable_mcp_servers`, removed `TODO(step-3)`. 21 guard tests + full unit suite pass
- [x] Step 4 — Streaming path: fatal-only guard, tolerate pending ([steps/step_4.md](steps/step_4.md)) — red: inverted `test_stream_aborts_on_pending_init` → `test_stream_pending_init_proceeds`; failed because the streaming init guard aborted on pending-only init with `McpServersUnavailableError`; green: switched streaming guard to `find_fatal_mcp_servers` (abort only on fatal), info-log pending via `find_unavailable_mcp_servers`, deleted the "intentional asymmetry" comment so blocking == streaming (D4). Added `test_stream_aborts_on_fatal_despite_thinking` (#998 intent), dropped stale `mcp-workspace=pending` assertion. 22 guard tests + full unit suite pass
- [x] Step 5 — Slow-MCP-stub integration: v1 self-heal + v2 clean-failure ([steps/step_5.md](steps/step_5.md)) — PASSED (claude v2.1.177 present). Built FastMCP stdio stub `_mcp_stub_server.py` (one `reveal_sentinel` tool; sentinel + startup delay via env). Stub goes `pending` by sleeping `MCP_STUB_STARTUP_DELAY_SECONDS` before `mcp.run()`. v1 (8s delay, MCP_TIMEOUT=60s): stub `pending` at init, model used ToolSearch wait-bridge then a real `mcp__mcp-stub__reveal_sentinel` tool_use whose result + final text carry the unguessable sentinel; init.tools has `ToolSearch`, excludes Bash/Edit/Read/Write. v2 (30s delay, MCP_TIMEOUT=3s): never connects → run fails cleanly, sentinel absent, no hallucinated tool_result (no extra backstop needed beyond the unguessable-sentinel scan). Permission gate solved via a temp settings file allowing the stub tool. red→green: temporarily reverted `CLAUDE_BUILTIN_TOOLS=""` → v1 failed `ToolSearch missing from init tools: []`; restored `"ToolSearch"` → green. Both integration tests pass; full fast unit suite (4083) + format/pylint/mypy/ruff green.
- [x] Step 6 — Confirm settings + full quality gates ([steps/step_6.md](steps/step_6.md)) — settings confirmed (no ToolSearch deny / no ENABLE_TOOL_SEARCH=false); dead-ref sweep: 0 hits in src/ and tests/ for all 4 removed symbols; vulture: only the FastMCP stub tool `reveal_sentinel` (false positive, MCP-invoked); format/ruff/pylint/mypy/lint-imports all green; fast suite 4083 passed / 2 skipped; Step 5 cold-start integration (the #999 acceptance tests) 2 passed (claude v2.1.177). Remaining `claude_cli_integration` failures (test_llm_sessions, test_execution_dir_integration) are pre-existing on main — those files untouched by this branch.

## Acceptance criteria (from issue #999)

- [x] `CLAUDE_BUILTIN_TOOLS = "ToolSearch"`; init.tools includes `ToolSearch`, excludes `Bash/Edit/Read/Write`; MCP tools still load
- [x] Slow-stub v1: red under `--tools ""`, green after fix (`ToolSearch` → real `tool_use`)
- [x] Slow-stub v2 (never connects): clean failure, no hallucinated tool results
- [x] Guard: `pending` no longer aborts/retries; `failed` still fails fast; blocking and streaming consistent
- [x] `.claude/settings.local.json` confirmed not to disable tool search / deny `ToolSearch`

## Pull Request

- [ ] PR summary
- [x] Code review — 2 rounds via `/implementation_review_supervisor`; round 1 fixed 3 minors (stale comment, pending-scan ordering notes, dead test assertion, commit `7e001ba`), round 2 clean; vulture + lint-imports clean; log `implementation_review_log_1.md`
