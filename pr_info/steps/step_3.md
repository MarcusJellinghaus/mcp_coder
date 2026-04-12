# Step 3: Trim pyproject_config.py formatter helpers

**Commit message:** `refactor: remove formatter helpers from pyproject_config`

**Context:** See `pr_info/steps/summary.md` for full issue context (#737).

## Goal

Remove `get_formatter_config()` and `check_line_length_conflicts()` from
`pyproject_config.py` and their corresponding test classes. These functions
were only used by the now-deleted `mcp_coder.formatters` package. The equivalent
functionality lives in mcp-tools-py's `utils/project_config.py`.

## WHERE — Files to modify

1. `src/mcp_coder/utils/pyproject_config.py` — remove 2 functions
2. `tests/utils/test_pyproject_config.py` — remove 2 test classes + unused imports

## WHAT — Functions to remove

### 1. From `src/mcp_coder/utils/pyproject_config.py`

**Remove:**
- `get_formatter_config(project_dir, filename)` — entire function (~20 lines)
- `check_line_length_conflicts(config)` — entire function (~20 lines)
- The `Any` import from `typing` (no longer needed)

**Keep:**
- `GitHubInstallConfig` dataclass
- `get_github_install_config()` function
- `tomllib` and `dataclasses` imports (still used)
- `Path` import (still used)

### 2. From `tests/utils/test_pyproject_config.py`

**Remove:**
- `TestGetFormatterConfig` class (3 tests)
- `TestCheckLineLengthConflicts` class (3 tests)
- Imports: `get_formatter_config`, `check_line_length_conflicts`

**Keep:**
- `TestGetGithubInstallConfig` class (4 tests)
- Import: `get_github_install_config`

## HOW — Edit procedure

1. Edit `pyproject_config.py`:
   - Remove `from typing import Any` (line 5 area)
   - Remove entire `get_formatter_config()` function
   - Remove entire `check_line_length_conflicts()` function
2. Edit `test_pyproject_config.py`:
   - Update import block to only import `get_github_install_config`
   - Remove `TestGetFormatterConfig` class
   - Remove `TestCheckLineLengthConflicts` class

## ALGORITHM — No new logic

This is deletion-only within existing files.

## DATA — Remaining module API

After trimming, `pyproject_config.py` exports:
- `GitHubInstallConfig` (frozen dataclass)
- `get_github_install_config(project_dir: Path) -> GitHubInstallConfig`

## Verification

```
mcp__tools-py__run_pytest_check   (unit tests, exclude integration)
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```
