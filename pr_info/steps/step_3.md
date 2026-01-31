# Step 3: Update Slash Commands for Dynamic Base Branch

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Update the slash commands to use dynamic base branch detection via the new CLI command.
Replace hardcoded 'main' references with the output of `mcp-coder gh-tool get-base-branch`.
```

## WHERE

- **Modify**: `.claude/commands/implementation_review.md`
- **Modify**: `.claude/commands/rebase.md`
- **Modify**: `.claude/commands/check_branch_status.md`

## WHAT

### 1. `implementation_review.md`

**Current** (hardcoded):
```markdown
git diff --unified=5 --no-prefix main...HEAD -- . ":(exclude)pr_info/.conversations/**"
```

**New** (dynamic):
```markdown
**First, determine the base branch:**
```bash
BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
```

Run this command to get the changes to review:
```bash
git diff --unified=5 --no-prefix ${BASE_BRANCH}...HEAD -- . ":(exclude)pr_info/.conversations/**"
```
```

### 2. `rebase.md`

**Current** (hardcoded):
```markdown
# Rebase Branch onto Main

Rebase the current feature branch onto `origin/main`...

2. `git rebase origin/main`
```

**New** (dynamic):
```markdown
# Rebase Branch onto Base Branch

Rebase the current feature branch onto its base branch.

## Determine Base Branch

First, detect the correct base branch:
```bash
BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
echo "Rebasing onto: $BASE_BRANCH"
```

## Workflow

1. `git fetch origin`
2. `git rebase origin/${BASE_BRANCH}`
...
```

### 3. `check_branch_status.md`

**Current**:
```markdown
| Rebase needed | Run `/rebase` to rebase onto main with conflict resolution |
```

**New**:
```markdown
| Rebase needed | Run `/rebase` to rebase onto base branch with conflict resolution |
```

## HOW

### Edit Pattern for Each File

Use precise string replacement to update only the affected sections:

1. **implementation_review.md**: Insert base branch detection before the diff command
2. **rebase.md**: 
   - Update title: "Main" → "Base Branch"
   - Add base branch detection section
   - Update rebase command to use variable
3. **check_branch_status.md**: Simple text replacement "onto main" → "onto base branch"

## ALGORITHM

```
For each slash command file:
1. Read current content
2. Identify hardcoded 'main' references
3. Replace with dynamic base branch pattern:
   - Add BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
   - Use ${BASE_BRANCH} in git commands
4. Update descriptive text ("onto main" → "onto base branch")
5. Verify markdown formatting is preserved
```

## DATA

### Changes Summary

| File | Change Type | Lines Changed |
|------|-------------|---------------|
| `implementation_review.md` | Add detection + update command | +4 lines |
| `rebase.md` | Add section + update commands | +8 lines |
| `check_branch_status.md` | Text only | 1 line |

### New Bash Pattern

```bash
# Standard pattern for slash commands
BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
# Use with: git diff ${BASE_BRANCH}...HEAD
# Use with: git rebase origin/${BASE_BRANCH}
```

## Acceptance Criteria

- [ ] `implementation_review.md` uses dynamic base branch for diff
- [ ] `rebase.md` uses dynamic base branch for rebase
- [ ] `check_branch_status.md` text updated (no hardcoded "main")
- [ ] All markdown formatting preserved
- [ ] Commands remain functional with same allowed-tools
