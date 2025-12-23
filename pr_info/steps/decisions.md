# Code Review Decisions

This document captures decisions made during the code review discussion for Issue #203.

## Review Date: 2025-12-23

## Decisions

### Topic 1: Code Duplication in Branch-Issue Extraction Logic

**Issue**: The regex pattern `r"^(\d+)-"` for extracting issue numbers from branch names is duplicated in:
- `issue_manager.py` → `update_workflow_label()`
- `core.py` → `validate_branch_issue_linkage()`

**Options Considered**:
- A) Keep as-is
- B) Extract to `git_operations/branches.py`
- C) Extract to `github_operations/github_utils.py`

**Decision**: **B** — Extract to `git_operations/branches.py`

**Rationale**: Follows DRY principle and the architecture's modular pattern for git operations.

---

### Topic 2: Logging Level Consistency

**Issue**: `validate_branch_issue_linkage()` uses `logger.warning()` for "branch not linked" case. This is an expected validation outcome, not an error.

**Options Considered**:
- A) Keep as `warning`
- B) Change to `info`
- C) Change to `debug`

**Decision**: **A** — Keep as `warning`

**Rationale**: Useful visibility that label updates will be skipped. Operators should know when this happens.

---

### Topic 3: Add Error Handling Test for `validate_branch_issue_linkage`

**Issue**: The exception handling path in `validate_branch_issue_linkage()` is untested.

**Options Considered**:
- A) Add a test for exception handling
- B) Skip this test

**Decision**: **B** — Skip this test

**Rationale**: The exception handling is simple (log + return None), and testing it adds little value. The pattern is well-established in the codebase.

---

### Topic 4: Documentation About GitHub Behavior

**Issue**: The code works around GitHub's behavior of removing `linkedBranches` when a PR is created. This context is not documented in the source code.

**Options Considered**:
- A) Add module-level docstring note
- B) Add inline comment near validation call
- C) Both A and B
- D) Skip

**Decision**: **B** — Add inline comment near the validation call

**Rationale**: Targeted documentation where it's most relevant, without over-documenting.
