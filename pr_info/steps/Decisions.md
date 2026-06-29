# Decisions — Issue #999

Decisions taken with the user during discussion (`/discuss`). Only logged
decisions actually discussed are recorded here.

## D1 — Guard shape: add `find_fatal_mcp_servers`, keep `find_unavailable_mcp_servers`
**Discussed:** yes (user chose "Add find_fatal_mcp_servers").
Introduce a new predicate `find_fatal_mcp_servers(system_message)` that returns
only servers whose status is **neither `connected` nor `pending`** (e.g.
`failed`/`unknown`). Keep `find_unavailable_mcp_servers` (all non-connected) so
`pending` servers can still be surfaced in logs without aborting. Cleaner
separation between "fatal" and "still starting" than repurposing one function.

## D2 — Carried data + message use a `dict {name: status}`
**Discussed:** yes (user proposed a dict; asked for the cleanest variant).
Both finders return `dict[str, str]` (server name → status) for a consistent
shape across the module (a dict naturally dedupes by name and formats well).
`McpServersUnavailableError.unavailable_servers` becomes `dict[str, str]` and
carries **only the fatal servers**. Pending servers are logged separately at
info level, not put in the abort error. Updating
`find_unavailable_mcp_servers`'s existing assertions from `[(name, status)]` to
`{name: status}` is mechanical and accepted for consistency.

## D3 — Drop the #998 bounded retry; `pending` is non-fatal
**Discussed:** yes (core of the issue, confirmed direction).
With `ToolSearch` restored, a `pending` server recovers within the same session,
so abort-and-retry would kill runs that would have succeeded. Remove
`MCP_UNAVAILABLE_MAX_RETRIES`, `MCP_UNAVAILABLE_RETRY_WAIT_SECONDS`,
`_MCP_RETRYABLE_STATUSES`, `mcp_failure_is_retryable`, and the blocking-path
retry loop (collapse to a single attempt). `failed`/terminal stays fatal.

## D4 — Path parity (blocking == streaming)
**Discussed:** yes.
Both paths use the same guard: tolerate `pending`, abort on fatal. Remove the
current "intentional asymmetry" where streaming fails fast on `pending`.

## D5 — Full, clean solution in this PR (build the slow-MCP stub now)
**Discussed:** yes (user: "I want a full and clean solution in this PR").
Build the slow-MCP stub and both integration scenarios in this PR rather than
deferring to a follow-up:
- **v1** (slow connect, `>5 s` cap but `< MCP_TIMEOUT`) → `pending` at init →
  model uses `ToolSearch` → real `tool_use` with correct result. Red under
  `--tools ""`, green after the fix.
- **v2** (never connects, `> MCP_TIMEOUT`) → run fails cleanly, **no hallucinated
  tool results**. Add a result-time backstop only if v2 shows hallucination.

## D6 — Keep `alwaysLoad: true`
**Discussed:** referenced from the issue, not contested.
`alwaysLoad` (5 s cap) and `ToolSearch` complement; do not drop.

## D-TDD — Verify each test is red before green
**Discussed:** yes (user: "follow TDD to verify the test").
For every step, the new/changed test must be executed and observed **failing for
the intended reason** before the source change, then observed **passing** after.
Record the red→green observation in the task tracker as each task is completed.
