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

### Step 1: `.mcp.json` — Separate tool env from project env
- [x] Implementation: update `command` fields to use `MCP_CODER_VENV_PATH` and `PYTHONPATH` to use `MCP_CODER_VENV_DIR`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `claude.bat` — Two-env aware launcher for end-users
- [x] Implementation: rewrite with two-env discovery, project env activation, MCP tool verification, and launch
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `claude_local.bat` — Two-env aware launcher for developers
- [ ] Implementation: rewrite with two-env discovery, editable-install check, and launch
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `tools/reinstall.bat` — Restructure with venv guard and non-editable install
- [ ] Implementation: restructure with venv guard, non-editable PyPI install, entry point verification
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: `tools/reinstall_local.bat` — New developer editable install script
- [ ] Implementation: create new script with editable install, GitHub overrides, entry point verification
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
