# Step 4 — Change `_collect_mcp_warnings` Return Type and Migrate `_run_mcp_edit_smoke_test`

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. Locate the target
> by function name when implementing.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Steps
> 1-3 are merged. Follow TDD: update tests first, then implement.
> Produce exactly one commit.

## WHERE

* **Source:** `src/mcp_coder/cli/commands/verify.py`
* **Tests:** `tests/cli/commands/test_verify_format_section.py`,
  `tests/cli/commands/test_verify_command.py`,
  `tests/cli/commands/test_verify_integration.py` (any test that exercises
  `_collect_mcp_warnings` or the smoke-test rendering).

## WHAT

### `_collect_mcp_warnings` (`verify.py:55-76`)

Change return type from `list[str]` to `list[tuple[str, str]]`.

```python
def _collect_mcp_warnings(mcp_json_path: str | None) -> list[tuple[str, str]]:
    """Return list of (label, value) pairs for unresolved ${...} env values."""
    ...
    findings: list[tuple[str, str]] = []
    for server_name, server in data.get("mcpServers", {}).items():
        for env_var, value in server.get("env", {}).items():
            if isinstance(value, str) and re.search(r"\$\{[^}]+\}", value):
                findings.append((f"{server_name} / {env_var}", value))
    return findings
```

Update the only caller in `execute_verify` (`verify.py` near
`MCP CONFIG WARNINGS`). The existing code already guards the whole
block on `if mcp_config_resolved:`; preserve that guard so the
section is only emitted when an MCP config path was resolved. Labels
of the form `<server> / <env_var>` can reach 35 chars (e.g.
`langchain-mcp-adapters / PYTHONPATH`), well past `_LABEL_WIDTH=22`.
Compute a per-section `label_width` so the section's value column shifts
consistently rather than overrunning row-by-row:

```python
if mcp_config_resolved:
    warnings = _collect_mcp_warnings(mcp_config_resolved)
    if warnings:
        print(_pad("MCP CONFIG WARNINGS"))
        section_label_width = max(
            _LABEL_WIDTH, max(len(label) for label, _ in warnings)
        )
        for label, value in warnings:
            print(_format_row(
                label, symbols["warning"], value,
                indent=2, label_width=section_label_width,
            ))
```

The marker symbol must match the existing verify.py code — use the
`symbols["warning"]` form (or whichever local alias the file uses, e.g.
`STATUS_SYMBOLS["warning"]`) rather than the literal `"[WARN]"` so a
future change to the symbol table cascades automatically.

**Note:** MCP CONFIG WARNINGS uses direct `print(_format_row(...))` —
no `textwrap.wrap` wrapping. Long unresolved values are emitted as a
single line; this matches existing behavior.

This is the Q2 design decision (round-1 plan review): per-section dynamic
width, clamped to `_LABEL_WIDTH` minimum. Other sections continue to use
the default `_LABEL_WIDTH`. The cross-section invariant in Step 6 relaxes
accordingly — see step_6.md for details.

### `_run_mcp_edit_smoke_test` (`verify.py:355-388`)

Replace the three return statements:

```python
return f"  {label:<20s} {symbols['success']} edit verified"
return f"  {label:<20s} {symbols['warning']} edit not verified (B not found...)"
return f"  {label:<20s} {symbols['warning']} edit not verified ({exc})"
```

with `_format_row("MCP edit smoke test", <marker>, <value>, indent=2)` calls.

## HOW

* No new imports.
* The label `"MCP edit smoke test"` is 19 chars — fits within `_LABEL_WIDTH=22`.

## ALGORITHM

Substitution; logic unchanged.

## DATA

* `_collect_mcp_warnings` return type: `list[tuple[str, str]]` (was `list[str]`).
* `_run_mcp_edit_smoke_test` continues to return `str` (single line).

## Tests

* Find every test that calls `_collect_mcp_warnings` directly. Update
  assertions from `list[str]` shape (e.g. `"server / env  ${VAR}"`) to
  `list[tuple[str, str]]` shape (e.g. `("server / env", "${VAR}")`).
* **`tests/cli/commands/test_verify_orchestration.py::TestMcpConfigWarnings`**
  has known string-pinned assertions on the old `list[str]` shape at
  **line 1093** and **lines 1117-1120**. Rewrite those assertions to the
  new `list[tuple[str, str]]` shape with the new label format
  `"<server> / <env_var>"`. (Without this update, those tests will fail
  at the type/shape level, not just on string spacing.)
* If there is no direct unit test, add one covering:
  - `None` input → `[]`
  - missing file → `[]`
  - one resolved env value → `[]`
  - one unresolved `${VAR}` → `[("server / env_var", "${VAR}/path")]`
* **Per-section dynamic width assertion (new):** add a test that drives
  the MCP CONFIG WARNINGS render path with a long label such as
  `langchain-mcp-adapters / PYTHONPATH` (35 chars) plus a short label
  in the same section. Assert that:
  1. all rows in that section have the value column at the same
     horizontal index, and
  2. that index equals `2 + max_label_len + 1 + _MARKER_SLOT_WIDTH + 1`
     (i.e. it shifts right of `32` and stays consistent within the
     section).
* Update any `test_verify_command.py` / `test_verify_integration.py`
  assertions that pin the smoke-test row format for the new widths.

## Verification

Run pylint, pytest, mypy.
