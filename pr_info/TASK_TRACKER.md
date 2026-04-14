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

### Step 1: Dependency + subprocess shims ([step_1.md](./steps/step_1.md))
- [x] Implementation: pin `mcp-coder-utils>=0.1.3` in pyproject.toml, replace `subprocess_runner.py` and `subprocess_streaming.py` with re-export shims, delete 3 broken subprocess test files
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `adopt mcp-coder-utils: subprocess shims + delete broken subprocess tests`

### Step 2: log_utils shim ([step_2.md](./steps/step_2.md))
- [x] Implementation: replace `log_utils.py` with re-export shim + wrapped `setup_logging()`, delete 2 broken log test files, create `test_log_utils_shim.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `adopt mcp-coder-utils: log_utils shim + delete broken log tests + add shim test`

### Step 3: stream_subprocess API update ([step_3.md](./steps/step_3.md))
- [x] Implementation: update `claude_code_cli_streaming.py` to use new `stream_subprocess` API — remove manual `StreamResult` wrapper, pass `inactivity_timeout_seconds` as kwarg
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `adopt mcp-coder-utils: adapt claude_code_cli_streaming to new stream_subprocess API`

### Step 4: Import-linter contract updates ([step_4.md](./steps/step_4.md))
- [x] Implementation: add `mcp_coder_utils_isolation` contract, update `subprocess_isolation`, tighten `structlog_isolation` and `jsonlogger_isolation`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `adopt mcp-coder-utils: update import-linter contracts for shim boundary`

### Step 5: Docs + stale import verification ([step_5.md](./steps/step_5.md))
- [x] Implementation: add shared-libraries note to `.claude/CLAUDE.md`, grep for stale imports
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `adopt mcp-coder-utils: add shared-libraries note to CLAUDE.md`

## Pull Request
- [ ] All steps committed and pushed
- [ ] PR review: verify all changes match plan
- [ ] PR summary prepared
