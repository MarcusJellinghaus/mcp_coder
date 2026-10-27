# Step 2 — Move `TestGetCacheRefreshMinutes` → `tests/utils/test_user_config_cache_refresh.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then do `pr_info/steps/step_2.md`. This is a pure refactor:
> move the class with `mcp__mcp-tools-py__move_symbol` (dry run first). Edit only imports and
> the one stale docstring bullet. Run every check listed. The step ends in exactly one commit.

## WHERE

- Source: `tests/cli/commands/coordinator/test_core.py`
- Destination (**new**): `tests/utils/test_user_config_cache_refresh.py`
- **Never** move it into `tests/utils/test_user_config.py`. That file already defines a class
  with the same name, which would shadow it and silently drop 4 tests.

## WHAT

- Move the class `TestGetCacheRefreshMinutes` (4 tests). It is mock-based: it patches
  `mcp_coder.utils.user_config.get_config_values`.

## HOW

1. **Pre-counts:** run `--collect-only -q` on each path below and note the numbers.

   | Path | Expected |
   |---|---:|
   | `test_core.py` | 49 |
   | `tests/utils/` | 441 |
   | `tests/cli/commands/coordinator/` | 156 |
   | whole suite | baseline |

   Run `-q tests/cli/commands/coordinator/test_core.py::TestGetCacheRefreshMinutes` → 4 passed.
2. **Dry run:**
   - Call `move_symbol(..., symbol_names=["TestGetCacheRefreshMinutes"],
     dest_file="tests/utils/test_user_config_cache_refresh.py", dry_run=True)`.
   - If it lists files other than the source and the destination: write one line to
     `pr_info/.blocked.txt` and stop.
3. **Move:** run the same call without `dry_run`.
4. **Destination imports**, exactly:
   ```python
   from unittest.mock import MagicMock, patch

   from mcp_coder.utils.user_config import get_cache_refresh_minutes
   ```
   No `pytest` import (it would be unused). No module docstring (`D` is ignored for tests).
5. **`test_core.py`:**
   - Remove the now-unused `from mcp_coder.utils.user_config import get_cache_refresh_minutes`.
   - In the module docstring, delete only the bullet
     `- Cache refresh settings (get_cache_refresh_minutes - moved to utils.user_config)`.

## ALGORITHM

```
record counts -> dry-run -> move to new file
set destination imports, drop unused import + stale bullet in test_core.py
format, ruff, pylint, mypy, pytest, collect counts
```

## DATA — expected after the step

| Path | Expected |
|---|---:|
| `test_core.py` | 45 |
| `tests/utils/test_user_config_cache_refresh.py` | 4 |
| `tests/utils/test_user_config.py` | 27 (unchanged) |
| `tests/utils/` | pre + 4 |
| `tests/cli/commands/coordinator/` | pre − 4 |
| whole suite | unchanged |

Run `-q tests/utils/test_user_config_cache_refresh.py` → 4 passed. If it fails: write one line
to `pr_info/.blocked.txt` and stop. Do not add fixtures or `conftest.py` entries.

## Checks

- `run_format_code`
- `run_ruff_check`
- `run_pylint_check`
- `run_mypy_check`
- fast unit `run_pytest_check` with `-n auto`
- `check_file_size`

## Commit

`test(user_config): move mock-based TestGetCacheRefreshMinutes out of coordinator tests`
