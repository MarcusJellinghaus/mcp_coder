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

### Step 1: Shared TOML plumbing in `mcp_coder.utils` ([step_1.md](./steps/step_1.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy, ruff — fix all issues
- [ ] Commit message prepared

### Step 2: `mcp_coder.install` package + `mcp-coder install` subcommand ([step_2.md](./steps/step_2.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy, ruff, tach, lint-imports, vulture, pycycle — fix all issues
- [ ] Commit message prepared

### Step 3: vscodeclaude switchover — spec field, argv, resolver removal ([step_3.md](./steps/step_3.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy, ruff, tach, lint-imports, vulture — fix all issues
- [ ] Commit message prepared

### Step 4: `validate_target_repo` ([step_4.md](./steps/step_4.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy, ruff — fix all issues
- [ ] Commit message prepared

### Step 5: Delete `tools/install.*`, rewrite `reinstall_local.*`, update CI ([step_5.md](./steps/step_5.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy, ruff, vulture — fix all issues
- [ ] Commit message prepared

### Step 6: Documentation ([step_6.md](./steps/step_6.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy, ruff — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Code review of the full branch diff — fix all findings
- [ ] PR summary prepared
