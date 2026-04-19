# Step 2: Update CLAUDE.md tool mapping and git operations section

**Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE

- `.claude/CLAUDE.md`

## WHAT

Three changes in this file:

### A. Tool mapping table — add 4 rows

Add these rows to the existing tool mapping table (after the "Refactoring" row):

| Task | MCP tool |
|------|----------|
| Git status | `mcp__workspace__git_status` |
| Git diff (includes compact diff) | `mcp__workspace__git_diff` |
| Git log | `mcp__workspace__git_log` |
| Git merge-base | `mcp__workspace__git_merge_base` |

### B. Git operations section — update "Allowed commands via Bash"

**Current block:**
```
git status / diff / commit / log / fetch / ls-tree
...
mcp-coder git-tool compact-diff
```

**New block** — remove `status`, `diff`, `log` and `mcp-coder git-tool compact-diff`:
```
git commit / fetch / show / ls-tree
```

### C. Compact diff guidance — replace

**Current text:**
> **Compact diff:** use `mcp-coder git-tool compact-diff` instead of `git diff` for code review. Detects moved code, collapses unchanged blocks. Supports `--exclude PATTERN`.

**New text:**
> **Compact diff:** use `mcp__workspace__git_diff` for code review. Has compact diff built-in with exclude pattern support.

## HOW

Direct markdown edits using `mcp__workspace__edit_file`.

## DATA

No data structures. Markdown documentation only.

## Tests

No tests — this is a documentation change with no code.

## Verification

After editing, confirm:
1. Tool mapping table has the 4 new git rows
2. Bash-allowed list no longer mentions `status`, `diff`, `log`, or `mcp-coder git-tool compact-diff`
3. Bash-allowed list still includes `commit`, `fetch`, `show`, `ls-tree`
4. Compact diff paragraph references `mcp__workspace__git_diff`

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_2.md.

Update .claude/CLAUDE.md with three changes:
1. Add 4 git MCP tool rows to the tool mapping table
2. Remove git status/diff/log and mcp-coder git-tool compact-diff from the Bash-allowed commands
3. Replace compact-diff guidance to reference mcp__workspace__git_diff
```
