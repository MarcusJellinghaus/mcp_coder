# Step 3 — Move cache classes → `tests/test_mcp_workspace_github_cache.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then do `pr_info/steps/step_3.md`. This is a pure refactor:
> move the three classes in one `mcp__mcp-tools-py__move_symbol` call (dry run first). Edit
> only imports and the stale docstring bullets. Run every check listed. The step ends in
> exactly one commit.

## WHERE

- Source: `tests/cli/commands/coordinator/test_core.py`
- Destination (**new**): `tests/test_mcp_workspace_github_cache.py`. It is a prefixed sibling
  of the existing `tests/test_mcp_workspace_github_smoke.py`, which stays unchanged.

## WHAT

Move these classes in one call, in source order (8 tests in total):

| Class | Tests | Tests these shim aliases |
|---|---:|---|
| `TestCacheFilePath` | 2 | `get_cache_file_path` |
| `TestCacheFileOperations` | 4 | `load_cache_file`, `save_cache_file` |
| `TestStalenessLogging` | 2 | `log_stale_cache_entries` |

All aliases come from `mcp_coder.mcp_workspace_github`.

## HOW

1. **Pre-counts:** run `--collect-only -q` on each path below and note the numbers.

   | Path | Expected |
   |---|---:|
   | `test_core.py` | 45 |
   | `tests/test_mcp_workspace_github_smoke.py` | 5 |
   | `tests/cli/commands/coordinator/` | — |
   | whole suite | — |

   Run the three classes in `test_core.py` with `-q` → 8 passed.
2. **Dry run:**
   - Call `move_symbol(..., symbol_names=["TestCacheFilePath", "TestCacheFileOperations",
     "TestStalenessLogging"], dest_file="tests/test_mcp_workspace_github_cache.py", dry_run=True)`.
   - If it lists files other than the source and the destination: write one line to
     `pr_info/.blocked.txt` and stop.
3. **Move:** run the same call without `dry_run`.
4. **Check the method-local imports:**
   - Each of `TestCacheFilePath`'s two test methods must still contain its own
     `from mcp_coder.mcp_workspace_github import RepoIdentifier`, verbatim.
   - If one was removed from its method (hoisted to module level) or dropped: write one line
     to `pr_info/.blocked.txt` and stop. Never restore it by hand.
   - If both method-local imports are still in place and the tool also added a module-level
     `RepoIdentifier` import, that is not hoisting. Delete the extra import (an `F401` import
     edit) and continue. Do not stop.
5. **Destination imports**, exactly:
   ```python
   import json
   import logging
   import tempfile
   from pathlib import Path

   import pytest

   from mcp_coder.mcp_workspace_github import (
       CacheData,
       IssueData,
       get_cache_file_path,
       load_cache_file,
       log_stale_cache_entries,
       save_cache_file,
   )
   from tests.github_factories import make_issue_data
   ```
   No module-level `RepoIdentifier`: it would be unused (`F401`). If the tool added one,
   delete it (see HOW 4).
6. **`test_core.py`:**
   - Remove these now-unused imports (ruff `F401` reports them): `json`, `tempfile`, `Path`,
     `CacheData`, `get_cache_file_path`, `load_cache_file`, `log_stale_cache_entries`,
     `save_cache_file`.
   - Keep these imports, which the remaining classes still use: `logging`, `IssueData`,
     `RepoIdentifier`, `make_issue_data`.
   - In the module docstring, delete only these two bullets:
     - `- Cache file operations (get_cache_file_path, load_cache_file, save_cache_file)`
     - `- Cache staleness logging (log_stale_cache_entries)`

## ALGORITHM

```
record counts -> dry-run -> move 3 classes in one call
verify method-local RepoIdentifier imports intact
set destination imports, drop unused imports + 2 stale bullets in test_core.py
format, ruff, pylint, mypy, pytest, collect counts
```

## DATA — expected after the step

| Path | Expected |
|---|---:|
| `test_core.py` | 37 |
| `tests/test_mcp_workspace_github_cache.py` | 8 |
| `tests/test_mcp_workspace_github_smoke.py` | 5 |
| `tests/cli/commands/coordinator/` | pre − 8 |
| whole suite | unchanged |

Run `-q tests/test_mcp_workspace_github_cache.py` → 8 passed. If it fails: write one line to
`pr_info/.blocked.txt` and stop.

## Checks

- `run_format_code`
- `run_ruff_check`
- `run_pylint_check`
- `run_mypy_check`
- fast unit `run_pytest_check` with `-n auto`
- `check_file_size`

## Commit

`test(mcp_workspace_github): move cache helper tests out of coordinator tests`
