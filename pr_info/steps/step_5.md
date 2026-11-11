# Step 5 — `verify_sections` helpers write through the builder

## LLM prompt

> Read `pr_info/steps/summary.md` (section 5) and this file. Implement step 5
> only: every `print` in `src/mcp_coder/cli/commands/verify_sections.py` goes
> through a `SectionBuilder` passed in as `out`; remove `_VALUE_COLUMN_INDENT`.
> `verify.py` passes its `out` to these helpers but its own inline `print`
> calls stay until step 6. Tests first, then code. Run pylint, pytest (fast unit
> filter, `-n auto`), mypy, vulture; all must pass. One commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py`
- `src/mcp_coder/cli/commands/verify_formatting.py` (delete `_VALUE_COLUMN_INDENT`)
- `src/mcp_coder/cli/commands/verify.py` (call sites only)
- tests listed below

## WHAT

```python
def _print_environment_section(out: SectionBuilder) -> None: ...
def _format_code_row(project_dir: Path, symbols: dict[str, str], out: SectionBuilder) -> bool: ...
def _formatter_row(project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4) -> bool: ...
def _toolkit_rows(project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4) -> bool: ...
def _print_project_section(project_dir: Path, symbols: dict[str, str], out: SectionBuilder) -> bool: ...
def _print_retired_env_var_warning(symbols: dict[str, str], out: SectionBuilder) -> None: ...
def _print_langchain_readiness_warning(symbols: dict[str, str], out: SectionBuilder) -> None: ...
```

Names and return values stay; only the `out` parameter is added.

## HOW

- Import `SectionBuilder` from `.verify_render`; import `Row`, `_hint` from
  `.verify_formatting`; drop the `_VALUE_COLUMN_INDENT` and (if unused)
  `_format_row` / `_pad` imports.
- `print(_format_row(l, m, v, indent=i))` → `out.add(Row(l, m, v, i))`.
- `print()` → `out.add("")`; `print("  [Python]")` → `out.add("  [Python]")`.
- Whole-section owners open **and** close:
  - `_print_environment_section`: `out.open("ENVIRONMENT")` … `out.close()`.
  - `_print_project_section`: `out.open("PROJECT")` first; `out.close()` before
    **every** return (both the no-pyproject branch and the end).
- Row contributors only `add` into the caller's section:
  - `_print_retired_env_var_warning`: `out.add(Row(old, symbols["warning"], msg))` —
    **no** `label_width` (the section widens automatically).
  - `_print_langchain_readiness_warning`: `out.add(Row("Langchain backend", ...))`
    and `out.add(_hint(f"-> {hint}"))`.
  - `_format_code_row`, `_formatter_row`, `_toolkit_rows`: `out.add(Row(...))`.
- Update docstrings that say "Print"/"Writes directly to stdout" to say rows
  are added to *out*.
- `verify.py`: pass `out` to the four helpers it calls (`_print_environment_section(out)`,
  `_print_project_section(project_dir, symbols, out)`,
  `_print_retired_env_var_warning(symbols, out)`,
  `_print_langchain_readiness_warning(symbols, out)`). No section is open at
  those call sites yet, so contributor rows print immediately — identical to
  today's output.
- Delete `_VALUE_COLUMN_INDENT` from `verify_formatting.py`.

## Tests (write first / update)

Helpers called directly in tests get a fresh `SectionBuilder()`: whole-section
helpers close themselves, and contributor rows print immediately when no
section is open, so `capsys` assertions keep working.

- `tests/cli/commands/conftest.py` `_mock_print_project_section`: side effect
  becomes `def _header(_project_dir, _symbols, out): out.section("PROJECT", []); return True`.
- `test_verify.py` (743 lines — net change must be ≤ 0): add
  `from mcp_coder.cli.commands.verify_render import SectionBuilder`, drop the
  `_VALUE_COLUMN_INDENT` import, delete the two
  `assert expected_col == _VALUE_COLUMN_INDENT…` lines, replace the two
  `' ' * _VALUE_COLUMN_INDENT` hint asserts with `' ' * _expected_value_column()`;
  `_print_environment_section()` → `_print_environment_section(SectionBuilder())`;
  `_print_project_section(tmp_path, symbols)` → `(tmp_path, symbols, SectionBuilder())`.
- `test_verify_format_pad.py`: drop `_VALUE_COLUMN_INDENT`; compare against
  `_expected_value_column()` / the literal `32`.
- `test_verify_format_section_basic.py`: no `_VALUE_COLUMN_INDENT` left (done in step 4).
- `test_verify_sections_config.py`: `_print_environment_section(SectionBuilder())`.
- `test_verify_alignment.py`: pass `SectionBuilder()` to
  `_print_environment_section` / `_print_project_section`.
- `test_verify_project_section.py`: `_run` and the direct `_print_project_section`
  / `_toolkit_rows` calls pass `SectionBuilder()`.
- `test_verify_orchestration_env.py` `test_row_keeps_the_value_column_aligned`:
  `_print_retired_env_var_warning(STATUS_SYMBOLS, SectionBuilder())`; expected
  column `_expected_value_column(label_width=len(self._OLD))` (unchanged result: 42).
- New test in `tests/cli/commands/test_verify_render.py`:
  `_print_project_section` inside one builder renders `[Python]` rows at indent 4
  with values at the same column as the indent-2 rows (`_assert_section_aligned`);
  and, with `MCP_CODER_LLM_LANGCHAIN_ENDPOINT` set via `monkeypatch`,
  `out.open("CONFIG"); out.add(Row("Config file", "[OK]", "ok")); _print_retired_env_var_warning(STATUS_SYMBOLS, out); out.close()`
  renders both rows at value column 42.

## DATA

No new data structures; helpers return the same `bool` / `None` as before.
