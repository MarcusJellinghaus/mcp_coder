# Issue #830 — Fix misleading WinError 2 diagnostics on Windows

## Goal

On Windows, `mcp-coder verify` and `mcp-coder prompt` currently surface
`[WinError 2] The system cannot find the file specified` in ways that hide
the real cause:

- **verify** prints only `str(exc)` — no path, no class name.
- **prompt** reclassifies the local launch failure as a remote API /
  SSL / truststore problem, because `FileNotFoundError ⊂ OSError` and
  `OSError` is in `CONNECTION_ERRORS`.
- Both paths print `pip install 'mcp-coder[truststore]'` with single quotes
  that are literal in `cmd.exe`.

## Architectural / design changes

1. **Narrow `CONNECTION_ERRORS`** in
   `src/mcp_coder/llm/providers/langchain/_exceptions.py` to real network
   types only (`httpx.ConnectError`, `httpx.ConnectTimeout`, `ConnectionError`;
   fallback `(ConnectionError,)`). This stops `FileNotFoundError` /
   `PermissionError` / any other `OSError` from masquerading as a remote
   connection failure.

2. **Introduce `LLMMCPLaunchError(Exception)`** in the same module. It
   inherits from `Exception` directly (not `ConnectionError`) and is **not**
   in `CONNECTION_ERRORS`, so `_handle_provider_error` passes it through
   unchanged.

3. **Wrap MCP subprocess-launch failures at source** in
   `src/mcp_coder/llm/providers/langchain/agent.py`. Both `run_agent` and
   `run_agent_stream` catch `FileNotFoundError` and `PermissionError` at
   `client.session(server_name)` and re-raise as `LLMMCPLaunchError` with
   the resolved command path and the original class name.

4. **Pre-flight each server in `verify`** in
   `src/mcp_coder/llm/providers/langchain/verification.py`. Before the
   async launch:
     - scan `command`, `args`, and `env` values for `${VAR}` residue;
     - `shutil.which(resolved_command)` check (covers both absolute paths
       and PATH-resolved bare executables like `python` / `npx`).
   Distinct, actionable messages: `unresolved placeholder ${…}` vs
   `binary not found at <path>`. If pre-flight passes but launch still
   fails, include the resolved path and exception class name in the
   reported message.

5. **SSL hint becomes classification-gated.** `_SSL_HINT` is appended only
   when `classify_connection_error(original).startswith("ssl-error")`.
   The duplicate truststore hint in `format_diagnostics` is removed.
   Install hint changes from `pip install 'mcp-coder[truststore]'` to
   `pip install mcp-coder[truststore]` (pastable in cmd, PowerShell, bash,
   zsh).

### What is explicitly not changing

- `verify.py` and `prompt.py` CLI error formatting — the new
  `LLMMCPLaunchError.__str__` already produces a clean one-liner that their
  existing generic handlers print as-is.
- No new helpers or abstractions for one-time operations.
- `TimeoutError` stays out of the narrowed tuple (flagged for future
  non-httpx paths). Grep confirmed: no existing test under
  `tests/llm/providers/langchain/` relies on `TimeoutError` being
  classified as a connection error.

## Files to modify

Production:
- `src/mcp_coder/llm/providers/langchain/_exceptions.py`
- `src/mcp_coder/llm/providers/langchain/agent.py`
- `src/mcp_coder/llm/providers/langchain/verification.py`

Tests:
- `tests/llm/providers/langchain/test_langchain_exceptions.py`
- `tests/llm/providers/langchain/test_langchain_diagnostics.py`
- `tests/llm/providers/langchain/test_langchain_agent.py`
- `tests/llm/providers/langchain/test_mcp_health_check.py`

No new folders, modules, or files are created. No CLI command files are
touched.

## Acceptance criteria (mirrored from the issue)

- `mcp-coder verify` names the resolved binary path on failure and
  distinguishes unresolved `${VAR}` from missing-binary.
- `mcp-coder prompt` does not mention "OpenAI API" or SSL/truststore for a
  local MCP subprocess-launch failure.
- `pip install mcp-coder[truststore]` printed by the CLI pastes into
  cmd.exe, PowerShell, and bash/zsh unchanged.
- Tests: `_handle_provider_error` does not rewrap `FileNotFoundError` or
  `PermissionError`; `CONNECTION_ERRORS` no longer contains bare `OSError`;
  SSL hint is absent for non-SSL classifications; `format_diagnostics`
  emits no truststore hint.

## Step order

All three steps are self-contained and each is a single commit.

1. **Step 1 — `_exceptions.py`**: narrow `CONNECTION_ERRORS`, add
   `LLMMCPLaunchError`, gate SSL hint on classification, remove duplicate
   truststore hint, un-quote pip install. Tests updated / added.
2. **Step 2 — `agent.py`**: wrap `FileNotFoundError` / `PermissionError`
   from `client.session(server_name)` as `LLMMCPLaunchError` in both
   `run_agent` and `run_agent_stream`. Tests added.
3. **Step 3 — `verification.py`**: add `_preflight_mcp_server` and use it
   in `_check_servers`; classify `${VAR}` residue and missing-binary
   cases; include resolved path + class name on launch-error fallback.
   Tests updated / added.

Step 2 depends on `LLMMCPLaunchError` from Step 1. Step 3 is independent
of Steps 1 and 2 but ordered last for cohesion (user-visible diagnostics
polish).
