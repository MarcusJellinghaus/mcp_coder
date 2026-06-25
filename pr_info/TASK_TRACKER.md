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

### Step 1: Remove the `commit clipboard` command

See [step_1.md](./steps/step_1.md) for details.

- [x] Implementation: remove `commit clipboard` command, code, tests, and docs (keep `utils/clipboard.py`)
- [x] Quality checks: pylint, pytest, mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 2: Migrate icoder to Textual clipboard, delete `clipboard.py`, drop `pyperclip`

See [step_2.md](./steps/step_2.md) for details.

- [x] Implementation: migrate icoder to `copy_to_clipboard`, delete `clipboard.py` + test, drop `pyperclip`/`types-pyperclip` + contract
- [x] Quality checks: pylint, pytest, mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 3: Relocate live helpers (errors.py + fold verify), repoint importers

See [step_3.md](./steps/step_3.md) for details.

- [x] Implementation: create `errors.py`, fold `_verify_claude_before_use`, repoint `ClaudeAPIError` imports, add tests
- [x] Quality checks: pylint, pytest, mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 4: Delete the Claude SDK/API path, formatter chain, and `claude-code-sdk`

See [step_4.md](./steps/step_4.md) for details.

- [x] Implementation: delete SDK/API modules + tests, trim formatters + importing tests, remove `claude-code-sdk` + contract + docs
- [x] Quality checks: pylint, pytest, mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 5: Remove four unused transitive deps + regenerate dependency docs

See [step_5.md](./steps/step_5.md) for details.

- [ ] Implementation: drop `GitPython`/`PyGithub`/`structlog`/`python-json-logger`, prune 2 contracts, update + regenerate dependency docs
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, vulture — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps complete and checks pass
- [ ] PR summary prepared
