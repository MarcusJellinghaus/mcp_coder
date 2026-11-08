# Step 4: Toolkit rows in `mcp-coder verify`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **step 4** as described in
> `pr_info/steps/step_4.md`. Steps 1–3 are done. Write the tests first, then change
> `cli/commands/verify_sections.py`. Run pylint, mypy, pytest (fast unit tests),
> lint-imports and format, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py`
- `tests/cli/commands/test_verify_project_section.py`

## WHAT

```python
def _toolkit_rows(project_dir: Path, symbols: dict[str, str], *, indent: int = 4) -> bool
```

Import `load_toolkit, verify_toolkit` from `...utils.toolkit_runner`. Keep
`from ...mcp_tools_py import resolve_steps` and `_formatter_row` unchanged: the steps row
(`ruff_imports → ruff_format`) stays on the wrapper until #1199.

## ALGORITHM

```
try: loaded = load_toolkit(project_dir); items = verify_toolkit(loaded, project_dir, "format")
except ValueError as exc: print(_format_row("Toolkit", symbols["failure"], str(exc), indent=indent)); return False
print(_format_row("Toolkit", symbols["success"], loaded.name, indent=indent))
status_symbol = {"ok": "success", "warning": "warning", "error": "failure"}
for item in items: skip item.name == "formatter" (the Formatter row covers it)
    print(_format_row(item.name, symbols[status_symbol[item.status]], item.message or item.status, indent=indent + 2))
return all(item.status != "error" for item in items if item.name != "formatter")
```

`_print_project_section`:
- no `pyproject.toml` branch: `ok = _formatter_row(..., indent=2)`, then
  `ok = _toolkit_rows(project_dir, symbols, indent=2) and ok`, return `ok` (toolkit items
  print even without a `pyproject.toml`, e.g. for a `mcp-coder.toml` project).
- Python branch: after the Formatter row, `ok = _toolkit_rows(project_dir, symbols) and ok`.

Call order matters only for output; evaluate both rows (no short-circuit skipping a row).

## DATA

- `_toolkit_rows` → `False` when the config fails to load or any non-`formatter` item has
  status `error`; `warning` items print with the warning symbol and do not fail.
- `mcp-coder verify` exit code keeps its meaning: it already turns a `False` PROJECT
  section into exit 1.

## HOW

- Existing tests in `test_verify_project_section.py` assert `ok is True` with only a
  formatter declared. Add an autouse fixture in that file patching
  `mcp_coder.cli.commands.verify_sections.verify_toolkit` to return
  `[VerifyItem("formatter", "ok")]`, so existing expectations stay unchanged; the new
  tests override it.

## Tests (write first)

New `TestToolkitRows`:
- Default (no toolkit table) → `Toolkit` row `[OK]` with `mcp-tools-py`.
- Items `[VerifyItem("ruff", "ok"), VerifyItem("formatter", "error", "x")]` → a `ruff`
  row `[OK]`, no `formatter` row from the toolkit, the wrapper's `Formatter` row still
  present; toolkit part does not fail the section.
- Item `VerifyItem("ruff", "error", "ruff not available")` → `[ERR]` row, section `False`.
- `warning` item → `[WARN]` row, section still `True`.
- Invalid `[tool.mcp-coder.toolkit]` (unknown key) → `Toolkit` `[ERR]` row with the
  message, section `False`.
- `verify_toolkit` raising `ValueError` → `Toolkit` `[ERR]` row, section `False`.
- No `pyproject.toml`, `mcp-coder.toml` with `[tool.mcp-coder.toolkit] toolkit = "mcp-tools-py"`
  → `Toolkit` row printed.
- Existing `TestFormatterRow` / `TestFormatCodeRow` / `TestLegacyKeyRow` /
  `TestExecuteVerifyProjectExit` pass unchanged.
