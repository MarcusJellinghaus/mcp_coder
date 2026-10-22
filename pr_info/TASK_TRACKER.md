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

### Step 1: Shared ❌ helper `is_marked()` — [step_1.md](./steps/step_1.md)

- [x] Implementation: `TestIsMarked` tests + `is_marked()` in `helpers.py`, used by `_find_marked_comment`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Count only outstanding feedback in `_check_review_comments()` — [step_2.md](./steps/step_2.md)

- [x] Implementation: typed builders + new/converted tests, shim re-exports, `_check_review_comments()` watermark logic for reviews and non-❌ comments
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Triage skill and docs — [step_3.md](./steps/step_3.md)

- [x] Implementation: update `SKILL.md`, `development-process.md`, `coordinator-vscodeclaude.md`, `label-setup.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `summary.md`, address findings
- [ ] PR summary prepared
