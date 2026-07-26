# Step 1 — Layer 1: treat `needs-auth` as non-fatal in the MCP guard

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_1.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` (log message only, ~lines 190–197)
- Tests: `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`

## WHAT

1. New public module constant in `claude_mcp_guard.py`:
   ```python
   # An account-level claude.ai connector that has not completed OAuth. Optional
   # by definition (tied to the login, not any config), so never fatal.
   MCP_NEEDS_AUTH_STATUS = "needs-auth"
   ```
2. `_scan_mcp_servers(system_message, *, tolerate_pending: bool)` — **signature unchanged**. When `tolerate_pending=True`, skip `needs-auth` in addition to `pending`. (`find_unavailable_mcp_servers` uses `tolerate_pending=False` and must keep reporting `needs-auth` servers with their status, so reporting consumers can see them.)
3. Update docstrings: `_scan_mcp_servers`, `find_fatal_mcp_servers`, `McpServersUnavailableError`, and the `_MCP_PENDING_STATUS` block comment — terminal means "non-connected, non-pending, non-needs-auth".
4. In `ask_claude_code_cli_stream`, replace the single "still starting; ToolSearch will wait" log with a partition of `find_unavailable_mcp_servers(msg)` by status:
   - `pending` entries → existing info log ("still starting; ToolSearch will wait").
   - `needs-auth` entries → separate info log, e.g. `"Unauthenticated account connector(s) (not part of configured-server health): %s"` — they must NOT be described as starting.

## HOW

- `claude_code_cli_streaming.py` already imports from `.claude_mcp_guard`; add `MCP_NEEDS_AUTH_STATUS` to that import.
- Optionally add `MCP_NEEDS_AUTH_STATUS` to the re-export list in `claude_code_cli.py` for consistency with the other guard names (keep `__all__` sorted).

## ALGORITHM (`_scan_mcp_servers` inner loop change)

```
status = normalized server status (lowercased, "unknown" fallback)  # unchanged
if status == connected: skip                                        # unchanged
if tolerate_pending and status in (pending, needs-auth): skip       # was: == pending
else: record name -> status
```

## DATA

- `find_fatal_mcp_servers` returns `{name: status}` **excluding** `connected`, `pending`, `needs-auth`.
- `find_unavailable_mcp_servers` unchanged: everything non-`connected`, including `needs-auth`.

## TESTS (write first)

In `test_claude_cli_stream_mcp_guard.py`:
- `find_fatal_mcp_servers` on an init event with servers `{a: connected, b: pending, c: needs-auth}` → `{}`.
- Same event plus `{d: failed}` → `{"d": "failed"}` (still fatal).
- `find_unavailable_mcp_servers` on that event still includes `c: needs-auth`.
- Streaming test (follow the file's existing mocked-subprocess pattern): an init event whose only non-connected servers are `needs-auth` connectors does NOT raise `McpServersUnavailableError`; one with a `failed` server still raises.
- Reproduce the incident event shape: `obsidian-wiki=pending` + three `claude.ai *=needs-auth` → no raise.

## Commit

`fix: treat needs-auth MCP servers as non-fatal in the availability guard (#1090)`
