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

### Step 1: Enable ruff `PLE2502` (covers bandit `B613`) — [step_1.md](./steps/step_1.md)

- [x] Implementation: add `"PLE2502"` with comment to `[tool.ruff.lint] select` in `pyproject.toml`; ruff check on `src tests tools` reports 0 hits
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Format `tools/` in CI, drop local formatter scripts — [step_2.md](./steps/step_2.md)

- [x] Implementation: extend CI black/isort jobs to `tools`; delete `tools/format_all.bat`, `tools/format_all.sh`, `tools/black.bat`, `tools/iSort.bat`; update `python.md`, `README.md`, `development-process.md`; no remaining references outside `pr_info/`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review all changes on the branch
- [ ] PR summary prepared
