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
- [ ] Step 4 — Streaming path: fatal-only guard, tolerate pending ([steps/step_4.md](steps/step_4.md))
- [ ] Step 5 — Slow-MCP-stub integration: v1 self-heal + v2 clean-failure ([steps/step_5.md](steps/step_5.md))
- [ ] Step 6 — Confirm settings + full quality gates ([steps/step_6.md](steps/step_6.md))

## Acceptance criteria (from issue #999)

- [ ] `CLAUDE_BUILTIN_TOOLS = "ToolSearch"`; init.tools includes `ToolSearch`, excludes `Bash/Edit/Read/Write`; MCP tools still load
- [ ] Slow-stub v1: red under `--tools ""`, green after fix (`ToolSearch` → real `tool_use`)
- [ ] Slow-stub v2 (never connects): clean failure, no hallucinated tool results
- [ ] Guard: `pending` no longer aborts/retries; `failed` still fails fast; blocking and streaming consistent
- [ ] `.claude/settings.local.json` confirmed not to disable tool search / deny `ToolSearch`

## Pull Request

- [ ] PR summary
- [ ] Code review
