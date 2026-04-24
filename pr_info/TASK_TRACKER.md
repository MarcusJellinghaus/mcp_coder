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

### Step 1: Add `--push` flag to commit parsers
- [x] Implementation: add `--push` to both parsers + tests in `test_parsers.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(cli): add --push flag to commit auto and clipboard parsers`

### Step 2: Add `_push_after_commit` helper with unit tests
- [ ] Implementation: add helper to `commit.py` + tests in `test_commit.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(cli): add _push_after_commit helper with safety guards`

### Step 3: Wire `--push` into execute functions + integration tests
- [ ] Implementation: add push call to both execute functions + tests in `test_commit.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(cli): integrate --push into commit auto and clipboard`

## Pull Request
- [ ] PR review: verify all steps complete and checks pass
- [ ] PR summary prepared
