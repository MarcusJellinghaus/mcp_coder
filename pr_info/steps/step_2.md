# Step 2: Include stderr in streaming error events (Claude & Copilot)

> **Context**: See [summary.md](summary.md) for full issue context.

## Goal

When CLI exits with non-zero code, include truncated stderr in the error event message. Currently only says `"CLI failed with code 1"` — should include diagnostics like the non-streaming variant does (see `claude_code_cli.py` line 614-615).

## WHERE

- **Production (Claude)**: `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — last few lines
- **Production (Copilot)**: `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` — last few lines
- **Tests (Claude)**: `tests/llm/providers/claude/test_claude_cli_stream_parsing.py`
- **Tests (Copilot)**: `tests/llm/providers/copilot/test_copilot_cli_streaming.py`

## WHAT

In both streaming files, change the `elif cmd_result.return_code != 0:` block from:

```python
yield {
    "type": "error",
    "message": f"CLI failed with code {cmd_result.return_code}",
}
```

To:

```python
error_msg = f"CLI failed with code {cmd_result.return_code}"
if cmd_result.stderr:
    error_msg += f": {cmd_result.stderr[:500]}"
yield {"type": "error", "message": error_msg}
```

## HOW

- `cmd_result` is `CommandResult` from `mcp_coder_utils.subprocess_runner`
- `CommandResult.stderr` is a `str` field (confirmed available in streaming context — same dataclass used by `stream_subprocess`)
- 500-char truncation matches the non-streaming variant's pattern
- No new imports needed

## ALGORITHM

```
1. After stream loop, cmd_result = stream.result
2. If return_code != 0:
3.   Build base message "CLI failed with code {code}"
4.   If cmd_result.stderr is non-empty, append ": {stderr[:500]}"
5.   Yield error event with enriched message
```

## DATA

- Input: `CommandResult` with `.return_code` (int) and `.stderr` (str)
- Output: `StreamEvent` with `type: "error"` and enriched `message`

## Tests (write first)

**Claude** (`tests/llm/providers/claude/test_claude_cli_stream_parsing.py`):
- **`test_stream_error_event_includes_stderr`** — mock `stream_subprocess` to return `CommandResult(return_code=1, stderr="auth failed")`, verify error event message contains both "CLI failed with code 1" and "auth failed"
- **`test_stream_error_event_without_stderr`** — mock with `stderr=""`, verify message is just "CLI failed with code 1" (no trailing colon)
- **`test_stream_error_event_truncates_long_stderr`** — mock with `stderr="x" * 1000`, verify message contains at most 500 chars of stderr

**Copilot** (`tests/llm/providers/copilot/test_copilot_cli_streaming.py`):
- Same three tests, adapted for `ask_copilot_cli_stream`

## LLM Prompt

```
Implement Step 2 from pr_info/steps/step_2.md.
Read pr_info/steps/summary.md for full context.

Add stderr to streaming error events in both Claude and Copilot streaming providers.
Write tests first, then implement. Run all three code quality checks after changes.
```
