# Issue #776: Fallback to PR closingIssuesReferences when branch has no issue number

## Problem

When a branch doesn't follow the `{issue_number}-{title}` naming convention (e.g. `extract/log-utils`), the `create-pr` workflow cannot detect the linked issue. The PR is correctly linked to the issue by GitHub, but the workflow doesn't query that information — so label updates are silently skipped with a misleading "completed successfully" message.

## Solution

Two changes:

1. **PR→Issue fallback via `closingIssuesReferences`**: After PR creation (step 4), if `cached_issue_number` is still `None`, query the newly created PR's `closingIssuesReferences` field via GraphQL to find the linked issue number. This runs *after* PR creation because the field only exists on an existing PR.

2. **Adjusted completion message**: When the label update was skipped (no issue found), change the final message from "completed successfully" to "completed with warnings".

## Architecture / Design Changes

### Data flow change

**Before:**
```
branch name → extract_issue_number_from_branch() → cached_issue_number → label update
                        ↓ (None if no number prefix)
                   skip label update
```

**After:**
```
branch name → extract_issue_number_from_branch() → cached_issue_number
                        ↓ (None if no number prefix)
              [PR created in step 4]
                        ↓
              PullRequestManager.get_closing_issue_numbers(pr_number) → fallback
                        ↓
              cached_issue_number (updated if fallback found issue) → label update
```

### New method

`PullRequestManager.get_closing_issue_numbers(pr_number: int) -> List[int]` — a GraphQL query on `closingIssuesReferences`, following the same pattern used in `IssueBranchManager.get_linked_branches()`. Placed on `PullRequestManager` because `closingIssuesReferences` is a PR field.

### No new modules or files created

All changes are additions to existing files.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Add `get_closing_issue_numbers()` method |
| `src/mcp_coder/workflows/create_pr/core.py` | Add fallback logic after step 4 + conditional completion message |
| `tests/utils/github_operations/test_pr_manager.py` | Tests for `get_closing_issue_numbers()` |
| `tests/workflows/create_pr/test_workflow.py` | Tests for fallback integration + completion message |

## Constraints (from issue)

- `validate_branch_issue_linkage()` runs *before* PR creation (GitHub removes `linkedBranches` when a PR is created)
- `closingIssuesReferences` fallback runs *after* PR creation (queries the PR)
- Multiple closing issues: warn and use the first one
- Return code stays `0` — PR creation is the core deliverable
- `set-status` failure outside git repo is out of scope (#746)

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `get_closing_issue_numbers()` to `PullRequestManager` with tests | Tests + method |
| 2 | Add fallback logic in workflow + conditional completion message with tests | Tests + workflow changes |
