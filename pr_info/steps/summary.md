# Summary — Split `tests/cli/commands/coordinator/test_core.py` (#1317)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal

`test_core.py` (~1170 lines, allowlisted) is split so every file is under 750 lines
and `test_core.py` leaves `.large-files-allowlist`. **Pure refactoring:** classes move
verbatim with the refactoring tools (`move_symbol`, dry run first). No logic edits,
renames, deletions or merges of tests.

## Architectural / design changes

No production code changes. `src/mcp_coder/cli/commands/coordinator/core.py` (~490 lines)
stays as is. Only the test layout changes:

- **Tests follow `core.py`'s three sections.** The source has three sections:
  Config, Eligibility and Dispatch. Each gets a prefixed sibling test file, the same
  pattern as `tests/workflows/implement/test_core_*.py`:
  - config tests stay in `test_core.py`
  - eligibility → `test_core_eligibility.py`
  - dispatch → `test_core_dispatch.py`
- **Misplaced classes move to the test namespace of the module they actually test:**
  - `TestCommandTemplates` → `test_command_templates.py` (tests `command_templates` constants)
  - `TestGetCacheRefreshMinutes` → `tests/utils/test_user_config_cache_refresh.py`
    (tests `utils.user_config`). It cannot go in `test_user_config.py`: that file already
    defines a class with the same name.
  - `TestCacheFilePath`, `TestCacheFileOperations`, `TestStalenessLogging` →
    `tests/test_mcp_workspace_github_cache.py`. They test the cache aliases of the shim
    `mcp_coder.mcp_workspace_github`; the new file is a sibling of
    `tests/test_mcp_workspace_github_smoke.py`.
- No `conftest.py`, `.importlinter` or `tach.toml` changes. The `tests/cli/commands/conftest.py`
  autouse fixtures that the cross-directory moves leave behind patch `cli.commands.*` modules
  only. The moved classes never reach those modules.

## TDD note

This change only moves tests, so there is no new test to write first. The existing tests are
the safety net. Each step records the collect counts before the move, moves the classes,
then checks that the counts moved by exactly that step's tests and that everything passes.

## Files created / modified

| File | Change |
|---|---|
| `tests/cli/commands/coordinator/test_core.py` | modified: keeps the config classes; imports trimmed; docstring bullet lines 5–10 deleted |
| `tests/cli/commands/coordinator/test_command_templates.py` | modified: `TestCommandTemplates` appended; import block unchanged |
| `tests/cli/commands/coordinator/test_core_eligibility.py` | **new** |
| `tests/cli/commands/coordinator/test_core_dispatch.py` | **new** |
| `tests/utils/test_user_config_cache_refresh.py` | **new** |
| `tests/test_mcp_workspace_github_cache.py` | **new** |
| `.large-files-allowlist` | modified: `tests/cli/commands/coordinator/test_core.py` entry removed |

No new folders and no `__init__.py` files: all destination directories already exist.

## Steps (one commit each)

| Step | Move | Tests moved |
|---|---|---:|
| 1 | `TestCommandTemplates` → `test_command_templates.py` | 1 |
| 2 | `TestGetCacheRefreshMinutes` → `tests/utils/test_user_config_cache_refresh.py` | 4 |
| 3 | 3 cache classes → `tests/test_mcp_workspace_github_cache.py` | 8 |
| 4 | 2 eligibility classes → `test_core_eligibility.py` | 5 |
| 5 | 2 dispatch classes → `test_core_dispatch.py`; final allowlist and docstring check | 18 |

End state: `test_core.py` has 14 tests. Whole-suite count is unchanged.
`tests/cli/commands/coordinator/` has 12 fewer tests, and `tests/utils/` has 4 more.

## Rules applying to every step

- **Allowed edits only:**
  - import statements
  - deleting the docstring bullets of `test_core.py` that the step's move makes stale
  - the `.large-files-allowlist` entry
- **Tools:**
  - MCP tools only, no Bash.
  - Move code with `move_symbol` only, never by hand.
  - Do not reorder classes.
- **Imports:**
  - Keep the original import sources: the package `mcp_coder.cli.commands.coordinator`,
    `mcp_coder.mcp_workspace_github`, `mcp_coder.utils.user_config`.
  - `make_issue_data` is exactly `from tests.github_factories import make_issue_data`.
  - Remove whatever ruff reports as `F401`.
- **Checks in every step:**
  - `run_format_code`, `run_ruff_check`, `run_pylint_check`, `run_mypy_check`
  - fast unit `run_pytest_check` with `-n auto` and the marker exclusion from CLAUDE.md
  - `check_file_size`
- **Allowlist:** if `check_file_size` reports `tests/cli/commands/coordinator/test_core.py`
  as a stale allowlist entry, remove that line from `.large-files-allowlist` in the same
  step. Expected in step 4.
- **Failure handling:** on any stop condition, write one line to `pr_info/.blocked.txt` and
  stop. Stop conditions:
  - a dry run lists files other than the source and the destination
  - a collect count is off
  - a test that passed before fails after the move
  - `F811` is reported
  - a decorator, class-level fixture or method-local import changed
