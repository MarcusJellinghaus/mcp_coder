# Issue #647: implement_direct — Implementation Summary

## Overview

Add a streamlined single-shot implementation skill (`/implement_direct`) for small, well-defined issues. It skips planning and task tracking — going straight from issue to code. For complex features, the full `/create_plan` → `/implement` workflow remains available.

## Architectural / Design Changes

### New Concept: Skills Directory

This introduces the first entry in `.claude/skills/` — a newer Claude Code format alongside the existing `.claude/commands/`. Skills use different frontmatter (`name`, `disable-model-invocation`, `argument-hint`, `allowed-tools`) compared to commands (`workflow-stage`, `suggested-next`).

### New CLI Subcommand Under `gh-tool`

`mcp-coder gh-tool checkout-issue-branch <number>` is a self-contained command that:
- Fetches from remote
- Resolves the issue's linked branch (or creates one via GitHub API)
- Checks out the branch locally

This lives under `gh-tool` (not `git-tool`) because it's fundamentally a GitHub operation (issue lookup, linked branch creation via GitHub GraphQL API). It delegates entirely to existing utilities — no new parsing or GitHub logic needed.

### Design Decisions

- **No new utility classes or abstractions** — the handler calls `IssueManager` and `IssueBranchManager` directly
- **Same error handling pattern** as existing `execute_get_base_branch()` — exit codes 0/1/2
- **Output**: prints branch name to stdout (clean for CLI piping), errors to stderr
- **Git operations** (`fetch`, `checkout`) use `subprocess.run` consistent with other CLI commands

## Files Created / Modified

| File | Action | Purpose |
|------|--------|---------|
| `.claude/skills/implement_direct/SKILL.md` | **Create** | New skill prompt |
| `src/mcp_coder/cli/parsers.py` | **Modify** | Add `checkout-issue-branch` subparser |
| `src/mcp_coder/cli/main.py` | **Modify** | Add dispatch route + import |
| `src/mcp_coder/cli/commands/gh_tool.py` | **Modify** | Add `execute_checkout_issue_branch()` |
| `tests/cli/commands/test_gh_tool.py` | **Modify** | Add tests for new subcommand |
| `.claude/settings.local.json` | **Modify** | Add `Skill(implement_direct)` permission |

## Modules / Packages Involved

- `src/mcp_coder/cli/` — CLI layer (parser, dispatcher, command handler)
- `src/mcp_coder/utils/github_operations/issues/` — Existing managers (no changes)
  - `manager.py` → `IssueManager.get_issue()` — fetches issue with `base_branch`
  - `branch_manager.py` → `IssueBranchManager.get_linked_branches()`, `.create_remote_branch_for_issue()`
- `.claude/skills/` — New directory for skills format
- `.claude/settings.local.json` — Permission configuration

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Tests + handler: `execute_checkout_issue_branch()` in `gh_tool.py` | tests + implementation |
| 2 | Parser + dispatch wiring for `checkout-issue-branch` | parser + main.py + CLI integration tests |
| 3 | Skill file + settings update | SKILL.md + settings.local.json |
