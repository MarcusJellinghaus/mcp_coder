# Step 4: Update Documentation

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Update the documentation to reflect the new `gh-tool get-base-branch` command 
and fix any remaining hardcoded "main" references in rebase-related descriptions.
```

## WHERE

- **Modify**: `docs/cli-reference.md`
- **Modify**: `docs/configuration/claude-code.md`
- **Modify**: `docs/processes-prompts/claude_cheat_sheet.md`

## WHAT

### 1. `docs/cli-reference.md`

**Add new section** (after `check file-size` section):

```markdown
---

## gh-tool get-base-branch

Detect the base branch for the current feature branch.

```bash
mcp-coder gh-tool get-base-branch [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)

**Description:** Detects the appropriate base branch for git operations (diff, rebase) using a priority-based approach:

1. **GitHub PR base branch** - If an open PR exists for the current branch
2. **Linked issue's base branch** - Extracts issue number from branch name and checks the `### Base Branch` section in the issue body
3. **Default branch** - Falls back to the repository's default branch (main/master)

**Exit Codes:**
- `0` - Success, base branch printed to stdout
- `1` - Could not detect base branch
- `2` - Error (not a git repo, API failure, etc.)

**Examples:**
```bash
# Detect base branch for current feature branch
mcp-coder gh-tool get-base-branch

# Use in shell scripts
BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
git diff ${BASE_BRANCH}...HEAD

# Specify project directory
mcp-coder gh-tool get-base-branch --project-dir /path/to/project
```

**Use Cases:**
- Slash commands (`/rebase`, `/implementation_review`) use this to determine correct base branch
- CI scripts that need to compare against the correct parent branch
- Workflows involving feature branches based on non-main branches
```

**Update existing text** in `check branch-status` section:

```markdown
# Current
- **Rebase Detection** - Checks if branch needs rebasing onto main

# New  
- **Rebase Detection** - Checks if branch needs rebasing onto base branch
```

**Add to Command List table** (under Quality Checks section):

```markdown
### GitHub Tools

| Command | Description |
|---------|-------------|
| [`gh-tool get-base-branch`](#gh-tool-get-base-branch) | Detect base branch for current feature branch |
```

### 2. `docs/configuration/claude-code.md`

**Update table**:

```markdown
# Current
| `/rebase` | Rebase branch onto main |

# New
| `/rebase` | Rebase branch onto base branch |
```

### 3. `docs/processes-prompts/claude_cheat_sheet.md`

**Update table**:

```markdown
# Current
| `/rebase` | Rebase branch onto main |

# New
| `/rebase` | Rebase branch onto base branch |
```

## HOW

### Simple Text Replacements

| File | Find | Replace |
|------|------|---------|
| `cli-reference.md` | "rebasing onto main" | "rebasing onto base branch" |
| `claude-code.md` | "Rebase branch onto main" | "Rebase branch onto base branch" |
| `claude_cheat_sheet.md` | "Rebase branch onto main" | "Rebase branch onto base branch" |

### Add New Section

In `cli-reference.md`, add the `gh-tool get-base-branch` section and update the command list table.

## ALGORITHM

```
1. Open docs/cli-reference.md
   a. Add "GitHub Tools" section to Command List
   b. Add gh-tool get-base-branch entry to table
   c. Add full command documentation section
   d. Update "rebasing onto main" text
2. Open docs/configuration/claude-code.md
   a. Find /rebase description
   b. Replace "onto main" with "onto base branch"
3. Open docs/processes-prompts/claude_cheat_sheet.md
   a. Find /rebase description  
   b. Replace "onto main" with "onto base branch"
```

## DATA

### Documentation Changes Summary

| File | Changes |
|------|---------|
| `cli-reference.md` | +1 table row, +1 full section (~40 lines), 1 text fix |
| `claude-code.md` | 1 text replacement |
| `claude_cheat_sheet.md` | 1 text replacement |

## Acceptance Criteria

- [ ] `docs/cli-reference.md` has new `gh-tool get-base-branch` section
- [ ] `docs/cli-reference.md` command list updated
- [ ] `docs/cli-reference.md` "onto main" text fixed
- [ ] `docs/configuration/claude-code.md` `/rebase` description updated
- [ ] `docs/processes-prompts/claude_cheat_sheet.md` `/rebase` description updated
- [ ] All markdown formatting valid
- [ ] No remaining hardcoded "onto main" references in rebase contexts
