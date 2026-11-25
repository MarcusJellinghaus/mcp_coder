# Summary — #1454 verify: one PROJECT layout for every repo, without Python-only rows

## Goal

`mcp-coder verify`'s PROJECT section stops assuming a Python repo. Every repo gets
the same flat layout; the `pyproject.toml` and `Language` rows are replaced by one
`Project config` row, and the `Toolkit [OK]` row names the file its config came from.

## Architectural / design changes

- **One code path instead of two.** `_print_project_section`
  (`src/mcp_coder/cli/commands/verify_sections.py`) today branches on
  `pyproject.toml` existing: a flat branch (indent 2) and a Python branch
  (`pyproject.toml found`, `Language Python (detected)`, blank line, `[Python]`
  sub-heading, rows at indent 4). The flat branch already passes `indent=2` to
  every helper, so it is kept and the Python branch is deleted.
- **Language detection is removed.** There is no notion of "Python repo" left in
  the section; what runs is shown by the `Toolkit` row.
- **`Project config` row (new, inline, no helper).** Lists the files of
  `MCP_CODER_CONFIG_FILES` (`config/toml_utils.py`) that exist, checked with
  `.is_file()` (same check as `setup_config`), in that tuple's order:
  `[OK] pyproject.toml, mcp-coder.toml` / `[OK] mcp-coder.toml` /
  `[WARN] none`. It never affects the section's return value; when neither file
  exists the `Toolkit [ERR]` row already fails `verify`.
- **`Toolkit [OK]` names its source**: `f"{loaded.name} ({loaded.config.source})"`,
  matching the `format_code` and `Setup` rows. `[ERR]` rows unchanged.
- **Rows that read only `pyproject.toml`** (`legacy format_code` and
  `check_type_hints`) move into the single path after `Setup`, at indent 2. No
  existence guard is needed: their readers (`has_legacy_format_code_key`,
  `get_leftover_check_type_hints`) already return nothing without the file.
- **Indent defaults unchanged.** `toolkit_rows`, `setup_rows` and
  `_format_code_row` keep `indent=4` as default; the single call site passes
  `indent=2` (as the surviving branch already does). `check_type_hints_row`'s
  hard-coded indent goes from 4 to 2.

Resulting PROJECT order: `Project config`, `.mcp-file-access`, `format_code`,
`Toolkit` (+ groups), `Setup` (+ sub-rows), `legacy format_code`,
`check_type_hints`, key-warning rows.

Exit-code behaviour unchanged: `[WARN]` rows are exit-neutral, error rows still
make the section return False.

Out of scope: `DEFAULT_IGNORED_BUILD_ARTIFACTS`, docs (#1453).

## Files modified

Source:
- `src/mcp_coder/cli/commands/verify_toolkit_rows.py` — `Toolkit [OK]` value names
  the source (step 1); `check_type_hints_row` indent 4 → 2 (step 2).
- `src/mcp_coder/cli/commands/verify_sections.py` — single-path
  `_print_project_section` with the `Project config` row (step 2).

Tests:
- `tests/cli/commands/test_verify_toolkit_rows.py` (step 1)
- `tests/cli/commands/test_verify_project_section.py` (steps 1 and 2)
- `tests/cli/commands/test_verify.py` — `TestProjectSection` (step 2)
- `tests/cli/commands/test_verify_alignment.py` (step 2)
- `tests/cli/commands/test_verify_render.py` (step 2)
- `tests/cli/commands/test_verify_setup.py` — `TestProjectSectionWiring` (step 2)
- `tests/cli/commands/test_verify_check_type_hints.py` (step 2)

No files or modules are created (besides these plan files).

## Steps

1. `step_1.md` — `Toolkit [OK]` row names its config source.
2. `step_2.md` — flat PROJECT layout with the `Project config` row.
