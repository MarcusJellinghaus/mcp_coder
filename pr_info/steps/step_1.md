# Step 1: Add --tools "" Flag to build_cli_command()

## Context

See [summary.md](summary.md) for full context. This is the sole implementation step for issue #645.

## LLM Prompt

> Implement issue #645: Disable all built-in tools via `--tools ""` flag.
>
> Read `pr_info/steps/summary.md` for context, then follow the instructions in this step exactly.
>
> **Production code changes** in `src/mcp_coder/llm/providers/claude/claude_code_cli.py`:
> 1. Add a constant `CLAUDE_BUILTIN_TOOLS = ""` after the existing constants block (~line 28).
> 2. In `build_cli_command()`, add `command.extend(["--tools", CLAUDE_BUILTIN_TOOLS])` right after the base command list is built (after the line that creates `command = [claude_cmd, "-p", "", "--output-format", output_format]`).
>
> **Test changes** in `tests/llm/providers/claude/test_claude_code_cli.py`:
> 1. Update `test_build_cli_command_without_session` — add `"--tools", ""` to the expected list.
> 2. Update `test_build_cli_command_with_stream_json_disabled` — add `"--tools", ""` to the expected list.
> 3. Add `test_build_cli_command_always_includes_tools_flag` — verify the flag is present across multiple command variants.
> 4. Update `test_build_cli_command_without_mcp_config` in `tests/llm/providers/claude/test_claude_mcp_config.py` — add `"--tools", ""` to the expected list.
>
> Run all three code quality checks (pylint, pytest, mypy) and fix any issues before committing.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Modify |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Modify |
| `tests/llm/providers/claude/test_claude_mcp_config.py` | Modify |

## WHAT

### Production Code

**New constant** in `claude_code_cli.py`:

```python
# Built-in tools override: empty string disables all built-in tools
# Forces Claude to use only MCP-provided tools
CLAUDE_BUILTIN_TOOLS = ""
```

**Modified function** — `build_cli_command()` signature unchanged:

```python
def build_cli_command(
    session_id: str | None,
    claude_cmd: str,
    mcp_config: str | None = None,
    use_stream_json: bool = True,
) -> list[str]:
```

### Test Code

**Updated tests** (exact list assertions gain `"--tools", ""`):
- `test_build_cli_command_without_session`
- `test_build_cli_command_with_stream_json_disabled`
- `test_build_cli_command_without_mcp_config` (in `test_claude_mcp_config.py`)

**New test:**

```python
def test_build_cli_command_always_includes_tools_flag(self) -> None:
    """Test that --tools "" is always present regardless of options."""
    # Test multiple variants: with/without session, with/without mcp_config, stream_json on/off
    # For each, assert "--tools" and "" appear consecutively in the result list
```

## HOW

### Integration Points

- `build_cli_command()` is called by:
  - `ask_claude_code_cli()` in `claude_code_cli.py` (non-streaming)
  - `ask_claude_code_cli_stream()` in `claude_code_cli_streaming.py` (streaming)
- Both paths are covered by the single change to `build_cli_command()`.
- No import changes needed — the constant is used in the same file.

## ALGORITHM

```
1. Define CLAUDE_BUILTIN_TOOLS = "" as module-level constant
2. In build_cli_command(), after building base command list:
3.   command.extend(["--tools", CLAUDE_BUILTIN_TOOLS])
4. (Existing stream-json, session, mcp_config flags follow unchanged)
```

## DATA

**Input:** No change to `build_cli_command()` parameters.

**Output:** The returned command list now includes `"--tools", ""` between the base command and the conditional flags. Example for default call:

```python
["claude", "-p", "", "--output-format", "stream-json", "--tools", "",
 "--verbose", "--input-format", "stream-json", "--replay-user-messages"]
```

## Commit Message

```
feat: disable built-in tools via --tools flag (#645)

Pass --tools "" to Claude CLI to disable all built-in tools,
forcing use of MCP-provided tools only.
```
