# Issue #203: Cache Branch-Issue Linkage Before PR Creation

## Problem Statement

The `--update-labels` flag in the `create-pr` command intermittently fails with:
```
Branch '24-work-on-pytest-warnings' is not linked to issue #24. Linked branches: []
```

**Root Cause**: GitHub automatically removes the `linkedBranches` association when a PR is created from that branch. The link transfers from branch → PR.

**Current Workflow Order** in `run_create_pr_workflow()`:
1. Check prerequisites
2. Generate PR summary
3. Push commits
4. **Create pull request** ← GitHub removes `linkedBranches` here
5. Cleanup repository
6. **Update labels** ← Queries `linkedBranches` which is now empty!

## Solution: Cache Validated Issue Number Early

### Design Decision

Add a `validated_issue_number` parameter to `update_workflow_label()` that allows passing a pre-validated issue number, skipping the branch linkage validation.

**Why this approach?**
- **KISS**: Single new optional parameter instead of complex caching mechanism
- **Self-documenting**: `validated_issue_number=24` clearly indicates pre-validation occurred
- **Backward compatible**: Parameter is optional, existing code works unchanged
- **Minimal changes**: Only 2 files need modification

### Architectural Changes

```
BEFORE:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ create_pull_    │────►│ GitHub removes   │────►│ update_workflow │
│ request()       │     │ linkedBranches   │     │ _label() FAILS  │
└─────────────────┘     └──────────────────┘     └─────────────────┘

AFTER:
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ validate_branch │────►│ create_pull_    │────►│ update_workflow  │
│ _issue_linkage()│     │ request()       │     │ _label() SUCCESS │
│ Returns: 24     │     │                 │     │ (uses cached 24) │
└─────────────────┘     └─────────────────┘     └──────────────────┘
```

### Data Flow

1. **Early validation** (before PR creation):
   - Extract issue number from branch name
   - Query `get_linked_branches()` via GitHub API
   - Cache issue number if branch is linked

2. **Label update** (after PR creation):
   - Pass cached `validated_issue_number` to `update_workflow_label()`
   - Method skips branch validation, uses provided issue number directly

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/utils/github_operations/issue_manager.py` | MODIFY | Add `validated_issue_number` parameter to `update_workflow_label()` |
| `src/mcp_coder/workflows/create_pr/core.py` | MODIFY | Add `validate_branch_issue_linkage()` helper; use it in workflow |
| `src/mcp_coder/utils/git_operations/branches.py` | MODIFY | Add `extract_issue_number_from_branch()` utility function |
| `tests/utils/github_operations/test_issue_manager_label_update.py` | MODIFY | Add tests for `validated_issue_number` parameter |
| `tests/workflows/create_pr/test_workflow.py` | MODIFY | Add tests for early validation in workflow |
| `tests/utils/git_operations/test_branches.py` | MODIFY | Add tests for new utility function |

## Acceptance Criteria

| Criteria | How Verified |
|----------|--------------|
| Label update succeeds when branch was created via GitHub UI | Early validation caches issue number before PR creation |
| Label update succeeds when branch was created via `IssueBranchManager` | Same mechanism |
| Label update still fails when branch has no association | Early validation returns `None`, label update skipped with warning |
| Existing tests pass | `validated_issue_number` is optional, backward compatible |
| Add test case for race condition scenario | New test simulates empty `linkedBranches` after PR creation |
| No code duplication | Shared `extract_issue_number_from_branch()` function |
| Clear documentation | Inline comment explains GitHub behavior |

## Implementation Steps

- **Step 1**: Add `validated_issue_number` parameter to `update_workflow_label()` with tests
- **Step 2**: Add `validate_branch_issue_linkage()` helper to workflow with tests; integrate into `run_create_pr_workflow()`
- **Step 3**: Extract `extract_issue_number_from_branch()` utility function to reduce code duplication (from code review)
- **Step 4**: Add inline comment explaining GitHub behavior (from code review)

## Code Review Decisions

See [decisions.md](./decisions.md) for detailed discussion and rationale for additional implementation steps.
