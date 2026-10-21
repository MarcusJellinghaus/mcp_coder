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

### Step 1: Move `git_repo` fixture to root conftest — [step_1.md](./steps/step_1.md)

- [x] Implementation: move `git_repo` + `setup_git_config` to `tests/conftest.py`, `git_repo_with_files` builds on `git_repo`, delete the two `tests.utils.conftest` imports and their `.importlinter` ignores
- [x] Quality checks: pylint, pytest (unit + `git_integration`), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 2: Remove unused imports in tests — [step_2.md](./steps/step_2.md)

- [ ] Implementation: hand edits A1–A3 (smoke-test asserts, `try/except ImportError` sites, `F811` re-imports), then `ruff --fix` `F401` sweep on `tests` and review of removed imports
- [ ] Quality checks: pylint, pytest (unit + `git_integration`, mlflow file once), mypy, ruff `F401`/`F811` on `tests` — fix all issues
- [ ] Commit message prepared

### Step 3: Enable ruff `F` and clean `src` — [step_3.md](./steps/step_3.md)

- [ ] Implementation: add `"F"` to ruff `select`, update `pyproject.toml` comments, delete 4 dead `src` imports, rewrite 5 optional-dependency checks as `import x` + `del x`
- [ ] Quality checks: pylint, pytest (unit + `git_integration`), mypy, ruff, lint-imports — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify acceptance criteria in step_3.md (ruff clean, no `noqa: F401/F811`, no `tests.utils.conftest` in `.importlinter`, shim `__all__` intact)
- [ ] PR summary prepared
