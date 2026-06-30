# Step 1 — Tool-list reader in the MCP guard

**Commit:** `feat: add find_exposed_mcp_tools reader to claude_mcp_guard`

Implements acceptance item 1: a pure, structured, reusable reader of the init
event's `tools` field. See `summary.md` for context. Reuse target: #1006.

## WHERE
- **Impl:** `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`
  (next to `find_fatal_mcp_servers`).
- **Re-export:** `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
  (add the name to the existing guard re-export block + `__all__`).
- **Tests:** `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`
  (new `TestFindExposedMcpTools` class).

## WHAT
```python
def find_exposed_mcp_tools(system_message: StreamMessage | None) -> list[str]:
    """Return sorted, de-duplicated ``mcp__*`` tool names from the init event.

    Reads the init event's ``tools`` field (the list of tools actually exposed
    to the model) and keeps only MCP tools (names starting with ``mcp__``).
    Built-in tools (e.g. ``ToolSearch``) are excluded. Returns ``[]`` when the
    message is ``None``, has no ``tools`` field, or exposed no MCP tools — so a
    healthy-but-toolless session is represented as an empty list, not an error.
    """
```

## HOW
- Pure function — no I/O, no logging side effects. Mirrors the existing
  `_scan_mcp_servers` style (defensive about JSON shape).
- In `claude_code_cli.py`, extend the existing
  `from .claude_mcp_guard import (...)` block and the module `__all__` to include
  `find_exposed_mcp_tools`, so importers can use either module (consistent with
  `find_fatal_mcp_servers`).
- `verify` (Step 2) and `env_setup` (Step 3) import it directly from
  `claude_mcp_guard`.

## ALGORITHM
```
if system_message is None: return []
tools = system_message.get("tools") or []
names = set()
for t in tools:                      # entries may be str or {"name": str}
    name = t if isinstance(t, str) else (t.get("name") if isinstance(t, dict) else None)
    if isinstance(name, str) and name.startswith("mcp__"):
        names.add(name)
return sorted(names)
```

## DATA
- **Returns:** `list[str]` — sorted unique `mcp__*` tool names. Count = `len(...)`.

## TESTS (write first)
`TestFindExposedMcpTools`, using the same `cast(StreamMessage, {...})` fixture
style already in the file:
1. `None` → `[]`.
2. No `tools` key → `[]`.
3. **Healthy:** `tools` mixes `["ToolSearch", "mcp__mcp-tools-py__run_pytest_check",
   "mcp__mcp-workspace__read_file"]` → returns the two `mcp__*` names, sorted,
   `ToolSearch` excluded.
4. **Degraded:** connected server but `tools: []` → `[]`.
5. Dict-shaped entries `[{"name": "mcp__x__y"}, {"name": "Bash"}]` → `["mcp__x__y"]`.
6. Duplicates collapse; output is sorted.

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (context in
> `pr_info/steps/summary.md`). TDD: first add the `TestFindExposedMcpTools`
> tests to `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`,
> then add the pure `find_exposed_mcp_tools()` function to `claude_mcp_guard.py`
> and re-export it from `claude_code_cli.py` (`__all__` + import block). Keep it
> a pure function in the style of `_scan_mcp_servers`. Run pylint, pytest
> (`-n auto` with the integration-exclusion markers from summary.md) and mypy;
> fix everything; format; commit as a single commit.
