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

### Step 1: Split `TestSessionRestart` into four classes — [step_1.md](./steps/step_1.md)
- [x] Implementation: record collect-only baselines, insert the four class headers, gates pass (16 passed, split 3/1/5/7)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move `TestPrepareAndLaunchSession` to `test_session_launch_prepare.py` — [step_2.md](./steps/step_2.md)
- [ ] Implementation: `move_symbol` (dry run first), fix imports, gates pass (3 passed / 13 passed, directory baseline)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Move `TestProcessEligibleIssuesMaxSessions` to `test_session_launch_process_issues.py` — [step_3.md](./steps/step_3.md)
- [ ] Implementation: `move_symbol` (dry run first), destination imports unchanged, gates pass (7 passed / 12 passed, directory baseline)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Move `TestRestartClosedSessionsLifecycle` to `test_session_restart_lifecycle.py` — [step_4.md](./steps/step_4.md)
- [ ] Implementation: `move_symbol` (dry run first), bare `_make_assessment(` calls, `import logging` stays in zombie test, gates pass (5 passed / 7 passed, directory baseline)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Move `TestRestartClosedSessionsIssueStatus` and `_make_assessment`, delete `test_session_restart.py`, update allowlist — [step_5.md](./steps/step_5.md)
- [ ] Implementation: move class, move helper to `conftest.py`, fix imports, pre-delete checks, delete file, remove allowlist line, final verification (22 passed, lint-imports, tach, vulture, file size, branch compact diff)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: compact diff of the whole branch against the base branch shows only moved blocks, import changes, four class headers, deleted file and allowlist line
- [ ] PR summary prepared
