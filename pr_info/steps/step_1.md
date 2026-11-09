# Step 1 — Remove dead check wrappers from the shim

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly. Trim `src/mcp_coder/mcp_tools_py.py` to the `resolve_steps` re-export. Reduce `tests/test_mcp_tools_py.py` to a module-level `test_resolve_steps_reexported`. Delete `tests/test_mcp_tools_py_integration.py`. Remove the `checker_integration` marker from `pyproject.toml` and the `has_mypy_errors` entry from `vulture_whitelist.py`. Do not touch docs or `tach.toml` (that is step 2). Run the checks listed below and make them pass. Produce one commit.

## Precondition

Search `src/` and `tests/` for `has_mypy_errors`, `run_mypy_check`, `run_pylint_check`, `run_pytest_check`, `run_format_code`, `MypyResult`, `PylintResult` and `FormatterResult` imported **from `mcp_coder.mcp_tools_py`**. Hits in `tests/test_mcp_tools_py.py` and `tests/test_mcp_tools_py_integration.py` are expected; ignore them. If any other file imports one of these names from `mcp_coder.mcp_tools_py`, write one line to `pr_info/.blocked.txt` naming the file and stop.

## WHERE

- `src/mcp_coder/mcp_tools_py.py`
- `tests/test_mcp_tools_py.py`
- `tests/test_mcp_tools_py_integration.py` (delete)
- `pyproject.toml` (`[tool.pytest.ini_options]`)
- `vulture_whitelist.py`

## WHAT

### `src/mcp_coder/mcp_tools_py.py`: full new content

```python
"""Shim for the mcp_tools_py library.

Sole permitted importer of mcp_tools_py. Re-exports resolve_steps for
cli verify; workflow checks run through the toolkit (utils/toolkit_runner).
"""

from mcp_tools_py.formatter.runner import resolve_steps

__all__ = ["resolve_steps"]
```

Removed: `run_format_code`, `run_pytest_check`, `run_pylint_check`, `run_mypy_check`, `has_mypy_errors`, the `FormatterResult` / `MypyResult` / `PylintResult` re-exports, and the imports of `sys`, `Path`, `Any` and all other `mcp_tools_py.*` modules.

### `tests/test_mcp_tools_py.py`: full new content

```python
"""Unit test for the mcp_tools_py shim's resolve_steps re-export."""


def test_resolve_steps_reexported() -> None:
    """resolve_steps is importable from the wrapper module."""
    from mcp_tools_py.formatter.runner import resolve_steps as upstream

    from mcp_coder.mcp_tools_py import resolve_steps

    assert resolve_steps is upstream
```

### `tests/test_mcp_tools_py_integration.py`

Delete the file.

### `pyproject.toml`

- Remove the markers-list line `"checker_integration: tests for code checker integration (pylint, pytest, mypy)",`.
- Remove the usage comment line `# -m "checker_integration"`.

### `vulture_whitelist.py`

Remove these two lines and the blank line after them:

```
# mcp_tools_py.py - Convenience function for simple pass/fail checks
_.has_mypy_errors
```

## HOW

- `cli/commands/verify_sections.py` keeps its `from mcp_coder.mcp_tools_py import resolve_steps` unchanged.
- No changes to `.importlinter` or `tach.toml`.

## ALGORITHM

None. This step only deletes code.

## DATA

The shim exports exactly `__all__ == ["resolve_steps"]`, and `resolve_steps` is the upstream object.

## Checks (all must pass)

1. `mcp__mcp-tools-py__run_format_code`
2. `mcp__mcp-tools-py__run_pylint_check`
3. `mcp__mcp-tools-py__run_mypy_check`
4. `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`
5. `mcp__mcp-tools-py__run_vulture_check`

## Commit

`refactor(mcp_tools_py): remove dead check wrappers from shim (#1388)`
