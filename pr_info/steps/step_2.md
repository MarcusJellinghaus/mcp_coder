# Step 2: Claude CLI — improved timeout message + double-error fix

> **Context**: See [summary.md](summary.md) for full issue context.

## Goal
1. Replace the raw `"Timed out after {timeout}s"` with an informative message including provider name and action hint.
2. Fix double-error: change `if` to `elif` so when `timed_out` is true, the redundant "CLI failed with code N" is suppressed.

## Files Modified

| File | Change |
|------|--------|
| `tests/llm/providers/claude/test_claude_code_cli.py` | Update timeout message assertion + add double-error suppression test |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Improved message + `elif` |

## Implementation Details

### 1. Tests first: `tests/llm/providers/claude/test_claude_code_cli.py`

**Update** `test_ask_claude_stream_timeout_yields_error` (line ~370):

Current assertion: `assert any("Timed out" in str(e["message"]) for e in error_events)`

New assertion — check for the new message pattern and verify only ONE error event (not two, since `timed_out=True` + `return_code=1`):
```python
assert len(error_events) == 1  # NEW: elif suppresses the second error
assert "LLM inactivity timeout (claude)" in error_events[0]["message"]
assert "no output for 30s" in error_events[0]["message"]
assert "--timeout" in error_events[0]["message"]
```

**Note**: The existing test uses `_make_stream_gen([], return_code=1, timed_out=True)` — both `timed_out` and `return_code != 0` are true. Before the fix this yielded 2 errors. After the `elif` fix it yields 1.

The separate `test_ask_claude_stream_nonzero_exit_yields_error` test (which uses `return_code=1, timed_out=False`) should remain unchanged — it tests the non-timeout failure path.

### 2. Source: `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`

**WHERE**: Lines 136–142 (end of `ask_claude_code_cli_stream`)

**WHAT**: Two changes in the post-stream error handling block:

**Current code** (lines 134–142):
```python
cmd_result: CommandResult = stream.result
if cmd_result.timed_out:
    yield {"type": "error", "message": f"Timed out after {timeout}s"}
if cmd_result.return_code != 0:
    yield {
        "type": "error",
        "message": f"CLI failed with code {cmd_result.return_code}",
    }
```

**New code**:
```python
cmd_result: CommandResult = stream.result
if cmd_result.timed_out:
    yield {
        "type": "error",
        "message": (
            f"LLM inactivity timeout (claude): no output for {timeout}s. "
            "Process terminated. You can retry, or use --timeout to increase the limit."
        ),
    }
elif cmd_result.return_code != 0:
    yield {
        "type": "error",
        "message": f"CLI failed with code {cmd_result.return_code}",
    }
```

Changes:
1. Timeout message now includes: provider name (`claude`), timeout value, what happened (`Process terminated`), action hint (`--timeout`).
2. `if` → `elif` on the return code check to suppress the redundant error.

## LLM Prompt

```
Implement Step 2 from pr_info/steps/step_2.md.
Read pr_info/steps/summary.md for context.

This step improves the Claude CLI timeout error message and fixes the double-error
by changing `if` to `elif`. Write tests first, then implement. Run all checks after.
```
