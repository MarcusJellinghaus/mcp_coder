# Step 2: Return tool descriptions from `_check_servers()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context on issue #639. Then implement Step 2:
> Change `_check_servers()` in `verification.py` to include tool descriptions in `tool_names`.
> Write tests first (TDD), then the implementation. Run all three code quality checks after changes.

## WHERE

- **Test:** `tests/llm/providers/langchain/test_mcp_health_check.py`
- **Impl:** `src/mcp_coder/llm/providers/langchain/verification.py` (`_check_servers()`)

## WHAT

No new functions. One-line change inside `_check_servers()`.

### Change

```python
# BEFORE
tool_names = [t.name for t in tools.tools]

# AFTER
tool_names = [(t.name, t.description or "") for t in tools.tools]
```

### Test changes

1. **Update `_make_tools_response_with_names`** to also set `.description` on each mock (accept `list[tuple[str, str]]`).
2. **Add new helper** `_make_tools_response_with_descriptions(tools: list[tuple[str, str]])` — creates mocks with both `.name` and `.description` attributes.
3. **Update `test_server_success_includes_tool_names`** — assert `tool_names` contains tuples `(name, description)` instead of plain strings.
4. **Add `test_server_success_includes_tool_descriptions`** — verify descriptions are captured, including empty string for `None` descriptions.

### Test signatures

```python
def _make_tools_response_with_descriptions(tools: list[tuple[str, str]]) -> MagicMock: ...

# In TestVerifyMcpServers:
def test_server_success_includes_tool_names(self, ...) -> None: ...  # updated
def test_server_success_includes_tool_descriptions(self, ...) -> None: ...  # new
```

## HOW

The `t.description` attribute is available on MCP tool objects from `session.list_tools()`. The `or ""` ensures `None` descriptions become empty strings.

## DATA

`tool_names` changes from `list[str]` to `list[tuple[str, str]]`:

```python
# Before
["read_file", "save_file", "edit_file"]

# After
[("read_file", "Read file contents"), ("save_file", "Write content to a file"), ("edit_file", "")]
```

## ALGORITHM

```
tools = await session.list_tools()
tool_names = [(t.name, t.description or "") for t in tools.tools]
# rest unchanged — tool count uses len(tools.tools), value string unchanged
```

## Side effects on existing tests

- `test_verify_format_section.py` — `TestFormatMcpSection` uses `tool_names: ["alpha", "beta"]` in mock data. These tests call `_format_mcp_section()` directly with hand-built dicts, so they will still pass with string lists until Step 3 updates them. No breakage here.
- `test_verify_orchestration.py` — `_mcp_servers_ok()` uses `tool_names: ["read_file", "save_file", "edit_file"]`. Same: hand-built mock data passed directly to the formatter. No breakage.

## Commit

```
Include tool descriptions in MCP server health check (#639)
```
