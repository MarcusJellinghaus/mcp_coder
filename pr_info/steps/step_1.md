# Step 1 — Shared walk `mcp_coder_section` in `config/toml_utils.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Write the tests first, then the code. Run pylint, the fast pytest set
> (`-n auto`), mypy and ruff; all must pass. Run `run_format_code`, then
> commit tests + code as one commit.

## WHERE

- `src/mcp_coder/config/toml_utils.py`
- `tests/config/test_toml_utils.py`

## WHAT

```python
def mcp_coder_section(
    data: dict[str, Any], label: str, table: str | None = None
) -> dict[str, Any]:
    """Return [tool.mcp-coder] (or [tool.mcp-coder.<table>]) of parsed TOML data.

    Raises:
        ValueError: If 'tool', 'mcp-coder' or *table* is present but not a
            table. Plain ValueError, not TomlReadError: the file itself parsed.
    """
```

## ALGORITHM

```
section: Any = data
for key in ("tool", "mcp-coder") + ((table,) if table else ()):
    section = section.get(key, {})
    if not isinstance(section, dict):
        raise ValueError(f"Invalid {key!r} in {label}: expected a table, "
                         f"got {type(section).__name__}: {section!r}")
return section
```

## HOW

- `find_mcp_coder_table`: replace its inline `for key in ("tool", "mcp-coder")`
  loop with `data = mcp_coder_section(load_toml(project_dir / file_name, strict=True), file_name)`.
  No `table` argument there (it also returns scalars such as `format_code`).
  The label stays the bare file name, so the message is byte-identical to today
  (`tests/utils/test_setup_config.py` matches `Invalid 'tool' in pyproject\.toml`).
- `toolkit_runner.py` keeps importing `find_mcp_coder_table` by name — no change.

## DATA

- Returns the innermost dict; `{}` for a missing level.

## Tests (`tests/config/test_toml_utils.py`, new class `TestMcpCoderSection`)

- missing levels → `{}` (empty data; `tool` without `mcp-coder`; `mcp-coder` without `table`).
- valid table returned (`{"tool": {"mcp-coder": {"install": {"extras": "dev"}}}}`, `"install"` → `{"extras": "dev"}`).
- parametrized non-table at each level (`{"tool": 1}`, `{"tool": {"mcp-coder": 1}}`,
  `{"tool": {"mcp-coder": {"install": "x"}}}` with `table="install"`):
  raises `ValueError`, `not isinstance(exc, TomlReadError)`, message contains the
  label and `'tool'` / `'mcp-coder'` / `'install'`.
- Existing `TestFindMcpCoderTable` in `tests/utils/test_setup_config.py` must pass unchanged.

## Commit message

`refactor(config): share the tool → mcp-coder table walk`
