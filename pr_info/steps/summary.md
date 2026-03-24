# Issue #550: Enhance verify — list MCP tool names and add MCP edit smoke test

## Summary

Three enhancements to `mcp-coder verify`:

1. **List tool names per MCP server** — show individual tool names (not just counts)
2. **MCP edit smoke test** — validate the LLM can actually use MCP tools to edit a file
3. **Fix `prompt_llm()` calls** — pass `mcp_config` and `execution_dir` for consistency

## Architectural / Design Changes

### Data flow change in `_check_servers()` (verification.py)
- The result dict per server gains a `"tool_names"` key (list of strings)
- No new functions, no new classes — one line added to existing dict literal

### Formatting change in `_format_mcp_section()` (verify.py)
- Existing function enhanced to render tool names inline with 80-column wrapping
- Uses `textwrap.wrap()` from stdlib — no new dependencies

### New function `_run_mcp_edit_smoke_test()` (verify.py)
- Extracted helper for testability, called once from `execute_verify()`
- Returns a formatted output line (string) — caller just prints it
- Only runs when `mcp_config_resolved` is set
- Informational only — does NOT affect `_compute_exit_code`

### `prompt_llm()` call fix (verify.py)
- Existing test prompt call and new smoke test call both pass `mcp_config` and `execution_dir`
- No interface changes — `prompt_llm()` already accepts these kwargs

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/verification.py` | Add `tool_names` to `_check_servers()` result |
| `src/mcp_coder/cli/commands/verify.py` | Update `_format_mcp_section()`, add `_run_mcp_edit_smoke_test()`, fix `prompt_llm()` kwargs |
| `tests/llm/providers/langchain/test_mcp_health_check.py` | Add test for `tool_names` in server result |
| `tests/cli/commands/test_verify_format_section.py` | Add tests for tool name rendering + wrapping |
| `tests/cli/commands/test_verify_exit_codes.py` | Add tests for smoke test integration |
| `tests/cli/commands/test_verify_orchestration.py` | Add test for `prompt_llm` kwargs |

## Implementation Steps

- **Step 1**: Store tool names in `_check_servers()` + tests
- **Step 2**: Render tool names in `_format_mcp_section()` with 80-col wrapping + tests
- **Step 3**: Fix `prompt_llm()` kwargs + add MCP edit smoke test + tests
