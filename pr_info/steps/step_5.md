# Step 5 — MCP Config Warnings Section + Log Filter

## Goal

Parse `.mcp.json` for unresolved `${...}` placeholders in `mcpServers[*].env[*]` values, render them as a new `=== MCP CONFIG WARNINGS ===` section, and suppress the raw `WARNING: env['PYTHONPATH']...` stdout lines from `langchain_mcp_adapters` via a scoped log filter.

Section is omitted when no findings or `.mcp.json` is missing/invalid.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement Step 5 as a single commit: add `_collect_mcp_warnings(path)` helper and `_DropUnexpandedWarnings` logging.Filter subclass in `src/mcp_coder/cli/commands/verify.py`. Apply the filter around the `verify_mcp_servers()` call (try/finally). Render the new section between the langchain-MCP section and the test-prompt / MLflow sections. Write tests first for the parser (found / not found / missing file / invalid JSON) and for the section being omitted when clean. Run pylint, pytest, mypy.

## WHERE

- **Modify:** `src/mcp_coder/cli/commands/verify.py`
- **Modify tests:** `tests/cli/commands/test_verify_orchestration.py` — add `TestMcpConfigWarnings` class

## WHAT

```python
class _DropUnexpandedWarnings(logging.Filter):
    """Scoped filter that drops langchain-mcp-adapters unresolved-var warnings."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "unexpanded variable" not in record.getMessage()


def _collect_mcp_warnings(mcp_json_path: str | None) -> list[str]:
    """Parse .mcp.json for unresolved ${...} placeholders in server env values.

    Args:
        mcp_json_path: Path to .mcp.json (or None).

    Returns:
        Pre-formatted lines "server / env_var  unresolved_template", empty if
        no findings or file is missing/invalid.
    """
```

Wrap the existing call in `execute_verify`:
```python
lc_logger = logging.getLogger("langchain_mcp_adapters")
log_filter = _DropUnexpandedWarnings()
lc_logger.addFilter(log_filter)
try:
    mcp_result = verify_mcp_servers(mcp_config_resolved, env_vars=env_vars)
finally:
    lc_logger.removeFilter(log_filter)
```

Immediately after the langchain-MCP server list is printed, BEFORE the MCP edit smoke test and test-prompt rows, call the warnings renderer:
```python
warnings = _collect_mcp_warnings(mcp_config_resolved)
if warnings:
    print(_pad("MCP CONFIG WARNINGS"))
    for line in warnings:
        print(f"  {line}")
```

Placement is explicit: the MCP CONFIG WARNINGS section appears directly after the langchain-MCP server list, and BEFORE the smoke-test / test-prompt rows that currently print at the end of the langchain-MCP section output.

## HOW

- Import at top of `verify.py`: add `import json` and `import re` (both new). `logging` and `from pathlib import Path` are already imported — the helper depends on them being available.
- Use `json.load` to read `.mcp.json`; wrap in `try/except (OSError, json.JSONDecodeError)` → return `[]`.
- Use `re.search(r"\$\{[^}]+\}", value)` to detect whether the value contains ANY unresolved placeholder.
- For each server in `config.get("mcpServers", {})`, iterate `server.get("env", {})` dict values.
- If any `${...}` placeholder is present, emit **one** row per `(server, env_var)` with the **full original value** (including any non-placeholder suffix like `/src` or `\Lib\`). Do not split on matches; do not emit multiple rows per value.
- Output row format: `f"{server_name} / {env_var}  {full_value}"` (two-space separator between label and full value). Example: `tools-py / PYTHONPATH  ${MCP_CODER_PROJECT_DIR}/src`.

## ALGORITHM

```
try: data = json.loads(Path(path).read_text())
except (OSError, json.JSONDecodeError): return []
lines = []
for server_name, server in data.get("mcpServers", {}).items():
    for env_var, value in server.get("env", {}).items():
        if re.search(r"\$\{[^}]+\}", value):
            lines.append(f"{server_name} / {env_var}  {value}")
return lines
```

One row per env var that contains any `${...}` placeholder; emit the full unresolved value. Aligns with the issue body's expected output and the existing `test_unresolved_placeholder_found` test (which asserts `"tools-py / PYTHONPATH  ${MCP_CODER_PROJECT_DIR}/src"` — full value including the `/src` suffix).

## DATA

- Input: `str | None` path.
- Output: `list[str]` of formatted rows (empty list → section omitted).

## Tests to Add

```python
class TestMcpConfigWarnings:
    def test_none_path_returns_empty(self) -> None:
        assert _collect_mcp_warnings(None) == []

    def test_missing_file_returns_empty(self, tmp_path) -> None:
        assert _collect_mcp_warnings(str(tmp_path / "nope.json")) == []

    def test_invalid_json_returns_empty(self, tmp_path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text("{not json")
        assert _collect_mcp_warnings(str(p)) == []

    def test_unresolved_placeholder_found(self, tmp_path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(json.dumps({
            "mcpServers": {
                "tools-py": {"env": {"PYTHONPATH": "${MCP_CODER_PROJECT_DIR}/src"}}
            }
        }))
        result = _collect_mcp_warnings(str(p))
        assert result == ["tools-py / PYTHONPATH  ${MCP_CODER_PROJECT_DIR}/src"]

    def test_no_placeholders_returns_empty(self, tmp_path) -> None:
        p = tmp_path / ".mcp.json"
        p.write_text(json.dumps({
            "mcpServers": {"srv": {"env": {"PATH": "/usr/bin"}}}
        }))
        assert _collect_mcp_warnings(str(p)) == []

    def test_multiple_servers_multiple_vars(self, tmp_path) -> None:
        # two servers, each with one unresolved var → 2 lines

    def test_section_omitted_when_clean(self, capsys, ...) -> None:
        # execute_verify with clean .mcp.json: "MCP CONFIG WARNINGS" NOT in output

    def test_section_rendered_when_findings(self, capsys, ...) -> None:
        # execute_verify with unresolved vars: section header and findings present

    def test_log_filter_suppresses_unexpanded_warning(self, caplog, ...) -> None:
        # stdout does not contain "WARNING: env['PYTHONPATH']..."


class TestDropUnexpandedFilter:
    def test_drops_unexpanded_message(self) -> None:
        f = _DropUnexpandedWarnings()
        rec = logging.LogRecord("x", logging.WARNING, "", 0,
            "env['PYTHONPATH'] contains unexpanded variable reference: 'X'",
            None, None)
        assert f.filter(rec) is False

    def test_passes_other_messages(self) -> None:
        f = _DropUnexpandedWarnings()
        rec = logging.LogRecord("x", logging.WARNING, "", 0, "normal warning", None, None)
        assert f.filter(rec) is True
```

## Verification

All three checks must pass. After this step, the full verify output matches the layout specified in the issue (Environment → Config → Prompts → … → MCP Config Warnings → MLflow → Install Instructions).
