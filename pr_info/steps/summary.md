# Summary — Split `cli/commands/verify.py` + `test_verify_orchestration.py`

Implements issue **#1021** (part of #353): reduce two oversized, allowlisted files
below the 750-line threshold by **moving** code — no logic changes, no back-compat
re-exports.

- `src/mcp_coder/cli/commands/verify.py` (~1130 lines)
- `tests/cli/commands/test_verify_orchestration.py` (~1868 lines)

## Guiding principles

- **Move, don't change.** Functions/classes/constants are relocated verbatim.
  The only edits are `import` statements. Verified per step with
  `mcp-coder git-tool compact-diff` (should show only import + new/deleted-file
  churn).
- **No back-compat.** Old locations are deleted; every importer is updated to the
  new location. No re-export shims.
- **One module per PR / one commit per step.** Three independent steps, each green
  on its own.
- **KISS.** Use `move_symbol` where it earns its keep (source symbols with many
  importers to auto-rewrite). Do **not** use it for the Step 3 test-class split —
  test modules have zero importers, so `move_symbol` buys nothing there; plain
  file ops are simpler.

## TDD note (applicability)

This is a **pure move refactor**, so the classic red→green cycle does not apply:
there is no new behavior to test-drive. The safety net is the **already-existing**
test suite, which exercises every moved symbol. "Test phase" for each step therefore
means: run the (auto-updated) existing tests and confirm they stay green after the
move. No new test logic is written; Step 3 *is* test code being reorganized.

## Architectural / design changes

The change is **structural only** — no runtime behavior, public CLI surface, or
call graph changes. `verify.py` goes from a single ~1130-line god-module to a small
orchestrator plus two pure leaf modules:

```
BEFORE                          AFTER
cli/commands/verify.py          cli/commands/verify.py          (orchestrator)
  ├─ formatting primitives        ├─ execute_verify
  ├─ constant maps                ├─ section printers
  ├─ exit-code logic              ├─ _validate_mcp_config
  ├─ section printers             ├─ _run_mcp_edit_smoke_test
  ├─ _validate_mcp_config         └─ _print_* / _DropUnexpandedWarnings
  ├─ smoke test                 cli/commands/verify_formatting.py  (NEW leaf)
  └─ execute_verify               └─ row/section formatters + constant maps
                                cli/commands/verify_exit_code.py   (NEW leaf)
                                  └─ _compute_exit_code, _collect_install_hints
```

**Dependency direction (one-way, no cycles):**

```
verify.py ──> verify_formatting      (needs row/section formatters + STATUS_SYMBOLS etc.)
verify.py ──> verify_exit_code       (needs _compute_exit_code / _collect_install_hints)
verify_formatting ──> (stdlib only)  reaches back into verify.py for nothing
verify_exit_code  ──> (stdlib only)  reaches back into verify.py for nothing
```

- **No import-linter / tach change.** The `layers` contract only orders
  `mcp_coder.cli | mcp_coder.icoder` at the top level; there is no sub-layer
  contract inside `cli.commands`. The two new modules are pure leaves with a
  single, one-directional edge each — no cycle, no contract update needed
  (confirmed against current `.importlinter`).
- **Constant-move caveat.** `move_symbol` advertises moving top-level functions,
  classes, **or variables**, so it may or may not relocate the module-level constants.
  Step 2 runs `move_symbol` with `dry_run=True` first to observe the actual behavior and
  only moves the constants manually (repointing importers by hand) if the dry-run leaves
  them behind. Either way, `_VALUE_COLUMN_INDENT` is computed at import time from
  `_format_row_prefix(...)`, so in the new file it must sit **after** that function.
- **Test structure already mirrors source.** ~11 companion test files
  (`test_verify_exit_codes*`, `test_verify_install_hints`, `test_verify_format_*`,
  `test_verify_alignment`, `test_verify_tools_exposed`, `test_verify_command`, plus
  `conftest.py`) already import these private helpers directly. Steps 1–2 update
  those imports (function imports auto via `move_symbol`; constant imports by hand).
  Step 3 only concerns the one remaining oversized orchestration test file.

## Steps (each = one commit / one PR)

| Step | Scope | New file | Allowlist action |
|------|-------|----------|------------------|
| 1 | Extract exit-code helpers | `verify_exit_code.py` | none (`verify.py` still ~1015 lines) |
| 2 | Extract formatting primitives + constant maps | `verify_formatting.py` | **remove** `verify.py` (now ~620) |
| 3 | Split orchestration test by test class | 2 new test files | **remove** `test_verify_orchestration.py` |

**Ordering dependency:** Step 3 assumes Steps 1 & 2 are merged (the orchestration
test's imports of `_format_mcp_section` and the in-function `_LABEL_WIDTH` /
`_MARKER_SLOT_WIDTH` reference `verify_formatting` after Step 2).

## Folders / modules / files created or modified

**No new folders.** No `.importlinter` / `tach.toml` changes.

### Created
- `src/mcp_coder/cli/commands/verify_exit_code.py` (Step 1)
- `src/mcp_coder/cli/commands/verify_formatting.py` (Step 2)
- `tests/cli/commands/test_verify_mcp_orchestration.py` (Step 3, name at implementer's discretion)
- `tests/cli/commands/test_verify_sections_orchestration.py` (Step 3, name at implementer's discretion)

### Modified
- `src/mcp_coder/cli/commands/verify.py` (Steps 1 & 2 — symbols removed, imports back added)
- `.large-files-allowlist` (Step 2 removes `verify.py`; Step 3 removes `test_verify_orchestration.py`)
- `tests/cli/commands/conftest.py` (Step 2 constant repoint; Step 3 gains shared helpers)
- `tests/cli/commands/test_verify_orchestration.py` (Step 2 import repoint; Step 3 reduced to one class group)
- Step 1 importers (function imports, auto): `test_verify_exit_codes.py`,
  `test_verify_exit_codes_git.py`, `test_verify_exit_codes_github.py`,
  `test_verify_install_hints.py`
- Step 2 importers: `test_verify.py`, `test_verify_alignment.py`,
  `test_verify_command.py`, `test_verify_format_mcp_section.py`,
  `test_verify_format_pad.py`, `test_verify_format_section_basic.py`,
  `test_verify_tools_exposed.py`

## Per-step verification (run all, all must pass)

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_lint_imports_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-workspace__check_file_size(max_lines=750)
```
Plus `tach check` via Bash (no MCP equivalent) and `git-tool compact-diff` to confirm
only imports moved.
