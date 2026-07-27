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

### Step 1: Create the pure `_depcheck` module (TDD)

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: create `tests/test_depcheck.py` (7 cases) and `src/mcp_coder/_depcheck.py` (`find_missing_dependencies`, `ensure_dependencies`, `_installed_version`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Wire the guard into `__init__.py` (fail-open)

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation: add 4-line fail-open guard to `src/mcp_coder/__init__.py` + smoke test and fail-open regression test
- [x] Quality checks: pylint, pytest, mypy, lint-imports — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] Code review of the full branch and address findings
- [ ] PR summary prepared
