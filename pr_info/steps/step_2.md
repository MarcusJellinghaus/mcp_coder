# Step 2 — Stub server docstring: drop the "~5 s `alwaysLoad` cap" wording

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`). Implement
> Step 2 only: update the module docstring of
> `tests/llm/providers/claude/_mcp_stub_server.py` as described below. Docstring only, no
> code change. Run the standard checks and commit as one commit.

## WHERE

`tests/llm/providers/claude/_mcp_stub_server.py`: module docstring, the
`MCP_STUB_STARTUP_DELAY_SECONDS` bullet (currently lines 11–15).

## WHAT

Replace the bullet text from "The sleep runs before ..." to the end of that bullet with:

```
  starts serving. The sleep runs before ``mcp.run()`` connects stdio, so the
  server's ``initialize`` is delayed. The Claude CLI reports it ``pending`` at
  the init event when its pre-turn wait for MCP servers (bounded by
  ``MCP_TIMEOUT``, overridable via ``CLAUDE_CODE_MCP_STARTUP_WAIT_MS``) ends
  before the delay does. A delay exceeding ``MCP_TIMEOUT`` means the server
  never connects in time.
```

Leave the rest of the docstring and all code unchanged.

## HOW / ALGORITHM / DATA

Not applicable (documentation only).

## TDD note

Docstring-only change. No test to write. Existing tests must stay green.

## Verification

- `run_pylint_check`, `run_mypy_check`, fast unit suite via `run_pytest_check` with
  `-n auto` and the non-integration marker filter from CLAUDE.md.
- `mcp__mcp-workspace__search_files` with pattern `5 s` in this file: no match.
- `run_format_code`, then commit.

## Commit

`docs(tests): describe current CLI MCP wait in cold-start stub docstring (#1267)`
