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

### Step 1: Register `require_pull_request` and show error notes on unverifiable protection rows
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: tests in `test_verify_format_section_basic.py` (cases 1–8) + `_LABEL_MAP`, `_BRANCH_PROTECTION_CHILDREN` and error-display conditions in `verify_formatting.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Document ruleset-aware branch protection checks
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: reword "not verifiable" note and add bypass-actors sentence in `docs/repository-setup/github.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against `pr_info/steps/summary.md` and `Decisions.md`
- [ ] PR summary prepared
