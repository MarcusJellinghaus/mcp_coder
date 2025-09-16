# Step 5: Verify Coverage and Remove Old Tests

## Objective
Verify that the new 30-test suite maintains adequate coverage of `git_operations.py`, run performance benchmarks, and safely remove the old test files to complete the simplification.

## WHERE
- Verify: `tests/utils/test_git_workflows.py` (20 tests)
- Verify: `tests/utils/test_git_error_cases.py` (10 tests)
- Remove: `tests/utils/test_git_operations.py` (300+ tests)
- Remove: `tests/utils/test_git_operations_integration.py` (150+ tests)

## WHAT
### Coverage Verification
```python
# Target coverage metrics
line_coverage >= 95%      # of git_operations.py
branch_coverage >= 90%    # of git_operations.py
function_coverage == 100% # All 10 functions tested
```

### Performance Benchmarks
```python
# Target performance metrics  
total_test_time < 2_seconds    # vs 45s previously
individual_test_time < 100ms   # per test method
fixture_setup_time < 50ms      # per simplified fixture
```

### Cleanup Tasks
- Remove old test files with 450+ tests
- Update CI configuration if needed
- Update test documentation
- Verify no import dependencies remain

## HOW
### Coverage Analysis Steps
1. Run `pytest --cov=src/mcp_coder/utils/git_operations --cov-report=html`
2. Analyze coverage report for missed lines/branches
3. Add targeted tests if coverage gaps found
4. Verify all 10 functions have at least one test

### Performance Measurement
```python
# Time measurement command
pytest tests/utils/test_git_* --durations=0 -v

# Expected results
test_git_workflows.py::TestGitWorkflows::* < 100ms each
test_git_error_cases.py::TestGitErrorCases::* < 50ms each
```

## ALGORITHM
```
1. Run new test suite and measure execution time
2. Generate coverage report for git_operations.py
3. Identify any coverage gaps and add minimal tests if needed
4. Verify all integration scenarios work correctly
5. Backup old test files (optional safety step)
6. Remove old test files and verify no import errors
```

## DATA
### Expected Coverage Results
```python
# Functions that must be covered
covered_functions = [
    "is_git_repository",
    "is_file_tracked", 
    "get_staged_changes",
    "get_unstaged_changes",
    "get_full_status",
    "stage_specific_files",
    "stage_all_changes", 
    "commit_staged_files",
    "commit_all_changes",
    "git_move"
]

# Coverage gaps to watch for
potential_gaps = [
    "Error handling branches",
    "Platform-specific code paths",
    "Edge case validation logic"
]
```

### Performance Comparison
```python
# Before vs After metrics
before = {
    "test_count": 450,
    "execution_time": "45 seconds",
    "mock_percentage": "80%",
    "files": 2
}

after = {
    "test_count": 30, 
    "execution_time": "<2 seconds",
    "mock_percentage": "0%",
    "files": 2
}
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and completed steps 1-5, implement Step 6 to verify coverage, measure performance, and clean up old tests.

Tasks to complete:

1. **Run Coverage Analysis**:
   - Execute: `pytest --cov=src/mcp_coder/utils/git_operations --cov-report=html tests/utils/test_git_*`
   - Verify line coverage >= 95% and branch coverage >= 90%
   - Check that all 10 functions in git_operations.py are covered
   - Identify any coverage gaps

2. **Measure Performance**:
   - Run: `pytest tests/utils/test_git_* --durations=0 -v`
   - Verify total execution time < 2 seconds
   - Check individual test times are reasonable
   - Compare against old test suite if possible

3. **Add Missing Coverage** (if needed):
   - Add minimal tests for any uncovered lines/branches
   - Focus on error paths or edge cases not covered
   - Keep additions minimal - don't recreate old test bloat

4. **Clean Up Old Tests**:
   - Backup old files if desired: `mv tests/utils/test_git_operations*.py /tmp/`
   - Remove old test files
   - Verify no import errors: `pytest --collect-only tests/`
   - Update any CI configurations that reference old test files

5. **Final Verification**:
   - Run full test suite: `pytest tests/utils/test_git_*`
   - Verify all 30 tests pass
   - Check coverage report shows good coverage
   - Confirm fast execution time

Create a summary report showing:
- Coverage percentages achieved
- Performance improvements (before/after)
- Test count reduction (450 → 30)
- Any remaining gaps or recommendations

Example verification script:
```python
import subprocess
import time

def verify_test_suite():
    \"\"\"Verify new test suite meets requirements.\"\"\"
    
    print("Running new test suite...")
    start_time = time.time()
    
    # Run tests with coverage
    result = subprocess.run([
        "pytest", 
        "--cov=src/mcp_coder/utils/git_operations",
        "--cov-report=term-missing",
        "tests/utils/test_git_*"
    ], capture_output=True, text=True)
    
    execution_time = time.time() - start_time
    
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    if "FAILED" in result.stdout:
        print("❌ Some tests failed")
        print(result.stdout)
    else:
        print("✅ All tests passed")
    
    # Extract coverage percentage
    for line in result.stdout.split('\\n'):
        if 'git_operations.py' in line:
            print(f"Coverage: {line}")
    
    return result.returncode == 0

if __name__ == "__main__":
    verify_test_suite()
```

Focus on ensuring the simplified test suite provides equivalent confidence with dramatically reduced complexity.
```

## Verification Checklist
- [ ] Coverage report shows ≥95% line coverage of git_operations.py
- [ ] All 10 functions have test coverage
- [ ] Total test execution time <2 seconds  
- [ ] All 30 new tests pass consistently
- [ ] Old test files (450+ tests) successfully removed
- [ ] No import errors or broken dependencies
- [ ] CI/test configuration updated if needed
- [ ] Documentation reflects new test structure

## Success Criteria
- **Coverage maintained**: ≥95% line coverage preserved
- **Performance improved**: 95% reduction in test execution time
- **Complexity reduced**: 93% reduction in test count (450→30)
- **Confidence maintained**: All git workflows still tested
- **Maintainability improved**: Zero mocking, simplified fixtures, focused integration tests
