# Step 4 — `labels-config` from either file, CLI help

See `pr_info/steps/summary.md` (design changes 1 and 2). Depends on step 2.

## WHERE

- `src/mcp_coder/config/label_config.py`
- `src/mcp_coder/cli/gh_parsers.py` (2 strings)
- `docs/getting-started/label-setup.md` (the `--config` row that mirrors the help string)
- `tests/config/test_label_config.py`

## WHAT

```python
# rename: _get_labels_config_from_pyproject -> _get_labels_config_from_project
def _get_labels_config_from_project(project_dir: Path) -> Path | None:
    """Read [tool.mcp-coder] labels-config from pyproject.toml, else mcp-coder.toml."""
```

`get_labels_config_path` keeps its signature.

## ALGORITHM

```
found = find_mcp_coder_table_lenient(project_dir, "labels-config")
if found is None: return None
resolved = project_dir / found[1]
return resolved if resolved.exists() else None
```

## HOW

- Rename the helper with `mcp__mcp-tools-py__rename_symbol`, so the tests
  follow, including `TestGetLabelsConfigFromPyproject`. Optionally rename that
  class to `TestGetLabelsConfigFromProject`.
- `from .toml_utils import find_mcp_coder_table_lenient`. This is a same-package
  import, so the layering is kept.
- Remove the `import tomllib` and the "duplicates ... on purpose" comment.
- Update the module docstring and the `get_labels_config_path` docstring: step 2
  of the resolution order becomes "`[tool.mcp-coder] labels-config` in
  `pyproject.toml`, else `mcp-coder.toml` (relative to the project root)".
- `cli/gh_parsers.py`:
  - the resolution list reads `2. [tool.mcp-coder] labels-config in pyproject.toml or mcp-coder.toml`;
  - the `--config` help reads `"Path to labels config file (overrides pyproject.toml / mcp-coder.toml and bundled defaults)"`.
- `docs/getting-started/label-setup.md` line with `--config PATH`: same text as
  the new help.

## DATA

Returns an absolute `Path`, or `None` so that the bundled defaults are used.

## Tests (write first)

In `tests/config/test_label_config.py`:
- `mcp-coder.toml` only, with `[tool.mcp-coder]\nlabels-config = "my_labels.json"\n`
  and the JSON file present → `get_labels_config_path(tmp_path)` returns that path;
- both files define `labels-config` → bundled `Traversable`, and a `caplog` warning;
- malformed `mcp-coder.toml` and a valid `pyproject.toml` `labels-config` →
  bundled `Traversable`, and a warning.

The existing pyproject tests, including `test_malformed_pyproject_toml_falls_back`,
keep passing.

## Checks

pylint, mypy, pytest (fast set), lint-imports, tach; then `run_format_code`.
One commit: `feat(config): read labels-config from mcp-coder.toml`.

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` with
> TDD:
> - add the `mcp-coder.toml` / conflict / malformed tests;
> - rename `_get_labels_config_from_pyproject` to `_get_labels_config_from_project`
>   and base it on `find_mcp_coder_table_lenient`;
> - update the docstrings, the two `gh_parsers.py` help strings and the
>   `label-setup.md` row.
>
> Run pylint, mypy, pytest, lint-imports and tach. Commit once.
