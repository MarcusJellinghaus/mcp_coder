# Step 3 — `docs/environments/environments.md`: update the `MCP_TIMEOUT` row

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`). Implement
> Step 3 only: replace the `MCP_TIMEOUT` row in `docs/environments/environments.md` as
> described below. Do not add a separate row for `CLAUDE_CODE_MCP_STARTUP_WAIT_MS`. Run the
> standard checks and commit as one commit.

## WHERE

`docs/environments/environments.md`: the `MCP_TIMEOUT` table row (currently line 33).

## WHAT

Replace the row with:

```
| `MCP_TIMEOUT` | `30000` (ms) | MCP server startup timeout for Claude CLI, so cold-start servers are not marked failed; in `-p` mode it also bounds how long the CLI waits for MCP servers before the first turn (`CLAUDE_CODE_MCP_STARTUP_WAIT_MS` overrides that wait; not set in production) | `claude_settings.py`, `env.py`, `command_templates.py`, `session_setup.py` (vscodeclaude), batch launchers | Claude CLI |
```

Changes compared with the current row:
- "raises the default 5 s window" is removed.
- The `-p` pre-turn wait and the `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` override are added.
- "Set by": `templates.py` (vscodeclaude) → `session_setup.py` (vscodeclaude). The actual
  setter is `src/mcp_coder/workflows/vscodeclaude/session_setup.py`.

Keep the column count (5) and the other columns unchanged.

## HOW / ALGORITHM / DATA

Not applicable (documentation only).

## TDD note

Docs-only change. No test to write.

## Verification

- Before editing, confirm `src/mcp_coder/workflows/vscodeclaude/session_setup.py` sets
  `env["MCP_TIMEOUT"]`. If it does not, write one line to `pr_info/.blocked.txt` and stop.
- `mcp__mcp-workspace__search_files` with pattern `5 s window|templates.py\` \(vscodeclaude\)`
  in `docs/`: no match.
- `run_pylint_check`, `run_mypy_check`, fast unit suite via `run_pytest_check` with
  `-n auto` and the non-integration marker filter from CLAUDE.md (expected unaffected).
- `run_format_code`, then commit.

## Commit

`docs(environments): describe MCP_TIMEOUT pre-turn wait, fix vscodeclaude setter (#1267)`
