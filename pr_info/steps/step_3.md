# Step 3 — `mcp_servers_of` helper; `rebase_settings` uses it (Scope 3, derivation)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`).
> Implement Step 3 only: move the `mcp__<server>__` prefix derivation from
> `workflows/rebase_permissions.py::rebase_settings` into
> `utils/toolkit_runner.py` as `mcp_servers_of`, and make `rebase_settings` use
> it. No behaviour change in `rebase_settings`. Tests first, then code. Run
> format, pylint, mypy, lint-imports, tach and the fast pytest set. One commit.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py` — add `WORKSPACE_SERVER`, `mcp_servers_of`
- `src/mcp_coder/workflows/rebase_permissions.py` — drop `_WORKSPACE_SERVER`, use the helper
- Tests: `tests/utils/test_toolkit_permissions.py` (or `test_toolkit_runner.py`)
  for the helper; existing rebase permission tests must stay green unchanged

## WHAT

```python
WORKSPACE_SERVER = "mcp-workspace"

def mcp_servers_of(permissions: Sequence[str]) -> list[str]:
    """MCP servers named by the mcp__<server>__ prefixes of permissions.

    Returns:
        "mcp-workspace" first, then the other servers sorted. Bash( entries and
        anything not starting with "mcp__" are ignored.
    """
```

## ALGORITHM

```
others = {p.split("__")[1] for p in permissions if p.startswith("mcp__")}
return [WORKSPACE_SERVER] + sorted(others - {WORKSPACE_SERVER})
```

`rebase_settings`: `servers = mcp_servers_of(extra)` replaces the two inline
lines; `_WORKSPACE_TOOLS` stays in `rebase_permissions.py`.

## DATA

`list[str]`, e.g. `["mcp-workspace", "mcp-tools-py"]`; `[]` input → `["mcp-workspace"]`.

## Tests (write first)

- `[]` → `["mcp-workspace"]`
- `["Bash(npm test)"]` → `["mcp-workspace"]`
- `["mcp__mcp-tools-py__run_pytest_check", "mcp__a__x", "mcp__mcp-workspace__git"]`
  → `["mcp-workspace", "a", "mcp-tools-py"]`
