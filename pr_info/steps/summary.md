# Issue #672: Replace Bash tool scripts with MCP equivalents in skills and settings

## Summary

Replace Bash invocations of `format_all.sh`, `lint_imports.sh`, and `vulture_check.sh` with their MCP tool equivalents across Claude Code configuration, skills, and documentation. Add new `get_library_source` permission. Decouple test fixtures from real tool names.

## Design Changes

**No Python source code changes.** This is a configuration, documentation, and test-fixture-only change.

### What changes conceptually

1. **Claude Code tool routing** — Three shell scripts that Claude previously invoked via `Bash()` are now invoked as MCP tools. This is a clean break: old Bash permissions are removed, MCP permissions are added.
2. **Skill definitions** — Three skills (`commit_push`, `implement_direct`, `rebase`) switch from allowing `Bash(./tools/format_all.sh)` to allowing `mcp__tools-py__run_format_code`.
3. **Instruction updates** — CLAUDE.md commit instructions reference MCP tools instead of shell scripts. New quality check tools and `get_library_source` are added to their natural sections (not as new tool mapping rows).
4. **Documentation approach** — Docs add brief inline notes about MCP equivalents. Shell scripts remain the primary reference for humans/CI.
5. **Test fixture decoupling** — `test_ci_log_parser.py` uses fictional tool names to avoid coupling test data to real tool names.

### What does NOT change

- Shell scripts themselves (`tools/*.sh`, `tools/*.bat`) — kept for CI and human use
- `ruff_check.sh` — no MCP equivalent, stays as Bash
- Python source code — no functional changes
- CI workflows — unchanged

## MCP Tool Mapping

| Bash Command | MCP Replacement | Runs |
|---|---|---|
| `./tools/format_all.sh` | `mcp__tools-py__run_format_code` | isort + black |
| `./tools/lint_imports.sh` | `mcp__tools-py__run_lint_imports_check` | import-linter |
| `./tools/vulture_check.sh` | `mcp__tools-py__run_vulture_check` | vulture dead code |
| *(new)* | `mcp__tools-py__get_library_source` | library source viewer |

## Files Modified

### Configuration
- `.claude/settings.local.json` — Add 4 MCP permissions, remove 3 Bash permissions

### Skills
- `.claude/skills/commit_push/SKILL.md` — Replace format_all.sh with MCP tool
- `.claude/skills/implement_direct/SKILL.md` — Add MCP tool to allowed-tools, replace format_all.sh reference
- `.claude/skills/rebase/SKILL.md` — Replace format_all.sh with MCP tool

### Instructions
- `.claude/CLAUDE.md` — Update commit instructions, add quality check tools to their natural sections, add `get_library_source` to Refactoring row

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
| 1 | `settings.local.json` permissions + 3 skill SKILL.md files | `chore: update permissions and skills for MCP tool replacements` |
| 2 | `CLAUDE.md` — commit instructions, quality checks section, refactoring row | `docs: update CLAUDE.md tool mapping and commit instructions` |
| 3 | 4 docs files — inline MCP notes | `docs: add MCP tool references to documentation` |
| 4 | `test_ci_log_parser.py` — fictional names | `test: decouple CI log parser fixtures from real tool names` |
