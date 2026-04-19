# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Update settings.local.json permissions
- [x] Implementation: Remove 4 Bash git permissions, add 4 MCP workspace git tool permissions
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Update CLAUDE.md tool mapping and git operations section
- [ ] Implementation: Add git MCP tool rows to tool mapping table, update Bash-allowed commands, replace compact-diff guidance
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Update all skills and rebase design doc
- [ ] Implementation: Update allowed-tools frontmatter and body text in 5 skill/design files
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review completed
- [ ] PR summary prepared
