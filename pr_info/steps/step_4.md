# Step 4 — Streaming path: fatal-only guard, tolerate pending

**Goal:** `ask_claude_code_cli_stream` tolerates `pending` (proceeds and yields
content) and aborts only on fatal MCP states — matching the blocking path (D4).

## TDD (red → green)
1. Invert the streaming guard test first: pending-only must now proceed and yield
   `text_delta`; run — **red** against the current fail-fast-on-pending code.
2. Implement; re-run — **green**.

## WHERE
- Src: `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`
  (init-event guard ~152-173; import ~25).
- Tests: `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`

## WHAT
- Import `find_fatal_mcp_servers` (replace `find_unavailable_mcp_servers` use).
- In the `msg.get("type") == "system"` branch: `fatal = find_fatal_mcp_servers(msg)`;
  if `fatal`: log + `raise McpServersUnavailableError(msg_text, unavailable_servers=fatal)`.
- Delete the "intentional asymmetry" comment (167-170) — both paths now identical.
- Optional: info-log pending via `find_unavailable_mcp_servers(msg)` before
  continuing.

## HOW
- The init/`thinking_tokens` capture (#998) is handled in `_parse_stream_lines`
  for the blocking path; the streaming path inspects each `system` message live,
  so the guard simply runs on every `system` event and only fatal raises.

## DATA
Yields the existing `StreamEvent` dicts; raises `McpServersUnavailableError`
(carrying the fatal dict) only on terminal states.

## Tests to change (streaming section)
- `TestMcpServerGuardInStream.test_raises_when_server_failed` (237): failed+pending
  → keep (raises because failed is fatal); assert message names the failed server.
- `TestStreamMcpGuard.test_stream_aborts_on_pending_init` (488): **invert** →
  rename `test_stream_pending_init_proceeds`: init pending-only + trailing
  `thinking_tokens` + assistant text → assert it yields the `text_delta` and does
  **not** raise.
- **Add** a fatal-despite-thinking case: init `failed` followed by
  `thinking_tokens` still aborts (keeps the #998 regression intent).

## LLM prompt
> Implement Step 4 from `pr_info/steps/summary.md`. Test-first per D-TDD. Switch
> the streaming init guard to `find_fatal_mcp_servers`, tolerate pending, remove
> the asymmetry comment (D4). Invert/add the streaming guard tests; confirm
> red→green.
