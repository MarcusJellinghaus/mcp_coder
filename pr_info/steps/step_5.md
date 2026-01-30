# Step 5: Update Slash Commands and Documentation

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 5.

Update the slash commands and documentation to explain the base branch feature:
1. Update .claude/commands/issue_analyse.md
2. Update .claude/commands/issue_create.md
3. Update .claude/commands/issue_update.md
4. Update docs/repository-setup.md

Follow the specifications in this step file exactly.
```

---

## Overview

Update slash commands and documentation to guide users on using the base branch feature.

---

## WHERE: File Paths

| File | Action |
|------|--------|
| `.claude/commands/issue_analyse.md` | Add base branch display guidance |
| `.claude/commands/issue_create.md` | Add base branch field documentation |
| `.claude/commands/issue_update.md` | Add base branch editing guidance |
| `docs/repository-setup.md` | Document the feature |

---

## WHAT: Changes to Each File

### 1. `.claude/commands/issue_analyse.md`

Add section to display and validate base branch.

**Current file ends with:**
```markdown
**Focus on:**
- Understanding the problem/feature request
- Technical feasibility
- Potential implementation approaches
- Questions that need clarification
- Impact on existing code
```

**Add after the gh issue view command section:**
```markdown
**Base Branch Handling:**
If the issue contains a `### Base Branch` section:
- Display the specified base branch prominently
- Verify the branch exists using: `git ls-remote --heads origin <branch-name>`
- If the branch does NOT exist, show a clear warning:
  "⚠️ Warning: Base branch 'X' does not exist on remote. Branch creation will fail."
- Continue with the analysis (non-blocking error)
```

### 2. `.claude/commands/issue_create.md`

Add base branch field documentation to the instructions.

**Add after the existing instructions:**
```markdown
**Optional: Base Branch**
If the feature should be based on a branch other than the default (main/master), include:

```markdown
### Base Branch

<branch-name>
```

Use cases:
- Hotfixes based on release branches
- Features building on existing work
- Long-running feature branches

**Important:** Before specifying a base branch, verify it exists:
```bash
git ls-remote --heads origin <branch-name>
```

If no base branch is needed, omit this section entirely.
```

### 3. `.claude/commands/issue_update.md`

Add guidance for editing base branch section.

**Add to the instructions:**
```markdown
**Editing Base Branch:**
- To add a base branch: Insert `### Base Branch` section with the branch name
- To change a base branch: Update the content under the existing section
- To remove a base branch: Delete the entire `### Base Branch` section

The base branch must be a single line. Multiple lines will cause an error during branch creation.
```

### 4. `docs/repository-setup.md`

Add new section documenting the feature.

**Add new section after "## Workflow Labels Setup" (or appropriate location):**

```markdown
## Base Branch Support for Issues

### Overview

Issues can specify a base branch to start work from a branch other than the repository default. This is useful for:
- **Hotfixes**: Starting from a release branch
- **Feature chains**: Building on existing feature work
- **Release preparation**: Working from release branches

### Issue Body Format

Add a `### Base Branch` section to your issue body:

```markdown
### Base Branch

feature/existing-work

### Description

The actual issue content...
```

### Parsing Rules

- **Case-insensitive**: `Base Branch`, `base branch`, `BASE BRANCH` all work
- **Any heading level**: `#`, `##`, `###` all work
- **Single line only**: Multiple lines will cause an error
- **Whitespace trimmed**: Leading/trailing whitespace is ignored
- **Empty = default**: If section is empty or missing, uses repository default branch

### Validation

The base branch is validated at branch creation time:
- If the branch doesn't exist, branch creation fails with a clear error
- The `/issue_analyse` command will warn if the specified branch doesn't exist

### Backward Compatibility

Existing issues without a `### Base Branch` section continue to work as before, using the repository's default branch (typically `main` or `master`).

### Example Issues

**Issue with base branch:**
```markdown
### Base Branch

release/2.0

### Description

Fix critical bug in release 2.0

### Acceptance Criteria

- Bug is fixed
- Tests pass
```

**Issue without base branch (uses default):**
```markdown
### Description

Add new feature to main branch

### Acceptance Criteria

- Feature works
- Tests pass
```
```

---

## ALGORITHM: N/A

This step involves documentation changes only, no code logic.

---

## DATA: N/A

No data structures involved, documentation only.

---

## Verification

After implementation:

1. **Verify markdown syntax** is valid in all files
2. **Check links** work in documentation
3. **Test slash commands** manually:
   - Create a test issue with `### Base Branch` section
   - Run `/issue_analyse` on it
   - Verify the base branch is displayed
   - If branch doesn't exist, verify warning is shown

---

## Full File Contents (For Reference)

### `.claude/commands/issue_analyse.md` (Updated)

```markdown
---
workflow-stage: issue-discussion
suggested-next: discuss -> issue_update -> issue_approve
---

# Analyse GitHub Issue

Fetch a GitHub issue and analyze its requirements, feasibility, and potential implementation approaches.

## Instructions

First, fetch the issue details:
```bash
gh issue view $ARGUMENTS
```

Then analyze the issue:

Can we discuss this requirement / implementation idea and its feasibility?
Please also look at the code base to understand the context (using the different tools with access to the project directory).
Do not provide code yet!

At the end of our discussion, I want to have an even better issue description.

**Base Branch Handling:**
If the issue contains a `### Base Branch` section:
- Display the specified base branch prominently
- Verify the branch exists using: `git ls-remote --heads origin <branch-name>`
- If the branch does NOT exist, show a clear warning:
  "⚠️ Warning: Base branch 'X' does not exist on remote. Branch creation will fail."
- Continue with the analysis (non-blocking error)

**Focus on:**
- Understanding the problem/feature request
- Technical feasibility
- Potential implementation approaches
- Questions that need clarification
- Impact on existing code
```

### `.claude/commands/issue_create.md` (Updated)

```markdown
---
allowed-tools: Bash(gh issue create:*)
workflow-stage: issue-discussion
suggested-next: discuss -> issue_update -> issue_approve
---

# Create GitHub Issue

Based on our prior discussion, create a GitHub issue.

**Instructions:**
1. Extract the issue title and body from the conversation context
2. Use a clear, descriptive title
3. Include relevant details from our discussion in the body
4. Use markdown formatting for better readability

**Optional: Base Branch**
If the feature should be based on a branch other than the default (main/master), include:

```markdown
### Base Branch

<branch-name>
```

Use cases:
- Hotfixes based on release branches
- Features building on existing work
- Long-running feature branches

**Important:** Before specifying a base branch, verify it exists:
```bash
git ls-remote --heads origin <branch-name>
```

If no base branch is needed, omit this section entirely.

**Create the issue using:**
```bash
gh issue create --title "TITLE" --body "BODY"
```

If no prior discussion context is found, respond: "No discussion context found. Please discuss the feature or bug first before creating an issue."
```

### `.claude/commands/issue_update.md` (Updated)

```markdown
---
allowed-tools: Bash(gh issue edit:*), Bash(gh issue view:*), Read, Glob, Grep
workflow-stage: issue-discussion
suggested-next: issue_approve
---

# Update GitHub Issue

Based on our prior `/issue_analyse` discussion, update the GitHub issue with refined content.

**Instructions:**
1. If no issue context is found from prior analysis, respond: "No issue context found. Please run `/issue_analyse <number>` first."

2. First, fetch the current issue content:
```bash
gh issue view <issue_number> --json title,body
```

3. Draft updated issue text with:
   - Clear, concise title
   - Well-structured body with implementation ideas
   - Preserve the original issue content at the bottom under:
     `# Original issue: [old title]\n[old body]`

4. Update the issue:
```bash
gh issue edit <issue_number> --title "NEW_TITLE" --body "NEW_BODY"
```

**Editing Base Branch:**
- To add a base branch: Insert `### Base Branch` section with the branch name
- To change a base branch: Update the content under the existing section
- To remove a base branch: Delete the entire `### Base Branch` section

The base branch must be a single line. Multiple lines will cause an error during branch creation.

**The updated issue should include:**
- Summary of the requirement
- Discussed implementation approach (concise)
- Any constraints or considerations identified
- Original issue content preserved
```
