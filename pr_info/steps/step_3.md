# Step 3: Render detailed MCP tool listing + orchestrator passthrough

## LLM Prompt

> Read `pr_info/steps/summary.md` for context on issue #639. Then implement Step 3:
> Update `_format_mcp_section()` to render two-column tool listing when `list_mcp_tools=True`.
> Update `execute_verify()` to pass the flag through. Update all test mock data to use tuples.
> Write tests first (TDD), then the implementation. Run all three code quality checks after changes.

## WHERE

- **Tests:**
  - `tests/cli/commands/test_verify_format_section.py` — format tests
  - `tests/cli/commands/test_verify_orchestration.py` — passthrough test
- **Impl:** `src/mcp_coder/cli/commands/verify.py`

## WHAT

### Signature change

```python
# BEFORE
def _format_mcp_section(mcp_results: dict[str, Any], symbols: dict[str, str]) -> str:

# AFTER
def _format_mcp_section(
    mcp_results: dict[str, Any],
    symbols: dict[str, str],
    *,
    list_mcp_tools: bool = False,
) -> str:
```

### `execute_verify()` change

```python
# BEFORE
print(_format_mcp_section(mcp_result, symbols))

# AFTER
list_mcp_tools = getattr(args, "list_mcp_tools", False)
print(_format_mcp_section(mcp_result, symbols, list_mcp_tools=list_mcp_tools))
```

## HOW

### Default mode (`list_mcp_tools=False`)

Update to extract name from tuple: `", ".join(name for name, _desc in tool_names)`. Existing wrapping logic unchanged.

### Detailed mode (`list_mcp_tools=True`)

Replace the comma-separated tool list with per-tool indented lines.

## ALGORITHM (detailed mode)

```python
# 1. Compute global max tool name width across ALL servers
max_name = max((len(name) for srv in servers.values()
               if srv.get("tool_names") for name, _ in srv["tool_names"]), default=0)

# 2. For each server:
#    a. Print status line: "  {server:<20s} {symbol} {value}"
#    b. For each (name, desc) in tool_names:
#       - If desc: print "    {name:<max_name+2s} {desc}"
#       - Else:    print "    {name}"

# 3. Failed servers: same as today (value + error)
```

## DATA

### Input (tool_names as tuples)

```python
"tool_names": [
    ("find_references", "Find all references to a symbol"),
    ("list_symbols", "List symbols in a module"),
    ("some_tool", ""),  # no description
]
```

### Output example

```
=== MCP SERVERS (via langchain-mcp-adapters) ===
  tools-py             [OK] 3 tools available
    find_references      Find all references to a symbol
    list_symbols         List symbols in a module
    some_tool
```

## Test changes

### `test_verify_format_section.py`

**Update existing `TestFormatMcpSection` mock data** — change `tool_names` from `["alpha", "beta"]` to `[("alpha", "Alpha tool"), ("beta", "Beta tool")]` in all tests.

**Add new tests to `TestFormatMcpSection`:**

```python
def test_list_mcp_tools_shows_per_tool_lines(self) -> None:
    """list_mcp_tools=True renders each tool on its own line."""

def test_list_mcp_tools_global_alignment(self) -> None:
    """Tool names across servers are aligned to the longest name globally."""

def test_list_mcp_tools_missing_description_shows_name_only(self) -> None:
    """Tools with empty description show name only, no placeholder."""

def test_list_mcp_tools_failed_server_shows_error(self) -> None:
    """Failed server shows error line; healthy server still lists tools."""

def test_list_mcp_tools_false_still_shows_comma_format(self) -> None:
    """Default mode with tuple data still produces comma-separated output."""

def test_list_mcp_tools_all_servers_failed(self) -> None:
    """All servers failed — no crash, no tool lines rendered."""
```

### `test_verify_orchestration.py`

**Update `_mcp_servers_ok()`** — change `tool_names` to tuples.

**Add test:**

```python
def test_list_mcp_tools_flag_passed_to_format(self) -> None:
    """--list-mcp-tools flag flows from args to _format_mcp_section."""
```

## Commit

```
Render detailed MCP tool listing with --list-mcp-tools flag (#639)
```
