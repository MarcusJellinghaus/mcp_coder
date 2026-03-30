# Step 1: Tool name formatting helper

> See `pr_info/steps/summary.md` for full context (Issue #642).

## Goal

Add `_format_tool_name()` to `formatters.py` with unit tests.

## WHERE

- **Implement**: `src/mcp_coder/llm/formatting/formatters.py`
- **Test**: `tests/llm/formatting/test_formatters.py`

## WHAT

```python
def _format_tool_name(name: str) -> str:
    """Format tool name for rendered display.

    Strip 'mcp__' prefix, split on first remaining '__':
      mcp__workspace__read_file  → workspace > read_file
      mcp__tools-py__run_pytest  → tools-py > run_pytest
      Bash                       → Bash (unchanged)
    """
```

## ALGORITHM

```
if name starts with "mcp__":
    rest = name[5:]
    server, sep, tool = rest.partition("__")
    if tool:  # found a "__" separator
        return f"{server} > {tool}"
    return server  # edge case: mcp__something with no second __
return name  # built-in tool, pass through
```

## DATA

- **Input**: tool name string from `StreamEvent["name"]`
- **Output**: formatted display string

## Tests to write (new class `TestFormatToolName`)

1. MCP name with two segments: `mcp__workspace__read_file` → `workspace > read_file`
2. MCP name with hyphenated server: `mcp__tools-py__run_pytest_check` → `tools-py > run_pytest_check`
3. Built-in tool name: `Bash` → `Bash` (unchanged)
4. MCP name with only one segment: `mcp__something` → `something`

## LLM Prompt

```
Implement Step 1 of Issue #642 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).

Add the _format_tool_name() helper function to src/mcp_coder/llm/formatting/formatters.py
and its unit tests to tests/llm/formatting/test_formatters.py. Follow TDD: write the tests
first, then implement the function. Run all three code quality checks after changes.
Produce one commit.
```
