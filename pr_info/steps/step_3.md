# Step 3: Return exit code 1 on error events in prompt command

> **Context**: See [summary.md](summary.md) for full issue context.  
> **Depends on**: Step 1 (`ResponseAssembler.has_error` property).

## Goal

`mcp-coder prompt` should return exit code 1 when the stream contained error events. Currently it always returns 0 and logs "completed successfully" even when errors occurred.

## WHERE

- **Production**: `src/mcp_coder/cli/commands/prompt.py` — `execute_prompt` function, lines ~168-172 (inside the `if output_format in ("rendered", "text", "ndjson", "json-raw")` block, after `store_response` handling)
- **Tests**: `tests/cli/commands/test_prompt_streaming.py`

## WHAT

Inside the streaming `if output_format in (...)` block (after store_response handling, ~line 172), add an early return on error:

```python
            # Inside the streaming if-block, after MLflow/store_response (line ~172):
            if assembler.has_error:
                logger.error("Prompt command completed with errors")
                return 1

        # ... other elif branches (session-id, json) unchanged ...

        # Shared return 0 at end of function stays — serves all format branches:
        logger.info("Prompt command completed successfully")
        return 0
```

The `assembler` variable only exists inside the streaming block, so the check **must** be an early return there — not at the shared `return 0` which also serves `session-id` and `json` branches.

## HOW

- `assembler` is already instantiated as `ResponseAssembler(provider)` at line ~121 of prompt.py
- `assembler.has_error` comes from Step 1
- The check goes as an **early return inside the streaming `if` block**, after store_response (line ~172), not at the shared `return 0`
- The shared `logger.info("Prompt command completed successfully")` and `return 0` at lines 219-220 remain unchanged — they serve all format branches
- On error, the early return at line ~173 skips the shared success log

## ALGORITHM

```
1. Stream events into assembler (existing loop, lines 141-153)
2. Build llm_response = assembler.result() (existing, line 155)
3. Do MLflow logging and store_response (existing, lines 157-172)
4. Inside streaming block: if assembler.has_error → log error, return 1 (early return)
5. Shared return 0 at end of function (line 220) remains for all format branches
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
