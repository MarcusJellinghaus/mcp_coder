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

### Step 1: Shim `mcp_coder.utils.fs` + import-linter, CLAUDE.md, architecture doc
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [x] Commit message prepared

### Step 2: Rename `write_lf_text` → `write_repo_text` (pure refactor)
See [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [x] Commit message prepared

### Step 3: `write_repo_text` follows the aligned line-ending policy
See [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared

### Step 4: `update_gitignore` writes via `write_repo_text`
See [step_4.md](./steps/step_4.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared

### Step 5: `persist.py` chooses its newline via `dominant_newline`
See [step_5.md](./steps/step_5.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared

### Step 6: `is_outside_project_dir` delegates to `check_path_within`
See [step_6.md](./steps/step_6.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the plan and fix any findings
- [ ] PR summary prepared (include the behaviour changes listed in summary.md)
