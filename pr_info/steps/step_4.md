# Step 4 — `validate_target_repo`

Makes the target-repo contract executable at launch. The `.mcp.json` row stays fatal;
the three new rows warn only (Decision 9).

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | add `validate_target_repo`; call it at `:175` in place of `validate_mcp_json` |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | export it (`:306` import block, `:453` `__all__`) |
| `tests/workflows/vscodeclaude/test_validate_target_repo.py` | **new** |

## WHAT

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
- Reads extras via `get_install_extras` and overrides via `get_github_install_config`,
  both lax (a malformed pyproject is the installer's problem, and it fails there with
  the file named).
- Warning messages name the file and the consequence, e.g.
  `"%s declares no [tool.mcp-coder.install] extras; falling back to 'dev'"`.

## ALGORITHM

```
validate_target_repo(folder_path):
    validate_mcp_json(folder_path)                       # fatal, unchanged

    data = _load_pyproject(folder_path)                  # lax; {} when missing
    if no [tool.mcp-coder.install] extras key:  warn "falling back to 'dev'"
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

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`.
>
> Implement Step 4 only. TDD: write `tests/workflows/vscodeclaude/test_validate_target_repo.py`
> first, then add `validate_target_repo` to `session_launch.py`, swap the call at
> `:175`, and export it from the package `__init__`.
>
> Keep `validate_mcp_json` as-is and call it from the new function. Keep the
> implementation as a plain sequence of checks — no registry or table abstraction.
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check` and the fast pytest
> selection. Commit once, green.
