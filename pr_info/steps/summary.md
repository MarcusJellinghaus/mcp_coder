# Issue #999 — Restore ToolSearch wait-bridge (headless MCP race)

## Problem

Under load, MCP-dependent headless Claude runs intermittently start with their
stdio MCP servers still cold-starting (`pending` at init), so the model runs
**without tools and hallucinates tool results** (e.g. `save_file` ×24 emitted as
text), then fails downstream validation.

**Root cause:** `build_cli_command` passes `--tools ""` (`CLAUDE_BUILTIN_TOOLS = ""`).
Per `claude --help`, `--tools ""` disables *all* built-in tools — including
`ToolSearch`, the tool Claude uses to **wait for a still-connecting MCP server**
before continuing. With no MCP tools (pending) *and* no wait-tool, the model runs
blind. The #998 bounded retry just re-hits the same cold start.

## Fix (one line of behaviour, plus guard cleanup)

Restore the built-in wait bridge and let Claude self-heal the cold-start window:

- `CLAUDE_BUILTIN_TOOLS = "ToolSearch"` → emits `--tools "ToolSearch"`. Keeps
  native file/exec tools (`Bash/Edit/Read/Write`) disabled while restoring
  `ToolSearch`. MCP tools still load (they come from `--mcp-config`, independent
  of `--tools`).
- Keep `alwaysLoad: true` on both servers — fast path (tools upfront when
  connected) and `ToolSearch` (slow-path bridge when pending) complement.
- Relax the guard: `pending` no longer aborts (self-heals via `ToolSearch`);
  drop the #998 bounded retry. `failed`/terminal stays fatal (fail fast — a
  crashed/missing server won't self-heal). Same behaviour on **both** the
  blocking and streaming paths (removes today's pending asymmetry).

## Scope of change

| Area | File |
|------|------|
| Flag | `src/mcp_coder/llm/providers/claude/claude_code_cli.py` (`CLAUDE_BUILTIN_TOOLS`) |
| Guard module | `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py` |
| Blocking path | `claude_code_cli.py` (`ask_claude_code_cli` retry loop + guard) |
| Streaming path | `claude_code_cli_streaming.py` (init-event guard) |
| Unit tests | `tests/llm/providers/claude/test_claude_code_cli.py`, `test_claude_cli_stream_mcp_guard.py` |
| Integration | new slow-MCP stub + `tests/llm/providers/claude/test_claude_mcp_coldstart_integration.py` (`claude_cli_integration`) |

`.mcp.json` is unchanged. `.claude/settings.local.json` already does not deny
`ToolSearch` / set `ENABLE_TOOL_SEARCH=false` (confirmed).

## Process

TDD, test-first. **Each test is run and observed failing (red) for the right
reason before the source change, then observed passing (green) after.** A test
that passes before the change tests nothing — see Decisions D-TDD.

See `Decisions.md` for the design decisions taken during discussion.

## Steps

1. `step_1.md` — `--tools "ToolSearch"` flag (unit, red→green)
2. `step_2.md` — guard module: `find_fatal_mcp_servers`, dict return type, drop retry machinery (unit)
3. `step_3.md` — blocking path: single attempt, fatal-only guard, log pending (unit/mock)
4. `step_4.md` — streaming path: fatal-only guard, tolerate pending, remove asymmetry (unit/mock)
5. `step_5.md` — slow-MCP-stub integration: v1 self-heal + v2 clean-failure (`claude_cli_integration`)
6. `step_6.md` — confirm settings + full quality gates
