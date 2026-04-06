# Issue #640: Improve developer environment setup scripts

## Summary

Clean up developer environment scripts: delete obsolete PyPI reinstall script, centralise `pyproject.toml` reading into a shared utility, make `reinstall_local.bat` read GitHub deps dynamically, and add version printing to launcher batch files.

## Architecture / Design Changes

### New shared utility: `pyproject_config.py`

Currently, `pyproject.toml` is read independently in three places:
- `formatters/config_reader.py` — reads `[tool.black]` and `[tool.isort]`
- `workspace.py:_build_github_install_section()` — reads `[tool.mcp-coder.install-from-github]`
- `formatters/__init__.py:_check_line_length_conflict()` — reads `[tool.black]` and `[tool.isort]` again (duplicating config_reader)

After this change, a single module `src/mcp_coder/utils/pyproject_config.py` centralises all `pyproject.toml` reading with typed, section-specific functions:
- `get_github_install_config(project_dir)` — returns `GitHubInstallConfig` (packages + packages-no-deps)
- `get_formatter_config(project_dir)` — returns formatter config dict
- `check_line_length_conflicts(config)` — moved here from `config_reader.py`

The existing consumers become thin wrappers delegating to this module.

### Two config systems — now documented

The project has two distinct config systems:
1. **`config.toml`** (user config) — per-user settings like API tokens, read by `utils/user_config.py`
2. **`pyproject.toml`** (project config) — project-level tool settings, read by `utils/pyproject_config.py`

Both modules now carry docstring notes explaining this distinction, and `docs/configuration/config.md` gets a new section.

### Bootstrap helper for batch scripts

`tools/read_github_deps.py` bridges the gap between Python config reading and batch script execution. It uses `sys.path.insert(0, "src")` to import `pyproject_config.py` without requiring an installed package, then prints `uv pip install` commands to stdout. The batch file captures and executes these lines.

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/utils/pyproject_config.py` | Shared pyproject.toml reader |
| `tools/read_github_deps.py` | Bootstrap helper for batch scripts |
| `tests/utils/test_pyproject_config.py` | Tests for pyproject_config |
| `tests/workflows/vscodeclaude/test_build_github_install_section.py` | Regression test for _build_github_install_section |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/formatters/config_reader.py` | Thin wrapper delegating to pyproject_config |
| `src/mcp_coder/formatters/__init__.py` | Use pyproject_config for line-length check |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Use get_github_install_config() |
| `src/mcp_coder/utils/user_config.py` | Add docstring note about config systems |

| `tests/test_pyproject_config.py` | May need updates if overlapping with new tests |
| `claude.bat` | Add version printing |
| `claude_local.bat` | Add version printing |
| `icoder.bat` | Add version printing |
| `icoder_local.bat` | Add version printing |
| `tools/reinstall_local.bat` | Use read_github_deps.py, create .venv, silent deactivate |
| `docs/configuration/config.md` | Add config systems section |
| `docs/environments/environments.md` | Targeted updates |

## Files Deleted

| File | Reason |
|------|--------|
| `tools/reinstall.bat` | Obsolete PyPI reinstall script |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Delete `tools/reinstall.bat`, clean stale refs in `reinstall_local.bat` and `docs/repository-setup.md` | `chore: delete obsolete PyPI reinstall script` |
| 2 | Create `pyproject_config.py` with tests | `feat: add shared pyproject.toml config reader` |
| 3 | Refactor `config_reader.py` to thin wrapper | `refactor: delegate config_reader to pyproject_config` |
| 4 | Refactor `_build_github_install_section()` + regression test | `refactor: use get_github_install_config in workspace` |
| 5 | Create `read_github_deps.py` + improve `reinstall_local.bat` | `feat: dynamic GitHub deps in reinstall_local.bat` |
| 6 | Add version printing to all four launchers + `.mcp.json` consistency verification | `feat: print MCP server versions in launcher scripts` |
| 7 | Documentation updates + config system docstrings | `docs: document config systems, update environments` |
