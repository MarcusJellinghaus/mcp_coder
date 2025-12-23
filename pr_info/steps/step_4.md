# Step 4: Add Inline Comment Explaining GitHub Behavior

## LLM Prompt

```
Implement Step 4 of Issue #203: Add inline comment explaining GitHub behavior.

Read pr_info/steps/summary.md for context and pr_info/steps/decisions.md for review decisions.
This is a documentation-only change, no tests needed.
```

## Overview

Add an inline comment in `run_create_pr_workflow()` explaining why early branch-issue validation is needed: GitHub removes `linkedBranches` when a PR is created.

## WHERE: File to Modify

1. `src/mcp_coder/workflows/create_pr/core.py` - Add inline comment

## WHAT: Comment to Add

Add a comment block before the `validate_branch_issue_linkage()` call in `run_create_pr_workflow()`.

## HOW: Location

In `run_create_pr_workflow()`, find this code:

```python
    # NEW: Cache branch-issue linkage before PR creation
    cached_issue_number: Optional[int] = None
    if update_labels:
        cached_issue_number = validate_branch_issue_linkage(project_dir)
```

## ALGORITHM: Updated Code

Replace with:

```python
    # Cache branch-issue linkage BEFORE PR creation.
    # GitHub automatically removes linkedBranches when a PR is created from a branch
    # (the link transfers to the PR). If we query linkedBranches after PR creation,
    # it returns empty, causing label updates to fail. By validating early and caching
    # the issue number, we can still update labels after PR creation succeeds.
    cached_issue_number: Optional[int] = None
    if update_labels:
        cached_issue_number = validate_branch_issue_linkage(project_dir)
```

## DATA: No Return Values

This is a documentation-only change.

## Tests

No tests needed - this is a comment addition only.

## Verification

After implementation:
1. Visual review of the comment placement and clarity
2. Run `pytest tests/workflows/create_pr/test_workflow.py -v` to ensure no syntax errors
