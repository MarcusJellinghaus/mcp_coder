# Summary — #1414 verify: report an invalid `.mcp-file-access` in the PROJECT section

## Goal

An invalid `.mcp-file-access` makes mcp-workspace refuse every MCP write. Today
`verify` mentions it only in the MCP edit smoke-test skip text, which needs a
resolvable `.mcp.json` and never affects the exit code. After this change the
PROJECT section always reports the rules file, and an invalid file exits 1.

## Architectural / design changes

- **New PROJECT row `.mcp-file-access`** (`verify_sections.py`), added by one
  new helper `_file_access_row()` right after the `Language` row, at section
  level (indent 2), in both branches of `_print_project_section` (with and
  without `pyproject.toml`).
- **Check order** (first match wins):

  | State | Row | Section result |
  |---|---|---|
  | `.mcp-file-access` path does not exist | `[OK] not present (gitignore defaults)` | neutral |
  | `FILE_ACCESS_SUPPORTED` is False | `[WARN] not checked (mcp-workspace in this environment does not support .mcp-file-access)` | neutral |
  | `validate_access_rules()` returns problems (incl. a directory at the path → `is a directory`) | `[ERR] invalid (<problems joined by "; ">)` | False → exit 1 |
  | otherwise | `[OK] valid` | neutral |

  `exists()` first: the old-version stand-in for `validate_access_rules` always
  returns `[]`, and `[]` also means "absent". The flag check comes before
  trusting `[]`.
- **Exit code:** no new plumbing. `_print_project_section` already returns
  `project_ok` to `_compute_exit_code`. The row's bool is kept in its own
  variable (`file_access_ok`) and ANDed into both branch returns, because `ok`
  is assigned fresh after the `Language` row.
- **One render path:** the row always uses `Row(..., wrap=True)`. Short values
  render on one line; long `[ERR]` / `[WARN]` values wrap at 80 columns.
- **No duplicate reporting:** the smoke-test skip text for an invalid file
  becomes `skipped: invalid .mcp-file-access (see PROJECT)`; the problem list
  appears only in the PROJECT row.
- **Imports:** `verify_sections.py` imports `FILE_ACCESS_SUPPORTED` and
  `validate_access_rules` from `mcp_coder.mcp_workspace` (never from
  `mcp_workspace`) as module globals, so tests patch
  `mcp_coder.cli.commands.verify_sections.<name>`. `verify.py` keeps its own
  bindings for the smoke test (`verify.<name>`).
- Upstream logs a WARNING once per distinct problem per process — accepted, not
  silenced, not asserted in tests.

## Files modified

| File | Step | Change |
|---|---|---|
| `src/mcp_coder/cli/commands/verify_sections.py` | 1 | imports, `_file_access_row()`, call in both branches of `_print_project_section`, docstring |
| `src/mcp_coder/cli/commands/verify_exit_code.py` | 1 | `project_ok` docstring, summary paragraph, comment list every PROJECT `[ERR]` source |
| `tests/cli/commands/test_verify_project_section.py` | 1 | module docstring, one parametrized test class |
| `docs/repository-setup/repo.md` | 1 | new bullet: invalid file → `verify` PROJECT row, exit 1 |
| `docs/cli-reference.md` | 1, 2 | `verify` sentence: project section reports `.mcp-file-access` (1); smoke-test skip wording (2) |
| `src/mcp_coder/cli/commands/verify.py` | 2 | `_smoke_test_skip_reason` invalid-file text |
| `tests/cli/commands/test_verify_mcp_edit_smoke.py` | 2 | update `test_smoke_test_skipped_when_rules_file_invalid` and its docstring |

No files or folders are created besides these plan files.

## Steps

1. [step_1.md](step_1.md) — PROJECT `.mcp-file-access` row, exit code, docs.
2. [step_2.md](step_2.md) — smoke-test skip text points to PROJECT.
