# Issue #645: Disable All Built-in Tools via --tools Flag

## Summary

When `mcp-coder` launches Claude Code as a subprocess (via `prompt` or `icoder` commands), Claude has access to all built-in tools (Bash, Read, Edit, Write, Grep, Glob, etc.). Since MCP tools (`mcp__workspace__*`, `mcp__tools-py__*`) already provide these capabilities, the built-in tools are redundant and bypass the controlled MCP layer.

**Solution:** Pass `--tools ""` to the Claude CLI command, disabling all built-in tools unconditionally.

## Architectural / Design Changes

- **No new modules or files created** — this is a surgical change to existing code.
- **Single point of change:** The `build_cli_command()` function in `claude_code_cli.py` is the sole command builder used by both the non-streaming (`ask_claude_code_cli()`) and streaming (`ask_claude_code_cli_stream()`) code paths. Adding `--tools ""` here covers both paths automatically.
- **New constant:** `CLAUDE_BUILTIN_TOOLS = ""` added to `claude_code_cli.py` alongside existing CLI constants. Using a named constant makes the intent clear and provides a single place to change if the value ever needs adjustment.
- **Unconditional application:** The `--tools` flag is always added — no opt-out parameter. This keeps the implementation simple (KISS) and can be extended later if needed.
- **SDK path out of scope:** `claude_code_api.py` (SDK-based interaction) is not affected.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Add `CLAUDE_BUILTIN_TOOLS` constant; add `--tools` flag to `build_cli_command()` |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Update 3 existing exact-match tests; add 1 new test for `--tools` presence |
| `tests/llm/providers/claude/test_claude_mcp_config.py` | Update 1 existing exact-match test to include `--tools ""` |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Add constant + modify `build_cli_command()` + update/add tests | Single commit: tests + implementation + checks passing |

## Why One Step

The entire change is ~15 lines across 3 files. Splitting into multiple steps would add process overhead without value. The test updates and new test are tightly coupled to the single production code change — they should ship together.
