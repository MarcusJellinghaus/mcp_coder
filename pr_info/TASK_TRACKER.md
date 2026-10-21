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

### Step 1: Relocate the existing PR-health tests (pure move)
See [step_1.md](./steps/step_1.md)

- [x] Implementation: move PR-health tests into `test_checks.py` / `test_checks_review_comments.py`, trim `test_session_launch_process_issues.py`, delete `test_session_launch_review_comments.py`, update `.large-files-allowlist`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `check_pr_health` with a shared branch/PR lookup
See [step_2.md](./steps/step_2.md)

- [x] Implementation: tests first, then `checks.py` helpers + `check_pr_health`, export in `__init__.py`, interim call from `process_eligible_issues`, interim `check_pr_health` patch in remaining session-launch tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Call `check_pr_health` from the CLI Step 4 loop, outside the capacity gate
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: tests first (`test_vscodeclaude_pr_health.py`, CLI autouse fixture), move call to `commands_vscodeclaude.py`, remove interim call/imports from `session_launch.py` and related test patches
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Remove the session-limit caveat from the docs
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: edit `docs/coordinator-vscodeclaude.md` and `docs/processes-prompts/development-process.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
