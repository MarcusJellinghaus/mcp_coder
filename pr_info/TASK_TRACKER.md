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

- [x] Implement test `test_update_workflow_label_removes_different_workflow_label` in `tests/utils/github_operations/test_issue_manager_label_update.py`
- [x] Run quality checks (pylint)
- [x] Run quality checks (pytest) - expect new test to FAIL (TDD approach)
- [x] Run quality checks (mypy)
- [x] Prepare git commit message for Step 1

**Commit Message (Step 1):**
```
test(issue-manager): Add test for removing all workflow labels during transition

Add test_update_workflow_label_removes_different_workflow_label to verify
that update_workflow_label removes ALL workflow labels (not just the source
label) when transitioning to a new workflow state. This test will fail until
the fix is implemented in Step 2 (TDD approach).

Related to: #193
```

### Step 2: Fix update_workflow_label Logic

- [x] Add INFO log in `src/mcp_coder/utils/github_operations/issue_manager.py` for missing source label case
- [x] Fix label removal logic to remove ALL workflow labels (change line ~372)
- [x] Run quality checks (pylint)
- [x] Run quality checks (pytest) - all tests should PASS
- [x] Run quality checks (mypy)
- [x] Prepare git commit message for Step 2

**Commit Message (Step 2):**
```
fix(issue-manager): remove ALL workflow labels during transition

- Add INFO log when source label is missing during workflow transition
- Fix update_workflow_label to remove ALL workflow labels before adding
  the target label, not just the source label. This ensures clean workflow
  state transitions even when labels were manually modified.

Fixes: #193
```

---

## Pull Request

- [x] Review all changes for Issue #193
- [x] Prepare PR summary describing the fix for update_workflow_label

**PR Summary:**
```
## Summary

Fix bug in `update_workflow_label` where transitioning workflow states didn't
remove ALL existing workflow labels - only the specified source label.

### Problem
When an issue had workflow label "planning" but the transition was from
"implementing" to "code_review", the "planning" label was NOT removed.
This left issues in an inconsistent state with multiple workflow labels.

### Solution
Changed the label removal logic (line ~372 in issue_manager.py) to remove
ALL workflow labels before adding the target label:

```python
# Before (bug):
new_labels = (current_labels - {from_label_name}) | {to_label_name}

# After (fix):
new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}
```

### Changes
- Add test `test_update_workflow_label_removes_different_workflow_label`
- Add INFO log when source label is missing during transition
- Fix label removal to remove ALL workflow labels

Fixes: #193
```
