# Step 1 — Emit `--tools "ToolSearch"`

**Goal:** `build_cli_command` restores the `ToolSearch` built-in (the MCP
wait-bridge) while keeping file/exec built-ins disabled.

## TDD (red → green)
1. Update the existing flag assertions to expect `"ToolSearch"`; run them — they
   go **red** against the current `--tools ""`.
2. Flip the constant; run again — **green**.

## WHERE
- Src: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- Tests: `tests/llm/providers/claude/test_claude_code_cli.py`

## WHAT
- `CLAUDE_BUILTIN_TOOLS = "ToolSearch"` (was `""`), at `claude_code_cli.py:45`.
- Update the comment (43-44): explain `ToolSearch` is kept as the wait-bridge so
  the model can wait for a still-`pending` MCP server instead of running blind;
  file/exec built-ins stay disabled; MCP tools load via `--mcp-config`.

## HOW
- The flag is emitted unconditionally at `claude_code_cli.py:230`
  (`command.extend(["--tools", CLAUDE_BUILTIN_TOOLS])`) — no structural change.

## Tests to change
- `test_build_cli_command_without_session` (~318): `--tools` value `"" → "ToolSearch"`.
- `test_build_cli_command_with_stream_json_disabled` (~330): same.
- `test_build_cli_command_always_includes_tools_flag` (~333): assert
  `cmd[tools_idx + 1] == "ToolSearch"` for all variants.
- Add `test_build_cli_command_tools_is_toolsearch`: explicit assert the value is
  exactly `"ToolSearch"` (guards against a future re-blanking).

## DATA
`build_cli_command(...) -> list[str]` containing `["--tools", "ToolSearch", ...]`.

## Note
`init.tools` actually containing `ToolSearch` and excluding `Bash/Edit/Read/Write`
(plus all MCP tools still loading) is asserted end-to-end in Step 5 — that needs a
real CLI, which `build_cli_command` alone cannot produce.

## LLM prompt
> Implement Step 1 from `pr_info/steps/summary.md`. Test-first: update the
> `--tools` assertions in `tests/llm/providers/claude/test_claude_code_cli.py` to
> expect `"ToolSearch"` and add an explicit assertion test; run them and confirm
> they fail red. Then set `CLAUDE_BUILTIN_TOOLS = "ToolSearch"` and update its
> comment. Re-run to green. Respect Decisions D1–D6.
