# Step 1 — Move `toml_utils` into `mcp_coder.config`

Pure refactor, no behaviour change. See `pr_info/steps/summary.md`
(design change 1).

## WHERE

- Move `src/mcp_coder/utils/toml_utils.py` → `src/mcp_coder/config/toml_utils.py`.
- Importers updated by the move tool:
  - `src/mcp_coder/utils/user_config.py`
  - `src/mcp_coder/utils/pyproject_config.py`
  - `src/mcp_coder/utils/setup_config.py`
  - `src/mcp_coder/utils/toolkit_runner.py`
  - `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
  - `tests/conftest.py`
  - `tests/utils/test_setup_config.py`
  - `tests/utils/test_user_config.py`

## WHAT

No new symbols. `load_toml`, `TomlReadError`, `MCP_CODER_CONFIG_FILES`,
`find_mcp_coder_table`, `format_toml_error` keep their signatures.

## HOW

1. Precondition: if `src/mcp_coder/config/toml_utils.py` already exists, write
   one line to `pr_info/.blocked.txt` and stop.
2. Run `mcp__mcp-tools-py__move_module(source_module="src/mcp_coder/utils/toml_utils.py",
   dest_package="src/mcp_coder/config")`. If the tool fails, write one line to
   `pr_info/.blocked.txt` and stop.
3. Search `src/` and `tests/` for any remaining `utils.toml_utils` /
   `from .toml_utils` references (including `patch("...")` strings) and fix them.
   In `utils/*` modules the relative import becomes
   `from ..config.toml_utils import ...`.
4. The moved module imports only the stdlib, so `mcp_coder.config` keeps
   `depends_on = []`. No `.importlinter` / `tach.toml` change.
5. Update the moved module's docstring if it says it lives in utils (it may
   keep naming `user_config` / `pyproject_config` as consumers).

## Tests

No new tests; the existing suite is the safety net.

## Checks

pylint, mypy, pytest (fast set), `run_lint_imports_check`, `run_tach_check`,
then `run_format_code`. One commit: `refactor(config): move toml_utils into mcp_coder.config`.

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`:
> move `src/mcp_coder/utils/toml_utils.py` into `src/mcp_coder/config/` with the
> `move_module` tool, fix any remaining references, and confirm pylint, mypy,
> pytest, lint-imports and tach pass. No behaviour changes. Commit once.
