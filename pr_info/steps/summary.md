# Summary — #1267: Cold-start v1 test: restore `pending` at init via `CLAUDE_CODE_MCP_STARTUP_WAIT_MS`

## Problem

`test_v1_pending_server_self_heals_via_toolsearch` (`claude_cli_integration`) fails on
Claude CLI 2.1.304 / 2.1.308 with `expected stub 'pending' at init, got 'connected'`.
Older CLIs stopped waiting for `--mcp-config` servers after 5 s in `-p` mode. Current CLIs
wait until the server connects (bounded by `MCP_TIMEOUT`), so the 8 s stub is already
`connected` when `init` arrives and the test never reaches the "pending at init" state it is
meant to check.

## Fix (test + docs only)

- v1 passes `CLAUDE_CODE_MCP_STARTUP_WAIT_MS=3000` to the CLI, which caps the wait before
  the first turn, so the stub is `pending` at `init` again.
- The v1 stub delay goes from 8 s to 20 s. Even with the 3 s cap, `init` was seen after
  ~9 s, so 8 s left almost no margin.
- If `init` still reports `connected` (a CLI that ignores the setting), v1 calls
  `pytest.skip` with the observed status in the reason. Any other status still fails.
- Comments and docs that describe the old 5 s limit are rewritten.

## Architectural / design changes

None. Production code, the `ToolSearch` wait-bridge, the MCP guard and v2 are unchanged.
The #999 mechanism stays as a safety net. The design decisions inside the test are:

- **Skip criterion = observed `init` status, not CLI version.** The exact CLI version that
  changed the behaviour is unknown. A check on the observed status also stays correct if
  the CLI default changes again.
- **The env override is test-only.** Production does not set
  `CLAUDE_CODE_MCP_STARTUP_WAIT_MS`. Docs mention it only inside the `MCP_TIMEOUT` row.
- **KISS.** The value `"3000"` is written inline next to `"MCP_TIMEOUT": "60000"`. There is
  no new constant, helper or unit test. The skip branch is three lines placed before the
  existing assertion.

## Files modified

| File | Change |
|---|---|
| `tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py` | v1: env var, delay 8 → 20 s, rewritten delay comment, `connected` → skip |
| `tests/llm/providers/claude/_mcp_stub_server.py` | Module docstring: replace "~5 s `alwaysLoad` cap" wording |
| `docs/environments/environments.md` | `MCP_TIMEOUT` row: new description; "Set by" `templates.py` → `session_setup.py` (vscodeclaude) |

No files or folders are created (apart from these plan files).

## Steps

1. [step_1.md](./step_1.md): v1 test fix, verified by an end-to-end real-CLI run
2. [step_2.md](./step_2.md): stub server docstring
3. [step_3.md](./step_3.md): `MCP_TIMEOUT` row in `docs/environments/environments.md`
