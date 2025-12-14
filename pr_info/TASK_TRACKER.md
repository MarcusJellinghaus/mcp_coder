# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Add Tests for Workflow Label Removal

- [ ] Implement test `test_update_workflow_label_removes_different_workflow_label` in `tests/utils/github_operations/test_issue_manager_label_update.py`
- [ ] Run quality checks (pylint)
- [ ] Run quality checks (pytest) - expect new test to FAIL (TDD approach)
- [ ] Run quality checks (mypy)
- [ ] Prepare git commit message for Step 1

### Step 2: Fix update_workflow_label Logic

- [ ] Add INFO log in `src/mcp_coder/utils/github_operations/issue_manager.py` for missing source label case
- [ ] Fix label removal logic to remove ALL workflow labels (change line ~372)
- [ ] Run quality checks (pylint)
- [ ] Run quality checks (pytest) - all tests should PASS
- [ ] Run quality checks (mypy)
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all changes for Issue #193
- [ ] Prepare PR summary describing the fix for update_workflow_label
