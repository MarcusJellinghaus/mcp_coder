# Step 2 — `_pyproject_section` + the legacy `implement` readers

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Step 1 (`mcp_coder_section` in `config/toml_utils.py`) is done. Write the
> tests first, then the code. Run pylint, the fast pytest set (`-n auto`),
> mypy and ruff; all must pass. Run `run_format_code`, then commit tests +
> code as one commit.

## WHERE

- `src/mcp_coder/utils/pyproject_config.py`
- `tests/utils/test_pyproject_config.py`
- `tests/workflow_steps/test_commit.py`

## WHAT

```python
def _pyproject_section(
    project_dir: Path, table: str, *, strict: bool = False
) -> dict[str, Any]:
    """Return [tool.mcp-coder.<table>] of pyproject.toml.

    Raises:
        TomlReadError: If strict and the file is malformed or unreadable.
        ValueError: If strict and 'tool', 'mcp-coder' or *table* is not a table.
    """
```

Rewired readers (signatures unchanged):

```python
def has_legacy_format_code_key(project_dir: Path) -> bool:
    return "format_code" in _pyproject_section(project_dir, "implement")

def get_leftover_check_type_hints(project_dir: Path) -> Any | None:
    return _pyproject_section(project_dir, "implement").get("check_type_hints")
```

## ALGORITHM

```
data = _load_pyproject(project_dir, strict=strict)
try:
    return mcp_coder_section(data, str(project_dir / "pyproject.toml"), table)
except ValueError:
    if strict: raise
    return {}          # lax: default, no logging
```

## HOW

- Import `mcp_coder_section` from `..config.toml_utils` next to the existing imports.
- Docstrings of the two readers: a non-table `tool` / `mcp-coder` / `implement`
  counts as absent (a string or list `implement` is not the legacy key).
- The install readers and `get_github_install_config` are untouched in this step.

## DATA

- `has_legacy_format_code_key` → `bool`; `get_leftover_check_type_hints` → raw value or `None`.

## Tests

`tests/utils/test_pyproject_config.py`:
- New module-level list `_NON_TABLE_IMPLEMENT` (pyproject.toml contents):
  `"tool = 1\n"`, `"[tool]\nmcp-coder = 1\n"`, `"[tool.mcp-coder]\nimplement = 1\n"`,
  `'[tool.mcp-coder]\nimplement = "format_code"\n'`,
  `'[tool.mcp-coder]\nimplement = ["format_code"]\n'`.
- New class `TestNonTableImplement`, parametrized over that list:
  `has_legacy_format_code_key(tmp_path) is False`,
  `get_leftover_check_type_hints(tmp_path) is None`, no WARNING records (`caplog`).
- `TestMalformedTomlRegression`: add `has_legacy_format_code_key` returns False on `MALFORMED_TOML`.

`tests/workflow_steps/test_commit.py`, class `TestCheckFormatterConfig`:
- Parametrized `check_formatter_config(tmp_path, warn_legacy_key=True)`:
  - `"tool = 1\n"` → returns a message containing `"'tool'"`;
  - `"[tool]\nmcp-coder = 1\n"` → message containing `"'mcp-coder'"`;
  - the three `implement` contents → returns `None`.
  - Every case: no exception, `LEGACY_WARNING not in caplog.text`.
  (The `tool` / `mcp-coder` error comes from `load_toolkit` → `find_mcp_coder_table`;
  the autouse `_resolvable_formatter` calls the real lookup first, so it still raises.)

## Commit message

`fix(config): treat a non-table implement, tool or mcp-coder as absent in legacy readers`
