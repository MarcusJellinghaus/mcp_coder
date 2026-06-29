# Step 3 — Blocking path: single attempt, fatal-only guard

**Goal:** `ask_claude_code_cli` no longer retries on `pending`; it aborts only on
fatal MCP states and logs pending servers as info.

## TDD (red → green)
1. Rewrite the blocking guard tests first (pending-only succeeds in one attempt;
   failed aborts in one attempt); run — **red** against the current retry loop.
2. Implement; re-run — **green**.

## WHERE
- Src: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
  (`ask_claude_code_cli`, the retry loop ~493-581).
- Tests: `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`

## WHAT
- Collapse the `while True` / `attempt` loop (493-581) into a single
  `execute_subprocess` call — no loop, no `time.sleep`, no `continue`.
- Replace the guard block (547-578):
  - `fatal = find_fatal_mcp_servers(parsed["system_message"])`
  - if `fatal`: build message from the dict (`name=status`, sorted/insertion
    order), `log_llm_error`, raise `McpServersUnavailableError(msg, unavailable_servers=fatal)`.
  - else: optionally `pending = find_unavailable_mcp_servers(...)`; if `pending`,
    `logger.info("MCP server(s) still starting; ToolSearch will wait: %s", pending)`.

## HOW
- Keep the existing `try/except (TimeoutExpired, CalledProcessError,
  McpServersUnavailableError)` re-raise structure (607-609).

## ALGORITHM
```
start; result = execute_subprocess(...)
handle timed_out / return_code != 0 as today
parsed = parse_stream_json_string(result.stdout)
fatal = find_fatal_mcp_servers(parsed.system_message)
if fatal: log + raise McpServersUnavailableError(dict)
else: log pending at info (if any)
return create_response_dict_from_stream(parsed, ...)
```

## DATA
Unchanged public return: response dict from `create_response_dict_from_stream`.

## Tests to change (blocking section)
- `test_raises_when_server_failed` (~155): failed+pending still raises; assert
  message contains `mcp-tools-py=failed`; pending need not appear.
- `test_succeeds_when_all_connected` (~178): keep.
- **Add** `test_pending_only_succeeds_single_attempt`: stub returns pending-only;
  assert no raise, result returned, `execute_subprocess` called once.
- Replace retry tests: delete `test_pending_then_connected_succeeds_after_retry`
  (406) and `test_pending_exhausts_retries_then_raises` (435); convert
  `test_failed_status_not_retried` (456) → `test_failed_aborts_single_attempt`
  (`call_count == 1`, no sleep).

## LLM prompt
> Implement Step 3 from `pr_info/steps/summary.md`. Test-first per D-TDD. Make
> `ask_claude_code_cli` a single attempt using `find_fatal_mcp_servers`; tolerate
> and info-log pending (D3). Update the blocking guard tests; confirm red→green.
