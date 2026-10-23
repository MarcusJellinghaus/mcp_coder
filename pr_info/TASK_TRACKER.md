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

### Step 1: fix-conflict sets the final label on every handled outcome — [step_1.md](./steps/step_1.md)

- [x] Implementation: extend `_patch_all`, parametrized status-74/status-10 tests, `_fail` helper and verdict branching in `core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Docs — describe the fix-conflict outcomes — [step_2.md](./steps/step_2.md)

- [ ] Implementation: update `docs/cli-reference.md`, `docs/processes-prompts/development-process.md`, `docs/getting-started/label-setup.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`
- [ ] PR summary prepared
