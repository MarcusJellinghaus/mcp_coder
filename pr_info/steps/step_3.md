# Step 3: Run Full Code Quality Checks and Verification

## Context
This step runs comprehensive code quality checks to ensure the implementation is correct, maintainable, and follows project standards. This is the **TDD verification phase** plus quality assurance.

**Reference:** See `pr_info/steps/summary.md` for full architectural context.

## WHERE: Test Execution
- **Test directory**: `tests/`
- **Source modules**: `src/mcp_coder/llm/env.py`
- **Test module**: `tests/llm/test_env.py`

## WHAT: Quality Checks to Run

### 1. Pytest - All Unit Tests
**Purpose:** Verify all tests pass (Step 1 tests + existing tests)

**Command:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
```

**Expected Result:** 
- ✅ All new tests from Step 1 pass
- ✅ All existing tests pass
- ✅ No regressions in other modules
- ✅ 100% test success rate

### 2. Pylint - Code Quality Analysis
**Purpose:** Check code style, potential bugs, and maintainability

**Command:**
```python
mcp__code-checker__run_pylint_check(
    target_directories=["src", "tests"]
)
```

**Expected Result:**
- ✅ No errors in `src/mcp_coder/llm/env.py`
- ✅ No errors in `tests/llm/test_env.py`
- ✅ Code follows project style guidelines
- ✅ No unused imports or variables

### 3. Mypy - Static Type Checking
**Purpose:** Verify type annotations are correct

**Command:**
```python
mcp__code-checker__run_mypy_check(
    target_directories=["src", "tests"]
)
```

**Expected Result:**
- ✅ No type errors in `env.py`
- ✅ Return type `dict[str, str]` is correct
- ✅ Path type handling is correct
- ✅ No type mismatches

## HOW: Execution Sequence

### Step-by-Step Process

```
1. Run pytest (fast unit tests only)
   → Verify Step 1 tests pass
   → Verify no regressions

2. If pytest passes:
   → Run pylint
   → Fix any style issues
   
3. If pylint passes:
   → Run mypy
   → Fix any type issues
   
4. If all checks pass:
   → Step 3 complete ✅
   
5. If any check fails:
   → Review errors
   → Fix issues in env.py or test_env.py
   → Re-run checks
   → Repeat until all pass
```

## ALGORITHM: Verification Logic

```
FOR each quality check (pytest, pylint, mypy):
    run_check()
    IF check fails:
        log_errors()
        fix_issues()
        re_run_check()
    END IF
END FOR

IF all checks pass:
    verification_complete = True
END IF
```

## DATA: Success Criteria

### Pytest Success
```
Expected pattern in output:
- "X passed" where X = total test count
- No "failed" or "error" entries
- Test coverage includes:
  ✓ test_prepare_llm_environment_uses_virtual_env_variable
  ✓ test_prepare_llm_environment_uses_conda_prefix
  ✓ test_prepare_llm_environment_uses_sys_prefix_fallback
  ✓ test_prepare_llm_environment_separate_runner_project
  ✓ test_prepare_llm_environment_success (updated)
  ✓ All other existing tests in test_env.py
```

### Pylint Success
```
Expected output:
"Your code has been rated at 10.00/10"

OR acceptable warnings only:
- No errors (E)
- No fatal (F)
- Warnings (W) that are project-standard exceptions
```

### Mypy Success
```
Expected output:
"Success: no issues found in X source files"

Type annotations verified:
- prepare_llm_environment(project_dir: Path) -> dict[str, str]
- Path types handled correctly
- os.environ type handling correct
```

## Specific Test Cases to Verify

### Core Functionality Tests
1. **Virtual environment detection**
   - VIRTUAL_ENV set → uses that path
   - Path is absolute and OS-native

2. **Conda environment detection**
   - VIRTUAL_ENV not set, CONDA_PREFIX set → uses conda path
   - Correct fallback behavior

3. **System Python fallback**
   - No environment variables → uses sys.prefix
   - Always succeeds (no RuntimeError)

4. **Separate directories**
   - Runner at `/runner/.venv`
   - Project at `/project`
   - MCP_CODER_VENV_DIR points to runner
   - MCP_CODER_PROJECT_DIR points to project
   - Paths are independent (not relative to each other)

5. **Backward compatibility**
   - Co-located runner and project still works
   - Existing workflows unaffected

### Edge Cases
1. **Path resolution**
   - Relative paths converted to absolute
   - Windows paths use backslashes
   - Unix paths use forward slashes

2. **Empty/None handling**
   - Empty VIRTUAL_ENV falls back correctly
   - None values handled gracefully

## Common Issues and Fixes

### Issue 1: Unused Import
```python
# Pylint error: "Unused import 'detect_python_environment'"

Fix: Remove the import from env.py
from ..utils.detection import detect_python_environment  # ❌ Delete this line
```

### Issue 2: Missing os Import
```python
# NameError: name 'os' is not defined

Fix: Ensure os is imported
import os  # ✅ Add if missing
```

### Issue 3: Type Annotation Mismatch
```python
# Mypy error: "Incompatible return value type"

Fix: Ensure return type matches
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:  # ✅ Correct type
```

### Issue 4: Test Mock Not Working
```python
# Test fails: VIRTUAL_ENV not being used

Fix: Use patch.dict correctly
with patch.dict(os.environ, {"VIRTUAL_ENV": str(venv_dir)}):  # ✅ Correct
    result = prepare_llm_environment(project_dir)
```

## Expected Output Examples

### Successful Pytest Run
```
============================= test session starts ==============================
platform win32 -- Python 3.11.x
collected 45 items

tests/llm/test_env.py::test_prepare_llm_environment_uses_virtual_env_variable PASSED [2%]
tests/llm/test_env.py::test_prepare_llm_environment_uses_conda_prefix PASSED [4%]
tests/llm/test_env.py::test_prepare_llm_environment_uses_sys_prefix_fallback PASSED [6%]
tests/llm/test_env.py::test_prepare_llm_environment_separate_runner_project PASSED [8%]
tests/llm/test_env.py::test_prepare_llm_environment_success PASSED [11%]
...
============================== 45 passed in 2.34s ===============================
```

### Successful Pylint Run
```
--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```

### Successful Mypy Run
```
Success: no issues found in 157 source files
```

## Manual Verification (Optional)

### Test with Real Environment
```python
# Set VIRTUAL_ENV to a test path
import os
os.environ["VIRTUAL_ENV"] = "C:\\test\\runner\\.venv"

# Run the function
from pathlib import Path
from mcp_coder.llm.env import prepare_llm_environment

result = prepare_llm_environment(Path("C:\\test\\project"))

# Verify output
print(result)
# Expected:
# {
#     'MCP_CODER_PROJECT_DIR': 'C:\\test\\project',
#     'MCP_CODER_VENV_DIR': 'C:\\test\\runner\\.venv'
# }
```

## LLM Prompt for Implementation

```
Implement Step 3 from pr_info/steps/step_3.md with reference to pr_info/steps/summary.md.

Run all code quality checks in sequence:

1. Run pytest with fast unit tests:
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
   )

2. If pytest passes, run pylint:
   mcp__code-checker__run_pylint_check(
       target_directories=["src", "tests"]
   )

3. If pylint passes, run mypy:
   mcp__code-checker__run_mypy_check(
       target_directories=["src", "tests"]
   )

4. If any check fails:
   - Read the error output carefully
   - Identify the issue (unused import, type error, test failure)
   - Use mcp__filesystem__read_file to examine the problematic file
   - Use mcp__filesystem__edit_file to fix the issue
   - Re-run the failing check

5. Report results:
   - Confirm all checks pass ✅
   - Or report specific errors that need attention

Use MCP tools exclusively for all operations.
```

## Success Criteria Checklist

- [ ] Pytest: All tests pass (no failures, no errors)
- [ ] Pylint: Code rated 10.00/10 or acceptable warnings only
- [ ] Mypy: No type errors found
- [ ] No unused imports in env.py
- [ ] No regressions in other modules
- [ ] All Step 1 tests pass
- [ ] All existing tests still pass
- [ ] Code follows project style guidelines

When all items are checked, Step 3 is complete!
