# Step 3: Final Verification and Cleanup

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md for context on Issue #285.
Implement Step 3: Final verification that all tests pass and prompt_manager.py works correctly.

Requirements:
- Run all data_files tests using MCP tools
- Run prompt_manager tests (caller that was updated)
- Verify pytest-xdist parallel execution works (the original issue)
- Clean up any unused imports in data_files.py
- Run mypy type checking
```

## WHERE: Verification Targets

| File | Verification Type |
|------|-------------------|
| `tests/utils/test_data_files.py` | Run all tests |
| `tests/test_prompt_manager.py` | Run all tests (compatibility check) |
| `src/mcp_coder/utils/data_files.py` | Code review for unused imports |

## WHAT: Verification Commands (using MCP tools per CLAUDE.md)

### 1. Run Data Files Tests
```python
mcp__code-checker__run_pytest_check(
    extra_args=["tests/utils/test_data_files.py", "-v", "-n", "auto"]
)
```

### 2. Run Prompt Manager Tests
```python
mcp__code-checker__run_pytest_check(
    extra_args=["tests/test_prompt_manager.py", "-v", "-n", "auto"]
)
```

### 3. Run with pytest-xdist (Original Issue - Critical Test)
```python
mcp__code-checker__run_pytest_check(
    extra_args=["tests/utils/test_data_files.py", "-v", "-n", "auto"]
)
# This must pass without flaky failures - that was the original issue
```

### 4. Run Mypy Type Checking
```python
mcp__code-checker__run_mypy_check(
    target_directories=["src/mcp_coder/utils"]
)
```

### 5. Run Full Unit Test Suite
```python
mcp__code-checker__run_pytest_check(
    extra_args=[
        "-n", "auto",
        "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"
    ]
)
```

## HOW: Cleanup Checklist

### Unused Imports to Remove from data_files.py

After refactoring, these imports should no longer be needed:

```python
# REMOVE:
import importlib.util  # Replaced by importlib.resources
import site            # No longer searching site-packages manually
import os              # No longer needed (was for os.name check in venv search)
import sys             # No longer manipulating sys.path
```

### Imports to Keep

```python
import logging
from importlib.resources import files
from pathlib import Path
from typing import List  # For find_package_data_files
# Note: Optional removed - no longer needed after removing development_base_dir parameter
```

## ALGORITHM: Verification Steps

```python
# 1. Run mcp__code-checker__run_pytest_check for data_files tests
#    - All tests should pass
#    - No sys.path manipulation warnings

# 2. Run mcp__code-checker__run_pytest_check for prompt_manager tests
#    - All tests should pass
#    - Confirms find_data_file returns compatible Path

# 3. Run mcp__code-checker__run_pytest_check with -n auto
#    - Tests should pass in parallel
#    - This was the original pytest-xdist issue

# 4. Run mcp__code-checker__run_mypy_check
#    - No type errors in modified files

# 5. Review data_files.py for unused imports
#    - Remove any imports no longer used
```

## DATA: Success Criteria

| Criterion | Status |
|-----------|--------|
| All `test_data_files.py` tests pass | [ ] |
| All `test_prompt_manager.py` tests pass | [ ] |
| Tests pass with `-n auto` (parallel) | [ ] |
| No unused imports in `data_files.py` | [ ] |
| No mypy type errors | [ ] |
| Code reduced from ~350 to ~50 lines | [ ] |

## Post-Implementation Notes

### If Tests Fail

1. **Import errors**: Check that `importlib.resources` is imported correctly
2. **Path issues**: Verify `files().joinpath()` returns a valid Traversable
3. **Parallel test failures**: Check for any remaining mocking that might conflict

### Documentation Updates (Required)

Update docstring in `find_data_file` to reflect:
- New implementation uses `importlib.resources`
- `development_base_dir` parameter has been removed
- Works automatically with editable installs
- Simpler API: just package_name and relative_path
