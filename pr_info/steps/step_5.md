# Step 5 — Slow-MCP-stub integration: v1 self-heal + v2 clean-failure

**Goal:** prove end-to-end that a `pending` server self-heals via `ToolSearch`
(v1) and a never-connecting server fails cleanly without hallucinated tool
results (v2). This is the acceptance proof the unit tests cannot give. (D5)

## TDD (red → green)
- v1 is the headline red→green: it **fails under `--tools ""`** (no real tool
  call) and **passes after the Step 1 fix** (`ToolSearch` → real `tool_use`).
  Since Step 1 already landed, verify v1 red by temporarily reverting the flag
  locally (or assert on captured init/tool events that prove the bridge fired),
  then green with the flag restored. Record the observation.

## WHERE
- New stub: `tests/llm/providers/claude/_mcp_stub_server.py` (throwaway MCP server).
- New tests: `tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py`
- Marker: `claude_cli_integration` (run via the integration marker, not the fast
  suite). Pattern reference: `test_claude_integration.py`,
  `tests/integration/test_mcp_config_integration.py`.

## WHAT — the stub MCP server
A minimal stdio MCP server exposing ONE tool that returns a **sentinel the model
cannot guess** (random/unique string written to a temp file, passed in via env so
the test knows the expected value). A startup delay is configurable via env
(e.g. `MCP_STUB_STARTUP_DELAY_SECONDS`) so the server's `initialize` is slow:
- **v1:** delay `> 5 s` (past the `alwaysLoad` cap) but `< MCP_TIMEOUT` → `pending`
  at init, connects shortly after.
- **v2:** delay `> MCP_TIMEOUT` (or never responds) → never connects.

Generate a test `.mcp.json` in a `tmp_path` registering the stub via the current
Python interpreter (`sys.executable`), with `alwaysLoad: true` to mirror prod.

## HOW — driving the run
- Call the real CLI through `ask_claude_code_cli` (blocking) and/or
  `ask_claude_code_cli_stream`, pointing `mcp_config` at the temp `.mcp.json`,
  `cwd` at `tmp_path`. Skip cleanly if the `claude` executable isn't found.
- Capture the stream-json log for assertions.

## DATA / ASSERTIONS
- **init.tools assertion (acceptance):** parse the init event — `tools` includes
  `ToolSearch`, excludes `Bash/Edit/Read/Write`; the stub MCP tool is present in
  the MCP tool list.
- **v1:** stub started `pending`; the session contains a real `tool_use` for the
  stub tool whose result equals the sentinel; the final text contains the
  sentinel; **no** fabricated tool blocks. (Connected control run, if added,
  calls the tool directly without `ToolSearch`.)
- **v2:** run fails cleanly (raises / error event); assert the sentinel does
  **not** appear and there is no hallucinated tool result. If v2 *does* show a
  hallucinated result, add a result-time backstop (scan final assistant text for
  fabricated tool-call markers and fail) — otherwise none needed. (D5)

## Notes
- Keep the stub tiny and self-contained; no third-party deps beyond the MCP SDK
  already used by the project's servers.
- Mark slow; these are excluded from the default fast suite.

## LLM prompt
> Implement Step 5 from `pr_info/steps/summary.md`. Build the slow-MCP stub and
> the v1 (self-heal) and v2 (never-connects) `claude_cli_integration` tests per
> D5, including the init.tools acceptance assertion. Use a unguessable sentinel.
> Confirm v1 demonstrates a real ToolSearch-mediated tool call; confirm v2 fails
> cleanly with no hallucination (add a backstop only if needed). First check the
> repo for any reusable stub/harness and build on it.
