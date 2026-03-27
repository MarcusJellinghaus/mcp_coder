# Step 4: Pass Heartbeat Parameters from `ask_claude_code_cli()`

## Context

See [summary.md](summary.md) for full context. This step makes `ask_claude_code_cli()` opt into heartbeat logging when calling `execute_subprocess()` for LLM calls.

## WHERE

- **Source**: `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — `ask_claude_code_cli()` function
- **Tests**: `tests/llm/providers/claude/test_claude_code_cli.py`

## WHAT

Update the `execute_subprocess()` call in `ask_claude_code_cli()` to pass heartbeat parameters:

```python
# Before:
result = execute_subprocess(command, options)

# After:
result = execute_subprocess(
    command,
    options,
    heartbeat_interval_seconds=120,
    heartbeat_message="LLM call in progress",
)
```

### Constant:

Add a module-level constant:

```python
LLM_HEARTBEAT_INTERVAL_SECONDS = 120  # 2 minutes
```

## HOW

- Single-line change in the `execute_subprocess()` call inside `ask_claude_code_cli()`
- Add a constant for the interval
- No changes to function signatures or return types

## DATA

- Heartbeat will log: `"LLM call in progress (elapsed: 2m 0s)"`, `"LLM call in progress (elapsed: 4m 0s)"`, etc.

## TESTS

Add to `tests/llm/providers/claude/test_claude_code_cli.py`:

```python
class TestAskClaudeCodeCliHeartbeat:
    def test_passes_heartbeat_params_to_execute_subprocess(self):
        """Verify heartbeat parameters are passed to execute_subprocess."""
        with patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable") as mock_find:
            mock_find.return_value = "claude"
            with patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess") as mock_exec:
                mock_exec.return_value = CommandResult(
                    return_code=0, stdout=make_valid_stream_output(), stderr="",
                    timed_out=False, command=["claude"], runner_type="subprocess",
                )
                with patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path"):
                    ask_claude_code_cli("test question", timeout=30)

                # Verify heartbeat params were passed
                call_kwargs = mock_exec.call_args
                assert call_kwargs.kwargs.get("heartbeat_interval_seconds") == 120 or \
                       call_kwargs[1].get("heartbeat_interval_seconds") == 120
                assert "LLM call in progress" in (
                    call_kwargs.kwargs.get("heartbeat_message", "") or
                    call_kwargs[1].get("heartbeat_message", "")
                )
```

## COMMIT

`feat(claude-cli): enable heartbeat logging for LLM subprocess calls (#598)`

## LLM PROMPT

```
Implement Step 4 from pr_info/steps/step_4.md.
Context: pr_info/steps/summary.md

1. Add `LLM_HEARTBEAT_INTERVAL_SECONDS = 120` constant to `src/mcp_coder/llm/providers/claude/claude_code_cli.py`.
2. Update the `execute_subprocess()` call in `ask_claude_code_cli()` to pass `heartbeat_interval_seconds=LLM_HEARTBEAT_INTERVAL_SECONDS` and `heartbeat_message="LLM call in progress"`.
3. Add a test that verifies the heartbeat parameters are passed through.

Run all code quality checks.
Commit: "feat(claude-cli): enable heartbeat logging for LLM subprocess calls (#598)"
```
