# Step 4 — `validate_target_repo`

Makes the target-repo contract executable at launch. The `.mcp.json` row stays fatal;
the three new rows warn only (Decision 9).

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder/utils/pyproject_config.py` | add `install_extras_declared` |
| `tests/utils/test_pyproject_config.py` | cases for `install_extras_declared` |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | add `validate_target_repo`; call it at `:175` in place of `validate_mcp_json` |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | export it (`:306` import block, `:453` `__all__`) |
| `tests/workflows/vscodeclaude/test_validate_target_repo.py` | **new** |

## WHAT

```python
# pyproject_config.py — public predicate; `get_install_extras` cannot serve here
# because it returns "dev" both when the repo declares "dev" and when it declares
# nothing. Step 1's `_load_pyproject` stays private to its own module.
def install_extras_declared(project_dir: Path) -> bool:
```

```python
def validate_target_repo(folder_path: Path) -> None:
    """Validate the launch-time contract of a target repo.

    Raises:
        FileNotFoundError: If the platform's MCP config file is missing.
    """
```

## HOW

- Keep `validate_mcp_json` (`workspace.py:315`) exactly as it is — it stays exported
  (`__init__.py:372,441`) and is now called *by* `validate_target_repo`. That is the
  smallest change and keeps the fatal row in one place.
- A plain sequential function: one fatal call, then three `logger.warning` checks.
  No contract registry, no table-driven dispatch — the prose table in
  `docs/repository-setup/README.md` (Step 6) documents the same four rows.
- Reads the extras row via the new `install_extras_declared` and overrides via
  `get_github_install_config`, both lax (a malformed pyproject is the installer's
  problem, and it fails there with the file named). `validate_target_repo` imports only
  public names from `pyproject_config` — no cross-package use of `_load_pyproject`.
- `install_extras_declared` is a two-line wrapper over `_load_pyproject(project_dir)`
  inside `pyproject_config`: `True` when `[tool.mcp-coder.install]` carries an `extras`
  key, `False` for a missing key, missing section, missing or malformed file.
- Warning messages name the file and the consequence, e.g.
  `"%s declares no [tool.mcp-coder.install] extras; falling back to 'dev'"`.

## ALGORITHM

```
validate_target_repo(folder_path):
    validate_mcp_json(folder_path)                       # fatal, unchanged

    if not install_extras_declared(folder_path): warn "falling back to 'dev'"
    if get_github_install_config(...) has no packages and no packages_no_deps:
                                                warn "no sibling pinning; PyPI versions win"
    venv = folder_path/".venv"
    if venv.exists() and not (venv/"pyvenv.cfg").exists(): warn "empty/broken venv"
    if (folder_path/"venv").exists():                     warn "second venv dir; installer uses .venv"
```

## DATA

Returns `None`. Raises only `FileNotFoundError`, from `validate_mcp_json`, with its
existing message. Every other outcome is a `logger.warning` and the launch continues.

## TESTS (write first)

`tests/workflows/vscodeclaude/test_validate_target_repo.py`, using `tmp_path` plus
`caplog`:

- `.mcp.json` absent → `FileNotFoundError` (fatal row unchanged; monkeypatch
  `platform.system` so the expected filename is deterministic).
- Fully compliant repo → no warnings.
- Each warn-only row in isolation → exactly one warning logged, no exception:
  no extras key; no `install-from-github` section; `.venv` without `pyvenv.cfg`;
  a `venv/` directory alongside `.venv`.
- Missing `pyproject.toml` → warns (extras + overrides rows) but does not raise.

`tests/utils/test_pyproject_config.py` — `install_extras_declared`: `True` for a
declared `extras` (including `extras = ""`); `False` for a missing key, a missing
section, a missing file and a malformed file.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`.
>
> Implement Step 4 only. TDD: write `tests/workflows/vscodeclaude/test_validate_target_repo.py`
> and the `install_extras_declared` cases first, then add `install_extras_declared` to
> `pyproject_config.py` and `validate_target_repo` to `session_launch.py`, swap the call
> at `:175`, and export it from the package `__init__`.
>
> `validate_target_repo` must use only public `pyproject_config` names — do not import
> `_load_pyproject` across packages.
>
> Keep `validate_mcp_json` as-is and call it from the new function. Keep the
> implementation as a plain sequence of checks — no registry or table abstraction.
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check` and the fast pytest
> selection. Commit once, green.
