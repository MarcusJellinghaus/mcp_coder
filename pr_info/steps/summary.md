# Issue #639: `verify --list-mcp-tools` — Implementation Summary

## Goal

Add `--list-mcp-tools` flag to the `verify` command that renders MCP tools with descriptions in a two-column aligned format, grouped by server, without invoking the LLM.

## Architectural / Design Changes

### Data flow change

The existing `_check_servers()` in `verification.py` already calls `session.list_tools()` per server and extracts tool names. The only structural change is **widening `tool_names` from `list[str]` to `list[tuple[str, str]]`** (name + description). This is a contained change — the field is produced in one place (`_check_servers`) and consumed in one place (`_format_mcp_section`).

### Rendering change

`_format_mcp_section()` gains a `list_mcp_tools` boolean parameter:
- **False (default):** Existing comma-separated tool list — extracts just names from tuples. Identical output to today.
- **True:** Two-column format with global alignment across all servers. Each tool on its own indented line.

### No new abstractions

- No new classes, data types, or helper functions
- No new files
- No changes to exit code logic, smoke tests, or other verify sections
- The flag is independent and combinable with `--check-models`

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Add `--list-mcp-tools` store_true flag to verify parser |
| `src/mcp_coder/llm/providers/langchain/verification.py` | `_check_servers()`: change `tool_names` from `[t.name]` to `[(t.name, t.description or "")]` |
| `src/mcp_coder/cli/commands/verify.py` | `_format_mcp_section()`: add `list_mcp_tools` param, render detailed format when True; `execute_verify()`: pass flag through |
| `tests/cli/commands/test_verify_parser.py` | Add tests for `--list-mcp-tools` flag |
| `tests/llm/providers/langchain/test_mcp_health_check.py` | Update `tool_names` assertions to expect `(name, desc)` tuples |
| `tests/cli/commands/test_verify_format_section.py` | Add tests for detailed MCP tool listing format |
| `tests/cli/commands/test_verify_orchestration.py` | Update mock data + add test for flag passthrough |

## Output Example (when `--list-mcp-tools` is set)

```
MCP Servers
  tools-py             [OK] 5 tools available
    find_references      Find all references to a symbol
    list_symbols         List symbols in a module
    move_symbol          Move a symbol to another module
    run_pytest_check     Run pytest
    some_tool
  workspace            [OK] 3 tools available
    read_file            Read file contents
    save_file            Write content to a file
    list_directory       List directory contents
```

## Implementation Steps

| Step | Focus | Commit |
|------|-------|--------|
| 1 | Parser: `--list-mcp-tools` flag + tests | tests + parsers.py |
| 2 | Data: `_check_servers()` returns descriptions + tests | tests + verification.py |
| 3 | Rendering: detailed format in `_format_mcp_section()` + orchestrator passthrough + tests | tests + verify.py |
