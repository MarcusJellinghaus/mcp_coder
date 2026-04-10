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

### Step 1: `parse_claude_mcp_list()` Parser + `ClaudeMCPStatus` Dataclass

- [x] Implementation: `ClaudeMCPStatus` dataclass, `parse_claude_mcp_list()` function, and tests in `test_mcp_verification.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Wire into RuntimeInfo + iCoder Startup Display + Event Log

- [ ] Implementation: `RuntimeInfo.mcp_connection_status` field, `setup_icoder_environment()` integration, `on_mount()` display, `session_start` event, and tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Verify Command — Claude MCP Section + Provider-Aware Display + Exit Code

- [ ] Implementation: `_format_claude_mcp_section()`, `execute_verify()` provider-aware sections, `_compute_exit_code()` update, and tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
