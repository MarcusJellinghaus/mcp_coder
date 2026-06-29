# Step 2 — Guard module: `find_fatal_mcp_servers`, dict types, drop retry machinery

**Goal:** the guard distinguishes *fatal* (abort) from *still-starting* (tolerate),
carries a `dict {name: status}`, and no longer contains retry machinery.

## TDD (red → green)
1. Write `TestFindFatalMcpServers` and the dict-return assertions first; run —
   **red** (function missing / wrong return shape).
2. Implement; re-run — **green**.

## WHERE
- Src: `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`
  (re-exported by `claude_code_cli.py`).
- Tests: `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`

## WHAT
- Add constant `_MCP_PENDING_STATUS = "pending"`.
- Add `find_fatal_mcp_servers(system_message: StreamMessage | None) -> dict[str, str]`
  — servers whose status is **neither `connected` nor `pending`**.
- Change `find_unavailable_mcp_servers(...) -> dict[str, str]` (all non-connected),
  was `list[tuple[str, str]]`.  (D2)
- `McpServersUnavailableError.unavailable_servers: dict[str, str]` (was list of
  tuples); update docstring — it now means a **terminal** non-connected state.
- **Remove:** `MCP_UNAVAILABLE_MAX_RETRIES`, `MCP_UNAVAILABLE_RETRY_WAIT_SECONDS`,
  `_MCP_RETRYABLE_STATUSES`, `mcp_failure_is_retryable`. Remove them from
  `__all__` / re-exports in `claude_code_cli.py` (lines ~26-33, 50-51).

## ALGORITHM (both finders share a scan)
```
servers = system_message.get("mcp_servers") or []   # defensive: may be non-dict
result = {}
for s in servers (dict only):
    status = str(s.get("status","")).strip().lower() or "unknown"
    if status == "connected": continue
    if FATAL-variant and status == "pending": continue   # tolerate
    result[str(s.get("name","?"))] = status
return result
```

## DATA
`dict[str, str]` mapping server name → lowercased status. Empty dict = nothing to
report (no init message / no servers / all ready) — sessions without MCP
unaffected.

## Tests to change
- Imports (19-26): drop `MCP_UNAVAILABLE_MAX_RETRIES`, `mcp_failure_is_retryable`;
  add `find_fatal_mcp_servers`.
- `TestFindUnavailableMcpServers`: convert expected `[(...)]` → `{...}` (dict).
- New `TestFindFatalMcpServers`: `pending` → `{}`; `failed`/`unknown`/missing →
  reported; `connected` → `{}`; mixed `failed`+`pending` → only the failed entry.
- Delete the `mcp_failure_is_retryable` tests (363-372).

## LLM prompt
> Implement Step 2 from `pr_info/steps/summary.md`. Test-first per D-TDD. Add
> `find_fatal_mcp_servers`, switch both finders and `McpServersUnavailableError`
> to `dict[str, str]` (D2), and remove the retry machinery (D3). Update the guard
> tests accordingly; confirm red before, green after. Do not touch the call sites
> yet (Steps 3–4).
