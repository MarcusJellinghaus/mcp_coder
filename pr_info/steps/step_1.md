# Step 1 — `Toolkit [OK]` row names its config source

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_1.md`)
only. Follow TDD: update/add the tests first, see them fail, then change the code.
Run `mcp__mcp-tools-py__run_format_code`, pylint, pytest (unit markers, `-n auto`)
and mypy; all must pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_toolkit_rows.py` — `toolkit_rows`
- `tests/cli/commands/test_verify_toolkit_rows.py`
- `tests/cli/commands/test_verify_project_section.py`

## WHAT

Signature unchanged:

```python
def toolkit_rows(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4
) -> bool: ...
```

Only the value of the `[OK]` `Toolkit` row changes.

## HOW

In `toolkit_rows`, replace

```python
out.add(Row("Toolkit", symbols["success"], loaded.name, indent))
```

with

```python
out.add(Row("Toolkit", symbols["success"], f"{loaded.name} ({loaded.config.source})", indent))
```

(`loaded.config` is the `ToolkitConfig`; `source` is the file name the table came
from.) The `[ERR]` row on `ValueError` stays unchanged. Update the docstring's first
line to say the Toolkit row names its config file.

## DATA

`Toolkit [OK] command (mcp-coder.toml)`, `Toolkit [OK] mcp-tools-py (pyproject.toml)`.

## Tests

Note: the autouse fixture `_resolvable_formatter` (`tests/conftest.py`) fakes
`("pyproject.toml", {"toolkit": "mcp-tools-py"})` when no file names a toolkit,
so the default Toolkit row reads `mcp-tools-py (pyproject.toml)` even without
`pyproject.toml`. Tests of the source below write the toolkit table into the file
under test.

`tests/cli/commands/test_verify_toolkit_rows.py`:
- Add `test_toolkit_row_names_source(run)`: `result = run()`;
  assert `"[OK]"` and `"fake (mcp-coder.toml)"` in `result.row("Toolkit")`
  (the `run` fixture writes `toolkit = "fake"` into `mcp-coder.toml`).

`tests/cli/commands/test_verify_project_section.py`:
- `TestToolkitRows.test_default_toolkit_row`: expected value
  `"mcp-tools-py (pyproject.toml)"` (indent stays 4 in this step).
- `TestToolkitRows.test_mcp_coder_toml_without_pyproject`: expected value
  `"mcp-tools-py (mcp-coder.toml)"`, indent 2.
- `TestCommandToolkitGating.test_command_project_has_no_formatter_row`: expected
  value `"command (mcp-coder.toml)"`, indent 2.
- Add `TestToolkitRows.test_toolkit_table_in_pyproject_names_it`:
  `_run(tmp_path, '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n', capsys)`;
  `row = _row(lines, "Toolkit")`; assert `"[OK]" in row` and
  `"mcp-tools-py (pyproject.toml)" in row` (indent-independent on purpose).

Search the tests for any other exact `Toolkit [OK]` expectation
(`_format_row("Toolkit", "[OK]", ...)`) and update its value the same way.
