# Summary — #1468: non-table `tool` / `mcp-coder` / `implement` / `install` / `install-from-github` in pyproject.toml

## Problem

Five readers in `src/mcp_coder/utils/pyproject_config.py` walk
`data.get("tool", {}).get("mcp-coder", {}).get(<sub>, {})` without type checks:
`has_legacy_format_code_key`, `get_leftover_check_type_hints`,
`get_install_extras`, `get_post_install_checks`, `get_github_install_config`.
A non-table value at any level raises `AttributeError` / `TypeError`, and a
string or list `implement` containing `format_code` gives a false positive in
`has_legacy_format_code_key`. This crashes `verify`, the format pre-flight,
`mcp-coder install`, `mcp-coder setup`'s `python` built-in and the vscodeclaude
Python policy check.

## Architectural / design changes

1. **One shared, type-checked walk** — `config/toml_utils.mcp_coder_section(data, label, table=None)`.
   Walks `tool` → `mcp-coder` (→ `table`) in already-parsed TOML data. A missing
   level gives `{}`; a non-table level raises a plain `ValueError`
   (never `TomlReadError`) with one message format for every level:
   `Invalid '<key>' in <label>: expected a table, got <type>: <value!r>`.
   - `find_mcp_coder_table` uses it with the bare file name as label, so its
     messages are unchanged (`Invalid 'tool' in pyproject.toml ...`).
   - The pyproject readers use it with the full file path as label.
2. **One-flag private wrapper in `pyproject_config.py`** —
   `_pyproject_section(project_dir, table, *, strict=False)`: loads
   pyproject.toml (`strict` → `TomlReadError` on a malformed file) and calls
   the walk; a shape `ValueError` is re-raised when `strict`, else `{}` is
   returned without logging.
   - `has_legacy_format_code_key`, `get_leftover_check_type_hints` → lax
     (`"implement"`); a non-table `implement` counts as absent.
   - `get_install_extras`, `get_post_install_checks` → `strict=strict` (`"install"`).
   - `get_github_install_config` → calls `mcp_coder_section` directly on the
     lax-loaded data: malformed file → defaults, non-table shape → `ValueError`.
3. **`verify` key warnings** (`cli/commands/verify_project_keys._classify`) —
   two small branches, exit-neutral as all key warnings:
   - non-table `implement` in pyproject.toml → existing
     `[tool.mcp-coder.implement] is retired and ignored` row;
   - non-table `install` / `install-from-github` in pyproject.toml →
     `[tool.mcp-coder.<key>] is not a table` row.
   `scan_project_keys`' own walk stays as is (it already handles non-table
   `tool` / `mcp-coder` with the "cannot be parsed" row).
4. **No entry-point code changes.** Existing `ValueError` handling in
   `execute_install`, `project_setup._run_python` (via `SetupError`),
   `session_launch._warn_python_policy` and `check_formatter_config`
   (`load_toolkit`) gives the required behaviour once the readers stop
   raising `AttributeError` / `TypeError`. Only tests are added there.

Out of scope: `prompts` keeps today's handling; no docs change (#1453 leaves
this case out of the project-config page).

## Files

Modified (source):
- `src/mcp_coder/config/toml_utils.py` — add `mcp_coder_section`; `find_mcp_coder_table` uses it.
- `src/mcp_coder/utils/pyproject_config.py` — add `_pyproject_section`; rewire the five readers.
- `src/mcp_coder/cli/commands/verify_project_keys.py` — two `_classify` branches.

Modified (tests):
- `tests/config/test_toml_utils.py` — `mcp_coder_section` tests.
- `tests/utils/test_pyproject_config.py` — parametrized non-table cases per reader; malformed-file additions.
- `tests/workflow_steps/test_commit.py` — pre-flight cases.
- `tests/cli/commands/test_install.py` — parametrize `test_invalid_target_pyproject_returns_one`.
- `tests/install/test_project_setup.py` — real `from_args` with `install = 1`; `ValueError` from `install()`.
- `tests/workflows/vscodeclaude/test_validate_target_repo_setup.py` — policy warning cases.
- `tests/cli/commands/test_verify_project_keys.py` — new key-warning rows.
- `tests/cli/commands/test_verify_project_section.py` — end-to-end `verify` cases.

No new files or modules.

## Steps

1. `step_1.md` — shared walk `mcp_coder_section` in `toml_utils.py`.
2. `step_2.md` — `_pyproject_section` + legacy `implement` readers; pre-flight tests.
3. `step_3.md` — install readers + `get_github_install_config`; install / setup / vscodeclaude tests.
4. `step_4.md` — `verify` key-warning rows + end-to-end `verify` tests.

## Test conventions (all steps)

- Fast unit tests: `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"])`.
- Then pylint, mypy, ruff check; `run_format_code` before committing.
- Match the "cannot be parsed" row by that phrase only (#1466 changes the rest).
