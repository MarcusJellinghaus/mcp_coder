# Step 4: Code Quality Verification and Final Testing

## Objective
Run all code quality checks (pylint, pytest, mypy) to ensure the implementation meets project standards, fix any issues, and verify no regressions.

---

## WHERE: Quality Checks Run From
**Project root:**
```
C:\Jenkins\environments\mcp-coder-dev
```

**Files to verify:**
- `src/mcp_coder/utils/github_operations/issues/branch_manager.py`
- `src/mcp_coder/cli/commands/coordinator/core.py`
- `tests/utils/github_operations/issues/test_branch_resolution.py`

---

## WHAT: Quality Checks to Run

### 1. pytest - All Tests
**Purpose:** Verify new tests pass and no regressions in existing tests

**Command:**
```bash
pytest tests/utils/github_operations/issues/test_branch_resolution.py -v
```

**Expected Output:**
```
test_branch_resolution.py::TestGetBranchWithPRFallback::test_linked_branch_found_returns_branch_name PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_no_linked_branch_single_draft_pr_returns_branch PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_no_linked_branch_single_open_pr_returns_branch PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_no_linked_branch_multiple_prs_returns_none PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_no_linked_branch_no_prs_returns_none PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_invalid_issue_number_returns_none PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_graphql_error_returns_none PASSED
test_branch_resolution.py::TestGetBranchWithPRFallback::test_repository_not_found_returns_none PASSED

========== 8 passed in X.XXs ==========
```

### 2. pytest - Existing Tests (No Regressions)
**Purpose:** Ensure existing tests still pass

**Command:**
```bash
# Run all github_operations tests
pytest tests/utils/github_operations/ -v -m "not github_integration"

# Run coordinator tests
pytest tests/cli/commands/coordinator/ -v -m "not github_integration"
```

**Expected:** All existing tests pass, no failures

### 3. mypy - Type Checking
**Purpose:** Verify type annotations are correct

**Command:**
```bash
mypy src/mcp_coder/utils/github_operations/issues/branch_manager.py
mypy src/mcp_coder/cli/commands/coordinator/core.py
```

**Expected Output:**
```
Success: no issues found in X source files
```

**Common Issues to Fix:**
- Missing type annotations
- Incorrect return types
- Untyped function parameters

### 4. pylint - Code Quality
**Purpose:** Ensure code follows project style guidelines

**Command:**
```bash
pylint src/mcp_coder/utils/github_operations/issues/branch_manager.py
pylint src/mcp_coder/cli/commands/coordinator/core.py
```

**Expected Score:** ≥9.0/10 (project standard)

**Common Issues to Fix:**
- Line too long (max 88 characters, enforced by black)
- Missing docstrings
- Unused variables
- Too many local variables

---

## HOW: Using MCP Code Checker Tools

### Preferred Method: MCP Tools
```python
# Run all checks in one command
mcp__code-checker__run_all_checks(
    target_directories=["src", "tests"],
    categories=["error", "fatal", "warning"],
    verbosity=2,
    extra_args=["-n", "auto"]  # Parallel execution
)

# Or run individually:

# 1. pytest
mcp__code-checker__run_pytest_check(
    extra_args=["tests/utils/github_operations/issues/test_branch_resolution.py", "-v"],
    verbosity=2
)

# 2. mypy
mcp__code-checker__run_mypy_check(
    strict=True,
    target_directories=["src"]
)

# 3. pylint
mcp__code-checker__run_pylint_check(
    categories=["error", "fatal", "warning"],
    target_directories=["src"]
)
```

---

## ALGORITHM: Quality Check Process

```
# Step 1: Run new test suite
execute: pytest test_branch_resolution.py -v
if failures:
    analyze_failures()
    fix_implementation()
    re_run_tests()

# Step 2: Run regression tests
execute: pytest existing_tests -v
if failures:
    analyze_regressions()
    fix_breaking_changes()
    re_run_tests()

# Step 3: Type checking
execute: mypy branch_manager.py core.py
if errors:
    add_type_annotations()
    fix_type_errors()
    re_run_mypy()

# Step 4: Code quality
execute: pylint branch_manager.py core.py
if score < 9.0:
    fix_linting_issues()
    re_run_pylint()

# Step 5: Full integration test
execute: run_all_checks()
if all_pass:
    mark_complete()
```

---

## DATA: Expected Results

### Test Coverage Summary
| Test Category | Count | Status |
|--------------|-------|--------|
| New tests (branch_resolution.py) | 8 | ✅ All pass |
| Existing branch_manager tests | ~30 | ✅ No regressions |
| Existing coordinator tests | ~10 | ✅ No regressions |
| **Total** | **~48** | **✅ All pass** |

### Code Quality Metrics
| Check | Target | Expected |
|-------|--------|----------|
| pytest | 100% pass | ✅ 48/48 |
| mypy | No errors | ✅ Success |
| pylint | ≥9.0/10 | ✅ 9.5+/10 |

### Files Modified Summary
| File | Lines Added | Lines Modified | Lines Deleted |
|------|-------------|----------------|---------------|
| branch_manager.py | ~100 | 0 | 0 |
| core.py | ~5 | ~15 | ~8 |
| test_branch_resolution.py (new) | ~350 | 0 | 0 |
| **Total** | **~455** | **~15** | **~8** |

---

## Common Issues and Fixes

### Issue 1: Import Order (pylint)
**Error:** `wrong-import-order`
**Fix:** Organize imports in standard order:
```python
# Standard library
from typing import Optional

# Third-party
from github import Github

# Local
from ..base_manager import _handle_github_errors
```

### Issue 2: Line Too Long (pylint)
**Error:** `line-too-long`
**Fix:** Break long lines (max 88 chars for black compatibility):
```python
# Before
logger.error(f"No branch found for issue #{issue['number']} after checking linkedBranches and draft/open PRs")

# After
logger.error(
    f"No branch found for issue #{issue['number']} "
    f"after checking linkedBranches and draft/open PRs"
)
```

### Issue 3: Missing Type Annotations (mypy)
**Error:** `Function is missing a type annotation`
**Fix:** Add complete type annotations:
```python
# Before
def helper_function(data):
    return data.get("key")

# After
def helper_function(data: dict[str, Any]) -> Optional[str]:
    return data.get("key")
```

### Issue 4: Test Failures - Mock Not Called
**Error:** `AssertionError: Expected call not found`
**Fix:** Verify mock setup and call signatures:
```python
# Ensure mock is set up before test execution
mock_manager.get_linked_branches = Mock(return_value=[])

# Use exact call signature
branch_manager.get_branch_with_pr_fallback(
    issue_number=123,  # Use keyword args
    repo_owner="owner",
    repo_name="repo"
)
```

---

## LLM Prompt for Implementation

```
I need to complete Step 4 of the branch resolution feature - code quality verification.

CONTEXT:
- Read pr_info/steps/summary.md for full context
- Steps 1-3 implemented the feature
- Now we verify everything works and meets quality standards

TASK:
Run all code quality checks and fix any issues found

STEP-BY-STEP PROCESS:

1. Run new test suite:
   mcp__code-checker__run_pytest_check(
       extra_args=["tests/utils/github_operations/issues/test_branch_resolution.py", "-v"],
       verbosity=2,
       show_details=True
   )
   
   Expected: All 8 tests pass
   If failures: Analyze and fix implementation

2. Run regression tests:
   mcp__code-checker__run_pytest_check(
       extra_args=[
           "tests/utils/github_operations/",
           "-v",
           "-m", "not github_integration"
       ],
       verbosity=2
   )
   
   Expected: All existing tests still pass
   If failures: Fix breaking changes

3. Run mypy type checking:
   mcp__code-checker__run_mypy_check(
       strict=True,
       target_directories=["src"]
   )
   
   Expected: No type errors
   If errors: Add type annotations, fix type issues

4. Run pylint code quality:
   mcp__code-checker__run_pylint_check(
       categories=["error", "fatal", "warning"],
       target_directories=["src"]
   )
   
   Expected: Score ≥9.0/10
   If issues: Fix linting problems (imports, line length, etc.)

5. Final verification - run all checks:
   mcp__code-checker__run_all_checks(
       target_directories=["src", "tests"],
       categories=["error", "fatal", "warning"],
       verbosity=2
   )
   
   Expected: All checks pass

COMMON FIXES:
- Import order: Follow standard library → third-party → local
- Line length: Max 88 characters (use string continuation)
- Type annotations: Add Optional, List, Dict types where needed
- Docstrings: Ensure all public methods have docstrings

DELIVERABLE:
- All quality checks passing
- No test failures
- No type errors
- pylint score ≥9.0/10
- Summary of any fixes made
```

---

## Expected Outcome

### Success Criteria
- ✅ All 8 new tests pass
- ✅ All existing tests pass (no regressions)
- ✅ mypy reports no type errors
- ✅ pylint score ≥9.0/10 for all modified files
- ✅ No warnings in test output
- ✅ Code follows project conventions

### Final Verification Checklist
- [ ] New test file runs successfully
- [ ] Existing branch_manager tests pass
- [ ] Existing coordinator tests pass
- [ ] Type checking passes (mypy)
- [ ] Code quality passes (pylint)
- [ ] No import errors
- [ ] No runtime errors in tests
- [ ] All acceptance criteria from issue #219 met

### Summary Report Format
```
Feature: Branch Resolution with PR Fallback (Issue #219)

Implementation Complete ✅

Files Modified:
- src/mcp_coder/utils/github_operations/issues/branch_manager.py (+100 lines)
- src/mcp_coder/cli/commands/coordinator/core.py (+5, ~15 modified)
- tests/utils/github_operations/issues/test_branch_resolution.py (+350 lines, new)

Quality Checks:
- pytest: 48/48 tests passing ✅
- mypy: No type errors ✅
- pylint: 9.5/10 average ✅

Test Coverage:
- New functionality: 8 tests, all scenarios covered
- Regression tests: All passing
- Integration: Coordinator workflow verified

Performance:
- Primary path (linkedBranches): <100ms
- Fallback path (PR timeline): ~500ms
- No performance regressions

Ready for Review ✅
```

---

## Post-Implementation Notes

### Documentation Updates Needed
None required - implementation is self-contained within existing architecture.

### Future Enhancements (Out of Scope)
- Cache PR timeline queries for performance
- Support for closed PRs (currently only draft/open)
- Metrics tracking for resolution source (linkedBranches vs PR)

### Rollback Procedure
If critical issues found:
1. Revert coordinator changes (restore old code)
2. Keep new method in branch_manager (no harm, not used)
3. Archive test file for future use

---

**Implementation Complete!** 🎉
