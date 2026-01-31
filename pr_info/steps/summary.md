# Issue #370: Dynamic Base Branch Detection

## Summary

Replace hardcoded `main` branch references in slash commands with dynamic base branch detection, enabling workflows where branches are based on non-main branches (e.g., hotfixes on release branches, features building on other features).

## Architectural / Design Changes

### New CLI Command Structure

```
mcp-coder
└── gh-tool                          # NEW command group
    └── get-base-branch              # NEW subcommand
        --project-dir PATH           # Optional project directory
```

### Detection Priority (3-tier)

1. **GitHub PR base branch** - If open PR exists for current branch
2. **Linked issue's `### Base Branch`** - Extract issue number from branch name, query issue body
3. **Default branch** - Fall back to repository's default (main/master)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - base branch printed to stdout |
| 1 | Could not detect base branch (graceful fallback failed) |
| 2 | Error (not a git repo, API failure, etc.) |

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/cli/commands/gh_tool.py` | New CLI command implementation |
| `tests/cli/commands/test_gh_tool.py` | Unit tests for new command |

## Files to Modify

| File | Change Type |
|------|-------------|
| `src/mcp_coder/cli/main.py` | Register `gh-tool` command group |
| `.claude/commands/implementation_review.md` | Use dynamic base branch for git diff |
| `.claude/commands/rebase.md` | Use dynamic base branch for rebase |
| `.claude/commands/check_branch_status.md` | Update descriptive text |
| `docs/cli-reference.md` | Add new command documentation |
| `docs/configuration/claude-code.md` | Update `/rebase` description |
| `docs/processes-prompts/claude_cheat_sheet.md` | Update `/rebase` description |

## Reused Existing Code

| Function | Location | Purpose |
|----------|----------|---------|
| `get_current_branch_name()` | `git_operations/readers.py` | Get current branch |
| `extract_issue_number_from_branch()` | `git_operations/readers.py` | Extract issue # from branch name |
| `get_default_branch_name()` | `git_operations/readers.py` | Get repo's default branch |
| `IssueManager.get_issue()` | `github_operations/issue_manager.py` | Fetch issue with `base_branch` field |
| `PullRequestManager.list_pull_requests()` | `github_operations/pr_manager.py` | List open PRs |
| `_parse_base_branch()` | `github_operations/issue_manager.py` | Already parses `### Base Branch` |

## Implementation Steps Overview

| Step | Description | Files |
|------|-------------|-------|
| 1 | Tests for `gh-tool get-base-branch` command | `tests/cli/commands/test_gh_tool.py` |
| 2 | Implement `gh-tool get-base-branch` command | `src/mcp_coder/cli/commands/gh_tool.py`, `src/mcp_coder/cli/main.py` |
| 3 | Update slash commands to use dynamic base branch | `.claude/commands/*.md` |
| 4 | Update documentation | `docs/*.md` |

## Backwards Compatibility

- Existing workflows without base branch specification continue to work (falls back to default branch)
- No breaking changes to existing CLI commands
- Slash commands remain functional with same interface
