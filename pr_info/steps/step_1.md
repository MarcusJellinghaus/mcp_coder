# Step 1: Update settings and CLAUDE.md

**Ref:** See `pr_info/steps/summary.md` for full context (issue #876).

## Prompt

> Implement step 1 of the plan in `pr_info/steps/summary.md`.
> Update `.claude/settings.local.json` and `.claude/CLAUDE.md` to migrate read-only git and gh commands from Bash permissions to MCP tools.
> See `pr_info/steps/step_1.md` for details.

## WHERE

- `.claude/settings.local.json`
- `.claude/CLAUDE.md`

## WHAT — `settings.local.json`

**Remove** these Bash permissions from `permissions.allow`:
- `Bash(git fetch:*)`
- `Bash(git ls-tree:*)`
- `Bash(gh issue view:*)`
- `Bash(gh pr view:*)`
- `Bash(gh run view:*)`
- `Bash(gh search:*)`

**Add** these MCP permissions (maintain alphabetical order among existing `mcp__workspace__*` entries):
- `mcp__workspace__git`
- `mcp__workspace__github_issue_list`
- `mcp__workspace__github_issue_view`
- `mcp__workspace__github_pr_view`
- `mcp__workspace__github_search`

## WHAT — `CLAUDE.md`

**Tool mapping table** — add these rows:

| Task | MCP tool |
|------|----------|
| Git read-only (fetch, ls-tree, show, ls-files, ls-remote, rev-parse, branch list) | `mcp__workspace__git` |
| `gh issue view` | `mcp__workspace__github_issue_view` |
| `gh issue list` | `mcp__workspace__github_issue_list` |
| `gh pr view` | `mcp__workspace__github_pr_view` |
| `gh search` | `mcp__workspace__github_search` |

**"Allowed commands via Bash tool" section** — remove `gh issue view / gh pr view / gh run view` line entirely. Replace `git commit / fetch / show / ls-tree` with `git commit / add / rebase / push` (keeping write operations, removing read-only ones now covered by MCP). Also update the preamble sentence: change `Skills that instruct bash commands (e.g. \`gh issue view\`) must also use Bash.` to `Skills that instruct bash commands (e.g. \`git commit\`) must also use Bash.` (since `gh issue view` is now an MCP tool, not a Bash command). The section should become:

```
git commit / add / rebase / push
mcp-coder check branch-status
mcp-coder check file-size --max-lines 750
mcp-coder gh-tool set-status <label>
```

## DATA

No code, no return values. Config and documentation only.

## Commit

`chore: migrate git/gh read-only permissions to MCP tools in settings and CLAUDE.md`
