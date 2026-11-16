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

### Step 1: `tools/check_sensitive_files.py` with unit tests — [step_1.md](./steps/step_1.md)

- [ ] Implementation: `tests/tools/test_check_sensitive_files.py` (TDD) and `tools/check_sensitive_files.py`
- [ ] Quality checks (ruff, pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 2: `check-sensitive-files` job in `ci.yml` — [step_2.md](./steps/step_2.md)

- [ ] Implementation: add PR-only advisory job after `check-forbidden-folders` in `.github/workflows/ci.yml`
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 3: Docs for `check-sensitive-files` — [step_3.md](./steps/step_3.md)

- [ ] Implementation: update `quality-and-security-checks.md` and `claude-permissions/design-concept.md`
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against `pr_info/steps/summary.md`
- [ ] PR summary prepared
