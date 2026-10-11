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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: Closing-reference helper — [step_1.md](./steps/step_1.md)

- [x] Implementation: `ensure_closing_reference` in `helpers.py`, re-export from `core.py`, tests in `test_parsing.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Always resolve the issue number and inject the closing reference — [step_2.md](./steps/step_2.md)

- [x] Implementation: remove `update_issue_labels` gate and inject closing reference in `run_create_pr_workflow`; new `conftest.py`, tests in `test_workflow.py`, patches in `test_create_pr_integration.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`
- [ ] PR summary prepared
