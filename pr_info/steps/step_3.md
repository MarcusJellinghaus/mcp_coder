# Step 3: Run Quality Checks and Verify (TDD - Refactor Phase)

## Context
After implementing the fix (Green phase), verify code quality and ensure no regressions (Refactor phase).

Refer to `pr_info/steps/summary.md` for overall architecture and design decisions.

## WHERE: Quality Check Scope
- **All Tests**: Run full test suite to catch regressions
- **Linting**: Check code style with pylint
- **Type Checking**: Verify type safety with mypy
- **Target Module**: `mcp_coder.workflows.create_pr`

## WHAT: Quality Checks to Run

### 1. Full Test Suite
**Purpose**: Ensure no regressions in other tests

### 2. Pylint Check
**Purpose**: Verify code style and conventions
**Target**: Modified files only

### 3. MyPy Check
**Purpose**: Verify type annotations are correct
**Target**: Modified files only

## HOW: Execution Commands

### Full Test Suite
```bash
# Run all create_pr tests
pytest tests/workflows/create_pr/ -v

# Expected: All tests pass
```

### Pylint Check
```bash
# Check modified source file
pylint src/mcp_coder/workflows/create_pr/core.py

# Expected: No new errors (10/10 or existing baseline score)
```

### MyPy Check
```bash
# Check modified source file
mypy src/mcp_coder/workflows/create_pr/core.py

# Expected: Success: no issues found
```

### Optional: Full Project Checks
```bash
# Run all tests in the project
pytest tests/ -v

# Run pylint on entire project (if time permits)
pylint src/mcp_coder/

# Run mypy on entire project (if time permits)
mypy src/mcp_coder/
```

## ALGORITHM: Verification Process (Pseudocode)
```
1. Run all prerequisite tests → Verify all pass
2. Run all create_pr workflow tests → Verify no regressions
3. Run pylint on modified file → Verify no new issues
4. Run mypy on modified file → Verify type safety
5. If any check fails:
   - Review failure
   - Fix issue
   - Re-run checks
6. Document results
```

## DATA: Expected Results

### Test Results
```
tests/workflows/create_pr/test_prerequisites.py::TestCheckPrerequisites
  ✓ test_prerequisites_all_pass
  ✓ test_prerequisites_dirty_working_directory
  ✓ test_prerequisites_incomplete_tasks
  ✓ test_prerequisites_same_branch
  ✓ test_prerequisites_no_current_branch
  ✓ test_prerequisites_no_base_branch
  ✓ test_prerequisites_git_exception
  ✓ test_prerequisites_task_tracker_exception
  ✓ test_prerequisites_branch_exception
  ✓ test_prerequisites_missing_task_tracker (NEW)

All tests passed: 10/10
```

### Pylint Results
```
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```

### MyPy Results
```
Success: no issues found in 1 source file
```

## Common Issues and Solutions

### Issue 1: Import Order
**Problem**: Pylint complains about import order
**Solution**: Ensure `TaskTrackerFileNotFoundError` is in alphabetical order in the import

### Issue 2: Line Length
**Problem**: Pylint complains about line too long
**Solution**: Break the INFO message across multiple lines if needed

### Issue 3: Test Discovery
**Problem**: Pytest doesn't find the new test
**Solution**: Verify test method name starts with `test_` and is in the correct class

## LLM Prompt for Implementation

```
I need to implement Step 3 of the plan in pr_info/steps/step_3.md.

Please:
1. Read pr_info/steps/summary.md for overall context
2. Read pr_info/steps/step_3.md for detailed requirements
3. Run the full test suite for create_pr workflow:
   pytest tests/workflows/create_pr/ -v
4. Run pylint on the modified file:
   pylint src/mcp_coder/workflows/create_pr/core.py
5. Run mypy on the modified file:
   mypy src/mcp_coder/workflows/create_pr/core.py
6. Document the results
7. Fix any issues that arise

All checks should pass cleanly.
```

## Success Criteria
- ✅ All 10 prerequisite tests pass (including new test)
- ✅ All create_pr workflow tests pass
- ✅ Pylint reports no new errors
- ✅ MyPy reports no type errors
- ✅ No regressions in other tests
- ✅ Code follows project conventions

## Verification Checklist

- [ ] New test `test_prerequisites_missing_task_tracker` passes
- [ ] Existing test `test_prerequisites_task_tracker_exception` still passes
- [ ] All other prerequisite tests pass
- [ ] No pylint errors in modified files
- [ ] No mypy errors in modified files
- [ ] Import statement follows conventions
- [ ] Exception handling follows existing pattern
- [ ] Log messages use correct severity levels

## Documentation of Results

After running checks, document:
1. Test pass/fail counts
2. Pylint score
3. MyPy status
4. Any issues found and fixed
5. Final verification that all acceptance criteria are met

## Next Steps
After all checks pass:
1. Review changes one final time
2. Commit changes with appropriate message
3. Create pull request
4. Reference issue #486 in PR description
