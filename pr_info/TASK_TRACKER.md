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

### Step 1: Replace the `branch_status` fork with a shim; delete dead code

See [step_1.md](./steps/step_1.md).

- [x] Implementation: rewrite `checks/branch_status.py` as a shim; delete `ci_log_parser.py`, `test_ci_log_parser.py`, `test_branch_status_pr_fields.py`; recreate small `test_branch_status.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: CLI — `--fail-on-reviews` flag + pure exit-code contract

See [step_2.md](./steps/step_2.md).

- [x] Implementation: add `--fail-on-reviews` flag, `_exit_code` helper (2→1→0), drop `replace()` enrichment, pass `fail_on_reviews` to formatters, update docs + docstring
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Review workflow reads PR review feedback (implementation lane only)

See [step_3.md](./steps/step_3.md).

- [ ] Implementation: add `thread_pr_feedback` flag on `ReviewConfig`, `pr_note` kwarg on `_run_reviewer`, `_pr_feedback_note` helper, per-round `collect_branch_status` threading into reviewer + supervisor
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review feedback addressed
- [ ] PR summary prepared
