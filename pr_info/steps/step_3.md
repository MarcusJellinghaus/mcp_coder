# Step 3 — Install readers and `get_github_install_config`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> Steps 1–2 are done (`mcp_coder_section` in `toml_utils.py`,
> `_pyproject_section` in `pyproject_config.py`). Write the tests first, then
> the code. Run pylint, the fast pytest set (`-n auto`), mypy and ruff; all
> must pass. Run `run_format_code`, then commit tests + code as one commit.

## WHERE

- `src/mcp_coder/utils/pyproject_config.py`
- `tests/utils/test_pyproject_config.py`
- `tests/cli/commands/test_install.py`
- `tests/install/test_project_setup.py`
- `tests/workflows/vscodeclaude/test_validate_target_repo_setup.py`

## WHAT (signatures unchanged)

```python
def get_install_extras(project_dir: Path, *, strict: bool = False) -> str | None
def get_post_install_checks(project_dir: Path, *, strict: bool = False) -> tuple[tuple[str, ...], ...]
def get_github_install_config(project_dir: Path) -> GitHubInstallConfig
```

## HOW

- `get_install_extras` / `get_post_install_checks`: replace
  `data = _load_pyproject(...)` + the `.get` chain with
  `section = _pyproject_section(project_dir, "install", strict=strict)`.
- `get_github_install_config`: replace the `.get` chain with
  `gh = mcp_coder_section(_load_pyproject(project_dir), str(path), "install-from-github")`
  (`path = project_dir / "pyproject.toml"`, moved above). Lax load keeps the
  malformed-file defaults; a non-table shape raises `ValueError`.
- Docstrings: add to `Raises` — strict install readers and
  `get_github_install_config` raise `ValueError` naming the file and key when
  `tool`, `mcp-coder` or the sub-table is not a table; add
  `# noqa: DOC502` where the raise comes from a callee.
- No entry-point source changes: `execute_install`, `project_setup`'s python
  built-in and `_warn_python_policy` already handle `ValueError`.

## ALGORITHM

None beyond the substitutions above.

## DATA

Unchanged return types. Lax non-table → `None` / `()` without logging;
strict / github non-table → `ValueError("Invalid 'install' in <path>: expected a table, got int: 1")`.

## Tests

`tests/utils/test_pyproject_config.py`:
- `_NON_TABLE_INSTALL = ["tool = 1\n", "[tool]\nmcp-coder = 1\n", "[tool.mcp-coder]\ninstall = 1\n"]`
  with the expected key fragment (`'tool'`, `'mcp-coder'`, `'install'`).
  - lax: `get_install_extras` → `None`, `get_post_install_checks` → `()`, no WARNING records.
  - strict: both raise `ValueError` whose message contains `str(tmp_path / "pyproject.toml")` and the key fragment.
- `_NON_TABLE_GITHUB = ["tool = 1\n", "[tool]\nmcp-coder = 1\n", "[tool.mcp-coder]\ninstall-from-github = 1\n"]`:
  `get_github_install_config` raises `ValueError` naming the path and key.
- Malformed-file additions (`MALFORMED_TOML`): `get_post_install_checks` lax → `()`;
  `get_post_install_checks(strict=True)` and `get_install_extras(strict=True)` raise `TomlReadError`
  (`pytest.raises(TomlReadError)`, import from `mcp_coder.config.toml_utils`).

`tests/cli/commands/test_install.py`:
- Parametrize the existing `test_invalid_target_pyproject_returns_one` over
  `(content, key)`: the existing `packages = "pkg-a"` case (`"packages"`),
  `"tool = 1\n"` (`"'tool'"`), `"[tool]\nmcp-coder = 1\n"` (`"'mcp-coder'"`),
  `"[tool.mcp-coder]\ninstall = 1\n"` (`"'install'"`),
  `"[tool.mcp-coder]\ninstall-from-github = 1\n"` (`"'install-from-github'"`).
  Keep `--check` and the `ensure_system_uv` stub. Add `caplog`: the logged error
  contains `str(tmp_path / "pyproject.toml")` and the key.

`tests/install/test_project_setup.py` (class holding `test_value_error_becomes_setup_error`):
- `test_non_table_install_becomes_setup_error`: write
  `"[tool.mcp-coder]\ninstall = 1\n"` to `tmp_path / "pyproject.toml"`,
  `mocks.set_steps(_PYTHON)`,
  `mocks.install_config.from_args.side_effect = InstallConfig.from_args`
  (real class: `from mcp_coder.install import InstallConfig`);
  `pytest.raises(SetupError, match="'install'")`; `mocks.install.assert_not_called()`.
- `test_install_value_error_becomes_setup_error`: `mocks.set_steps(_PYTHON)`,
  `mocks.install.side_effect = ValueError("bad overrides")` →
  `pytest.raises(SetupError, match="bad overrides")`.

`tests/workflows/vscodeclaude/test_validate_target_repo_setup.py`:
- New class `TestNonTablePolicy`, parametrized over
  `"[tool.mcp-coder]\ninstall = 1\n"` and `"[tool.mcp-coder]\ninstall-from-github = 1\n"`:
  `_write_mcp_json(tmp_path)`, write pyproject, `validate_target_repo(tmp_path)` does not
  raise; exactly one warning, containing `"cannot be read as target-repo policy"`
  and the key name.

## Commit message

`fix(install): reject a non-table install or install-from-github with a clear error`
