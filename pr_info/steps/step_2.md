# Step 2 — Flat PROJECT layout with the `Project config` row

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_2.md`)
only; step 1 (Toolkit row names its source) is already done. Follow TDD: update/add
the tests first, see them fail, then change the code. Run
`mcp__mcp-tools-py__run_format_code`, pylint, pytest (unit markers, `-n auto`) and
mypy; all must pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py` — `_print_project_section`
- `src/mcp_coder/cli/commands/verify_toolkit_rows.py` — `check_type_hints_row`
- Tests: `test_verify.py`, `test_verify_project_section.py`,
  `test_verify_alignment.py`, `test_verify_render.py`, `test_verify_setup.py`,
  `test_verify_check_type_hints.py` (all under `tests/cli/commands/`)

## WHAT

Signatures unchanged:

```python
def _print_project_section(project_dir: Path, symbols: dict[str, str], out: SectionBuilder) -> bool
def check_type_hints_row(project_dir: Path, symbols: dict[str, str], out: SectionBuilder) -> bool
```

## HOW

- `verify_sections.py`: add `from ...config.toml_utils import MCP_CODER_CONFIG_FILES`
  (same import `verify_project_keys.py` uses).
- Delete the `pyproject_exists` check and the Python branch (`pyproject.toml found`,
  `Language`, blank line, `"  [Python]"`, indent-4 calls). Keep one path.
- `legacy format_code` row: indent 4 → 2 (or drop the indent argument; `Row`'s
  default is 2).
- `check_type_hints_row`: both hard-coded `4` → `2` (or drop them; `Row` default 2).
- Update `_print_project_section`'s docstring: no "language detection"; it
  prints the project config files, `.mcp-file-access` and tool config.
- Do not change the `indent` defaults of `toolkit_rows`, `setup_rows`,
  `_format_code_row`; the call site passes `indent=2`.

## ALGORITHM

```
out.open("PROJECT")
found = [n for n in MCP_CODER_CONFIG_FILES if (project_dir / n).is_file()]
add Row("Project config", success, ", ".join(found)) if found else Row("Project config", warning, "none")
file_access_ok = _file_access_row(...); ok = _format_code_row(..., indent=2)
ok = toolkit_rows(..., indent=2) and ok; ok = setup_rows(..., indent=2) and ok
if has_legacy_format_code_key: add legacy row (failure, indent 2); ok = False
ok = check_type_hints_row(...) and ok; add key_warning_rows; out.close(); return ok and file_access_ok
```

## DATA

Returns `bool` as before. The `Project config` row never changes it.
Row order: `Project config`, `.mcp-file-access`, `format_code`, `Toolkit` (+ groups
at indent 4/6), `Setup` (+ sub-rows at indent 4), `legacy format_code`,
`check_type_hints`, key-warning rows.

## Tests

Every nested toolkit row moves 2 columns left: group headers `"    format"`
(was 6 spaces), items at 6 spaces (was 8).

`test_verify.py` `TestProjectSection`:
- `test_project_section_python_both_enabled` / `_python_defaults`: replace the
  `pyproject.toml` / `Language` asserts with
  `_format_row("Project config", "[OK]", "pyproject.toml", indent=2) in out`;
  `format_code` expected at indent 2; assert `"Language" not in out` and
  `"[Python]" not in out`.
- `test_project_section_non_python` → rename to `test_project_section_no_config_files`:
  capture the return value; assert
  `_format_row("Project config", "[WARN]", "none", indent=2) in out`, `ok is True`,
  no `Language`, no `[Python]`. No `real_toolkit_config` marker (the faked
  toolkit passes, so only this row is under test).

`test_verify_project_section.py`:
- `TestFileAccessRow.test_row`: anchor on the line whose stripped text starts with
  `"Project config "` instead of `"Language "`; the next line still starts with
  `"  .mcp-file-access "`. Update the class docstring.
- `TestFormatCodeRow`: the three `indent=4` expectations → `indent=2`.
- `TestToolkitRows`:
  - `test_default_toolkit_row`: indent 2.
  - `test_formatter_item_shown`: `"    format" in lines`; `ruff`/`formatter` at indent 6.
  - `test_error_item_fails_section`: `ruff` at indent 6.
  - `test_warning_item_does_not_fail`: `"    check" in lines`; `mypy` at indent 6.
  - `test_verify_raising_is_error`: `lines.index("    format")`.
  - `test_toolkit_item_row_aligns_with_section`: prefixes `"      ruff "`,
    `"  format_code "`, and `_row(lines, "Project config").startswith("  Project config ")`.
- `TestCommandToolkitGating.test_command_project_has_no_formatter_row` (acceptance:
  only `mcp-coder.toml`, `toolkit = "command"`): additionally assert
  `_row(lines, "Project config") == _format_row("Project config", "[OK]", "mcp-coder.toml", indent=2)`,
  `not any("pyproject.toml" in line for line in lines)`, and no line with
  `"Language"` or `"[Python]"`.
- Add `TestProjectLayout.test_both_files_order` (acceptance: both files):
  - `pyproject.toml`: `"[tool.mcp-coder.implement]\nformat_code = true\ncheck_type_hints = true\n"`
  - `mcp-coder.toml`: `'[tool.mcp-coder]\nbogus = 1\n[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n'`
  - run `_print_project_section`; assert
    `_row(lines, "Project config") == _format_row("Project config", "[OK]", "pyproject.toml, mcp-coder.toml", indent=2)`;
  - for labels `["Project config", ".mcp-file-access", "format_code", "Toolkit",
    "Setup", "legacy format_code", "check_type_hints", "mcp-coder.toml"]`, take
    `lines.index(_row(lines, label))` and assert the indices are strictly
    increasing (`mcp-coder.toml` is the key-warning row for `bogus`);
  - assert every one of those rows starts with exactly 2 spaces then a non-space.

`test_verify_alignment.py` `test_print_project_section`: `"      ruff "` (6 spaces).

`test_verify_render.py` `test_project_section_nested_rows_share_value_column`:
`"  [Python]" not in lines`; prefixes `("  Project config ", "  format_code ", "      ruff ")`.
(Leave the `"  [Python]"` sample strings at lines ~98/147 alone; they test the
builder, not this section.)

`test_verify_setup.py` `TestProjectSectionWiring.test_setup_row_present`:
both parametrize cases use indent 2 (`(False, 2, "nothing to do")`,
`(True, 2, "default: python built-in")`); update the class docstring
("in both branches" no longer applies).

`test_verify_check_type_hints.py` `test_non_false_value_warns`:
`lines[0].startswith("  check_type_hints")`.

Also update the docstring of `test_verify_project_section.py` if it mentions
`Language`.
