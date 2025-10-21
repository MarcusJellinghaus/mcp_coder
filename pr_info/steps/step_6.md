# Step 6: Run Comprehensive Code Quality Checks

## Objective

Verify all code changes pass quality checks (pylint, pytest, mypy) before proceeding to cleanup. This ensures the migration maintains code quality and all functionality works correctly.

## Reference

Review `summary.md` for the full context and `.claude/CLAUDE.md` for mandatory code quality requirements.

## WHERE: File Paths

### Directories to Check
- `src/mcp_coder/cli/commands/` - New CLI command handler
- `src/mcp_coder/workflows/` - Migrated workflow module
- `tests/cli/commands/` - New CLI tests
- `tests/workflows/create_plan/` - Updated workflow tests

## WHAT: Quality Checks Required

### 1. Pylint - Code Quality and Style
Check for:
- Code style violations
- Potential bugs
- Unused imports
- Undefined variables

### 2. Pytest - All Tests Passing
Verify:
- All existing tests still pass
- New CLI tests pass
- No regressions introduced

### 3. Mypy - Type Checking
Check for:
- Type annotation correctness
- Type consistency
- Return type accuracy

## HOW: Execution Steps

### Check Execution Order

**Run checks in this order for fastest feedback:**

1. **Pylint First** (catches syntax errors, import issues)
2. **Mypy Second** (catches type errors)
3. **Pytest Last** (most comprehensive, slowest)

### Check Configuration

All checks use default configurations from `pyproject.toml`:
- Pylint: Checks for errors and fatal issues
- Pytest: Runs all tests with parallel execution
- Mypy: Strict type checking enabled

## ALGORITHM: Quality Check Process

```python
# 1. Run Pylint on affected modules
pylint_result = run_pylint_check(
    categories=["error", "fatal"],
    target_directories=["src", "tests"]
)
if not pylint_result.success:
    # Fix errors before continuing
    return

# 2. Run Mypy on affected modules
mypy_result = run_mypy_check(
    strict=True,
    target_directories=["src", "tests"]
)
if not mypy_result.success:
    # Fix type errors before continuing
    return

# 3. Run all tests (excluding slow integration tests)
pytest_result = run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration ..."]
)
if not pytest_result.success:
    # Fix failing tests
    return

# All checks passed!
```

## DATA: Expected Results

### Pylint Results
```
Expected: No errors or fatal issues
Score: 10.00/10 or close to it

If issues found:
- Review each error
- Fix or justify (add pylint: disable comment with explanation)
```

### Mypy Results
```
Expected: Success: no issues found in X files

If issues found:
- Add missing type hints
- Fix type inconsistencies
- Use proper typing constructs
```

### Pytest Results
```
Expected: All tests pass
Format: ===== X passed in Y.XXs =====

Test categories:
- tests/cli/commands/test_create_plan.py: 7 tests
- tests/workflows/create_plan/: ~33 tests
- Total new/modified: ~40 tests

If failures:
- Review failure output
- Fix broken tests or code
- Ensure mocks are correctly configured
```

## Implementation Details

### Step 1: Run Pylint

```bash
# Check all affected code
mcp__code-checker__run_pylint_check(
    categories=["error", "fatal"],
    target_directories=["src", "tests"]
)
```

**Expected Output:**
```
--------------------------------------------------------------------
Your code has been rated at 10.00/10

✓ Pylint check passed
```

**Common Issues and Fixes:**
- **Import errors:** Check import paths are correct
- **Undefined variables:** Verify variable names match
- **Unused imports:** Remove or use imported modules

### Step 2: Run Mypy

```bash
# Check type consistency
mcp__code-checker__run_mypy_check(
    strict=True,
    target_directories=["src", "tests"]
)
```

**Expected Output:**
```
Success: no issues found in X source files

✓ Mypy check passed
```

**Common Issues and Fixes:**
- **Missing return type:** Add `-> int` or `-> None` to functions
- **Type mismatch:** Ensure types align (e.g., `Path` vs `str`)
- **Optional handling:** Use proper `Optional[T]` types

### Step 3: Run Pytest (Fast Unit Tests)

```bash
# Run fast unit tests (exclude slow integration tests)
mcp__code-checker__run_pytest_check(
    extra_args=[
        "-n", "auto",
        "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"
    ]
)
```

**Expected Output:**
```
===== X passed in Y.XXs =====

✓ All tests passed
```

**Common Issues and Fixes:**
- **Import errors:** Check module paths
- **Mock configuration:** Verify patch paths match actual module structure
- **Test assertions:** Ensure expected values match actual behavior

### Step 4: Run Pytest (Specific Test Files)

If full test suite is slow, run specific test files:

```bash
# Test only create-plan related tests
mcp__code-checker__run_pytest_check(
    extra_args=[
        "-n", "auto",
        "-v",
        "tests/cli/commands/test_create_plan.py",
        "tests/workflows/create_plan/"
    ]
)
```

## Verification Checklist

After running all checks, verify:

- [ ] ✅ Pylint: No errors or fatal issues
- [ ] ✅ Mypy: No type errors
- [ ] ✅ Pytest: All tests pass
- [ ] ✅ No new test failures introduced
- [ ] ✅ Code coverage maintained or improved
- [ ] ✅ No regressions in existing functionality

## Troubleshooting Guide

### If Pylint Fails

**Import Errors:**
```python
# Error: Unable to import 'mcp_coder.workflows.create_plan'
# Fix: Check module path and __init__.py files exist
```

**Undefined Variables:**
```python
# Error: Undefined variable 'args'
# Fix: Check variable is defined before use
```

### If Mypy Fails

**Type Errors:**
```python
# Error: Incompatible return value type (got "None", expected "int")
# Fix: Ensure all code paths return correct type

def run_workflow(...) -> int:
    if error:
        return 1  # Ensure this is int, not None
    return 0
```

**Import Errors:**
```python
# Error: Cannot find implementation for 'mcp_coder.workflows.create_plan'
# Fix: Ensure module exists and is importable
```

### If Pytest Fails

**Import Errors:**
```python
# Error: ModuleNotFoundError: No module named 'workflows.create_plan'
# Fix: Update import path to 'mcp_coder.workflows.create_plan'
```

**Mock Path Errors:**
```python
# Error: Patch target not found
# Fix: Update patch path to match new module structure

# Wrong:
@patch("workflows.create_plan.function")

# Correct:
@patch("mcp_coder.workflows.create_plan.function")
```

**Assertion Errors:**
```python
# Error: AssertionError: assert 1 == 0
# Fix: Check return values match expected behavior
# Workflow should return 0 on success, 1 on error
```

## Success Criteria

**All checks must pass:**
- ✅ Pylint: Score ≥ 9.50/10, no errors
- ✅ Mypy: Success, no issues found
- ✅ Pytest: All tests pass, no failures

**If any check fails, fix issues before proceeding to Step 7.**

## Next Steps

Proceed to **Step 7** to delete old files and complete the migration.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_6.md.

Implement Step 6: Run Comprehensive Code Quality Checks

Requirements:
1. Run pylint on all affected code (src and tests)
2. Run mypy on all affected code
3. Run pytest on all tests (fast unit tests)
4. Fix any issues found before proceeding

Execute in this order:

1. Pylint check:
   mcp__code-checker__run_pylint_check(
       categories=["error", "fatal"],
       target_directories=["src", "tests"]
   )

2. Mypy check:
   mcp__code-checker__run_mypy_check(
       strict=True,
       target_directories=["src", "tests"]
   )

3. Pytest check:
   mcp__code-checker__run_pytest_check(
       extra_args=[
           "-n", "auto",
           "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"
       ]
   )

After running checks:
1. Report any failures or issues
2. Fix issues if found
3. Re-run checks until all pass
4. Confirm all quality checks pass before proceeding

IMPORTANT: All checks MUST pass before moving to Step 7.

Do not proceed to the next step yet - wait for confirmation.
```
