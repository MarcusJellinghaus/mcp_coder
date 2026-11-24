# Summary — #1450 config: read every project table from mcp-coder.toml, report unknown project keys

## Goal

- `[tool.mcp-coder.prompts]`, `[tool.mcp-coder] format_code` and
  `[tool.mcp-coder] labels-config` are read from `pyproject.toml`, else a root
  `mcp-coder.toml`, each setting on its own (the same rule as `toolkit` / `setup`).
- Reading at run time stays lenient: a malformed file, or the same setting in
  both files, gives the default plus a logged warning. No new crash points.
- `mcp-coder verify` warns (exit code unchanged) about unknown keys and tables,
  the retired `implement` table, Python-only tables in `mcp-coder.toml`,
  malformed files and settings defined in both files.
- `verify` shows the `format_code` row for every repo, naming the source file.

## Architectural / design changes

1. **TOML helpers move down one layer.** `mcp_coder/utils/toml_utils.py` moves
   to `mcp_coder/config/toml_utils.py` (stdlib-only, so `config` keeps
   `depends_on = []` in `tach.toml` and stays the lowest import-linter layer).
   This lets `config/label_config.py` reuse the lookup instead of its own
   duplicated `tomllib` reader. All imports are updated; there is no shim.
2. **One lenient lookup, no new types.** `find_mcp_coder_table_lenient()` wraps
   the existing strict `find_mcp_coder_table()`: on `ValueError` (malformed file,
   non-table `tool`/`mcp-coder`, both files define the key) it logs a warning and
   returns `None`. The three getters use it, so the lenient behaviour lives in
   the getters and none of their callers change.
3. **`FormatCodeSetting.explicit` becomes `source: str | None`.** "Explicit" was
   exactly "a file defines the key"; the file name is what the verify row and the
   non-bool error message need. `get_format_code`'s `ValueError` keeps its single
   meaning: a non-bool value, now naming the real file.
4. **The unknown-key scan lives with its only consumer.** New
   `cli/commands/verify_project_keys.py` holds the known schema (one dict), a scan
   that reads every file in `MCP_CODER_CONFIG_FILES` itself, and a row builder.
   Each warning carries the verify section it belongs to (`PROMPTS` or
   `PROJECT`). Rows are always `[WARN]` and never feed `ok` / `prompts_ok`, so
   `verify`'s exit code is unchanged. `toolkit` and `setup` keep their own
   validation; the existing `implement` `format_code` / `check_type_hints` rows
   are unchanged.
5. `install` / `install-from-github` and the legacy `implement` readers stay
   `pyproject.toml`-only.

## Files

Created:
- `src/mcp_coder/config/toml_utils.py` (moved from `src/mcp_coder/utils/toml_utils.py`)
- `src/mcp_coder/cli/commands/verify_project_keys.py`
- `tests/config/test_toml_utils.py`
- `tests/cli/commands/test_verify_project_keys.py`

Deleted (by the move):
- `src/mcp_coder/utils/toml_utils.py`

Modified:
- `src/mcp_coder/utils/user_config.py`, `src/mcp_coder/utils/setup_config.py`,
  `src/mcp_coder/utils/toolkit_runner.py`,
  `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (import path only)
- `src/mcp_coder/utils/pyproject_config.py` (`get_format_code`, `FormatCodeSetting`, `get_prompts_config`)
- `src/mcp_coder/config/label_config.py` (labels-config lookup)
- `src/mcp_coder/cli/commands/verify_sections.py` (`_format_code_row`, `_print_project_section`)
- `src/mcp_coder/cli/commands/verify.py` (PROMPTS warning rows)
- `src/mcp_coder/cli/gh_parsers.py` (two help strings)
- `docs/getting-started/label-setup.md` (mirror of the `--config` help string)
- Tests: `tests/conftest.py`, `tests/utils/test_setup_config.py`,
  `tests/utils/test_user_config.py` (import path);
  `tests/utils/test_pyproject_config.py`, `tests/config/test_label_config.py`,
  `tests/cli/commands/test_verify_project_section.py`,
  `tests/cli/commands/test_verify.py`

## Steps

1. Move `toml_utils` into `mcp_coder.config` (pure refactor).
2. Lenient lookup + `get_format_code` from either file + `format_code` row for every repo.
3. `get_prompts_config` from either file.
4. `labels-config` from either file + CLI help.
5. `verify` unknown/misplaced-key warnings (PROJECT and PROMPTS).

Out of scope: the full config reference docs (#1453), the `pyproject.toml` /
`Language` rows for `mcp-coder.toml` repos (#1454).
