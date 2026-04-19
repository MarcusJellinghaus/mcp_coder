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

### Step 1: Remove error swallowing from `PullRequestManager.create_pull_request()`
- [x] Implementation: remove decorator + exception catch, convert `return {}` to `raise ValueError`, update tests in `test_pr_manager.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Change `core.py` wrapper to return `(result, error_msg)` tuple
- [ ] Implementation: change return type to `tuple[PullRequestData | None, str | None]`, update `test_repository.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Wire error message through Step 5 + update workflow/failure tests
- [ ] Implementation: unpack tuple in `run_create_pr_workflow()` step 5, update `test_workflow.py` and `test_failure_handling.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review completed
- [ ] PR summary prepared
