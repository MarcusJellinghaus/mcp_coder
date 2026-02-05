# Future Issue: GitHub Issue Creation for Test File Splitting

## Task Completed

Created a comprehensive GitHub issue draft to track the splitting of `test_issue_manager.py` into a modular test structure.

## What Was Done

### 1. Issue Draft Created
**File**: `pr_info/.github_issue_draft.md`

The issue draft includes:
- **Context**: References completion of Issue #306 and the current 2,485-line test file
- **Motivation**: Explains benefits (maintainability, consistency, developer experience, file size policy)
- **Proposed Structure**: Four focused test files:
  - `test_issue_manager_core.py` - CRUD operations
  - `test_issue_manager_comments.py` - Comment operations
  - `test_issue_manager_labels.py` - Label operations
  - `test_issue_manager_events.py` - Event operations
- **Implementation Guidelines**: Clear principles and steps
- **Acceptance Criteria**: Checklist for completion
- **Labels**: Appropriate labels (refactoring, testing, technical-debt)

### 2. Task Tracker Updated
Marked the "Create GitHub issue to track test file splitting" sub-task as complete in `pr_info/TASK_TRACKER.md`.

### 3. Commit Message Prepared
Created commit message in `pr_info/.commit_message.txt` documenting the issue creation work.

## Next Steps

To publish the GitHub issue, run:

```bash
gh issue create \
  --title "Split test_issue_manager.py into Modular Test Structure" \
  --body-file pr_info/.github_issue_draft.md \
  --label "refactoring,testing,technical-debt"
```

## Rationale

This issue creation follows the project's practice of:
1. **Incremental Refactoring**: Large refactoring work is broken into manageable PRs
2. **Clear Documentation**: Each follow-up task is properly documented
3. **Traceability**: Links between related issues (#306 → this new issue)
4. **Community Transparency**: Public issue for tracking and discussion

## Files Created/Modified

- ✅ `pr_info/.github_issue_draft.md` (created)
- ✅ `pr_info/TASK_TRACKER.md` (updated)
- ✅ `pr_info/.commit_message.txt` (created)
- ✅ `pr_info/steps/future_issue_creation.md` (this file)
