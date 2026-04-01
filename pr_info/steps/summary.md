# Issue #672: Replace Bash tool scripts with MCP equivalents in skills and settings

## Summary

Replace Bash invocations of `format_all.sh`, `lint_imports.sh`, and `vulture_check.sh` with their MCP tool equivalents across Claude Code configuration, skills, and documentation. Add new `get_library_source` permission. Decouple test fixtures from real tool names.

## Already Completed (prior PR on main)

The following changes were completed via a prior PR merged to main:

- **settings.local.json**: All 4 MCP permissions added, all 3 Bash permissions removed
- **3 skill files** (commit_push, implement_direct, rebase): `mcp__tools-py__run_format_code` in allowed-tools and instructions, old Bash entries removed
- **CLAUDE.md** (partial): Tool mapping table has 4 new rows (format_code, lint_imports, vulture_check, get_library_source), "Before ANY commit" and "Format all code" sections updated, Quick Examples updated

## Design Changes

**No Python source code changes.** This is a configuration, documentation, and test-fixture-only change.

### What changes conceptually

1. **Instruction updates** — CLAUDE.md Code Quality Requirements section updated from "ALL THREE" to "ALL FIVE" checks, adding lint_imports_check and vulture_check. Refactoring row gets `get_library_source()`.
2. **Documentation approach** — Docs add brief inline notes about MCP equivalents. Shell scripts remain the primary reference for humans/CI.
3. **Test fixture decoupling** — `test_ci_log_parser.py` uses fictional tool names to avoid coupling test data to real tool names.

### What does NOT change

- Shell scripts themselves (`tools/*.sh`, `tools/*.bat`) — kept for CI and human use
- `ruff_check.sh` — no MCP equivalent, stays as Bash
- Python source code — no functional changes
- CI workflows — unchanged
- settings.local.json — already done
- Skill files — already done

## MCP Tool Mapping

| Bash Command | MCP Replacement | Runs |
|---|---|---|
| `./tools/format_all.sh` | `mcp__tools-py__run_format_code` | isort + black |
| `./tools/lint_imports.sh` | `mcp__tools-py__run_lint_imports_check` | import-linter |
| `./tools/vulture_check.sh` | `mcp__tools-py__run_vulture_check` | vulture dead code |
| *(new)* | `mcp__tools-py__get_library_source` | library source viewer |

## Files Modified (remaining)

### Instructions
- `.claude/CLAUDE.md` — Update Code Quality Requirements section (THREE→FIVE), add `get_library_source` to Refactoring row

### Documentation
- `docs/repository-setup.md` — Add MCP tool notes
- `docs/configuration/claude-code.md` — Update permissions example
- `docs/processes-prompts/refactoring-guide.md` — Add MCP tool notes
- `docs/architecture/dependencies/readme.md` — Add MCP tool notes

### Tests
- `tests/checks/test_ci_log_parser.py` — Replace real tool names with fictional names

## Implementation Steps

| Step | Scope | Commit |
|------|-------|--------|
| 1 | `CLAUDE.md` — Code Quality Requirements section (THREE→FIVE), Refactoring row (add get_library_source) | `docs: update CLAUDE.md quality checks section and refactoring row` |
| 2 | 4 docs files — inline MCP notes | `docs: add MCP tool references to documentation` |
| 3 | `test_ci_log_parser.py` — fictional names | `test: decouple CI log parser fixtures from real tool names` |
