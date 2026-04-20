# Issue #822: Claude call with exit code 1 — runs forever

## Problem Summary

When Claude CLI exits with code 1, three things go wrong:
1. **iCoder busy indicator stuck** — never resets because `done` event is never emitted
2. **Error message missing stderr** — streaming providers omit `cmd_result.stderr` diagnostics
3. **`mcp-coder prompt` reports success on failure** — exits 0 even when error events occurred

## Architectural / Design Changes

**No new modules, classes, or abstractions.** All changes are small behavioral fixes in existing code paths:

- **`ResponseAssembler`** gets a `has_error` property (1-line accessor for existing `_error` field). This is the only API surface change. It exposes read-only state that `_error` already tracks, enabling clean exit-code logic in `prompt.py` without reaching into `raw_response` internals.
- **`_stream_llm` finally block** — expanded to always reset the busy indicator on any exit path. `show_ready()` is idempotent, so double-calling after a `done` event is harmless.
- **Streaming error messages** — enriched with truncated stderr (≤500 chars), matching the pattern the non-streaming `ask_claude_code_cli` already uses (line 614-615 of `claude_code_cli.py`).
- **Prompt command exit code** — changes from unconditional `return 0` to conditional `return 1` when `assembler.has_error` is true.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/types.py` | Add `has_error` property to `ResponseAssembler` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Include stderr in error event message |
| `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` | Include stderr in error event message |
| `src/mcp_coder/cli/commands/prompt.py` | Return exit code 1 when `assembler.has_error` |
| `src/mcp_coder/icoder/ui/app.py` | Reset busy indicator in `finally` block |
| `tests/llm/test_types.py` | Add tests for `has_error` property |
| `tests/cli/commands/test_prompt_streaming.py` | Update + add tests for error exit code |
| `tests/llm/providers/claude/test_claude_cli_stream_parsing.py` | Add test for stderr in error event |
| `tests/llm/providers/copilot/test_copilot_cli_streaming.py` | Add test for stderr in error event |
| `tests/icoder/ui/test_app.py` | Add test for busy indicator reset on error stream |

## Implementation Steps

- **Step 1**: `ResponseAssembler.has_error` property + tests
- **Step 2**: Streaming providers include stderr in error events + tests (Claude & Copilot)
- **Step 3**: `execute_prompt` returns exit code 1 on error + test updates
- **Step 4**: iCoder busy indicator reset on stream end + test
