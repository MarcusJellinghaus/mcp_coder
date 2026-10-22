# Step 1 — v1 test: cap the CLI's MCP wait, raise the stub delay, skip on `connected`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`). Implement
> Step 1 only: change v1 in
> `tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py` exactly as
> described below. Do not touch v2, production code, or other files. Run the end-to-end v1
> + v2 integration run and the standard checks, then commit as one commit.

## WHERE

`tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py`
- module constant `_V1_STARTUP_DELAY_SECONDS` and its comment (currently lines 48–50)
- `TestClaudeMcpColdStartIntegration.test_v1_pending_server_self_heals_via_toolsearch`

## WHAT

No new functions, constants or imports (`pytest` is already imported).

1. Constant:
   ```python
   # v1: the CLI waits for MCP servers before the first ``-p`` turn (bounded by
   # MCP_TIMEOUT); v1 caps that wait via CLAUDE_CODE_MCP_STARTUP_WAIT_MS=3000. Even
   # so, init was observed ~9 s after start, so the delay must clearly exceed the
   # time until init (not just the 3 s wait) for the stub to be pending at init,
   # while staying well under MCP_TIMEOUT so it connects and self-heals in-session.
   _V1_STARTUP_DELAY_SECONDS = 20
   ```
2. In the `ask_claude_code_cli(...)` call of v1:
   ```python
   env_vars={
       "MCP_TIMEOUT": "60000",
       "CLAUDE_CODE_MCP_STARTUP_WAIT_MS": "3000",
   },
   ```
3. In the `# --- v1: stub was pending at init ---` block, put the skip right before the
   existing assertion and keep the assertion unchanged:
   ```python
   stub_status = _mcp_server_status(init_msg, "stub")
   if stub_status == "connected":
       pytest.skip(
           f"stub {stub_status!r} at init; CLI ignored "
           "CLAUDE_CODE_MCP_STARTUP_WAIT_MS, pending-at-init not reachable"
       )
   assert (
       stub_status == "pending"
   ), f"expected stub 'pending' at init, got {stub_status!r}"
   ```

## HOW

- `env_vars` reaches the CLI unchanged (`ask_claude_code_cli` → `CommandOptions(env=...)`
  → `prepare_env` overlays it on `os.environ`).
- The `init.tools` assertions stay before the status check, so they run even when the
  test skips.

## ALGORITHM

```
run CLI with MCP_TIMEOUT=60000, CLAUDE_CODE_MCP_STARTUP_WAIT_MS=3000, stub delay 20 s
assert init.tools: ToolSearch present, Bash/Edit/Read/Write absent
status = stub status at init
if status == "connected": pytest.skip(reason naming status)
assert status == "pending"
assert real tool_use, sentinel in tool_result, sentinel in final text (unchanged)
```

## DATA

No new data structures. The skip reason string contains `'connected'`.

## TDD note

The test itself is the subject of this step. The failing test already exists: on `main`
it fails with `got 'connected'`. After the change it must pass for real.

## Verification

1. End-to-end run (real Claude CLI):
   ```
   mcp__mcp-tools-py__run_pytest_check(
       markers=["claude_cli_integration"],
       extra_args=["tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py", "-v", "-rs", "--tb=short"],
   )
   ```
   - v1 must **pass** (not skip): `pending` at init, a real `tool_use`, the sentinel in a
     `tool_result` and in the final text. v2 must pass.
   - If v1 skips with `'connected'`, `init` time grows with the stub delay. Do not accept
     the skip: write one line to `pr_info/.blocked.txt` and stop.
   - If v1 fails after `pending` (no `tool_use` / no sentinel), retry once with
     `_V1_STARTUP_DELAY_SECONDS = 15`. If it still fails, write one line to
     `pr_info/.blocked.txt` and stop.
   - If both tests skip because the `claude` CLI is unavailable, write one line to
     `pr_info/.blocked.txt` and stop.
2. Standard checks: `run_pylint_check`, `run_mypy_check`, fast unit suite via
   `run_pytest_check` with `-n auto` and the non-integration marker filter from CLAUDE.md.
3. `run_format_code`, then commit.

## Commit

`test(claude): restore pending-at-init in cold-start v1 via CLAUDE_CODE_MCP_STARTUP_WAIT_MS (#1267)`
