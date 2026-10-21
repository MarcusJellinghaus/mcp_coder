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

### Step 1: Shared helper `is_branch_linked_to_issue` + `ClosingPRRef` shim re-export
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `ClosingPRRef` shim re-export, `workflow_utils/branch_linkage.py`, `tests/workflow_utils/test_branch_linkage.py`, architecture doc update
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `update_workflow_label()` uses `is_branch_linked_to_issue`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: re-patch `tests/workflow_utils/test_label_transitions.py`, add closing-PR parametrized test, update `label_transitions.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `validate_branch_issue_linkage()` uses `is_branch_linked_to_issue` (closes #708)
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: update `TestValidateBranchIssueLinkage` tests, change `validate_branch_issue_linkage()` in `create_pr/core.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against `pr_info/steps/summary.md`
- [ ] PR summary prepared
