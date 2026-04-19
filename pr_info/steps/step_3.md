# Step 3: Update all skills and rebase design doc

**Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE

5 files:
- `.claude/skills/commit_push/SKILL.md`
- `.claude/skills/implementation_review/SKILL.md`
- `.claude/skills/plan_review/SKILL.md`
- `.claude/skills/rebase/SKILL.md`
- `.claude/skills/rebase/rebase_design.md`

## WHAT

For each file, two types of changes:

### A. Frontmatter `allowed-tools` updates

| File | Remove | Add |
|------|--------|-----|
| `commit_push/SKILL.md` | `Bash(git status *)`, `Bash(git diff *)`, `Bash(git log *)` | `mcp__workspace__git_status`, `mcp__workspace__git_diff`, `mcp__workspace__git_log` |
| `implementation_review/SKILL.md` | `Bash(git status *)`, `Bash(git diff *)`, `Bash(mcp-coder git-tool *)` | `mcp__workspace__git_status`, `mcp__workspace__git_diff` |
| `plan_review/SKILL.md` | `Bash(git status *)` | `mcp__workspace__git_status` |
| `rebase/SKILL.md` | `Bash(git status *)`, `Bash(git diff *)`, `Bash(git log *)` | `mcp__workspace__git_status`, `mcp__workspace__git_diff`, `mcp__workspace__git_log` |
| `rebase/rebase_design.md` | N/A (no frontmatter) | N/A |

### B. Body text updates

**`commit_push/SKILL.md`:**
- Replace bash `git status` / `git diff` commands in "Review Changes" section with MCP tool references

**`implementation_review/SKILL.md`:**
- Replace `git status` with `mcp__workspace__git_status` reference
- Replace `mcp-coder git-tool compact-diff` with `mcp__workspace__git_diff`

**`plan_review/SKILL.md`:**
- Replace `git status` with `mcp__workspace__git_status` reference

**`rebase/SKILL.md`:**
- Replace `git status` with `mcp__workspace__git_status` in pre-flight check context
- Replace `git diff` with `mcp__workspace__git_diff` where used for inspection (not for `git diff` in rebase conflict contexts which stay as bash)
- Replace `git log` with `mcp__workspace__git_log` where used for inspection

**`rebase/rebase_design.md`:**
- In the "Rebase-Specific Permissions" code block, replace `Bash(git status:*)` and `Bash(git log:*)` with their MCP equivalents
- Add a note that these are now MCP tools, not Bash permissions

## HOW

Direct markdown edits using `mcp__workspace__edit_file` for each file.

**Important for rebase/SKILL.md:** Only replace read-only uses. Git commands used for *write* operations (e.g., `git add`, `git rebase --continue`) stay as Bash. The `!git status` auto-run directive at the top should reference the MCP tool.

## DATA

No data structures. Markdown/YAML frontmatter only.

## Tests

No tests — these are documentation/config changes with no code.

## Verification

After editing, confirm for each file:
1. Frontmatter `allowed-tools` no longer has `Bash(git status *)`, `Bash(git diff *)`, `Bash(git log *)`, or `Bash(mcp-coder git-tool *)`
2. Corresponding MCP tools are present in `allowed-tools`
3. Body text references MCP tools for read-only git operations
4. Write operations (`git add`, `git commit`, `git push`, `git rebase`) remain as Bash

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_3.md.

Update all 5 files listed in the step:
- Replace Bash git read permissions with MCP tool equivalents in allowed-tools frontmatter
- Update body text to reference MCP tools for read-only git operations
- Keep all git write operations as Bash commands
- Replace mcp-coder git-tool compact-diff references with mcp__workspace__git_diff
```
