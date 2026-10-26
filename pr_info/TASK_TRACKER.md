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

### Step 1: Split `test_issues.py` into eligibility and branch-check siblings — [step_1.md](./steps/step_1.md)

- [ ] Implementation: move eligibility classes → `test_issues_eligibility.py`, `TestBuildEligibleIssuesWithBranchCheck` → `test_issues_branch_check.py` via `move_symbol`, fix imports, drop `.large-files-allowlist` entry
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Move `TestBuildEligibleIssuesPrefetched` to `test_issues_branch_check.py` — [step_2.md](./steps/step_2.md)

- [ ] Implementation: move class from `coordinator/test_core.py` via `move_symbol`, verify method-local imports intact, dedupe destination imports
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch
- [ ] PR summary prepared
