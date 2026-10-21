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

### Step 1: Import walker, classification tests, import-health test
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `tests/_import_walker.py` + `tests/test_module_imports.py` (classification tests, SystemExit walker test, subprocess import-health test)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Run the import-health test against upstream main in CI
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: update `.github/workflows/upstream-mypy-check.yml` (rename job, install extras, independent mypy + strict import-test steps)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`
- [ ] PR summary prepared
