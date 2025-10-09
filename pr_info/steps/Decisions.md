# Implementation Decisions

## Discussed and Decided

### 1. Step Structure
**Decision:** Keep Step 1 as separate step for branch name sanitization
**Rationale:** Easier to review, clearer milestone

### 2. Deletion Flow
**Decision:** Keep two-step approach (query for ID, then delete)
**Rationale:** Safer, confirms branch exists before deletion

### 3. BranchCreationResult Type
**Decision:** Keep `existing_branches: List[str]` field in TypedDict
**Rationale:** Caller can show user which branches already exist

### 4. PyGithub Version Constraint
**Decision:** Test with current installed version, document it, add constraint later if needed
**Rationale:** Avoid premature optimization, validate real-world compatibility first

### 5. Branch Name Length Limit
**Decision:** Use 244 characters (GitHub's exact limit)
**Rationale:** GitHub limits refs to 255 bytes total = `refs/heads/` (11 bytes) + branch name (244 bytes)
**Note:** This is BYTES not characters (matters for Unicode)
**Source:** GitHub documentation and Stack Overflow validation

### 6. Multiple Branches Per Issue
**Decision:** Add `allow_multiple: bool = False` parameter to `create_remote_branch_for_issue()`
**Behavior:**
- Default (`False`): Check if issue has ANY linked branches, block creation if found
- When `True`: Skip duplicate check, allow multiple branches per issue
**Rationale:** Default prevents confusion, force flag enables advanced workflows

### 7. Base Branch Resolution
**Decision:** Use `repo.default_branch` from PyGithub when `base_branch` not provided
**Rationale:** Uses GitHub's configured default branch (usually "main" or "master")

### 8. Error Handling Documentation
**Decision:** No separate error scenarios document
**Rationale:** Current test plan covers error cases adequately, trust integration test

### 9. Branch Name Utility Export
**Decision:** Export `generate_branch_name_from_issue()` as public utility
**Rationale:** Others might need consistent branch naming logic

### 10. Type Safety
**Decision:** Add `Literal` type hints for GraphQL operation names
**Example:** `OperationType = Literal["createLinkedBranch", "deleteLinkedBranch"]`
**Rationale:** Stricter typing, catches typos at development time
