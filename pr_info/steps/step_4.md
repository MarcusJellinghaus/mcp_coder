# Step 4 — Change `_collect_mcp_warnings` Return Type and Migrate `_run_mcp_edit_smoke_test`

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
`MCP CONFIG WARNINGS`):

```python
warnings = _collect_mcp_warnings(mcp_config_resolved)
if warnings:
    print(_pad("MCP CONFIG WARNINGS"))
    for label, value in warnings:
        print(_format_row(label, "", value, indent=2))
```

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
* If there is no direct unit test, add one covering:
  - `None` input → `[]`
  - missing file → `[]`
  - one resolved env value → `[]`
  - one unresolved `${VAR}` → `[("server / env_var", "${VAR}/path")]`
* Update any `test_verify_command.py` / `test_verify_integration.py`
  assertions that pin the smoke-test row format for the new widths.

## Verification

Run pylint, pytest, mypy.
