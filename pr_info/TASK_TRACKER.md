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

### Step 1: Add `--list-mcp-tools` flag to verify parser
- [x] Implementation: tests (`test_verify_parser.py`) + production code (`parsers.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `Add --list-mcp-tools flag to verify parser (#639)`

### Step 2: Return tool descriptions from `_check_servers()`
- [ ] Implementation: tests (`test_mcp_health_check.py`) + production code (`verification.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `Include tool descriptions in MCP server health check (#639)`

### Step 3: Render detailed MCP tool listing + orchestrator passthrough
- [ ] Implementation: tests (`test_verify_format_section.py`, `test_verify_orchestration.py`) + production code (`verify.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `Render detailed MCP tool listing with --list-mcp-tools flag (#639)`

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
