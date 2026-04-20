# Step 2: Update skill files to use MCP tools

**Ref:** See `pr_info/steps/summary.md` for full context (issue #876).

## Prompt

> Implement step 2 of the plan in `pr_info/steps/summary.md`.
> Update all affected skill files to replace Bash git/gh commands with MCP tool calls.
> See `pr_info/steps/step_2.md` for details.

## WHERE

- `.claude/skills/rebase/SKILL.md`
- `.claude/skills/issue_create/SKILL.md`
- `.claude/skills/issue_analyse/SKILL.md`
- `.claude/skills/implementation_review/SKILL.md`
- `.claude/skills/plan_review/SKILL.md`
- `.claude/skills/rebase/rebase_design.md`

## WHAT — Frontmatter `allowed-tools` changes

### `/rebase` (SKILL.md)
**Remove:**
- `Bash(git branch *)`
- `Bash(git ls-files *)`
- `Bash(git fetch *)`
- `Bash(git rev-parse *)`
- `Bash(gh run view *)`
- `Bash(gh issue view *)`

**Add:**
- `mcp__workspace__git`

Write operations stay: `Bash(git rebase *)`, `Bash(git add *)`, `Bash(git rm *)`, `Bash(git commit *)`, `Bash(git checkout --ours *)`, `Bash(git checkout --theirs *)`, `Bash(git remote get-url *)`, `Bash(git restore *)`, `Bash(git stash *)`, `Bash(git push --force-with-lease *)`.

### `/issue_create` (SKILL.md)
**Remove:** `Bash(git ls-remote *)`
**Add:** `mcp__workspace__git`

### `/issue_analyse` (SKILL.md)
**Remove:** `Bash(gh issue view *)`, `Bash(git ls-remote *)`
**Add:** `mcp__workspace__github_issue_view`, `mcp__workspace__git`

### `/implementation_review` (SKILL.md)
**Remove:** `Bash(git fetch *)`
**Add:** `mcp__workspace__git`

### `/plan_review` (SKILL.md)
**Remove:** `Bash(git fetch *)`
**Add:** `mcp__workspace__git`

## WHAT — Skill body changes

Replace bash code blocks with explicit MCP parameter style. Examples of replacements:

| Old (Bash) | New (MCP) |
|------------|-----------|
| `` `git fetch` `` / `` `git fetch origin` `` | Call `mcp__workspace__git` with command `"fetch"` and args `["origin"]` |
| `` `git branch --list` `` | Call `mcp__workspace__git` with command `"branch"` and args `["--list"]` |
| `` `git ls-files --unmerged` `` | Call `mcp__workspace__git` with command `"ls-files"` and args `["--unmerged"]` |
| `` `git rev-parse --abbrev-ref HEAD` `` | Call `mcp__workspace__git` with command `"rev-parse"` and args `["--abbrev-ref", "HEAD"]` |
| `` `git ls-remote --heads origin <branch>` `` | Call `mcp__workspace__git` with command `"ls-remote"` and args `["--heads", "origin", "<branch-name>"]` |
| `` `gh issue view <number>` `` | Call `mcp__workspace__github_issue_view` with issue number |

### `/rebase` body
- Replace `git fetch origin` with MCP call
- Replace any `git branch`, `git ls-files`, `git rev-parse` occurrences with MCP calls
- Remove `gh run view` and `gh issue view` references (no longer available in this skill)

### `/issue_create` body
- Replace `git ls-remote --heads origin <branch-name>` with MCP call

### `/issue_analyse` body
- Replace `gh issue view <issue_number>` with MCP call
- Replace `git ls-remote --heads origin <branch-name>` with MCP call

### `/implementation_review` body
- Replace `git fetch` with MCP call

### `/plan_review` body
- Replace `git fetch` with MCP call

## WHAT — `rebase_design.md`

Update the "Rebase-Specific Permissions" section to reflect that read-only git commands now use `mcp__workspace__git`:

**Old entries to remove/replace:**
```
Bash(git branch:*)
Bash(git ls-files:*)
Bash(git fetch:*)
```

**New entry:**
```
mcp__workspace__git  # read-only: fetch, branch, ls-files, rev-parse
```

Keep all write Bash entries unchanged.

## DATA

No code, no return values. Skill documentation only.

## Commit

`chore: update skills to use MCP tools for read-only git/gh commands`
