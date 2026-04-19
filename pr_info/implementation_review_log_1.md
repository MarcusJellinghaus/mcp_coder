# Implementation Review Log — Issue #864

**Issue:** chore: prefer MCP git tools over bash git commands in Claude config
**Branch:** 864-chore-prefer-mcp-git-tools-over-bash-git-commands-in-claude-config
**Date:** 2026-04-19

## Round 1 — 2026-04-19
**Findings:**
- (Accept) `implementation_review_supervisor/SKILL.md` still has `Bash(mcp-coder git-tool *)` and is missing MCP git tool equivalents — consistency gap with other updated skills
- (Accept) `knowledge_base/refactoring_principles.md` references removed `mcp-coder git-tool compact-diff` — Boy Scout fix
- (Skip) Ordering of `allowed-tools` entries in skill frontmatter — cosmetic, pre-existing
- (Skip) `pr_info/` planning artifacts — out of scope

**Decisions:**
- Accept both findings — bounded effort, same type of change as the rest of the PR
- Skip cosmetic and out-of-scope items

**Changes:**
- Updated `implementation_review_supervisor/SKILL.md`: removed `Bash(mcp-coder git-tool *)`, added `mcp__workspace__git_status` and `mcp__workspace__git_diff` to allowed-tools
- Updated `knowledge_base/refactoring_principles.md`: replaced `mcp-coder git-tool compact-diff` with `mcp__workspace__git_diff`

**Status:** Committed as edb9000

## Round 2 — 2026-04-19
**Findings:** No issues found — implementation is clean.
**Decisions:** N/A
**Changes:** None
**Status:** No changes needed

## Final Status
- **Rounds:** 2 (1 with fixes, 1 clean)
- **Commits:** 1 (edb9000)
- **Vulture:** Clean
- **Lint-imports:** All 23 contracts kept
- **Remaining issues:** None

