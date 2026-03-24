# Step 2: Render tool names in `_format_mcp_section()` with 80-column wrapping

## LLM Prompt

> Implement Step 2 from `pr_info/steps/summary.md` (Issue #550).
> Update `_format_mcp_section()` in `verify.py` to display tool names per server with 80-column wrapping.
> Follow TDD: write tests first, then implement. Run all three code quality checks after changes.

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/test_verify_format_section.py` | Add tests for tool name rendering |
| `src/mcp_coder/cli/commands/verify.py` | Modify `_format_mcp_section()` |

## WHAT

### Modified function

```python
def _format_mcp_section(mcp_results: dict[str, Any], symbols: dict[str, str]) -> str:
    # existing signature unchanged
```

## HOW

- Import `textwrap` at top of `verify.py`
- In `_format_mcp_section()`, when a server entry has `tool_names`, format as:
  `N tools: name1, name2, ...` with 80-column wrapping
- Use `textwrap.wrap()` with `width=80`, `initial_indent` matching the label+symbol prefix, `subsequent_indent` aligned after the symbol

## ALGORITHM

```
for name, entry in servers.items():
    symbol = [OK] or [!!]
    tool_names = entry.get("tool_names")
    # Note: empty tool_names=[] is falsy, intentionally falls through to value-string path
    if tool_names:
        prefix = f"  {name:<20s} {symbol} "
        tools_text = f"{len(tool_names)} tools: {', '.join(tool_names)}"
        wrapped = textwrap.wrap(tools_text, width=80,
                                initial_indent=prefix,
                                subsequent_indent=" " * len(prefix))
        lines.extend(wrapped)
    else:
        lines.append(f"  {name:<20s} {symbol} {value}")
```

## DATA

Input (server entry with tool_names):
```python
{"ok": True, "value": "3 tools available", "tools": 3, "tool_names": ["run_pytest_check", "run_pylint_check", "run_mypy_check"]}
```

Output:
```
  tools-py             [OK] 3 tools: run_pytest_check, run_pylint_check,
                            run_mypy_check
```

Input (server entry without tool_names — error case):
```python
{"ok": False, "value": "connection refused", "error": "ConnectionError"}
```

Output (unchanged from current behavior):
```
  broken               [!!] connection refused
```

## TESTS

Add to `test_verify_format_section.py` in a new `TestFormatMcpSection` class:

1. **`test_tool_names_displayed_inline`** — 3 short tool names fit on one line
2. **`test_tool_names_wrap_at_80_columns`** — 10 tool names with long names cause wrapping, continuation lines indented
3. **`test_no_tool_names_falls_back_to_value`** — Server with no `tool_names` key shows `value` string (backward compat)
4. **`test_failed_server_shows_value_not_tools`** — Failed server with `ok=False` shows error value
5. **`test_empty_tool_names_falls_back_to_value`** — Server with `tool_names=[]` shows value string (0 tools case)

## COMMIT

```
feat(verify): display MCP tool names per server with 80-col wrapping

Update _format_mcp_section() to show individual tool names inline,
wrapping at 80 columns with indented continuation lines. Falls back
to the existing value string when tool_names is not present.

Refs #550
```
