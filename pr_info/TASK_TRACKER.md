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

### Step 1: New `CIStatus.UNAVAILABLE` state + presentation (data layer)

See [step_1.md](./steps/step_1.md).

- [ ] Implementation: add `CIStatus.UNAVAILABLE`, `GITHUB_TOKEN_HINT` constant, 🔒 icon-map entry, inline hint in `format_for_human`/`format_for_llm`, and `UNAVAILABLE` recommendation branch — with tests first (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Detection — shim re-export + `_collect_ci_status` early-return

See [step_2.md](./steps/step_2.md).

- [ ] Implementation: re-export `get_github_token` in the shim (bump `__all__` 24→25), add token early-return in `_collect_ci_status`, repair the three direct `_collect_ci_status` tests — with tests first (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: CLI integration — guard `--wait-for-pr`, gate `--ci-timeout` wait, consistent exit code `2`

See [step_3.md](./steps/step_3.md).

- [ ] Implementation: import `get_github_token`/`GITHUB_TOKEN_HINT`, guard `--wait-for-pr` path, gate the CI-wait block, hoist `UNAVAILABLE → return 2` above `--fix`, repair existing wait/PR + CI-timeout tests — with tests first (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
