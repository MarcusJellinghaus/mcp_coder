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

### Step 1: Switch formatter to ruff, update CI / import-linter / comments, reformat
See [step_1.md](./steps/step_1.md)

- [x] Implementation: config, CI, import-linter, gitignore and comment edits; run `run_format_code` over `src`, `tests`, `tools`
- [x] Quality checks: pylint, pytest, mypy (plus format check, ruff check, lint-imports) — fix all issues
- [x] Commit message prepared

### Step 2: Update docs to the ruff toolchain
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: update the five documentation files to describe the ruff toolchain
- [ ] Quality checks: pylint, pytest, mypy (plus format check, `isort|black` search) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`
- [ ] PR summary prepared
