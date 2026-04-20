# Step 3: Return exit code 1 on error events in prompt command

> **Context**: See [summary.md](summary.md) for full issue context.  
> **Depends on**: Step 1 (`ResponseAssembler.has_error` property).

## Goal

`mcp-coder prompt` should return exit code 1 when the stream contained error events. Currently it always returns 0 and logs "completed successfully" even when errors occurred.

## WHERE

- **Production**: `src/mcp_coder/cli/commands/prompt.py` — `execute_prompt` function, streaming block
- **Tests**: `tests/cli/commands/test_prompt_streaming.py`

## WHAT

After the streaming loop and MLflow logging, check `assembler.has_error` before returning:

```python
# After MLflow logging and store_response handling, replace unconditional return 0:
if assembler.has_error:
    logger.error("Prompt command completed with errors")
    return 1

logger.info("Prompt command completed successfully")
return 0
```

## HOW

- `assembler` is already instantiated as `ResponseAssembler(provider)` at line ~121 of prompt.py
- `assembler.has_error` comes from Step 1
- The check goes after the MLflow/store_response block but before the final `return 0`
- The existing `logger.info("Prompt command completed successfully")` should only run when there's no error

## ALGORITHM

```
1. Stream events into assembler (existing loop)
2. Build llm_response = assembler.result() (existing)
3. Do MLflow logging and store_response (existing)
4. If assembler.has_error → log error, return 1
5. Else → log success, return 0
```

## DATA

- Input: `assembler.has_error` (bool from Step 1)
- Output: exit code `int` — 0 on success, 1 on error

## Tests

**Update existing** in `tests/cli/commands/test_prompt_streaming.py`:
- **`test_error_event_printed_to_stderr_in_text_format`** (line ~407): Change `assert result == 0` to `assert result == 1`. This test has events `[error, done]` — the error event should now cause exit code 1.

**Add new**:
- **`test_error_only_stream_returns_exit_code_1`** — stream with only `[{"type": "error", "message": "CLI failed with code 1"}]` (no `done` event), verify `result == 1`
- **`test_successful_stream_returns_exit_code_0`** — stream with `[text_delta, done]`, verify `result == 0`

## LLM Prompt

```
Implement Step 3 from pr_info/steps/step_3.md.
Read pr_info/steps/summary.md for full context.
Step 1 (has_error property) must already be implemented.

Update `execute_prompt` in `src/mcp_coder/cli/commands/prompt.py` to return 1 on error.
Update and add tests in `tests/cli/commands/test_prompt_streaming.py`.
Run all three code quality checks after changes.
```
