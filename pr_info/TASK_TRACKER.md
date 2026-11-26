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

### Step 1: Add `project-config.md`, move prompts docs, fix `config.md`, index and root README
See [step_1.md](./steps/step_1.md)

- [x] Implementation (check #1466 precondition; create `docs/configuration/project-config.md`; move prompts text out of `python.md`; update `config.md`, `docs/README.md`, root `README.md`, prompt links in `cli-reference.md` and `toolkit-interface.md`)
- [x] Quality checks (pytest `tests/docs`, pylint, mypy, anchor search) — fix all issues
- [x] Commit message prepared

### Step 2: Add step-to-request table, fix grant/verify/formatting statements
See [step_2.md](./steps/step_2.md)

- [ ] Implementation (`toolkits.md` step-to-request table, stale rules and npm example; `toolkit-interface.md`; `cli-reference.md` rebase and verify; `architecture.md`)
- [ ] Quality checks (pytest `tests/docs`, pylint, mypy, phrase/anchor search) — fix all issues
- [ ] Commit message prepared

### Step 3: Add Non-Python Repos section, fix `repository-setup/README.md` verify text, final sweep
See [step_3.md](./steps/step_3.md)

- [ ] Implementation (`## Non-Python Repos` section, move adapting-deployed-files heading under it, `mcp-coder.toml` row, Testing Your Setup step 0; final anchor and phrase sweep)
- [ ] Quality checks (full unit pytest, pylint, mypy) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `pr_info/steps/summary.md`
- [ ] PR summary prepared
