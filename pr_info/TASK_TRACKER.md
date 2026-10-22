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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: v1 test — cap CLI MCP wait, raise stub delay, skip on `connected` — [step_1.md](./steps/step_1.md)
- [x] Implementation: set `CLAUDE_CODE_MCP_STARTUP_WAIT_MS=3000`, `_V1_STARTUP_DELAY_SECONDS = 20` with rewritten comment, skip on `connected` before the `pending` assertion; verify via end-to-end `claude_cli_integration` run (v1 and v2 pass)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Stub server docstring — drop "~5 s `alwaysLoad` cap" wording — [step_2.md](./steps/step_2.md)
- [x] Implementation: update `MCP_STUB_STARTUP_DELAY_SECONDS` bullet in `_mcp_stub_server.py` module docstring
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `docs/environments/environments.md` — update `MCP_TIMEOUT` row — [step_3.md](./steps/step_3.md)
- [ ] Implementation: confirm `session_setup.py` sets `MCP_TIMEOUT`, then replace the row (pre-turn wait, `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` override, setter `session_setup.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
