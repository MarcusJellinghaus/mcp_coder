# Step 8: `validate_target_repo` gates Python warnings on the `python` built-in

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_8.md`) only. Step 2 must be done: if `mcp_coder.utils.setup_config.load_setup_config` does not exist, write one line to `pr_info/.blocked.txt` and stop.
Write the tests first, then the implementation. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Modify `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — `validate_target_repo`
- Create `tests/workflows/vscodeclaude/test_validate_target_repo_setup.py`
- Adjust `tests/workflows/vscodeclaude/test_validate_target_repo.py` only where a fixture now needs a `pyproject.toml` (default python built-in) to keep its warnings

## WHAT

```python
def validate_target_repo(folder_path: Path) -> None:  # signature unchanged
```

## ALGORITHM

```
validate_mcp_json(folder_path)                       # still fatal
try: uses_python = load_setup_config(folder_path).uses_python()
except ValueError as exc: logger.warning("%s: invalid [tool.mcp-coder.setup]; `mcp-coder setup` will fail on it:\n%s", folder_path, exc); return
if not uses_python: return
<existing extras / install-from-github / post_install_checks / .venv / second venv checks, unchanged>
```

## HOW

- Import `load_setup_config` from `...utils.setup_config`.
- Extract the existing Python checks into `_warn_python_policy(folder_path)` so the gate reads as one `if`. Behaviour of those checks is unchanged.
- Update the docstring: Python rows only apply when the resolved setup steps include the `python` built-in.

## Tests

- `npm ci` setup in `mcp-coder.toml`, no `pyproject.toml` → no Python warnings, no error.
- `pyproject.toml` with `[tool.mcp-coder.setup] steps = [{ argv = ["npm", "ci"] }]` → no Python warnings.
- `pyproject.toml` without setup table (default) → existing extras warning still logged.
- Broken setup config → one warning naming it, launch continues (no raise); missing `.mcp.json` still raises.

## DATA

None (logs warnings; raises only for the MCP config).
