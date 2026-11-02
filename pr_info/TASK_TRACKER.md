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

### Step 1: Row mapping helper and section wiring
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: `_map_security_row` helper, remove `_derive_code_scanning_alerts`, wire `code_scanning_alerts` in `_print_github_security_section`, update tests and conftest default
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Tests that call the real probe
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: new `tests/cli/commands/test_verify_github_security_probe.py` (code-scanning cases 200/403/404/error, repo-unresolvable case)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Documentation
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: update `docs/repository-setup/github.md` and `docs/repository-setup/quality-and-security-checks.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch
- [ ] PR summary prepared
