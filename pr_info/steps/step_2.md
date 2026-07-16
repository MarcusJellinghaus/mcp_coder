# Step 2 — `MCPManager` canonical-name stamping + accessor

**Read first:** `pr_info/steps/summary.md` (design change §1).

The langchain tool's `.name` is the bare MCP name and carries no server identity.
`server_name` is in scope only inside `_connect_and_discover`, so we stamp the
canonical name there and expose a pure accessor.

## WHERE
- Source: `src/mcp_coder/llm/providers/langchain/mcp_manager.py` (`MCPManager`).
- Tests: `tests/llm/test_mcp_manager.py` (extend).

## WHAT
```python
def canonical_name(self, tool: Any) -> str | None:
    """Return the stamped mcp__server__tool identity, or None if absent."""
```
Plus a stamp inside `_connect_and_discover` (right after `lc_tool` is built,
before `all_tools.append(lc_tool)`).

## HOW
- In `_connect_and_discover`, after `convert_mcp_tool_to_langchain_tool(...)`:
  ```python
  lc_tool.metadata = {
      **(lc_tool.metadata or {}),
      "mcp_canonical_name": f"mcp__{server_name}__{tool.name}",
  }
  ```
  (`tool.name` is the MCP tool's bare name; `server_name` is the loop variable.)
- `canonical_name` reads that key defensively (returns `None` when metadata or key
  is missing / not a str). Pure, cache-safe, no re-discovery.

## ALGORITHM
```
# canonical_name
meta = getattr(tool, "metadata", None) or {}
value = meta.get("mcp_canonical_name")
return value if isinstance(value, str) else None
```

## DATA
- `canonical_name(tool)` → `str` like `"mcp__workspace__read_file"`, or `None`.
- Stamping mutates each freshly-built tool's `metadata` dict once at discovery
  (cache-safe: `tools()` returns these same cached objects).

## Tests (write first)
- `canonical_name` returns the stamped value for a stub tool whose
  `metadata = {"mcp_canonical_name": "mcp__srv__foo"}`.
- `canonical_name` returns `None` for a tool with no metadata / missing key /
  non-string value.
- *(Optional, `langchain_integration` marker)* an integration assertion that after a
  real discover, every tool has a `mcp__…__…` canonical name — only if a lightweight
  fixture already exists; otherwise rely on the unit tests above.

## Definition of done
Accessor + stamping implemented; `tests/llm/test_mcp_manager.py` passes; checks green.
One commit.

## LLM prompt
> Implement Step 2 from `pr_info/steps/step_2.md` (context in `pr_info/steps/summary.md`).
> Using TDD, first add tests to `tests/llm/test_mcp_manager.py` for a new
> `MCPManager.canonical_name(tool)` accessor (stamped-metadata read; `None` fallbacks),
> then implement the accessor and stamp `mcp__{server_name}__{tool.name}` onto each
> tool's `metadata` inside `_connect_and_discover`. Keep it pure and cache-safe. Run
> pylint, pytest (unit markers per CLAUDE.md), and mypy; fix all issues. One commit.
