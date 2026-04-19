# Summary: Prefer MCP git tools over bash git commands in Claude config

**Issue:** #864

## Goal

Replace Bash-based git read operations (`git status`, `git diff`, `git log`) with MCP workspace tools (`mcp__workspace__git_status`, `mcp__workspace__git_diff`, `mcp__workspace__git_log`, `mcp__workspace__git_merge_base`) across Claude configuration files and skills. This enables permission-prompt-free execution for read-only git operations.

Also remove `Bash(mcp-coder git-tool:*)` — its compact-diff functionality is replaced by `mcp__workspace__git_diff` which has compact diff built-in.

## Architectural / Design Changes

- **Permission model shift:** Read-only git operations move from Bash-allowed permissions (which require user approval prompts) to MCP tool permissions (which run without prompts). Write operations (`git commit`, `git push`, `git add`, `git rebase`, etc.) remain Bash-only.
- **Compact diff consolidation:** `mcp-coder git-tool compact-diff` (a CLI command) is replaced by `mcp__workspace__git_diff` (an MCP tool with built-in compact diff and `--exclude` support). One tool instead of two.
- **Skill permission scoping:** Each skill's `allowed-tools` frontmatter is updated to reference MCP tools instead of Bash git commands for read operations. This is consistent with the project's principle of preferring MCP tools over Bash.
- **Forward-compatible:** The MCP git tools are not yet registered in the workspace server, but config is prepared ahead of time so it's ready when the workspace package is updated.

## Constraints

- `git show` remains Bash-only — no MCP equivalent exists
- `git fetch`, `git commit`, `git add`, `git rebase`, `git push`, `git ls-tree` remain Bash-only
- No source code (`.py`) changes — purely config/documentation
- No tests required (no code changes)

## Files Modified

| File | Change |
|------|--------|
| `.claude/settings.local.json` | Remove 4 Bash permissions, add 4 MCP permissions |
| `.claude/CLAUDE.md` | Add tool-mapping rows, update git operations section, replace compact-diff guidance |
| `.claude/skills/commit_push/SKILL.md` | Update `allowed-tools` and body references |
| `.claude/skills/implementation_review/SKILL.md` | Update `allowed-tools` and body references |
| `.claude/skills/plan_review/SKILL.md` | Update `allowed-tools` and body references |
| `.claude/skills/rebase/SKILL.md` | Update `allowed-tools` and body references |
| `.claude/skills/rebase/rebase_design.md` | Update permissions documentation |

## Implementation Steps

| Step | Description | Files |
|------|-------------|-------|
| 1 | Update settings.local.json permissions | `.claude/settings.local.json` |
| 2 | Update CLAUDE.md tool mapping and git operations section | `.claude/CLAUDE.md` |
| 3 | Update all skills and rebase design doc | 5 files under `.claude/skills/` |
