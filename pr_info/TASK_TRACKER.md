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

### Step 1: TuiPreflightAbort + TuiChecker skeleton + warning checks
- [x] Implementation: TuiPreflightAbort exception, TuiChecker class with run_all_checks() orchestrator, _present_prompt(), four warning checks (SSH/dumb, locale, tmux/screen, macOS Terminal.app), Windows Terminal no-op stub, and all tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Silent fix — Windows CMD codepage auto-fix
- [x] Implementation: _check_windows_cmd_codepage() with ctypes.windll detection, SetConsoleOutputCP(65001) fix, atexit restore, wired into run_all_checks(), and all tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Prompted check — VS Code gpuAcceleration detection
- [x] Implementation: _check_vscode_gpu_acceleration() with platform/SSH/TERM_PROGRAM gates, regex settings.json search, prompt flow, wired into run_all_checks(), and all tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Integration into execute_icoder() + manual test tool
- [x] Implementation: Wire TuiChecker into icoder.py between dir resolution and setup, except TuiPreflightAbort before except Exception, integration tests, and tools/test_scroll.py
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [x] PR review
- [ ] PR summary
