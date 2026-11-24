# Step 2 — Lenient lookup, `format_code` from either file, `format_code` row for every repo

See `pr_info/steps/summary.md` (design changes 2 and 3).

## WHERE

- `src/mcp_coder/config/toml_utils.py` — add `find_mcp_coder_table_lenient`, a module `logger`.
- `src/mcp_coder/utils/pyproject_config.py` — `FormatCodeSetting`, `get_format_code`.
- `src/mcp_coder/cli/commands/verify_sections.py` — `_format_code_row`, `_print_project_section`.
- Tests:
  - new `tests/config/test_toml_utils.py`;
  - `tests/utils/test_pyproject_config.py` (`TestGetFormatCode`);
  - `tests/cli/commands/test_verify_project_section.py` (`TestFormatCodeRow`);
  - `tests/cli/commands/test_verify.py` (`TestProjectSection`).

## WHAT

```python
# config/toml_utils.py
logger = logging.getLogger(__name__)

def find_mcp_coder_table_lenient(project_dir: Path, key: str) -> tuple[str, Any] | None:
    """Like find_mcp_coder_table, but log a warning and return None on a problem."""

# utils/pyproject_config.py
@dataclass(frozen=True)
class FormatCodeSetting:
    enabled: bool          # True when absent
    source: str | None     # file the key came from; None = default

def get_format_code(project_dir: Path) -> FormatCodeSetting: ...  # Raises ValueError only for a non-bool value

# cli/commands/verify_sections.py
def _format_code_row(project_dir: Path, symbols: dict[str, str], out: SectionBuilder, indent: int = 4) -> bool: ...
```

## ALGORITHM

```
find_mcp_coder_table_lenient(dir, key):
    try: return find_mcp_coder_table(dir, key)
    except ValueError as exc:
        logger.warning("%s; using the default for [tool.mcp-coder] %s", exc, key)
        return None

get_format_code(dir):
    found = find_mcp_coder_table_lenient(dir, "format_code")
    if found is None: return FormatCodeSetting(enabled=True, source=None)
    source, value = found
    if not isinstance(value, bool): raise ValueError(... names dir / source ...)
    return FormatCodeSetting(enabled=value, source=source)
```

`_format_code_row` value text:
- `source is None` → `"enabled (default)"`
- otherwise → `f"{'enabled' if enabled else 'disabled'} ({source})"`, e.g.
  `"disabled (mcp-coder.toml)"`.

The `ValueError` branch still adds an `[ERR]` row and returns False, but
uses the new `indent` parameter instead of the hard-coded 4. The `[OK]` row
uses `indent` as well.

`_print_project_section`, no-`pyproject.toml` branch: after `_file_access_row`
call `ok = _format_code_row(project_dir, symbols, out, indent=2)`, then
`ok = toolkit_rows(...) and ok`, then `ok = setup_rows(...) and ok`. The
`pyproject.toml` branch is unchanged. It still calls the row with indent 4.

## HOW

- `get_format_code` no longer calls `_load_pyproject`. `_load_pyproject` stays
  for the install and legacy readers.
- Callers of `get_format_code` (`workflow_steps/commit.py`,
  `verify_toolkit_rows._formatting_enabled`) use only `.enabled` and need no
  change.
- Update the `get_format_code` docstring: it reads `pyproject.toml`, else
  `mcp-coder.toml`. A malformed file, or the key in both files, gives the
  default and a logged warning.

## DATA

`FormatCodeSetting(enabled: bool, source: str | None)`. The `explicit` field
is removed; `explicit` is equivalent to `source is not None`.

## Tests (write first)

`tests/config/test_toml_utils.py::TestFindMcpCoderTableLenient`:
- key absent / no files → None;
- `pyproject.toml` only → `("pyproject.toml", value)`;
- `mcp-coder.toml` only → `("mcp-coder.toml", value)`;
- both files define the key → None, and `caplog` WARNING names both files;
- malformed `mcp-coder.toml` → None, and a warning;
- `tool = 1` → None, and a warning.

`tests/utils/test_pyproject_config.py::TestGetFormatCode`:
- replace `explicit=...` with `source=...` in the existing asserts;
- the malformed `pyproject.toml` case still gives the default (now also logs a warning);
- new: `mcp-coder.toml` only, `format_code = false` → `FormatCodeSetting(False, "mcp-coder.toml")`;
- new: both files → default and a warning;
- new: malformed `mcp-coder.toml` → default and a warning;
- new: non-bool in `mcp-coder.toml` → `ValueError` whose message contains
  `str(tmp_path / "mcp-coder.toml")`.

`tests/cli/commands/test_verify_project_section.py::TestFormatCodeRow`:
- `test_true_is_enabled` expects `"enabled (pyproject.toml)"`;
- `test_false_is_disabled` expects `"disabled (pyproject.toml)"`;
- new: only `mcp-coder.toml`, containing
  `[tool.mcp-coder]\nformat_code = false\n[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n`
  → row `_format_row("format_code", "[OK]", "disabled (mcp-coder.toml)", indent=2)`;
- new: no files → row `"enabled (default)"` at indent 2;
- new: only `mcp-coder.toml` with `format_code = "no"` → `[ERR]` row at indent 2,
  and `_print_project_section` returns False.

`tests/cli/commands/test_verify.py::TestProjectSection::test_project_section_python_both_enabled`
expects `"enabled (pyproject.toml)"`.

## Checks

pylint, mypy, pytest (fast set), lint-imports, tach, vulture; then
`run_format_code`. One commit: `feat(config): read format_code from mcp-coder.toml`.

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` with
> TDD: write and update the listed tests first, then:
> - add `find_mcp_coder_table_lenient` to `config/toml_utils.py`;
> - switch `get_format_code` to it, replacing `FormatCodeSetting.explicit` with `source`;
> - make `_format_code_row` name the source and show it for repos without
>   `pyproject.toml`.
>
> Run pylint, mypy, pytest, lint-imports, tach and vulture. Commit once.
