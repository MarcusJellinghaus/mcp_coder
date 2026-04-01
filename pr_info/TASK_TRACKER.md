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

### Step 1: Update test to expect new config name (TDD red)
- [x] Implementation: rename test function and references in `tests/test_pyproject_config.py` to expect `install-from-github`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `test: expect install-from-github config key (#684)`

### Step 2: Rename from_github → install_from_github across all source and config
- [x] Implementation: rename in `pyproject.toml`, 7 source files, and 14 test files (see [step_2.md](./steps/step_2.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `rename from-github to install-from-github across all layers (#684)`

## Pull Request
- [ ] PR review: verify all changes are consistent and no old references remain
- [ ] PR summary prepared
