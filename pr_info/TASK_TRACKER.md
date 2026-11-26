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

### Step 1: Pass HEAD as `expected_sha` at implement step 5.6 — [step_1.md](./steps/step_1.md)

- [ ] Implementation: import `get_latest_commit_sha` in `core.py`, add autouse `_stub_head_sha` fixture in `tests/workflows/implement/conftest.py`, add parametrized `test_ci_check_receives_head_sha_as_expected_sha` (confirm red), then pass `expected_sha=get_latest_commit_sha(project_dir)` at step 5.6
- [ ] Quality checks: format code, pylint, mypy, fast pytest (`-n auto`) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
