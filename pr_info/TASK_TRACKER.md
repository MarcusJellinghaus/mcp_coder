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

### Step 1: Test fixture cleanup — decouple from real tool names
- [x] Implementation: replace real tool names with fictional names in test fixtures (`test_ci_log_parser.py`, `test_branch_status.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2A: Config — update settings.local.json with MCP permissions
- [x] Implementation: add 4 MCP permissions, remove 3 Bash permissions in `settings.local.json`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2B: Config — update CLAUDE.md with MCP tool references
- [x] Implementation: update tool mapping table, git operations section, and quick examples in `CLAUDE.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3A: Skills — replace format_all.sh with MCP tool in commit_push
- [x] Implementation: swap allowed-tools entries and update step 1 in `commit_push/SKILL.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3B: Skills — replace format_all.sh with MCP tool in implement_direct
- [x] Implementation: add MCP tool to allowed-tools and update step 6 in `implement_direct/SKILL.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3C: Skills — replace format_all.sh with MCP tool in rebase
- [x] Implementation: swap allowed-tools entries in `rebase/SKILL.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4A: Docs — audience-split updates in repository-setup.md
- [x] Implementation: add MCP tool notes after formatting tools table and architecture tools examples
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4B: Docs — update settings example in claude-code.md
- [x] Implementation: replace format_all.sh in settings example with MCP tools, update security note
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4C: Docs — add MCP alternatives in refactoring-guide.md
- [x] Implementation: add MCP alternatives in standard checks section
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4D: Docs — add MCP column in dependencies/readme.md
- [ ] Implementation: add MCP Tool column to tools table, add Claude Code alternative block
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps complete and checks pass
- [ ] PR summary prepared
