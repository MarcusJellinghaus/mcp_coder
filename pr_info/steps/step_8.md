# Step 8 — Per-section alignment tests, including indent 6

## LLM prompt

> Read `pr_info/steps/summary.md` and this file. Implement step 8 only:
> replace the per-indent alignment checks with the per-section consistency
> check, cover indent 6 with a toolkit-item row, and remove the now-unneeded
> filters. Test-only step — if a new assertion fails, fix the production code
> it exposes (the column rule must hold in every section). Run pylint, pytest
> (fast unit filter, `-n auto`), mypy; all must pass. One commit.

## WHERE

- `tests/cli/commands/conftest.py`
- `tests/cli/commands/test_verify_alignment.py`
- `tests/cli/commands/test_verify_project_section.py`

## WHAT

`conftest.py` — non-autouse fixture:

```python
@pytest.fixture
def toolkit_with_ruff() -> Generator[None, None, None]:
    """Stub the toolkit so a non-formatter item (ruff) renders at indent 6."""
    from mcp_tools_py.toolkit import PythonToolkit
    with (
        patch("mcp_coder.utils.toolkit_runner._toolkit_class", lambda _name: PythonToolkit),
        patch("mcp_coder.cli.commands.verify_sections.verify_toolkit",
              lambda _l, _p, _a: [VerifyItem("formatter", "ok"), VerifyItem("ruff", "ok")]),
    ):
        yield
```

The formatter-only autouse `_stub_toolkit` stays local to
`test_verify_project_section.py`.

`test_verify_alignment.py`:
- Delete `_GROUP_HEADER_RE`, `_NOTICE_PREFIXES`, `_content_lines`,
  `_assert_aligned_by_indent` and the `defaultdict` import; update the module
  docstring (per-section invariant, no hard-coded widths; MCP CONFIG WARNINGS
  is no longer special).
- Layer 1 (`TestPerFormatterAlignment`): each test asserts
  `_assert_section_aligned(_render(...)) > 0` for `_format_section`,
  `_format_mcp_section` (both `list_mcp_tools` values),
  `_format_claude_mcp_section`; and `_assert_sections_aligned(captured)` for
  `_print_environment_section(SectionBuilder())` (patch `verify_sections.version`
  so one package raises `PackageNotFoundError`, guaranteeing an `[ERR]` row) and
  `_print_project_section(tmp_path, _symbols(), SectionBuilder())`.
  Add a `_format_section` case with `[Permissions]` rows and one with a long
  JENKINS JOBS repo name (e.g. `"a-very-long-repository-name-x"`).
- `test_print_project_section` requests `toolkit_with_ruff` and additionally
  asserts a line starting with `"      ruff "` (indent 6) exists in the
  `has_pyproject=True` case.
- Layer 2 (`TestExecuteVerifyAlignmentSmoke.test_all_tabular_rows_aligned`):
  run `execute_verify` under `_make_verify_mocks()` with `toolkit_with_ruff`
  active and the autouse `_mock_print_project_section` overridden by patching
  `mcp_coder.cli.commands.verify._print_project_section` with the real
  `verify_sections._print_project_section` (so PROJECT renders its indent-4/6
  rows); `project_dir` = a `tmp_path` holding `pyproject.toml` with
  `[tool.black]`. Assert `_assert_sections_aligned(output)`, and that
  `=== LLM TEST` and `      ruff ` are in the output.

`test_verify_project_section.py`: add
`test_toolkit_item_row_aligns_with_section` using `toolkit_with_ruff`: the
`ruff` row (indent 6), `format_code` (indent 4) and `pyproject.toml` (indent 2)
rows share the value column (`_assert_section_aligned` on the captured output).

## ALGORITHM

Already provided by `_assert_section_aligned` / `_assert_sections_aligned`
(step 3): group by `=== ` header; a tabular row is a line containing a
`STATUS_SYMBOLS` token; marker column = token index; value column = first
non-space after the token, checked with `_assert_value_at_column`; lines without
a marker are skipped; all rows in a section share both columns.

## DATA

No production data changes.
