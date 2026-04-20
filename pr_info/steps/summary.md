# Summary: Migrate read-only git and gh commands to MCP tools

**Issue:** #876

## Goal

Replace Bash-based read-only git and GitHub CLI commands with their MCP tool equivalents across configuration and skill files. Write operations remain as Bash.

## Architectural / Design Changes

- **Permission model shift:** Read-only git commands (`fetch`, `ls-tree`, `show`, `ls-files`, `ls-remote`, `rev-parse`, `branch --list`) move from individual `Bash(git <cmd>:*)` permissions to a single `mcp__workspace__git` MCP permission. This reduces permission surface and aligns with the MCP-first architecture.
- **GitHub CLI abstraction:** `gh issue view`, `gh issue list`, `gh pr view`, and `gh search` move from Bash to dedicated MCP tools (`mcp__workspace__github_issue_view`, etc.). `gh run view` is dropped entirely (no MCP equivalent, not needed).
- **Skill instruction style:** Skills switch from bash code blocks to explicit MCP parameter style (e.g., `Call mcp__workspace__git with command "fetch" and args ["origin"]`), making tool usage unambiguous for the LLM.
- **No Python code changes.** This is purely a configuration and documentation migration.

## Files Modified

| File | Change |
|------|--------|
| `.claude/settings.local.json` | Remove 6 Bash permissions, add 5 MCP permissions |
| `.claude/CLAUDE.md` | Add tool mapping rows, trim Bash-allowed section |
| `.claude/skills/rebase/SKILL.md` | Swap allowed-tools + replace bash commands with MCP calls |
| `.claude/skills/issue_create/SKILL.md` | Swap allowed-tools + replace bash commands with MCP calls |
| `.claude/skills/issue_analyse/SKILL.md` | Swap allowed-tools + replace bash commands with MCP calls |
| `.claude/skills/implementation_review/SKILL.md` | Swap allowed-tools + replace bash commands with MCP calls |
| `.claude/skills/plan_review/SKILL.md` | Swap allowed-tools + replace bash commands with MCP calls |
| `.claude/skills/rebase/rebase_design.md` | Update permissions listing to reflect MCP tools |

## Files Created

None.

## Constraints

- Write operations (`git commit`, `git add`, `git rebase`, `git push`, `gh issue create`) stay as Bash
- `mcp-coder check branch-status` stays as Bash (out of scope — #877)
- `gh run view` dropped entirely (no MCP equivalent)
- `settings.local.json` entries maintain alphabetical ordering
- No Python source or test changes — TDD not applicable
