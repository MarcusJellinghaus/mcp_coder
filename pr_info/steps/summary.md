# Issue #672: Replace Bash tool scripts with MCP equivalents in skills and settings

## Summary

Replace three Bash-invoked shell scripts (`format_all.sh`, `lint_imports.sh`, `vulture_check.sh`) with their MCP tool equivalents in Claude Code configuration, skills, and documentation. Add new `get_library_source` permission. Shell scripts themselves are kept for CI and human use.

## Architectural / Design Changes

**Before:** Claude Code invoked `format_all.sh`, `lint_imports.sh`, and `vulture_check.sh` via `Bash()` permissions. This required platform-specific entries (`.sh` / `.bat`), shell execution overhead, and inconsistent tool invocation (some checks via MCP, some via Bash).

**After:** All code quality tools are invoked uniformly via MCP (`mcp__tools-py__*`). Shell scripts remain for CI pipelines and human developers. Documentation uses audience-split: "For Claude Code" (MCP tools) vs "For humans/CI" (shell scripts).

**Key decisions:**
- Clean break: remove old Bash permissions in same PR (no transition period)
- `ruff_check.sh` stays as Bash — no MCP equivalent exists
- Test fixtures use fictional tool names to decouple from real tool names
- `get_library_source` is a net-new permission addition, not a replacement

## Files Modified

### Configuration (2 files)
| File | Change |
|------|--------|
| `.claude/settings.local.json` | Add 4 MCP permissions, remove 3 Bash permissions |
| `.claude/CLAUDE.md` | Update tool mapping table + git operations sections |

### Skills (3 files)
| File | Change |
|------|--------|
| `.claude/skills/commit_push/SKILL.md` | Replace format_all.sh/.bat with MCP tool |
| `.claude/skills/implement_direct/SKILL.md` | Replace format_all.sh with MCP tool |
| `.claude/skills/rebase/SKILL.md` | Replace format_all.sh/.bat with MCP tool |

### Documentation (4 files)
| File | Change |
|------|--------|
| `docs/repository-setup.md` | Audience-split for format/lint/vulture tools |
| `docs/configuration/claude-code.md` | Update settings example |
| `docs/processes-prompts/refactoring-guide.md` | Add MCP alternatives in standard checks |
| `docs/architecture/dependencies/readme.md` | Add MCP column to tools table |

### Tests (2 files)
| File | Change |
|------|--------|
| `tests/checks/test_ci_log_parser.py` | Replace real tool names with fictional names |
| `tests/checks/test_branch_status.py` | Replace vulture references with fictional names in TestExtractFailedStepLog |

**No files created. No files deleted. 11 files modified total.**

## Steps Overview

| Step | Scope | Files |
|------|-------|-------|
| 1 | Test fixture cleanup | `tests/checks/test_ci_log_parser.py`, `tests/checks/test_branch_status.py` |
| 2 | Config: settings + CLAUDE.md | `settings.local.json`, `CLAUDE.md` |
| 3 | Skills: commit_push, implement_direct, rebase | 3 SKILL.md files |
| 4 | Docs: audience-split updates | 4 docs files |
