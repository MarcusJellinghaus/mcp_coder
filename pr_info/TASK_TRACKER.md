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

### Step 1: Add `prepare_env` helper + `env_remove` on `CommandOptions`
- [x] Implementation: tests + production code ([step_1.md](./steps/step_1.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Refactor `_run_subprocess` + `stream_subprocess` to use `prepare_env`; update Claude CLI callers
- [x] Implementation: tests + production code ([step_2.md](./steps/step_2.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Fix `launch_process()` env inheritance
- [ ] Implementation: tests + production code ([step_3.md](./steps/step_3.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Merge utility functions from p_tools reference
- [ ] Implementation: tests + production code ([step_4.md](./steps/step_4.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps complete and checks pass
- [ ] PR summary prepared
