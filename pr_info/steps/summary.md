# Summary — Issue #916: iCoder Claude Code streaming fix (mcp-coder side)

## Context

`stream_subprocess()` in `mcp-coder-utils` previously ignored `options.input_data` —
it never set `stdin=subprocess.PIPE` and never wrote input data to the process.
This broke `ask_claude_code_cli_stream()` and, transitively, iCoder when the
Claude provider was used: prompts never reached the CLI subprocess.

The fix lives upstream in `mcp-coder-utils` (PR #26, merged). This issue covers
the **mcp-coder side** only:

1. Bump the `mcp-coder-utils` dependency to a release containing the fix.
2. Add real-CLI integration tests for the streaming path that was never previously
   exercised end-to-end.
3. Rename a misleadingly-named existing test file.

## Architectural / design changes

**None.** This issue does not change architecture, public APIs, or module layout.
It bumps a dependency and adds tests. The streaming pipeline
(`prompt_llm_stream` → `ask_claude_code_cli_stream` → `stream_subprocess`)
already exists; it just lacked real-CLI test coverage, which is why the
upstream regression went undetected.

## Test-layering decisions (preserved from issue)

- **Session continuity** is tested only at the lowest layer
  (`ask_claude_code_cli_stream`) — not duplicated at higher layers.
- **`prompt_llm_stream` test** verifies events flow through, no content/session
  assertions (already covered below).
- **iCoder smoke test** verifies a single call: events arrive and `session_id`
  is populated.
- **Error-path branches** (timeout, non-zero exit) remain unit-tested with
  mocks; real-CLI integration covers happy path only.

## Files to create / modify

### Modify
- `pyproject.toml` — bump `mcp-coder-utils>=0.1.3` to the version containing
  upstream PR #26.
- `tests/icoder/test_llm_service.py` — add one new smoke test
  (`@pytest.mark.claude_cli_integration`).

### Rename
- `tests/llm/providers/claude/test_claude_cli_stream_integration.py`
  → `tests/llm/providers/claude/test_claude_cli_stream_logging_integration.py`
  (no content change; existing file actually tests stream-json file logging
  via the non-streaming `ask_claude_code_cli`).

### Create
- `tests/llm/providers/claude/test_claude_code_cli_streaming_integration.py`
  — 3 integration tests exercising `ask_claude_code_cli_stream` and
  `prompt_llm_stream(provider="claude")` against the real Claude CLI.

### No changes (intentionally)
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — fix is
  upstream.
- `src/mcp_coder/icoder/services/llm_service.py` — already correct.

## Steps

1. **step_1.md** — Bump `mcp-coder-utils` dependency.
2. **step_2.md** — Rename existing stream-logging test file.
3. **step_3.md** — Add real-CLI streaming integration tests
   (`test_claude_code_cli_streaming_integration.py`).
4. **step_4.md** — Add iCoder `RealLLMService.stream()` smoke test.

## Outstanding input needed

- Exact `mcp-coder-utils` release version that contains PR #26 (placeholder
  used in step 1; replace with concrete version before applying).

## Manual verification (post-merge, operator's task — not automated)

Run iCoder with the Claude provider:
1. Send: "Remember: my favorite color is blue. Reply 'noted'."
2. Send (same session): "What is my favorite color?"
3. Confirm response references "blue" (proves session resumed via streaming
   subprocess stdin path).
